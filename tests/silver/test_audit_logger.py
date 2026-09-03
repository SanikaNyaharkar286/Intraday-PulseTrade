from datetime import datetime, timezone

from google.cloud import bigquery
import uuid

from src.transform.silver.audit_logger import (
    write_audit_record,
)


PROJECT_ID = "project-001658fa-3ce5-4746-980"

AUDIT_TABLE = (
    f"{PROJECT_ID}."
    "migration_silver_v2."
    "silver_audit_log"
)


def test_write_audit_record():

    client = bigquery.Client(
        project=PROJECT_ID,
        location="us-east1",
    )

    run_id = f"TEST-AUDIT-{uuid.uuid4().hex[:8]}"

    started_at = datetime.now(timezone.utc)
    completed_at = datetime.now(timezone.utc)

    write_audit_record(
        client=client,
        run_id=run_id,
        symbol="360ONE",
        load_type="TEST",
        source_table=(
            "migration_bronze_v2.market_prices"
        ),
        target_table=(
            "migration_silver_v2.silver_1min"
        ),
        started_at=started_at,
        completed_at=completed_at,
        bronze_rows=667775,
        validated_rows=667775,
        silver_rows=667775,
        status="SUCCESS",
    )

    query = f"""
    SELECT
        run_id,
        symbol,
        load_type,
        bronze_rows,
        validated_rows,
        silver_rows,
        status
    FROM `{AUDIT_TABLE}`
    WHERE run_id = @run_id
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter(
                "run_id",
                "STRING",
                run_id,
            )
        ]
    )

    rows = list(
        client.query(
            query,
            job_config=job_config,
            location="us-east1",
        ).result()
    )

    assert len(rows) == 1

    row = rows[0]

    assert row.run_id == run_id
    assert row.symbol == "360ONE"
    assert row.status == "SUCCESS"

    assert row.bronze_rows == 667775
    assert row.validated_rows == 667775
    assert row.silver_rows == 667775

    print("\nAUDIT LOGGER TEST PASSED")

def test_write_failed_audit_record():

    client = bigquery.Client(
        project=PROJECT_ID,
        location="us-east1",
    )

    run_id = f"TEST-AUDIT-FAILED-{uuid.uuid4().hex[:8]}"

    started_at = datetime.now(timezone.utc)
    completed_at = datetime.now(timezone.utc)

    write_audit_record(
        client=client,
        run_id=run_id,
        symbol="360ONE",
        load_type="TEST",
        source_table=(
            "migration_bronze_v2.market_prices"
        ),
        target_table=(
            "migration_silver_v2.silver_1min"
        ),
        started_at=started_at,
        completed_at=completed_at,

        bronze_rows=667775,
        validated_rows=0,
        silver_rows=0,

        status="FAILED",

        failed_stage="VALIDATION",
        error_type="ValueError",
        error_message="Test validation failure",
    )

    query = f"""
    SELECT
        run_id,
        symbol,
        status,
        failed_stage,
        error_type,
        error_message,
        bronze_rows,
        validated_rows,
        silver_rows
    FROM `{AUDIT_TABLE}`
    WHERE run_id = @run_id
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter(
                "run_id",
                "STRING",
                run_id,
            )
        ]
    )

    rows = list(
        client.query(
            query,
            job_config=job_config,
            location="us-east1",
        ).result()
    )

    assert len(rows) == 1

    row = rows[0]

    assert row.run_id == run_id
    assert row.symbol == "360ONE"

    assert row.status == "FAILED"

    assert row.failed_stage == "VALIDATION"
    assert row.error_type == "ValueError"
    assert row.error_message == "Test validation failure"

    assert row.bronze_rows == 667775
    assert row.validated_rows == 0
    assert row.silver_rows == 0

    print("\nFAILED AUDIT LOGGER TEST PASSED")