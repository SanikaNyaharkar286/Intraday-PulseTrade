from google.cloud import bigquery


from src.utils.config import (
    GCP_PROJECT_ID,
    BQ_AUDIT_DATASET,
    BQ_AUDIT_TABLE,
)


client = bigquery.Client(
    project=GCP_PROJECT_ID
)


# ==========================================================
# AUDIT TABLE ID
# ==========================================================

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

    table = bigquery.Table(
        table_id,
        schema=[

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
                "INT64"
            ),

            bigquery.SchemaField(
                "started_at",
                "TIMESTAMP",
                mode="REQUIRED"
            ),

            bigquery.SchemaField(
                "completed_at",
                "TIMESTAMP"
            ),

            bigquery.SchemaField(
                "error_message",
                "STRING"
            ),
        ]
    )

    table.time_partitioning = (
        bigquery.TimePartitioning(
            type_=(
                bigquery.TimePartitioningType.DAY
            ),
            field="started_at"
        )
    )

    table.clustering_fields = [
        "status",
        "symbol"
    ]

    return client.create_table(
        table,
        exists_ok=True
    )


# ==========================================================
# WRITE AUDIT
# ==========================================================

def write_audit_record(
    batch_id,
    source_file,
    source_gcs_uri,
    symbol,
    attempt_number,
    status,
    row_count,
    started_at,
    completed_at=None,
    error_message=None,
):

    table_id = get_audit_table_id()

    row = {

        "batch_id":
            batch_id,

        "source_file":
            source_file,

        "source_gcs_uri":
            source_gcs_uri,

        "symbol":
            symbol,

        "attempt_number":
            attempt_number,

        "status":
            status,

        "row_count":
            row_count,

        "started_at":
            started_at.isoformat()
            if started_at
            else None,

        "completed_at":
            completed_at.isoformat()
            if completed_at
            else None,

        "error_message":
            error_message,

    }

    errors = client.insert_rows_json(
        table_id,
        [row]
    )

    if errors:

        raise RuntimeError(
            f"Audit insert failed: {errors}"
        )


# ==========================================================
# SUCCESSFUL FILES
# ==========================================================

def get_successful_files():

    table_id = get_audit_table_id()

    query = f"""
        SELECT DISTINCT
            source_gcs_uri
        FROM `{table_id}`
        WHERE status = 'SUCCESS'
    """

    results = client.query(
        query
    ).result()

    return {
        row.source_gcs_uri
        for row in results
    }