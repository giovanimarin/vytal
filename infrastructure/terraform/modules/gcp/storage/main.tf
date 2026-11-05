resource "google_storage_bucket" "raw" {
  name          = "vytal-raw-${var.project_id}-${var.env}"
  location      = var.region
  force_destroy = false

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition { age = 90 }
    action {
      type          = "SetStorageClass"
      storage_class = "NEARLINE"
    }
  }

  lifecycle_rule {
    condition { age = 365 }
    action {
      type          = "SetStorageClass"
      storage_class = "COLDLINE"
    }
  }

  uniform_bucket_level_access = true
}

resource "google_storage_bucket" "processed" {
  name          = "vytal-processed-${var.project_id}-${var.env}"
  location      = var.region
  force_destroy = false

  uniform_bucket_level_access = true
}
