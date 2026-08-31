from google.cloud import bigquery


# ==========================================================
# BRONZE MARKET DATA SCHEMA
# ==========================================================

BRONZE_SCHEMA = [

    bigquery.SchemaField(
        "date",
        "DATETIME",
        mode="REQUIRED"
    ),

    bigquery.SchemaField(
        "open",
        "FLOAT64",
        mode="REQUIRED"
    ),

    bigquery.SchemaField(
        "high",
        "FLOAT64",
        mode="REQUIRED"
    ),

    bigquery.SchemaField(
        "low",
        "FLOAT64",
        mode="REQUIRED"
    ),

    bigquery.SchemaField(
        "close",
        "FLOAT64",
        mode="REQUIRED"
    ),

    bigquery.SchemaField(
        "volume",
        "FLOAT64",
        mode="REQUIRED"
    ),

    bigquery.SchemaField(
        "symbol",
        "STRING",
        mode="REQUIRED"
    ),
]


# ==========================================================
# AUDIT SCHEMA
# ==========================================================

AUDIT_SCHEMA = [

    bigquery.SchemaField(
        "batch_id",
        "STRING",
        mode="REQUIRED"
    ),

    bigquery.SchemaField(
        "source_file",
        "STRING",
        mode="REQUIRED"
    ),

    bigquery.SchemaField(
        "source_gcs_uri",
        "STRING",
        mode="REQUIRED"
    ),

    bigquery.SchemaField(
        "symbol",
        "STRING",
        mode="REQUIRED"
    ),

    bigquery.SchemaField(
        "attempt_number",
        "INT64",
        mode="REQUIRED"
    ),

    bigquery.SchemaField(
        "status",
        "STRING",
        mode="REQUIRED"
    ),

    bigquery.SchemaField(
        "row_count",
        "INT64",
        mode="NULLABLE"
    ),

    bigquery.SchemaField(
        "started_at",
        "TIMESTAMP",
        mode="REQUIRED"
    ),

    bigquery.SchemaField(
        "completed_at",
        "TIMESTAMP",
        mode="NULLABLE"
    ),

    bigquery.SchemaField(
        "error_message",
        "STRING",
        mode="NULLABLE"
    ),
]