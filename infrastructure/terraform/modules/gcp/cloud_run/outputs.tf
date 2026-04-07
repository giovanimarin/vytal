output "url" {
  description = "URL pública do Cloud Run"
  value       = google_cloud_run_v2_service.backend.uri
}
