resource "google_bigquery_dataset" "bronze" {
  dataset_id = var.bronze_dataset_id
  project    = var.project_id
  location   = var.region

  description = "Bronze layer - raw and minimally processed migration data"
}

resource "google_bigquery_dataset" "silver" {
  dataset_id = var.silver_dataset_id
  project    = var.project_id
  location   = var.region

  description = "Silver layer - cleaned and standardized data"
}

resource "google_bigquery_dataset" "gold" {
  dataset_id = var.gold_dataset_id
  project    = var.project_id
  location   = var.region

  description = "Gold layer - analytics-ready business data"
}