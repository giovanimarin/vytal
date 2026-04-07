variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "us-central1"
}

variable "env" {
  description = "Environment name (staging | production)"
  type        = string
  default     = "staging"
}

variable "backend_image" {
  description = "Docker image URI no Artifact Registry (gcr.io/PROJECT/vytal-backend:TAG)"
  type        = string
}

variable "backend_domain" {
  description = "Domínio público do backend (usado no redirect URI do OAuth)"
  type        = string
}
