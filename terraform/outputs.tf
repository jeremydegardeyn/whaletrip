output "api_url" {
  description = "Cloud Run API service URL"
  value       = google_cloud_run_v2_service.api.uri
}

output "agents_url" {
  description = "Cloud Run agents service URL"
  value       = google_cloud_run_v2_service.agents.uri
}

output "artifact_registry_url" {
  description = "Artifact Registry URL for Docker images"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/whaletrip"
}

output "service_account_email" {
  description = "WhaleTrip service account email"
  value       = google_service_account.whaletrip.email
}

output "bigquery_dataset" {
  description = "BigQuery dataset ID"
  value       = google_bigquery_dataset.whaletrip.dataset_id
}

output "dns_cname_instruction" {
  description = "DNS CNAME record to add for whtrp.datadinosaur.com"
  value       = "Add CNAME: whtrp.datadinosaur.com → ${trimprefix(google_cloud_run_v2_service.api.uri, "https://")}"
}
