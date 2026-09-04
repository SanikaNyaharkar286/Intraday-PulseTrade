output "bronze_table_id" {
  description = "Fully qualified Bronze table ID"
  value       = google_bigquery_table.intraday_master.id
}

output "audit_table_id" {
  description = "Fully qualified audit table ID"
  value       = google_bigquery_table.pipeline_audit.id
}
