# Deployment Guide

## Live URLs

| Service | URL |
|---------|-----|
| Frontend | https://whtrp.datadinosaur.com |
| API | https://whaletrip-api-fdkbl4wtua-uc.a.run.app |
| Agents | https://whaletrip-agents-fdkbl4wtua-uc.a.run.app |

---

## Prerequisites

```bash
gcloud auth login
gcloud config set project strongsville-city-schools
gcloud auth configure-docker us-central1-docker.pkg.dev
npm install -g firebase-tools
```

---

## Step 1 — Provision Infrastructure (Terraform)

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars: set project_id, region

terraform init
terraform plan
terraform apply
```

If Firestore already exists in the project, import it first:
```bash
terraform import google_firestore_database.default strongsville-city-schools/(default)
```

---

## Step 2 — Create BigQuery Views

```bash
PROJECT_ID=strongsville-city-schools

cmd /c "bq query --use_legacy_sql=false --project_id=$PROJECT_ID < data/sql/views/whale_sightings.sql"
cmd /c "bq query --use_legacy_sql=false --project_id=$PROJECT_ID < data/sql/views/species_summary.sql"
cmd /c "bq query --use_legacy_sql=false --project_id=$PROJECT_ID < data/sql/materialized/seasonal_heatmap.sql"
```

> The `seasonal_heatmap` table scans ~4M rows from GBIF on first run (~$0.02, within free tier).

---

## Step 3 — Build and Deploy (Cloud Build)

```bash
gcloud builds submit --config cloudbuild/cloudbuild.yaml --project strongsville-city-schools .
```

The build pipeline:
1. Builds `whaletrip/api` and `whaletrip/agents` Docker images in parallel
2. Pushes both to Artifact Registry (`us-central1-docker.pkg.dev`)
3. Deploys both to Cloud Run (us-central1), routes 100% traffic to latest revision

---

## Step 4 — Deploy Frontend

```bash
cd frontend

# Set production API URL
echo "NEXT_PUBLIC_API_URL=https://whaletrip-api-fdkbl4wtua-uc.a.run.app" > .env.local

npm install
EXPORT_STATIC=true npm run build
firebase deploy --only hosting:whtrp --project strongsville-city-schools
```

The frontend is served from Firebase Hosting site `whtrp` → https://whtrp.web.app  
Custom domain: https://whtrp.datadinosaur.com (CNAME → whtrp.web.app)

---

## Environment Variables Reference

### API Service (`whaletrip-api`)

| Variable | Value | Description |
|---|---|---|
| `GCP_PROJECT_ID` | `strongsville-city-schools` | GCP project |
| `GCP_REGION` | `us-central1` | GCP region |
| `BQ_DATASET` | `whaletrip` | BigQuery dataset name |
| `AGENTS_URL` | `https://whaletrip-agents-fdkbl4wtua-uc.a.run.app` | Agents service URL |
| `ALLOWED_ORIGINS` | `https://whtrp.datadinosaur.com,...` | CORS allowed origins |

### Agents Service (`whaletrip-agents`)

| Variable | Value | Description |
|---|---|---|
| `GCP_PROJECT_ID` | `strongsville-city-schools` | GCP project (required for Model Armor) |
| `GOOGLE_GENAI_USE_VERTEXAI` | `1` | Use Vertex AI auth instead of API key |
| `GOOGLE_CLOUD_PROJECT` | `strongsville-city-schools` | Vertex AI project |
| `GOOGLE_CLOUD_LOCATION` | `us-central1` | Vertex AI region |
| `COORDINATOR_MODEL` | `gemini-3-flash` | Model for coordinator agent |
| `AGENT_MODEL` | `gemini-3-flash` | Model for all specialist sub-agents |
| `MODEL_ARMOR_TEMPLATE` | `whaletrip-guardrails` | Model Armor template name |

---

## Upgrading Gemini Models

Models are configurable at runtime — no code change or rebuild required.

```bash
# Upgrade coordinator only
gcloud run services update whaletrip-agents \
  --region=us-central1 \
  --project=strongsville-city-schools \
  --update-env-vars COORDINATOR_MODEL=gemini-3.5-flash

# Upgrade all agents at once
gcloud run services update whaletrip-agents \
  --region=us-central1 \
  --project=strongsville-city-schools \
  --update-env-vars COORDINATOR_MODEL=gemini-3.5-flash,AGENT_MODEL=gemini-3.5-flash
```

Available Gemini Flash models on Vertex AI (as of June 2026):
- `gemini-3.5-flash` — latest, highest capability
- `gemini-3-flash` — current default, best balance of speed/cost
- `gemini-2.5-flash` — previous generation
- `gemini-2.0-flash` — stable fallback

---

## Model Armor

The `whaletrip-guardrails` template screens every prompt and response for:
- Hate speech (medium confidence and above)
- Harassment (medium confidence and above)
- Sexually explicit content (medium confidence and above)
- Dangerous content (high confidence only)
- Prompt injection / jailbreak attempts (low confidence — aggressive)
- Malicious URLs

Free tier: 5,000 requests/month (1 user message = 2 requests: prompt + response check).

To inspect or update the template:
```bash
# View current template
curl -s \
  "https://modelarmor.us-central1.rep.googleapis.com/v1/projects/strongsville-city-schools/locations/us-central1/templates/whaletrip-guardrails" \
  -H "Authorization: Bearer $(gcloud auth print-access-token)"
```

---

## Wiring Up Real Travel APIs (TODO)

The travel and tour tools use mock data by default. To enable real data:

### Amadeus (flights + hotels)
1. Sign up at https://developers.amadeus.com (free tier: 2,000 calls/month)
2. Implement `AmadeusFlightProvider` in `services/agents/agents/tools/travel_tools.py`
3. Add env vars to Cloud Run agents service:
   ```bash
   gcloud run services update whaletrip-agents --region=us-central1 \
     --update-env-vars AMADEUS_CLIENT_ID=xxx,AMADEUS_CLIENT_SECRET=xxx
   ```

### Viator (tour operators)
1. Apply at https://partnerresources.viator.com (commission-based, $0 cost)
2. Implement `ViatorProvider` in `services/agents/agents/tools/tour_tools.py`
3. Add env var: `VIATOR_API_KEY=xxx`

---

## Scheduled BigQuery Refresh

The `seasonal_heatmap` table should be refreshed weekly:

```bash
gcloud scheduler jobs create http whaletrip-heatmap-refresh \
  --schedule="0 2 * * 1" \
  --location=us-central1 \
  --project=strongsville-city-schools \
  --uri="https://bigquery.googleapis.com/bigquery/v2/projects/strongsville-city-schools/jobs" \
  --message-body='{"configuration":{"query":{"useLegacySql":false,"query":"CALL whaletrip.refresh_seasonal_heatmap()"}}}' \
  --oauth-service-account-email=whaletrip-sa@strongsville-city-schools.iam.gserviceaccount.com
```
