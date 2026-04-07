resource "google_bigquery_dataset" "vytal" {
  dataset_id  = "vytal_${var.env}"
  description = "Vytal health analytics warehouse"
  location    = var.region

  delete_contents_on_destroy = false
}

locals {
  tables = {
    raw_google_fit_events = {
      description = "Eventos brutos do Google Fit"
      schema      = file("${path.module}/schemas/raw_google_fit_events.json")
    }
    normalized_sleep = {
      description = "Dados de sono normalizados"
      schema      = file("${path.module}/schemas/normalized_sleep.json")
    }
    normalized_steps = {
      description = "Dados de passos normalizados"
      schema      = file("${path.module}/schemas/normalized_steps.json")
    }
    normalized_heart_rate = {
      description = "Dados de frequência cardíaca normalizados"
      schema      = file("${path.module}/schemas/normalized_heart_rate.json")
    }
    normalized_activity = {
      description = "Dados de atividades normalizados"
      schema      = file("${path.module}/schemas/normalized_activity.json")
    }
    fact_daily_readiness = {
      description = "Daily Readiness Score calculado por dia"
      schema      = file("${path.module}/schemas/fact_daily_readiness.json")
    }
    dim_user = {
      description = "Dimensão de usuários"
      schema      = file("${path.module}/schemas/dim_user.json")
    }
  }
}

resource "google_bigquery_table" "tables" {
  for_each = local.tables

  dataset_id  = google_bigquery_dataset.vytal.dataset_id
  table_id    = each.key
  description = each.value.description
  schema      = each.value.schema

  time_partitioning {
    type  = "DAY"
    field = "date"
  }

  deletion_protection = true
}
