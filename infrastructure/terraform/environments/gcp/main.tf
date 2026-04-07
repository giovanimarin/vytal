terraform {
  required_version = ">= 1.7"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }

  backend "gcs" {
    bucket = "vytal-terraform-state"
    prefix = "gcp/state"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# ── Módulos ──────────────────────────────────────────────────────────────────

module "storage" {
  source     = "../../modules/gcp/storage"
  project_id = var.project_id
  region     = var.region
  env        = var.env
}

module "bigquery" {
  source     = "../../modules/gcp/bigquery"
  project_id = var.project_id
  region     = var.region
  env        = var.env
}

module "pubsub" {
  source     = "../../modules/gcp/pubsub"
  project_id = var.project_id
  env        = var.env
}

module "cloud_run" {
  source     = "../../modules/gcp/cloud_run"
  project_id = var.project_id
  region     = var.region
  env        = var.env
  image      = var.backend_image

  env_vars = {
    ENVIRONMENT          = "production"
    CONFIG_PATH          = "/app/config.yaml"
    GOOGLE_REDIRECT_URI  = "https://${var.backend_domain}/api/v1/connect/google_fit/callback"
  }

  secret_vars = {
    GOOGLE_CLIENT_ID     = google_secret_manager_secret.google_client_id.secret_id
    GOOGLE_CLIENT_SECRET = google_secret_manager_secret.google_client_secret.secret_id
    SECRET_KEY           = google_secret_manager_secret.secret_key.secret_id
  }
}

# ── Secrets (Secret Manager) ─────────────────────────────────────────────────

resource "google_secret_manager_secret" "google_client_id" {
  secret_id = "vytal-google-client-id-${var.env}"
  replication { auto {} }
}

resource "google_secret_manager_secret" "google_client_secret" {
  secret_id = "vytal-google-client-secret-${var.env}"
  replication { auto {} }
}

resource "google_secret_manager_secret" "secret_key" {
  secret_id = "vytal-secret-key-${var.env}"
  replication { auto {} }
}
