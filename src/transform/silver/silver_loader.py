import uuid

import pandas as pd
from google.cloud import bigquery

from src.utils.config import (
    GCP_PROJECT_ID,
    BQ_SILVER_DATASET,
)


# ==========================================================
# CONFIGURATION
# ==========================================================

SILVER_TABLE_NAME = "silver_1min"

SILVER_TABLE = (
    f"{GCP_PROJECT_ID}."
    f"{BQ_SILVER_DATASET}."
    f"{SILVER_TABLE_NAME}"
)


# ==========================================================
# FINAL SILVER TABLE COLUMNS
# ==========================================================

SILVER_COLUMNS = [
    "symbol",
    "date",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "sma_20",
    "ema_9",
    "ema_20",
    "rsi_14",
    "macd",
    "macd_signal",
    "macd_histogram",
    "stoch_k",
    "stoch_d",
    "atr_14",
    "atr_pct",
    "bollinger_upper",
    "bollinger_lower",
    "volume_sma_20",
    "relative_volume_20",
    "obv",
    "vwap",
    "vwap_deviation_pct",
    "previous_session_close",
    "gap_pct",
    "adx_14",
    "price_change_pct",
    "indicator_version",
    "processed_at",
]


# ==========================================================
# LOAD SILVER DATA
# ==========================================================

