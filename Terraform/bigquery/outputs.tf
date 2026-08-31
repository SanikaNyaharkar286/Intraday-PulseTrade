output "bronze_dataset_id" {
  description = "Bronze BigQuery dataset"
  value       = google_bigquery_dataset.migration_bronze.dataset_id
}

output "audit_dataset_id" {
  description = "Audit BigQuery dataset"
  value       = google_bigquery_dataset.migration_audit.dataset_id
}