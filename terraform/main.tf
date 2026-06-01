terraform {
  required_version = ">= 1.5"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# ── Enable APIs ────────────────────────────────────────────────────────────────
resource "google_project_service" "services" {
  for_each = toset([
    "run.googleapis.com",
    "bigquery.googleapis.com",
    "firestore.googleapis.com",
    "secretmanager.googleapis.com",
    "artifactregistry.googleapis.com",
    "cloudbuild.googleapis.com",
    "logging.googleapis.com",
    "monitoring.googleapis.com",
    "aiplatform.googleapis.com",
    "cloudtrace.googleapis.com",
  ])
  service            = each.key
  disable_on_destroy = false
}

# ── Artifact Registry ──────────────────────────────────────────────────────────
resource "google_artifact_registry_repository" "whaletrip" {
  repository_id = "whaletrip"
  location      = var.region
  format        = "DOCKER"
  description   = "WhaleTrip container images"
  depends_on    = [google_project_service.services]
}

# ── Service Account ────────────────────────────────────────────────────────────
resource "google_service_account" "whaletrip" {
  account_id   = "whaletrip-sa"
  display_name = "WhaleTrip Service Account"
}

resource "google_project_iam_member" "whaletrip_bq_reader" {
  project = var.project_id
  role    = "roles/bigquery.dataViewer"
  member  = "serviceAccount:${google_service_account.whaletrip.email}"
}

resource "google_project_iam_member" "whaletrip_bq_job" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.whaletrip.email}"
}

resource "google_project_iam_member" "whaletrip_firestore" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.whaletrip.email}"
}

resource "google_project_iam_member" "whaletrip_secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.whaletrip.email}"
}

resource "google_project_iam_member" "whaletrip_aiplatform" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.whaletrip.email}"
}

resource "google_project_iam_member" "whaletrip_logging" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.whaletrip.email}"
}

# ── BigQuery Dataset ───────────────────────────────────────────────────────────
resource "google_bigquery_dataset" "whaletrip" {
  dataset_id    = "whaletrip"
  friendly_name = "WhaleTrip"
  description   = "Whale sighting views and materialized tables"
  location      = var.bq_location
  depends_on    = [google_project_service.services]
}

# ── Secrets ────────────────────────────────────────────────────────────────────
resource "google_secret_manager_secret" "api_secret_key" {
  secret_id = "whaletrip-api-secret-key"
  replication {
    auto {}
  }
  depends_on = [google_project_service.services]
}

# ── Cloud Run: API ─────────────────────────────────────────────────────────────
resource "google_cloud_run_v2_service" "api" {
  name     = "whaletrip-api"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = google_service_account.whaletrip.email

    scaling {
      min_instance_count = 0
      max_instance_count = 3
    }

    containers {
      image = var.api_image != "gcr.io/google-samples/hello-app:1.0" ? var.api_image : "us-docker.pkg.dev/cloudrun/container/hello:latest"

      resources {
        limits = { cpu = "1", memory = "512Mi" }
        cpu_idle = true
        startup_cpu_boost = true
      }

      env {
        name  = "GCP_PROJECT_ID"
        value = var.project_id
      }
      env {
        name  = "GCP_REGION"
        value = var.region
      }
      env {
        name  = "BQ_DATASET"
        value = "whaletrip"
      }
      env {
        name  = "AGENTS_URL"
        value = "https://whaletrip-agents-${var.region}-run.app"  # set after agents deploy
      }
      env {
        name  = "ALLOWED_ORIGINS"
        value = var.allowed_origins
      }
    }
  }

  depends_on = [google_project_service.services, google_artifact_registry_repository.whaletrip]
}

# ── Cloud Run: Agents ──────────────────────────────────────────────────────────
resource "google_cloud_run_v2_service" "agents" {
  name     = "whaletrip-agents"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = google_service_account.whaletrip.email

    scaling {
      min_instance_count = 0
      max_instance_count = 2
    }

    containers {
      image = var.agents_image != "gcr.io/google-samples/hello-app:1.0" ? var.agents_image : "us-docker.pkg.dev/cloudrun/container/hello:latest"

      resources {
        limits   = { cpu = "2", memory = "1Gi" }
        cpu_idle = true
        startup_cpu_boost = true
      }

      env {
        name  = "GCP_PROJECT_ID"
        value = var.project_id
      }
      env {
        name  = "VERTEX_AI_LOCATION"
        value = var.region
      }
      env {
        name  = "BQ_DATASET"
        value = "whaletrip"
      }
      env {
        name  = "GEMINI_MODEL"
        value = var.gemini_model
      }
    }
  }

  depends_on = [google_project_service.services, google_artifact_registry_repository.whaletrip]
}

# Public access to API (frontend calls it directly)
resource "google_cloud_run_v2_service_iam_member" "api_public" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.api.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Firestore database (native mode, required for session storage)
resource "google_firestore_database" "default" {
  project     = var.project_id
  name        = "(default)"
  location_id = "nam5"
  type        = "FIRESTORE_NATIVE"
  depends_on  = [google_project_service.services]

  lifecycle {
    prevent_destroy = true
    ignore_changes  = [location_id, type, concurrency_mode, app_engine_integration_mode]
  }
}