def load_silver_data(
    client,
    df,
    target_table,
) -> int:
    """
    Load transformed 1-minute Silver data into BigQuery.

    Flow:
        Silver dataframe
            ↓
        validate required columns
            ↓
        timestamp -> date
            ↓
        normalize data types
            ↓
        deduplicate symbol + date
            ↓
        temporary staging table
            ↓
        MERGE into timeframe-specific Silver table
            ↓
        delete staging table

    Business key:
        symbol + date

    Returns:
        Number of rows processed after defensive
        deduplication.
    """

    # ======================================================
    # EMPTY INPUT
    # ======================================================

    if df is None or df.empty:
        return 0

    df = df.copy()

    # ======================================================
    # VALIDATE INPUT
    #
    # indicators.py returns timestamp, not date.
    # ======================================================

    required_input_columns = [
        "symbol",
        "timestamp",
        "open",
        "high",
        "low",
        "close",
        "volume",
    ]

    missing_input_columns = [
        column
        for column in required_input_columns
        if column not in df.columns
    ]

    if missing_input_columns:
        raise ValueError(
            "Missing required Silver input columns: "
            + ", ".join(missing_input_columns)
        )

    # ======================================================
    # TIMESTAMP -> DATE
    #
    # indicators.py:
    #     timestamp
    #
    # BigQuery silver_1min:
    #     date DATETIME
    # ======================================================

    df = df.rename(
        columns={
            "timestamp": "date"
        }
    )

    # ======================================================
    # NORMALIZE DATE
    #
    # BigQuery DATETIME must be timezone-naive.
    # ======================================================

    df["date"] = pd.to_datetime(
        df["date"],
        errors="raise",
    )

    if df["date"].dt.tz is not None:
        df["date"] = (
            df["date"]
            .dt.tz_localize(None)
        )

    # ======================================================
    # NORMALIZE PROCESSED_AT
    #
    # BigQuery processed_at is TIMESTAMP.
    # Keep it UTC-aware.
    # ======================================================

    if "processed_at" not in df.columns:
        raise ValueError(
            "Missing final Silver column: processed_at"
        )

    df["processed_at"] = pd.to_datetime(
        df["processed_at"],
        utc=True,
        errors="raise",
    )

    # ======================================================
    # VALIDATE FINAL SILVER SCHEMA
    # ======================================================

    missing_silver_columns = [
        column
        for column in SILVER_COLUMNS
        if column not in df.columns
    ]

    if missing_silver_columns:
        raise ValueError(
            "Missing final Silver columns: "
            + ", ".join(missing_silver_columns)
        )

    # ======================================================
    # KEEP ONLY FINAL BIGQUERY COLUMNS
    # ======================================================

    df = df[
        SILVER_COLUMNS
    ].copy()

    # ======================================================
    # DEFENSIVE DEDUPLICATION
    #
    # Even though validator.py handles Bronze duplicates,
    # we protect the loader as well.
    #
    # Only one record can enter staging for:
    #
    #     symbol + date
    # ======================================================

    df = (
        df.sort_values(
            [
                "symbol",
                "date",
            ]
        )
        .drop_duplicates(
            subset=[
                "symbol",
                "date",
            ],
            keep="last",
        )
        .reset_index(drop=True)
    )

    # ======================================================
    # CREATE UNIQUE STAGING TABLE
    # ======================================================

    staging_table_name = (
        "_staging_silver_1min_"
        + uuid.uuid4().hex[:12]
    )

    staging_table = (
        f"{GCP_PROJECT_ID}."
        f"{BQ_SILVER_DATASET}."
        f"{staging_table_name}"
    )

    try:

        # ==================================================
        # LOAD PANDAS DATAFRAME -> STAGING
        # ==================================================

        load_job_config = (
            bigquery.LoadJobConfig(
                write_disposition=(
                    bigquery.WriteDisposition.WRITE_TRUNCATE
                )
            )
        )

        load_job = (
            client.load_table_from_dataframe(
                df,
                staging_table,
                job_config=load_job_config,
            )
        )

        load_job.result()

        # ==================================================
        # MERGE STAGING -> FINAL SILVER
        #
        # Business key:
        #
        #     symbol + date
        # ==================================================

        merge_query = f"""
        MERGE `{target_table}` AS target

        USING `{staging_table}` AS source

        ON target.symbol = source.symbol
        AND target.date = source.date

        WHEN MATCHED THEN
          UPDATE SET

            target.open =
                source.open,

            target.high =
                source.high,

            target.low =
                source.low,

            target.close =
                source.close,

            target.volume =
                source.volume,

            target.sma_20 =
                source.sma_20,

            target.ema_9 =
                source.ema_9,

            target.ema_20 =
                source.ema_20,

            target.rsi_14 =
                source.rsi_14,

            target.macd =
                source.macd,

            target.macd_signal =
                source.macd_signal,

            target.macd_histogram =
                source.macd_histogram,

            target.stoch_k =
                source.stoch_k,

            target.stoch_d =
                source.stoch_d,

            target.atr_14 =
                source.atr_14,

            target.atr_pct =
                source.atr_pct,

            target.bollinger_upper =
                source.bollinger_upper,

            target.bollinger_lower =
                source.bollinger_lower,

            target.volume_sma_20 =
                source.volume_sma_20,

            target.relative_volume_20 =
                source.relative_volume_20,

            target.obv =
                source.obv,

            target.vwap =
                source.vwap,

            target.vwap_deviation_pct =
                source.vwap_deviation_pct,

            target.previous_session_close =
                source.previous_session_close,

            target.gap_pct =
                source.gap_pct,

            target.adx_14 =
                source.adx_14,

            target.price_change_pct =
                source.price_change_pct,

            target.indicator_version =
                source.indicator_version,

            target.processed_at =
                source.processed_at


        WHEN NOT MATCHED THEN

          INSERT
          (
            symbol,
            date,
            open,
            high,
            low,
            close,
            volume,

            sma_20,
            ema_9,
            ema_20,
            rsi_14,

            macd,
            macd_signal,
            macd_histogram,

            stoch_k,
            stoch_d,

            atr_14,
            atr_pct,

            bollinger_upper,
            bollinger_lower,

            volume_sma_20,
            relative_volume_20,

            obv,

            vwap,
            vwap_deviation_pct,

            previous_session_close,
            gap_pct,

            adx_14,
            price_change_pct,

            indicator_version,
            processed_at
          )

          VALUES
          (
            source.symbol,
            source.date,
            source.open,
            source.high,
            source.low,
            source.close,
            source.volume,

            source.sma_20,
            source.ema_9,
            source.ema_20,
            source.rsi_14,

            source.macd,
            source.macd_signal,
            source.macd_histogram,

            source.stoch_k,
            source.stoch_d,

            source.atr_14,
            source.atr_pct,

            source.bollinger_upper,
            source.bollinger_lower,

            source.volume_sma_20,
            source.relative_volume_20,

            source.obv,

            source.vwap,
            source.vwap_deviation_pct,

            source.previous_session_close,
            source.gap_pct,

            source.adx_14,
            source.price_change_pct,

            source.indicator_version,
            source.processed_at
          )
        """

        merge_job = client.query(
            merge_query
        )

        merge_job.result()

        # Number of unique dataframe rows processed
        return len(df)

    finally:

        # ==================================================
        # ALWAYS REMOVE TEMPORARY STAGING TABLE
        # ==================================================

        client.delete_table(
            staging_table,
            not_found_ok=True,
        )