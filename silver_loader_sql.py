from datetime import datetime, timezone
from uuid import uuid4

import pandas as pd
from google.cloud import bigquery

from src.utils.config import (
    GCP_PROJECT_ID,
    GCP_REGION,
    BQ_BRONZE_DATASET,
    BQ_BRONZE_TABLE,
    BQ_SILVER_DATASET,
)

from src.transform.silver.validator import validate_ohlcv
from src.transform.silver.indicators import calculate_indicators
from src.transform.silver.audit_logger import write_audit_record


# ==========================================================
# CONFIGURATION
# ==========================================================

SILVER_TABLE = "silver_1min"

SOURCE_TABLE = (
    f"{BQ_BRONZE_DATASET}.{BQ_BRONZE_TABLE}"
)

TARGET_TABLE = (
    f"{BQ_SILVER_DATASET}.{SILVER_TABLE}"
)


# ==========================================================
# BIGQUERY CLIENT
# ==========================================================

client = bigquery.Client(
    project=GCP_PROJECT_ID,
    location=GCP_REGION,
)


# ==========================================================
# READ BRONZE DATA
# ==========================================================

def read_bronze_data(
    symbol: str,
) -> pd.DataFrame:

    query = f"""
        SELECT
            symbol,
            date AS timestamp,
            open,
            high,
            low,
            close,
            volume
        FROM `{GCP_PROJECT_ID}.{SOURCE_TABLE}`
        WHERE symbol = @symbol
        ORDER BY date
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter(
                "symbol",
                "STRING",
                symbol,
            )
        ]
    )

    print("Reading Bronze data...")

    df = client.query(
        query,
        job_config=job_config,
    ).to_dataframe()

    print(f"Bronze rows: {len(df)}")

    return df


# ==========================================================
# GET EXISTING SILVER KEYS
# ==========================================================

def get_existing_silver_keys(
    symbol: str,
) -> pd.DataFrame:

    query = f"""
        SELECT
            symbol,
            date AS timestamp
        FROM `{GCP_PROJECT_ID}.{TARGET_TABLE}`
        WHERE symbol = @symbol
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter(
                "symbol",
                "STRING",
                symbol,
            )
        ]
    )

    return client.query(
        query,
        job_config=job_config,
    ).to_dataframe()


# ==========================================================
# REMOVE EXISTING SILVER RECORDS
# FROM THE DATASET WE ARE ABOUT TO LOAD
# ==========================================================

def remove_existing_silver_records(
    df: pd.DataFrame,
) -> pd.DataFrame:

    if df.empty:
        return df

    existing = get_existing_silver_keys(
        df["symbol"].iloc[0]
    )

    if existing.empty:
        return df

    df["timestamp"] = pd.to_datetime(
        df["timestamp"]
    )

    existing["timestamp"] = pd.to_datetime(
        existing["timestamp"]
    )

    merged = df.merge(
        existing,
        on=["symbol", "timestamp"],
        how="left",
        indicator=True,
    )

    new_rows = merged[
        merged["_merge"] == "left_only"
    ].drop(
        columns=["_merge"]
    )

    return new_rows.reset_index(
        drop=True
    )


# ==========================================================
# NORMALIZE SILVER DATAFRAME
# ==========================================================

