from datetime import datetime, timezone

from google.cloud import bigquery

from src.utils.config import (
    GCP_PROJECT_ID,
    BQ_AUDIT_DATASET,
    BQ_AUDIT_TABLE,
)


# ==========================================================
# BIGQUERY CLIENT
# ==========================================================

client = bigquery.Client(
    project=GCP_PROJECT_ID
)


# ==========================================================
# AUDIT TABLE ID
# ==========================================================
AUDIT_TABLE = (
    f"{GCP_PROJECT_ID}."
    f"{BQ_AUDIT_DATASET}."
    f"{BQ_AUDIT_TABLE}"
)
def get_audit_table_id():

    return (
        f"{GCP_PROJECT_ID}."
        f"{BQ_AUDIT_DATASET}."
        f"{BQ_AUDIT_TABLE}"
    )


# ==========================================================
# CREATE AUDIT TABLE
# ==========================================================

def create_audit_table():

    table_id = get_audit_table_id()

    schema = [

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

    table = bigquery.Table(
        table_id,
        schema=schema
    )

    return client.create_table(
        table,
        exists_ok=True
    )


# ==========================================================
# WRITE AUDIT RECORD
# ==========================================================

def write_audit_record(
    batch_id: str,
    source_file: str,
    source_gcs_uri: str,
    symbol: str,
    attempt_number: int,
    status: str,
    row_count: int | None,
    started_at: datetime,
    completed_at: datetime | None = None,
    error_message: str | None = None,
):

    table_id = get_audit_table_id()

    row = {

        "batch_id": batch_id,

        "source_file": source_file,

        "source_gcs_uri": source_gcs_uri,

        "symbol": symbol,

        "attempt_number": attempt_number,

        "status": status,

        "row_count": row_count,

        "started_at": started_at.isoformat(),

        "completed_at": (
            completed_at.isoformat()
            if completed_at
            else None
        ),

        "error_message": error_message,
    }

    errors = client.insert_rows_json(
        table_id,
        [row]
    )

    if errors:

        raise RuntimeError(
            f"Failed to write audit record: "
            f"{errors}"
        )
def get_successful_files() -> set[str]:
    """
    Return all GCS URIs that have already been loaded
    successfully into Bronze.

    Used by historical_runner.py for resume support.
    """

    query = f"""
    SELECT DISTINCT
        source_gcs_uri
    FROM `{AUDIT_TABLE}`
    WHERE status = 'SUCCESS'
      AND source_gcs_uri IS NOT NULL
    """

    query_job = client.query(
        query
    )

    rows = query_job.result()

    successful_files = {
        row.source_gcs_uri
        for row in rows
        if row.source_gcs_uri
    }

    return successful_files