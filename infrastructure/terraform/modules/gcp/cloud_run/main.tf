resource "google_cloud_run_v2_service" "backend" {
  name     = "vytal-backend-${var.env}"
  location = var.region

  template {
    scaling {
      min_instance_count = 0
      max_instance_count = 3
    }

    containers {
      image = var.image

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }

      ports {
        container_port = 8000
      }

      # Variáveis de ambiente simples
      dynamic "env" {
        for_each = var.env_vars
        content {
          name  = env.key
          value = env.value
        }
      }

      # Variáveis sensíveis via Secret Manager
      dynamic "env" {
        for_each = var.secret_vars
        content {
          name = env.key
          value_source {
            secret_key_ref {
              secret  = env.value
              version = "latest"
            }
          }
        }
      }
    }
  }
}

# Acesso público (sem auth no nível do Cloud Run — auth é feita via JWT na API)
resource "google_cloud_run_v2_service_iam_member" "public" {
  name     = google_cloud_run_v2_service.backend.name
  location = var.region
  role     = "roles/run.invoker"
  member   = "allUsers"
}
