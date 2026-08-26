resource "google_service_account" "migration" {
  project      = var.project_id
  account_id   = "data-migration-sa"
  display_name = "Data Migration Service Account"
  description  = "Service account used by the data migration application"
}
resource "google_project_iam_member" "storage_admin" {
  project = var.project_id
  role    = "roles/storage.admin"
  member  = "serviceAccount:${google_service_account.migration.email}"
}

resource "google_project_iam_member" "bigquery_admin" {
  project = var.project_id
  role    = "roles/bigquery.admin"
  member  = "serviceAccount:${google_service_account.migration.email}"
}