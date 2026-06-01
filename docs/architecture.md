# WhaleTrip Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                     whaletrip.datadinosaur.com                      │
│                    (Firebase Hosting / NGINX)                       │
│                                                                     │
│   ┌───────────────────────────────────────────────────────────┐    │
│   │             Next.js Frontend (TypeScript)                  │    │
│   │   ┌──────────────┐  ┌──────────┐  ┌────────────────────┐ │    │
│   │   │  MapLibre GL │  │  deck.gl │  │  ChatPanel (React) │ │    │
│   │   │  + CARTO     │  │  layers  │  │  + MessageBubble   │ │    │
│   │   └──────┬───────┘  └────┬─────┘  └────────┬───────────┘ │    │
│   └──────────┼───────────────┼─────────────────┼─────────────┘    │
└──────────────┼───────────────┼─────────────────┼───────────────────┘
               │               │                 │
               └───────────────┴────────┬────────┘
                                        │ HTTP REST
                        ┌───────────────▼──────────────────┐
                        │    FastAPI (Cloud Run)            │
                        │    whaletrip-api                  │
                        │  /sightings  /chat  /health       │
                        └───────┬──────────────┬────────────┘
                                │              │
              ┌─────────────────▼──┐    ┌──────▼─────────────────────┐
              │  BigQuery          │    │  ADK Agent Service          │
              │  (public GBIF data)│    │  (Cloud Run, internal)      │
              │                   │    │                             │
              │  whale_sightings   │    │  ┌──────────────────────┐  │
              │  seasonal_heatmap  │    │  │  CoordinatorAgent    │  │
              │  species_summary   │    │  │  ├─ WhaleIntelligence│  │
              └───────────────────┘    │  │  ├─ TravelPlanner    │  │
                                       │  │  ├─ TourRecommender  │  │
                        ┌──────────────┤  │  └─ DestinationAgent │  │
                        │  Vertex AI   │  └──────────────────────┘  │
                        │  Gemini 1.5  ◄──────────────────────────   │
                        │  Flash       │                             │
                        └──────────────┘  InMemorySessionService    │
                                          └─────────────────────────┘
```

## ADK Multi-Agent Architecture

```
User Message
     │
     ▼
CoordinatorAgent (gemini-1.5-flash)
     │  Reads conversation context
     │  Decides which specialist to call
     │
     ├──► WhaleIntelligenceAgent
     │       Tools: query_whale_sightings, get_species_seasonal_pattern,
     │              get_top_whale_destinations
     │       → Calls BigQuery GBIF views
     │
     ├──► TravelPlannerAgent
     │       Tools: search_flights, search_hotels, estimate_trip_budget
     │       → Calls flight/hotel providers (mock or real via adapters)
     │
     ├──► TourRecommendationAgent
     │       Tools: find_whale_watching_tours, get_tour_details
     │       → Queries operator database (mock or Viator API)
     │
     └──► DestinationAgent
             Tools: get_destination_info, compare_destinations
             → Returns curated destination knowledge
```

## Data Flow

```
GBIF BigQuery Public Dataset
bigquery-public-data.gbif.occurrences
    (2B rows, Order=Cetacea filter → ~4M rows)
           │
           ▼
  whale_sightings VIEW
  (filtered, enriched with region/zone fields)
           │
           ├──► seasonal_heatmap TABLE  (pre-aggregated 1° grid, partitioned by month)
           │          → powers map heatmap + playback animation
           │
           └──► species_summary VIEW    (top species with peak months)
                       → powers filter dropdown + agent context
```

## Deployment Options

### Option A — Cloud Run (recommended, ~$0/mo)
- API: `us-central1-docker.pkg.dev/PROJECT/whaletrip/api:latest`
- Agents: same region, internal ingress
- Frontend: Firebase Hosting (free CDN)
- Scale-to-zero on Cloud Run keeps idle cost $0

### Option B — GCE VM (Docker Compose)
- Single e2-micro ($6/mo) or e2-small for production
- NGINX reverse proxy + Let's Encrypt TLS
- All services in docker-compose.yml
- Good for full control and local dev parity

### Option C — Cloud Run + Custom Domain
- Cloud Run domain mapping for `whaletrip.datadinosaur.com`
- Google manages TLS automatically
- DNS: CNAME → ghs.googlehosted.com

## Cost Breakdown

| Component | Free Tier | Expected Usage | Monthly Cost |
|---|---|---|---|
| Cloud Run (API) | 2M req, 360K GB-sec | ~50K req, low mem | $0 |
| Cloud Run (Agents) | same | ~5K req | $0 |
| BigQuery | 1TB queries/mo | ~5GB/mo | $0 |
| Firestore | 50K reads/day | ~1K reads/day | $0 |
| Vertex AI Gemini 2.5 Flash (coordinator) | None | 100 chats/mo ≈ 50K tokens | ~$0.01 |
| Vertex AI Gemini 2.0 Flash (sub-agents) | None | included above | ~$0.01 |
| Firebase Hosting | 10GB transfer | <1GB | $0 |
| Artifact Registry | 0.5GB | ~0.3GB | $0 |
| **Total** | | | **~$0.01** |

Heavy usage (1000 chats/mo, 1M tokens): ~$0.10/mo. Still nearly zero.
