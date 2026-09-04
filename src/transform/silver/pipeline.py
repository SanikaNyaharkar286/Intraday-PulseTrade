import uuid
from datetime import datetime, timezone
from src.transform.silver.timeframe.aggregator import (
    aggregate_timeframe,
)
from src.transform.silver.readers import (
    read_silver_timeframe_data
)


from src.utils.timeframe_config import (
    get_timeframe_config,
)
import pandas as pd
from google.cloud import bigquery

from src.transform.silver.bronze_reader import (
    read_bronze_data,
)

from src.transform.silver.validator import (
    validate_bronze_data,
)

from src.transform.silver.quarantine_loader import (
    load_quarantine_data,
)

from src.transform.silver.indicators import (
    calculate_indicators,
)

from src.transform.silver.silver_loader import (
    load_silver_data,
)

from src.transform.silver.audit_logger import (
    write_audit_record,
)

from src.utils.config import (
    GCP_PROJECT_ID,
    BQ_BRONZE_DATASET,
    BQ_BRONZE_TABLE,
    BQ_SILVER_DATASET,
)

# ==========================================================
# TABLE NAMES
# ==========================================================

BRONZE_SOURCE_TABLE = (
    f"{GCP_PROJECT_ID}."
    f"{BQ_BRONZE_DATASET}."
    f"{BQ_BRONZE_TABLE}"
)
def get_source_table_for_timeframe(timeframe):

    sources = {

        "1min":
        f"{GCP_PROJECT_ID}.{BQ_BRONZE_DATASET}.{BQ_BRONZE_TABLE}",


        "5min":
        f"{GCP_PROJECT_ID}.{BQ_SILVER_DATASET}.silver_1min",


        "15min":
        f"{GCP_PROJECT_ID}.{BQ_SILVER_DATASET}.silver_5min",


        "1hour":
        f"{GCP_PROJECT_ID}.{BQ_SILVER_DATASET}.silver_15min",


        "daily":
        f"{GCP_PROJECT_ID}.{BQ_SILVER_DATASET}.silver_1hour",

    }


    return sources.get(timeframe)

    print(
        f"[{symbol}] Processing {timeframe} from {SOURCE_TABLE}"
    )

"""TARGET_TABLE = (
    f"{GCP_PROJECT_ID}."
    f"{BQ_SILVER_DATASET}."
    f"{timeframe_config['target_table']}"
)"""
# ==========================================================
# RANGE HELPER
# ==========================================================

def _filter_date_range(
    df: pd.DataFrame,
    date_column: str,
    start_date: str | None,
    end_date: str | None,
) -> pd.DataFrame:
    """
    Keep only rows inside the requested incremental range.

    start_date / end_date may be YYYY-MM-DD strings.

    end_date is treated as an inclusive calendar date.
    """

    if df is None or df.empty:
        return df.copy()

    result = df.copy()

    result[date_column] = pd.to_datetime(
        result[date_column],
        errors="coerce",
    )

    if start_date is not None:

        start_ts = pd.Timestamp(
            start_date
        )

        result = result[
            result[date_column] >= start_ts
        ]

    if end_date is not None:

        # --------------------------------------------------
        # Inclusive end-date handling.
        #
        # Example:
        # end_date = 2026-04-09
        #
        # We keep everything before:
        # 2026-04-10 00:00:00
        # --------------------------------------------------

        end_exclusive = (
            pd.Timestamp(end_date)
            + pd.Timedelta(days=1)
        )

        result = result[
            result[date_column]
            < end_exclusive
        ]

    return (
        result
        .copy()
        .reset_index(drop=True)
    )


# ==========================================================
# SILVER PIPELINE
# ==========================================================

