resource "google_bigquery_dataset" "bronze" {
  dataset_id = var.bronze_dataset
  project    = var.project_id
  location   = var.bigquery_location
}

resource "google_bigquery_table" "intraday_master" {
  dataset_id          = google_bigquery_dataset.bronze.dataset_id
  table_id            = var.bronze_table
  project             = var.project_id
  deletion_protection = var.deletion_protection

  schema = jsonencode([
    {
      name = "timestamp"
      type = "TIMESTAMP"
      mode = "REQUIRED"
    },
    {
      name = "open"
      type = "FLOAT"
      mode = "NULLABLE"
    },
    {
      name = "high"
      type = "FLOAT"
      mode = "NULLABLE"
    },
    {
      name = "low"
      type = "FLOAT"
      mode = "NULLABLE"
    },
    {
      name = "close"
      type = "FLOAT"
      mode = "NULLABLE"
    },
    {
      name = "volume"
      type = "FLOAT"
      mode = "NULLABLE"
    },
    {
      name = "symbol"
      type = "STRING"
      mode = "REQUIRED"
    }
  ])
}

resource "google_bigquery_dataset" "audit" {
  dataset_id = var.audit_dataset
  project    = var.project_id
  location   = var.bigquery_location
}

resource "google_bigquery_table" "pipeline_audit" {
  dataset_id          = google_bigquery_dataset.audit.dataset_id
  table_id            = var.audit_table
  project             = var.project_id
  deletion_protection = var.deletion_protection

  schema = jsonencode([
    {
      name = "batch_id"
      type = "STRING"
      mode = "REQUIRED"
    },
    {
      name = "pipeline_type"
      type = "STRING"
      mode = "REQUIRED"
    },
    {
      name = "process_date"
      type = "TIMESTAMP"
      mode = "REQUIRED"
    },
    {
      name = "year"
      type = "INTEGER"
      mode = "NULLABLE"
    },
    {
      name = "month"
      type = "INTEGER"
      mode = "NULLABLE"
    },
    {
      name = "file_name"
      type = "STRING"
      mode = "NULLABLE"
    },
    {
      name = "status"
      type = "STRING"
      mode = "REQUIRED"
    },
    {
      name = "rows_processed"
      type = "INTEGER"
      mode = "NULLABLE"
    },
    {
      name = "message"
      type = "STRING"
      mode = "NULLABLE"
    }
  ])
}
