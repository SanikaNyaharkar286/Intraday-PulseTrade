from datetime import datetime, timezone

import pandas as pd
from google.cloud import bigquery

from src.utils.config import (
    GCP_PROJECT_ID,
    BQ_SILVER_DATASET,
)


# ==========================================================
# CONFIGURATION
# ==========================================================

QUARANTINE_TABLE_NAME = "silver_quarantine"

QUARANTINE_TABLE = (
    f"{GCP_PROJECT_ID}."
    f"{BQ_SILVER_DATASET}."
    f"{QUARANTINE_TABLE_NAME}"
)


QUARANTINE_COLUMNS = [
    "run_id",
    "symbol",
    "date",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "failure_reason",
    "load_type",
    "source_table",
    "quarantined_at",
]


# ==========================================================
# LOAD REJECTED ROWS
# ==========================================================

def load_quarantine_data(
    client: bigquery.Client,
    rejected_df: pd.DataFrame,
    run_id: str,
    load_type: str,
    source_table: str,
) -> int:
    """
    Persist rejected Silver validation rows into
    silver_quarantine.

    Returns:
        Number of rejected rows loaded.
    """

    # ======================================================
    # EMPTY INPUT
    # ======================================================

    if (
        rejected_df is None
        or rejected_df.empty
    ):
        return 0

    df = rejected_df.copy()

    # ======================================================
    # ADD PIPELINE METADATA
    # ======================================================

    df["run_id"] = run_id
    df["load_type"] = load_type
    df["source_table"] = source_table

    df["quarantined_at"] = (
        datetime.now(timezone.utc)
    )

    # ======================================================
    # NORMALIZE DATE
    #
    # Target column is DATETIME.
    # ======================================================

    df["date"] = pd.to_datetime(
        df["date"],
        errors="coerce",
    )

    if df["date"].dt.tz is not None:
        df["date"] = (
            df["date"]
            .dt.tz_localize(None)
        )

    # ======================================================
    # NORMALIZE NUMERIC COLUMNS
    # ======================================================

    numeric_columns = [
        "open",
        "high",
        "low",
        "close",
        "volume",
    ]

    for column in numeric_columns:

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    # ======================================================
    # KEEP ONLY FINAL QUARANTINE COLUMNS
    # ======================================================

    missing_columns = [
        column
        for column in QUARANTINE_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:

        raise ValueError(
            "Missing quarantine columns: "
            + ", ".join(missing_columns)
        )

    df = df[
        QUARANTINE_COLUMNS
    ].copy()

    # ======================================================
    # LOAD INTO BIGQUERY
    #
    # APPEND is intentional:
    #
    # quarantine is an audit/history table.
    # Every rejected pipeline run should be traceable.
    # ======================================================

    job_config = bigquery.LoadJobConfig(
        write_disposition=(
            bigquery.WriteDisposition.WRITE_APPEND
        )
    )

    load_job = (
        client.load_table_from_dataframe(
            df,
            QUARANTINE_TABLE,
            job_config=job_config,
        )
    )

    load_job.result()

    return len(df)