def run_silver_pipeline(
    client,
    symbol,
    load_type,
    start_date=None,
    end_date=None,
    timeframe="1min",
) -> dict:
    """
    Run Silver pipeline for one symbol and timeframe.

    HISTORICAL
    ----------
    1min reads Bronze.
    Higher timeframes read previous Silver timeframe,
    aggregate candles, calculate indicators,
    and load Silver output.

    INCREMENTAL
    -----------
    Read full Bronze historical context up to end_date,
    calculate indicators using that complete history,
    then write only start_date -> end_date into Silver.

    This prevents rolling indicators such as SMA, EMA,
    RSI, MACD, ATR, ADX, etc. from restarting at the
    beginning of every incremental batch.
    """

    # ======================================================
    # RUN METADATA
    # ======================================================

    run_id = str(
            uuid.uuid4()
            )
    timeframe_config = get_timeframe_config(
        timeframe
    )

    SOURCE_TABLE = timeframe_config["source_table"]

    

    AGGREGATION = timeframe_config["aggregation"]

    TARGET_TABLE = (
    f"{GCP_PROJECT_ID}."
    f"{BQ_SILVER_DATASET}."
    f"{timeframe_config['target_table']}"
    )

    

    started_at = datetime.now(
        timezone.utc
    )

    load_type = (
        str(load_type)
        .strip()
        .upper()
    )

    if load_type not in {
        "HISTORICAL",
        "INCREMENTAL",
    }:
        raise ValueError(
            "load_type must be "
            "HISTORICAL or INCREMENTAL"
        )

    # ------------------------------------------------------
    # Incremental requires a range.
    # ------------------------------------------------------

    if load_type == "INCREMENTAL":

        if start_date is None:
            raise ValueError(
                "start_date is required "
                "for INCREMENTAL processing."
            )

        if end_date is None:
            raise ValueError(
                "end_date is required "
                "for INCREMENTAL processing."
            )

    bronze_rows = 0
    validated_rows = 0
    rejected_rows = 0
    quarantine_rows = 0
    silver_rows = 0

    current_stage = "bronze_read"

    try:

        # ==================================================
        # 1. READ SOURCE DATA
        # ==================================================

        current_stage = "source_read"


        if timeframe == "1min":

            print(
                f"[{symbol}] Reading Bronze source"
            )

            source_df = read_bronze_data(
                client=client,
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
            )

        else:

            print(
                f"[{symbol}] Reading Silver source table:"
            )

            print(
                f"        {SOURCE_TABLE}"
            )

            source_df = read_silver_timeframe_data(
                client=client,
                symbol=symbol,
                table_name=SOURCE_TABLE,
                start_date=start_date,
                end_date=end_date,
            )


        source_rows = len(source_df)


        print(
            f"[{symbol}] "
            f"Source rows read: {source_rows}"
        )


        # ==================================================
        # 2. TIMEFRAME AGGREGATION
        # ==================================================

        if timeframe != "1min":

            aggregation_rule = AGGREGATION


            print(
                f"[{symbol}] "
                f"Aggregating source data "
                f"to {timeframe}"
            )


            source_df = aggregate_timeframe(
                source_df,
                aggregation_rule,
            )


            print(
                f"[{symbol}] "
                f"{timeframe} rows after aggregation: "
                f"{len(source_df)}"
            )


        input_df = source_df
        # ==================================================
        # NO BRONZE DATA
        # ==================================================

        if input_df.empty:

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
                bronze_rows=0,
                validated_rows=0,
                silver_rows=0,
                status="SUCCESS",
            )

            return {
                "run_id": run_id,
                "symbol": symbol,
                "load_type": load_type,
                "status": "SUCCESS",
                "bronze_rows": 0,
                "validated_rows": 0,
                "rejected_rows": 0,
                "quarantine_rows": 0,
                "silver_rows": 0,
            }

        # ==================================================
        # 2. VALIDATE FULL CALCULATION CONTEXT
        # ==================================================

        current_stage = "validation"

        valid_df, rejected_df = (
            validate_bronze_data(
                input_df
            )
        )

        # ==================================================
        # INCREMENTAL QUARANTINE RANGE
        #
        # Historical context may contain old bad records.
        #
        # We do NOT want an incremental run to quarantine
        # those old rows again.
        #
        # Therefore:
        #
        # validation uses all context
        # quarantine stores only newly affected range
        # ==================================================

        if load_type == "INCREMENTAL":

            rejected_output_df = (
                _filter_date_range(
                    df=rejected_df,
                    date_column="date",
                    start_date=start_date,
                    end_date=end_date,
                )
            )

        else:

            rejected_output_df = (
                rejected_df.copy()
            )

        rejected_rows = len(
            rejected_output_df
        )

        print(
            f"[{symbol}] "
            f"Valid context rows: "
            f"{len(valid_df)}"
        )

        print(
            f"[{symbol}] "
            f"Rejected output rows: "
            f"{rejected_rows}"
        )

        # ==================================================
        # 3. QUARANTINE
        # ==================================================

        if not rejected_output_df.empty:

            current_stage = (
                "quarantine_load"
            )

            quarantine_rows = (
                load_quarantine_data(
                    client=client,
                    rejected_df=(
                        rejected_output_df
                    ),
                    run_id=run_id,
                    load_type=load_type,
                    source_table=SOURCE_TABLE,
                )
            )

            print(
                f"[{symbol}] "
                f"Quarantine rows: "
                f"{quarantine_rows}"
            )

        else:

            print(
                f"[{symbol}] "
                "Quarantine rows: 0"
            )

        # ==================================================
        # NO VALID DATA
        # ==================================================

        if valid_df.empty:

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
                validated_rows=0,
                silver_rows=0,
                status="SUCCESS",
            )

            return {
                "run_id": run_id,
                "symbol": symbol,
                "load_type": load_type,
                "status": "SUCCESS",
                "bronze_rows": bronze_rows,
                "validated_rows": 0,
                "rejected_rows": (
                    rejected_rows
                ),
                "quarantine_rows": (
                    quarantine_rows
                ),
                "silver_rows": 0,
            }

        # ==================================================
        # 4. INDICATORS
        #
        # IMPORTANT:
        #
        # Calculate using ALL valid historical context.
        # ==================================================

        current_stage = "indicators"

        calculated_df = (
            calculate_indicators(
                valid_df
            )
        )

        print(
            f"[{symbol}] "
            f"Calculated indicator rows: "
            f"{len(calculated_df)}"
        )

        # ==================================================
        # 5. OUTPUT RANGE
        #
        # Historical:
        #     write calculated dataframe normally.
        #
        # Incremental:
        #     historical rows were used only as calculation
        #     context.
        #
        #     Only the requested incremental period is
        #     written into Silver.
        # ==================================================

        if load_type == "INCREMENTAL":

            silver_df = (
                _filter_date_range(
                    df=calculated_df,
                    date_column="timestamp",
                    start_date=start_date,
                    end_date=end_date,
                )
            )

        else:

            silver_df = (
                calculated_df.copy()
            )

        validated_rows = len(
            silver_df
        )

        print(
            f"[{symbol}] "
            f"Silver output rows after "
            f"range filter: "
            f"{validated_rows}"
        )

        # ==================================================
        # NO OUTPUT ROWS
        # ==================================================

        if silver_df.empty:

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
                validated_rows=0,
                silver_rows=0,
                status="SUCCESS",
            )

            return {
                "run_id": run_id,
                "symbol": symbol,
                "load_type": load_type,
                "status": "SUCCESS",
                "bronze_rows": bronze_rows,
                "validated_rows": 0,
                "rejected_rows": (
                    rejected_rows
                ),
                "quarantine_rows": (
                    quarantine_rows
                ),
                "silver_rows": 0,
            }

        # ==================================================
        # 6. SILVER LOAD
        # ==================================================

        current_stage = "silver_load"

        silver_rows = (
            load_silver_data(
            client=client,
            df=silver_df,
            target_table=TARGET_TABLE,
            )
        )

        print(
            f"[{symbol}] "
            f"Silver rows processed: "
            f"{silver_rows}"
        )

        # ==================================================
        # 7. SUCCESS AUDIT
        # ==================================================

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

        # ==================================================
        # RESULT
        # ==================================================

        return {
            "run_id": run_id,
            "symbol": symbol,
            "load_type": load_type,
            "status": "SUCCESS",
            "bronze_rows": bronze_rows,
            "validated_rows": (
                validated_rows
            ),
            "rejected_rows": (
                rejected_rows
            ),
            "quarantine_rows": (
                quarantine_rows
            ),
            "silver_rows": (
                silver_rows
            ),
        }

    except Exception as exc:
        # ==================================================
        # FAILURE AUDIT
        # ==================================================

        completed_at = datetime.now(
            timezone.utc
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
                validated_rows=(
                    validated_rows
                ),
                silver_rows=(
                    silver_rows
                ),
                status="FAILED",
                failed_stage=(
                    current_stage
                ),
                error_type=(
                    type(exc).__name__
                ),
                error_message=(
                    str(exc)[:2000]
                ),
            )

        except Exception as audit_exc:

            print(
                f"[{symbol}] "
                f"Audit logging also failed: "
                f"{audit_exc}"
            )

        raise
