resource "google_bigquery_dataset" "migration_bronze" {
  dataset_id = "migration_bronze"
  project    = var.project_id
  location   = var.region

  description = "Bronze layer for historical market data migration"
}

resource "google_bigquery_dataset" "migration_audit" {
  dataset_id = "migration_audit"
  project    = var.project_id
  location   = var.region

  description = "Audit metadata for historical market data migration"
}