from pathlib import Path
from datetime import timedelta
import sys

import pandas as pd
from google.cloud import bigquery


# ==========================================================
# PROJECT ROOT
#
# Allows this script to be executed directly:
#
# python tests/incremental/generate_incremental_test_csv.py
# ==========================================================

PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[2]
)

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT)
    )


from src.utils.config import (
    GCP_PROJECT_ID,
    BQ_SILVER_DATASET,
)
# ==========================================================
# TEST CONFIGURATION
# ==========================================================

SYMBOL = "360ONE"

SILVER_TABLE = (
    f"{GCP_PROJECT_ID}."
    f"{BQ_SILVER_DATASET}."
    f"silver_1min"
)

OUTPUT_DIR = Path(
    "tests/incremental/generated"
)

OUTPUT_FILE = (
    OUTPUT_DIR
    / f"{SYMBOL}_minute_new.csv"
)


# ==========================================================
# FETCH LAST SILVER TIMESTAMP
# ==========================================================

def get_last_silver_timestamp(
    client: bigquery.Client,
    symbol: str,
) -> pd.Timestamp:
    """
    Find the most recent timestamp already available
    in silver_1min for the test symbol.
    """

    query = f"""
    SELECT
        MAX(date) AS last_timestamp

    FROM `{SILVER_TABLE}`

    WHERE symbol = @symbol
    """

    job_config = (
        bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter(
                    "symbol",
                    "STRING",
                    symbol,
                )
            ]
        )
    )

    row = next(
        iter(
            client.query(
                query,
                job_config=job_config,
            ).result()
        )
    )

    if row.last_timestamp is None:

        raise RuntimeError(
            f"No existing Silver data found "
            f"for {symbol}."
        )

    return pd.Timestamp(
        row.last_timestamp
    )


# ==========================================================
# FIND NEXT BUSINESS DAY
# ==========================================================

def get_next_business_day(
    timestamp: pd.Timestamp,
) -> pd.Timestamp:
    """
    Move to the next Monday-Friday date.

    This does not attempt to model exchange holidays.
    It is sufficient for our controlled incremental test.
    """

    next_day = (
        timestamp.normalize()
        + pd.Timedelta(days=1)
    )

    while next_day.weekday() >= 5:

        next_day += pd.Timedelta(
            days=1
        )

    return next_day


# ==========================================================
# GENERATE VALID TEST ROWS
# ==========================================================

def generate_valid_rows(
    trading_day: pd.Timestamp,
) -> list[dict]:
    """
    Generate deterministic valid one-minute OHLCV rows.

    We use enough valid rows to verify that the new
    incremental range enters Bronze and Silver correctly.
    """

    rows = []

    start_timestamp = (
        trading_day
        + pd.Timedelta(
            hours=9,
            minutes=15,
        )
    )

    base_price = 1000.0

    # ------------------------------------------------------
    # 30 valid one-minute records
    # ------------------------------------------------------

    for index in range(30):

        timestamp = (
            start_timestamp
            + pd.Timedelta(
                minutes=index
            )
        )

        open_price = (
            base_price
            + index
        )

        close_price = (
            open_price
            + 0.50
        )

        high_price = (
            close_price
            + 1.00
        )

        low_price = (
            open_price
            - 1.00
        )

        volume = (
            1000
            + (index * 10)
        )

        rows.append(
            {
                "date": timestamp.strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "open": open_price,
                "high": high_price,
                "low": low_price,
                "close": close_price,
                "volume": volume,
            }
        )

    return rows


# ==========================================================
# ADD SILVER VALIDATION EDGE CASES
# ==========================================================

