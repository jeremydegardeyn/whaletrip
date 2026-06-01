variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "Primary GCP region"
  type        = string
  default     = "us-central1"
}

variable "bq_location" {
  description = "BigQuery dataset location"
  type        = string
  default     = "US"
}

variable "api_image" {
  description = "Container image for the API service"
  type        = string
  default     = "gcr.io/google-samples/hello-app:1.0"
}

variable "agents_image" {
  description = "Container image for the agents service"
  type        = string
  default     = "gcr.io/google-samples/hello-app:1.0"
}

variable "allowed_origins" {
  description = "Comma-separated CORS origins"
  type        = string
  default     = "https://whaletrip.datadinosaur.com"
}

variable "gemini_model" {
  description = "Gemini model ID"
  type        = string
  default     = "gemini-2.0-flash-001"
}
