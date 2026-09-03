import uuid

import pandas as pd
from google.cloud import bigquery

from src.transform.silver.validator import (
    validate_bronze_data,
)

from src.transform.silver.quarantine_loader import (
    load_quarantine_data,
)

from src.utils.config import (
    GCP_PROJECT_ID,
    BQ_BRONZE_DATASET,
    BQ_BRONZE_TABLE,
)


def main():

    client = bigquery.Client(
        project=GCP_PROJECT_ID
    )

    # ======================================================
    # 1. CREATE FAKE BAD BRONZE ROW
    # ======================================================

    test_df = pd.DataFrame(
        {
            "symbol": [
                "TEST_QUARANTINE"
            ],
            "date": [
                "2026-09-02 09:15:00"
            ],
            "open": [
                0
            ],
            "high": [
                0
            ],
            "low": [
                0
            ],
            "close": [
                0
            ],
            "volume": [
                100
            ],
        }
    )

    print(
        "\nInput rows:",
        len(test_df),
    )

    # ======================================================
    # 2. RUN REAL VALIDATOR
    # ======================================================

    valid_df, rejected_df = (
        validate_bronze_data(
            test_df
        )
    )

    print(
        "Valid rows:",
        len(valid_df),
    )

    print(
        "Rejected rows:",
        len(rejected_df),
    )

    if len(valid_df) != 0:
        raise AssertionError(
            "Expected zero valid rows."
        )

    if len(rejected_df) != 1:
        raise AssertionError(
            "Expected one rejected row."
        )

    failure_reason = (
        rejected_df.iloc[0][
            "failure_reason"
        ]
    )

    print(
        "Failure reason:",
        failure_reason,
    )

    if (
        "NON_POSITIVE_OHLC"
        not in failure_reason
    ):
        raise AssertionError(
            "Expected NON_POSITIVE_OHLC."
        )

    # ======================================================
    # 3. LOAD INTO QUARANTINE
    # ======================================================

    run_id = str(
        uuid.uuid4()
    )

    source_table = (
        f"{GCP_PROJECT_ID}."
        f"{BQ_BRONZE_DATASET}."
        f"{BQ_BRONZE_TABLE}"
    )

    quarantine_rows = (
        load_quarantine_data(
            client=client,
            rejected_df=rejected_df,
            run_id=run_id,
            load_type="TEST",
            source_table=source_table,
        )
    )

    print(
        "Quarantine rows loaded:",
        quarantine_rows,
    )

    if quarantine_rows != 1:
        raise AssertionError(
            "Expected exactly one "
            "quarantine row."
        )

    # ======================================================
    # 4. VERIFY BIGQUERY
    # ======================================================

    quarantine_table = (
        f"{GCP_PROJECT_ID}."
        "migration_silver_v2."
        "silver_quarantine"
    )

    query = f"""
    SELECT
        run_id,
        symbol,
        date,
        open,
        high,
        low,
        close,
        volume,
        failure_reason,
        load_type,
        source_table,
        quarantined_at

    FROM `{quarantine_table}`

    WHERE run_id = @run_id
    """

    job_config = (
        bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter(
                    "run_id",
                    "STRING",
                    run_id,
                )
            ]
        )
    )

    rows = list(
        client.query(
            query,
            job_config=job_config,
        ).result()
    )

    print(
        "Rows found in BigQuery:",
        len(rows),
    )

    if len(rows) != 1:
        raise AssertionError(
            "Quarantine record was not "
            "found in BigQuery."
        )

    row = rows[0]

    print(
        "\nBigQuery quarantine row:"
    )

    print(
        "run_id:",
        row.run_id,
    )

    print(
        "symbol:",
        row.symbol,
    )

    print(
        "date:",
        row.date,
    )

    print(
        "open:",
        row.open,
    )

    print(
        "failure_reason:",
        row.failure_reason,
    )

    print(
        "load_type:",
        row.load_type,
    )

    # ======================================================
    # SUCCESS
    # ======================================================

    print(
        "\n"
        + "=" * 70
    )

    print(
        "PASS: Rejected row was "
        "written to Silver quarantine."
    )

    print(
        "=" * 70
    )


if __name__ == "__main__":

    main()