def prepare_silver_dataframe(
    df: pd.DataFrame,
) -> pd.DataFrame:

    df = df.copy()

    # Pandas indicator logic uses timestamp
    # but Silver BigQuery uses date.
    df["date"] = pd.to_datetime(
        df["timestamp"]
    )

    # Keep exactly the approved 31 columns.
    columns = [
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
        "bollinger_lower",
        "bollinger_upper",
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

    df = df[columns]

    return df


# ==========================================================
# LOAD DATAFRAME INTO SILVER
# ==========================================================

def load_to_silver(
    df: pd.DataFrame,
) -> int:

    if df.empty:
        return 0

    table_ref = (
        f"{GCP_PROJECT_ID}."
        f"{TARGET_TABLE}"
    )

    job_config = bigquery.LoadJobConfig(
        write_disposition=(
            bigquery.WriteDisposition.WRITE_APPEND
        ),
    )

    print(
        "Loading transformed data into Silver..."
    )

    job = client.load_table_from_dataframe(
        df,
        table_ref,
        job_config=job_config,
    )

    job.result()

    return len(df)


# ==========================================================
# MAIN SILVER LOADER
# ==========================================================

def load_symbol_to_silver_1min(
    symbol: str,
    load_type: str = "HISTORICAL",
):

    run_id = (
        f"SILVER-{symbol}-"
        f"{uuid4().hex[:8]}"
    )

    started_at = datetime.now(
        timezone.utc
    )

    bronze_rows = 0
    validated_rows = 0
    silver_rows = 0

    try:

        print("\n" + "=" * 80)
        print(
            f"SILVER 1-MIN LOAD: {symbol}"
        )
        print("=" * 80)

        # --------------------------------------------------
        # STEP 1: READ BRONZE
        # --------------------------------------------------

        df = read_bronze_data(
            symbol
        )

        bronze_rows = len(df)

        if df.empty:
            raise ValueError(
                f"No Bronze data found for {symbol}"
            )

        # --------------------------------------------------
        # STEP 2: VALIDATE BRONZE
        # --------------------------------------------------

        print(
            "Validating Bronze data..."
        )

        df = validate_ohlcv(df)

        validated_rows = len(df)

        print(
            f"Rows after validation: "
            f"{validated_rows}"
        )

        if df.empty:
            raise ValueError(
                f"No valid Bronze rows remain "
                f"after validation for {symbol}"
            )

        # --------------------------------------------------
        # STEP 3: CALCULATE INDICATORS
        # --------------------------------------------------

        print(
            "Calculating indicators with Pandas..."
        )

        df = calculate_indicators(df)

        print(
            f"Rows after indicators: "
            f"{len(df)}"
        )

        # --------------------------------------------------
        # STEP 4: INCREMENTAL DUPLICATE HANDLING
        # --------------------------------------------------

        if load_type.upper() == "INCREMENTAL":

            print(
                "Checking existing Silver records..."
            )

            df_to_load = (
                remove_existing_silver_records(
                    df
                )
            )

        else:

            df_to_load = df

        print(
            f"Rows to load into Silver: "
            f"{len(df_to_load)}"
        )

        # --------------------------------------------------
        # STEP 5: PREPARE FINAL 31-COLUMN DATAFRAME
        # --------------------------------------------------

        df_to_load = prepare_silver_dataframe(
            df_to_load
        )

        # --------------------------------------------------
        # STEP 6: LOAD SILVER
        # --------------------------------------------------

        silver_rows = load_to_silver(
            df_to_load
        )

        # --------------------------------------------------
        # STEP 7: SUCCESS AUDIT
        # --------------------------------------------------

        completed_at = datetime.now(
            timezone.utc
        )

        write_audit_record(
            client=client,
            run_id=run_id,
            symbol=symbol,
            load_type=load_type,
            source_table=SOURCE_TABLE,
            target_table=TARGET_TABLE,
            started_at=started_at,
            completed_at=completed_at,
            bronze_rows=bronze_rows,
            validated_rows=validated_rows,
            silver_rows=silver_rows,
            status="SUCCESS",
        )

        print(
            f"Silver 1-min load completed: "
            f"{symbol}"
        )

        print(
            f"Audit status: SUCCESS"
        )

        return {
            "run_id": run_id,
            "symbol": symbol,
            "status": "SUCCESS",
            "bronze_rows": bronze_rows,
            "validated_rows": validated_rows,
            "silver_rows": silver_rows,
        }

    except Exception as exc:

        # --------------------------------------------------
        # FAILURE AUDIT
        # --------------------------------------------------

        completed_at = datetime.now(
            timezone.utc
        )

        error_type = type(exc).__name__
        error_message = str(exc)

        failed_stage = (
            "READ_BRONZE"
            if bronze_rows == 0
            else
            "VALIDATION"
            if validated_rows == 0
            else
            "INDICATOR_CALCULATION"
            if silver_rows == 0
            else
            "SILVER_LOAD"
        )

        try:

            write_audit_record(
                client=client,
                run_id=run_id,
                symbol=symbol,
                load_type=load_type,
                source_table=SOURCE_TABLE,
                target_table=TARGET_TABLE,
                started_at=started_at,
                completed_at=completed_at,
                bronze_rows=bronze_rows,
                validated_rows=validated_rows,
                silver_rows=silver_rows,
                status="FAILED",
                failed_stage=failed_stage,
                error_type=error_type,
                error_message=error_message,
            )

        except Exception as audit_error:

            print(
                "WARNING: Failed to write "
                f"audit record: {audit_error}"
            )

        print(
            f"Silver load FAILED: {symbol}"
        )

        print(
            f"Stage : {failed_stage}"
        )

        print(
            f"Error : {error_type}"
        )

        print(
            f"Message: {error_message}"
        )

        raise