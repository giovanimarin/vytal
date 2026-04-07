resource "google_pubsub_topic" "health_events" {
  name = "vytal-health-events-${var.env}"

  message_retention_duration = "86400s" # 24h
}

resource "google_pubsub_subscription" "health_events_pipeline" {
  name  = "vytal-health-events-pipeline-${var.env}"
  topic = google_pubsub_topic.health_events.name

  ack_deadline_seconds       = 60
  message_retention_duration = "86400s"

  dead_letter_policy {
    dead_letter_topic     = google_pubsub_topic.health_events_dlq.id
    max_delivery_attempts = 5
  }

  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "300s"
  }
}

resource "google_pubsub_topic" "health_events_dlq" {
  name = "vytal-health-events-dlq-${var.env}"
}

resource "google_pubsub_subscription" "health_events_dlq" {
  name  = "vytal-health-events-dlq-sub-${var.env}"
  topic = google_pubsub_topic.health_events_dlq.name

  ack_deadline_seconds = 60
}
