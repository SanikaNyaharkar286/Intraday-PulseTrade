from datetime import datetime, timezone
from google.cloud import bigquery


# ==========================================================
# CONFIGURATION
# ==========================================================

from src.utils.config import (
    GCP_PROJECT_ID,
    BQ_SILVER_DATASET,
    BQ_SILVER_AUDIT_TABLE
)
AUDIT_TABLE = (
    f"{GCP_PROJECT_ID}."
    f"{BQ_SILVER_DATASET}."
    f"{BQ_SILVER_AUDIT_TABLE}"
)


# ==========================================================
# CREATE AUDIT RECORD
# ==========================================================

def write_audit_record(
    client: bigquery.Client,
    run_id: str,
    symbol: str,
    load_type: str,
    source_table: str,
    target_table: str,
    started_at: datetime,
    completed_at: datetime,
    bronze_rows: int,
    validated_rows: int,
    silver_rows: int,
    status: str,
    failed_stage: str | None = None,
    error_type: str | None = None,
    error_message: str | None = None,
):
    """
    Write one Silver pipeline execution record
    into the Silver audit table.
    """

    query = f"""
    INSERT INTO `{AUDIT_TABLE}`
    (
        run_id,
        symbol,
        load_type,
        source_table,
        target_table,
        started_at,
        completed_at,
        bronze_rows,
        validated_rows,
        silver_rows,
        status,
        failed_stage,
        error_type,
        error_message,
        created_at
    )
    VALUES
    (
        @run_id,
        @symbol,
        @load_type,
        @source_table,
        @target_table,
        @started_at,
        @completed_at,
        @bronze_rows,
        @validated_rows,
        @silver_rows,
        @status,
        @failed_stage,
        @error_type,
        @error_message,
        @created_at
    )
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter(
                "run_id",
                "STRING",
                run_id,
            ),
            bigquery.ScalarQueryParameter(
                "symbol",
                "STRING",
                symbol,
            ),
            bigquery.ScalarQueryParameter(
                "load_type",
                "STRING",
                load_type,
            ),
            bigquery.ScalarQueryParameter(
                "source_table",
                "STRING",
                source_table,
            ),
            bigquery.ScalarQueryParameter(
                "target_table",
                "STRING",
                target_table,
            ),
            bigquery.ScalarQueryParameter(
                "started_at",
                "TIMESTAMP",
                started_at,
            ),
            bigquery.ScalarQueryParameter(
                "completed_at",
                "TIMESTAMP",
                completed_at,
            ),
            bigquery.ScalarQueryParameter(
                "bronze_rows",
                "INT64",
                bronze_rows,
            ),
            bigquery.ScalarQueryParameter(
                "validated_rows",
                "INT64",
                validated_rows,
            ),
            bigquery.ScalarQueryParameter(
                "silver_rows",
                "INT64",
                silver_rows,
            ),
            bigquery.ScalarQueryParameter(
                "status",
                "STRING",
                status,
            ),
            bigquery.ScalarQueryParameter(
                "failed_stage",
                "STRING",
                failed_stage,
            ),
            bigquery.ScalarQueryParameter(
                "error_type",
                "STRING",
                error_type,
            ),
            bigquery.ScalarQueryParameter(
                "error_message",
                "STRING",
                error_message,
            ),
            bigquery.ScalarQueryParameter(
                "created_at",
                "TIMESTAMP",
                datetime.now(timezone.utc),
            ),
        ]
    )

    job = client.query(
        query,
        job_config=job_config,
        location="us-east1",
    )

    job.result()

    print(
        f"Audit record written: "
        f"{symbol} | {status} | {run_id}"
    )