def add_validation_edge_cases(
    rows: list[dict],
    trading_day: pd.Timestamp,
) -> list[dict]:
    """
    Add controlled invalid records.

    These records are intended to reach the Silver
    validator and be routed to silver_quarantine.
    """

    edge_start = (
        trading_day
        + pd.Timedelta(
            hours=10,
            minutes=30,
        )
    )

    # ======================================================
    # 1. ZERO OHLC
    # ======================================================

    rows.append(
        {
            "date": (
                edge_start
            ).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "open": 0,
            "high": 0,
            "low": 0,
            "close": 0,
            "volume": 100,
        }
    )

    # ======================================================
    # 2. OPEN = 0
    # ======================================================

    rows.append(
        {
            "date": (
                edge_start
                + timedelta(minutes=1)
            ).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "open": 0,
            "high": 1002,
            "low": 999,
            "close": 1001,
            "volume": 100,
        }
    )

    # ======================================================
    # 3. HIGH < LOW
    # ======================================================

    rows.append(
        {
            "date": (
                edge_start
                + timedelta(minutes=2)
            ).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "open": 1000,
            "high": 995,
            "low": 999,
            "close": 998,
            "volume": 100,
        }
    )

    # ======================================================
    # 4. HIGH < OPEN
    # ======================================================

    rows.append(
        {
            "date": (
                edge_start
                + timedelta(minutes=3)
            ).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "open": 1000,
            "high": 999,
            "low": 995,
            "close": 998,
            "volume": 100,
        }
    )

    # ======================================================
    # 5. HIGH < CLOSE
    # ======================================================

    rows.append(
        {
            "date": (
                edge_start
                + timedelta(minutes=4)
            ).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "open": 1000,
            "high": 1001,
            "low": 998,
            "close": 1002,
            "volume": 100,
        }
    )

    # ======================================================
    # 6. LOW > OPEN
    # ======================================================

    rows.append(
        {
            "date": (
                edge_start
                + timedelta(minutes=5)
            ).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "open": 1000,
            "high": 1005,
            "low": 1001,
            "close": 1003,
            "volume": 100,
        }
    )

    # ======================================================
    # 7. LOW > CLOSE
    # ======================================================

    rows.append(
        {
            "date": (
                edge_start
                + timedelta(minutes=6)
            ).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "open": 1003,
            "high": 1005,
            "low": 1002,
            "close": 1001,
            "volume": 100,
        }
    )

    # ======================================================
    # 8. NEGATIVE VOLUME
    # ======================================================

    rows.append(
        {
            "date": (
                edge_start
                + timedelta(minutes=7)
            ).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "open": 1000,
            "high": 1005,
            "low": 995,
            "close": 1002,
            "volume": -100,
        }
    )

    # ======================================================
    # 9. ZERO VOLUME
    #
    # IMPORTANT:
    # This is VALID and should reach Silver.
    # ======================================================

    rows.append(
        {
            "date": (
                edge_start
                + timedelta(minutes=8)
            ).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "open": 1000,
            "high": 1005,
            "low": 995,
            "close": 1002,
            "volume": 0,
        }
    )

    # ======================================================
    # 10. INVALID OPEN
    #
    # Bronze SAFE_CAST will convert this to NULL.
    # Silver validator should reject it as INVALID_OPEN.
    # ======================================================

    rows.append(
        {
            "date": (
                edge_start
                + timedelta(minutes=9)
            ).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "open": "BAD_OPEN",
            "high": 1005,
            "low": 995,
            "close": 1002,
            "volume": 100,
        }
    )

    # ======================================================
    # 11. INVALID CLOSE
    # ======================================================

    rows.append(
        {
            "date": (
                edge_start
                + timedelta(minutes=10)
            ).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "open": 1000,
            "high": 1005,
            "low": 995,
            "close": "BAD_CLOSE",
            "volume": 100,
        }
    )

    return rows


# ==========================================================
# GENERATE TEST FILE
# ==========================================================

def generate_incremental_test_file():

    client = bigquery.Client(
        project=GCP_PROJECT_ID
    )

    # ======================================================
    # FIND CURRENT SILVER END
    # ======================================================

    last_timestamp = (
        get_last_silver_timestamp(
            client=client,
            symbol=SYMBOL,
        )
    )

    print(
        "\nExisting Silver last timestamp:"
    )

    print(
        last_timestamp
    )

    # ======================================================
    # CREATE NEXT TEST TRADING DAY
    # ======================================================

    trading_day = (
        get_next_business_day(
            last_timestamp
        )
    )

    print(
        "\nSynthetic incremental trading date:"
    )

    print(
        trading_day.date()
    )

    # ======================================================
    # VALID ROWS
    # ======================================================

    rows = generate_valid_rows(
        trading_day
    )

    valid_test_rows = len(
        rows
    )

    # ======================================================
    # EDGE CASES
    # ======================================================

    rows = add_validation_edge_cases(
        rows=rows,
        trading_day=trading_day,
    )

    # ======================================================
    # CREATE DATAFRAME
    # ======================================================

    df = pd.DataFrame(
        rows
    )

    # ======================================================
    # OUTPUT DIRECTORY
    # ======================================================

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # ======================================================
    # WRITE CSV
    # ======================================================

    df.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    # ======================================================
    # SUMMARY
    # ======================================================

    print(
        "\n"
        + "=" * 70
    )

    print(
        "INCREMENTAL TEST FILE GENERATED"
    )

    print(
        "=" * 70
    )

    print(
        f"Symbol: {SYMBOL}"
    )

    print(
        f"Previous Silver end: "
        f"{last_timestamp}"
    )

    print(
        f"New test date: "
        f"{trading_day.date()}"
    )

    print(
        f"Valid base rows: "
        f"{valid_test_rows}"
    )

    print(
        f"Total CSV rows: "
        f"{len(df)}"
    )

    print(
        f"Edge-case rows: "
        f"{len(df) - valid_test_rows}"
    )

    print(
        f"Output file: "
        f"{OUTPUT_FILE}"
    )

    print(
        "=" * 70
    )

    print(
        "\nExpected Silver behavior:"
    )

    print(
        "  ZERO OHLC       -> quarantine"
    )

    print(
        "  OPEN = 0        -> quarantine"
    )

    print(
        "  HIGH < LOW      -> quarantine"
    )

    print(
        "  HIGH < OPEN     -> quarantine"
    )

    print(
        "  HIGH < CLOSE    -> quarantine"
    )

    print(
        "  LOW > OPEN      -> quarantine"
    )

    print(
        "  LOW > CLOSE     -> quarantine"
    )

    print(
        "  Negative volume -> quarantine"
    )

    print(
        "  BAD_OPEN        -> quarantine"
    )

    print(
        "  BAD_CLOSE       -> quarantine"
    )

    print(
        "  Zero volume     -> VALID"
    )


# ==========================================================
# ENTRY POINT
# ==========================================================

if __name__ == "__main__":

    generate_incremental_test_file()