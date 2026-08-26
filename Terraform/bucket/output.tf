output "bucket_name" {
  description = "Migration GCS bucket name"
  value       = google_storage_bucket.migration.name
}

output "bucket_url" {
  description = "Migration GCS bucket URL"
  value       = google_storage_bucket.migration.url
}