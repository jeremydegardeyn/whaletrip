# WhaleTrip 🐋

Conversational AI travel planning platform for whale-watching experiences worldwide.

## Architecture

```
whaletrip/
├── terraform/          # GCP Infrastructure as Code
├── services/
│   ├── api/            # FastAPI backend (Cloud Run)
│   └── agents/         # Google ADK multi-agent system (Cloud Run)
├── frontend/           # Next.js + TypeScript (Firebase Hosting)
├── data/               # BigQuery SQL views & schemas
├── infra/              # NGINX, Docker Compose, startup scripts
├── cloudbuild/         # CI/CD pipelines
└── docs/               # Architecture & deployment docs
```

## Prerequisites

- Google Cloud project with billing enabled
- `gcloud` CLI authenticated
- Terraform >= 1.5
- Node.js 20+
- Python 3.11+
- Docker

## Quick Start

### 1. Configure environment

```bash
cp .env.example .env
# Edit .env with your GCP project ID and API keys
```

### 2. Provision GCP infrastructure

```bash
cd terraform
terraform init
terraform apply -var="project_id=YOUR_PROJECT_ID"
```

### 3. Deploy Option A — Cloud Run (recommended, $0)

```bash
gcloud builds submit --config cloudbuild/cloudbuild.yaml \
  --substitutions=_PROJECT_ID=YOUR_PROJECT_ID
```

### 4. Deploy Option B — Firebase Hosting (frontend only)

```bash
cd frontend
npm install && npm run build
firebase deploy --only hosting
```

### 5. Deploy Option C — GCE VM (Docker Compose)

```bash
# On the VM after running infra/scripts/startup.sh
docker compose up -d
```

## Data Source

Whale sighting data comes from the **GBIF public BigQuery dataset**:
`bigquery-public-data.gbif.occurrences` (Order: Cetacea)

Millions of validated cetacean observations globally. No ingestion pipeline needed — views are created on top of this public dataset.

## Cost Estimate

| Component | Monthly Cost |
|---|---|
| Cloud Run (API + Agents) | $0 (free tier) |
| BigQuery queries | $0 (free tier 1TB/mo) |
| Firebase Hosting | $0 (free tier) |
| Firestore sessions | $0 (free tier) |
| Gemini 1.5 Flash | ~$0.01–$2 at low traffic |
| Map tiles (CARTO/OSM) | $0 |
| **Total** | **~$0–$2/mo** |

Set `MAPS_PROVIDER=google` in `.env` to use Google Maps Platform ($200/mo free credit covers normal usage).

## Local Development

```bash
# API
cd services/api
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Agents
cd services/agents
pip install -r requirements.txt
python main.py

# Frontend
cd frontend
npm install
npm run dev
```

## Domain Setup

Point `whaletrip.datadinosaur.com` to your Cloud Run URL via DNS CNAME, or to your GCE VM IP via A record. See `docs/deployment.md` for full instructions.

## Environment Variables

See `.env.example` for all required variables.
