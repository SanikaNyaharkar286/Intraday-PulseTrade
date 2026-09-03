from datetime import datetime, timezone

import pandas as pd
from google.cloud import bigquery

from src.transform.silver.silver_loader import (
    load_silver_data,
)


PROJECT_ID = "project-001658fa-3ce5-4746-980"

SILVER_TABLE = (
    f"{PROJECT_ID}."
    "migration_silver_v2."
    "silver_1min"
)

SYMBOL = "360ONE"
TEST_DATE = "2015-02-02 09:15:00"


def main():

    client = bigquery.Client(
        project=PROJECT_ID
    )

    # ======================================================
    # 1. READ CURRENT SILVER ROW
    # ======================================================

    query = f"""
    SELECT *
    FROM `{SILVER_TABLE}`
    WHERE symbol = @symbol
      AND date = DATETIME(@date)
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter(
                "symbol",
                "STRING",
                SYMBOL,
            ),
            bigquery.ScalarQueryParameter(
                "date",
                "STRING",
                TEST_DATE,
            ),
        ]
    )

    current_df = (
        client.query(
            query,
            job_config=job_config,
        )
        .result()
        .to_dataframe()
    )

    print(
        "\nRows BEFORE loader:",
        len(current_df),
    )

    if current_df.empty:

        raise RuntimeError(
            "Test row does not exist in Silver."
        )

    print(
        "\nExisting processed_at:"
    )

    print(
        current_df[
            [
                "symbol",
                "date",
                "processed_at",
            ]
        ]
    )

    # ======================================================
    # IMPORTANT
    #
    # If duplicates still exist for this exact key,
    # stop the test.
    #
    # We want to test loader behavior against ONE clean
    # target row.
    # ======================================================

    if len(current_df) != 1:

        raise RuntimeError(
            f"Expected exactly 1 existing row, "
            f"found {len(current_df)}. "
            f"Clean this test key first."
        )

    # ======================================================
    # 2. PREPARE DATAFRAME FOR SILVER LOADER
    #
    # silver_loader expects "timestamp", while BigQuery
    # contains "date".
    # ======================================================

    test_df = current_df.copy()

    test_df = test_df.rename(
        columns={
            "date": "timestamp"
        }
    )

    # Force a new processed_at so we can confirm UPDATE
    # occurred instead of INSERT.
    test_df["processed_at"] = (
        datetime.now(timezone.utc)
    )

    # ======================================================
    # 3. CALL REAL PRODUCTION SILVER LOADER
    # ======================================================

    processed_rows = load_silver_data(
        client=client,
        df=test_df,
    )

    print(
        "\nLoader processed rows:",
        processed_rows,
    )

    # ======================================================
    # 4. READ SAME BUSINESS KEY AGAIN
    # ======================================================

    after_df = (
        client.query(
            query,
            job_config=job_config,
        )
        .result()
        .to_dataframe()
    )

    print(
        "\nRows AFTER loader:",
        len(after_df),
    )

    print(
        "\nProcessed_at AFTER:"
    )

    print(
        after_df[
            [
                "symbol",
                "date",
                "processed_at",
            ]
        ]
    )

    # ======================================================
    # 5. ASSERT IDEMPOTENCY
    # ======================================================

    if len(after_df) != 1:

        raise AssertionError(
            f"FAIL: duplicate created. "
            f"Expected 1 row, found "
            f"{len(after_df)}."
        )

    print(
        "\n"
        + "=" * 70
    )

    print(
        "PASS: Silver loader did NOT create a duplicate."
    )

    print(
        "Existing symbol + date was updated by MERGE."
    )

    print(
        "=" * 70
    )


if __name__ == "__main__":

    main()