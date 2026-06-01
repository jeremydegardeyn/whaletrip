# Deployment Guide

## Prerequisites

```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
gcloud auth configure-docker us-central1-docker.pkg.dev
```

## Step 1 — Provision Infrastructure

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars: set project_id

terraform init
terraform plan
terraform apply
```

## Step 2 — Create BigQuery Views

```bash
PROJECT_ID=$(gcloud config get-value project)

# Replace YOUR_PROJECT_ID in all SQL files
for f in data/sql/**/*.sql; do
  sed -i "s/YOUR_PROJECT_ID/$PROJECT_ID/g" "$f"
done

# Run setup
bq query --use_legacy_sql=false < data/sql/setup.sql
bq query --use_legacy_sql=false < data/sql/views/whale_sightings.sql
bq query --use_legacy_sql=false < data/sql/views/species_summary.sql
bq query --use_legacy_sql=false < data/sql/materialized/seasonal_heatmap.sql
```

> Note: The `seasonal_heatmap` materialized table will scan ~4M rows from GBIF on first run.
> This is a one-time cost of ~$0.02 within your 1TB free tier.

## Step 3 — Build and Deploy (Cloud Run)

```bash
gcloud builds submit \
  --config cloudbuild/cloudbuild.yaml \
  --substitutions=_PROJECT_ID=$PROJECT_ID,_REGION=us-central1
```

## Step 4 — Configure DNS

After terraform apply, run:
```bash
terraform output dns_cname_instruction
```

Add the shown CNAME record to your DNS:
```
whaletrip.datadinosaur.com  CNAME  <cloud-run-url>.run.app
```

Or map to an A record if using GCE VM (get IP from `gcloud compute instances describe`).

## Step 5 — Deploy Frontend

```bash
cd frontend
cp .env.example .env.local
# Set NEXT_PUBLIC_API_URL to your Cloud Run API URL

npm install
npm run build

# Firebase Hosting
npm install -g firebase-tools
firebase login
firebase init hosting  # choose existing project, out dir = "out"
EXPORT_STATIC=true npm run build
firebase deploy --only hosting
```

## GCE VM Deployment (Option B)

```bash
# On the VM
git clone https://github.com/YOUR_ORG/whaletrip /opt/whaletrip
cd /opt/whaletrip
cp .env.example .env
# Edit .env

bash infra/scripts/setup-ssl.sh  # first time only
docker compose up -d
```

## Environment Variables Reference

| Variable | Required | Description |
|---|---|---|
| `GCP_PROJECT_ID` | Yes | Your GCP project ID |
| `GCP_REGION` | No | Default: us-central1 |
| `BQ_DATASET` | No | Default: whaletrip |
| `GEMINI_MODEL` | No | Default: gemini-1.5-flash-001 |
| `ALLOWED_ORIGINS` | Yes | Comma-separated frontend URLs |
| `API_SECRET_KEY` | Yes | Random secret for API |
| `GOOGLE_MAPS_API_KEY` | No | Only if using Google Maps |

## Scheduled BigQuery Refresh

The `seasonal_heatmap` table should be refreshed weekly. Set up Cloud Scheduler:

```bash
gcloud scheduler jobs create http whaletrip-heatmap-refresh \
  --schedule="0 2 * * 1" \
  --uri="https://bigquery.googleapis.com/bigquery/v2/projects/$PROJECT_ID/jobs" \
  --message-body='{"configuration":{"query":{"query":"..."}}}' \
  --oauth-service-account-email=whaletrip-sa@$PROJECT_ID.iam.gserviceaccount.com
```
