from google.cloud import bigquery

from src.transform.silver.validator import validate_ohlcv
from src.transform.silver.indicators import calculate_indicators


PROJECT_ID = "project-001658fa-3ce5-4746-980"

BRONZE_TABLE = (
    f"{PROJECT_ID}."
    "migration_bronze_v2."
    "market_prices"
)


def test_real_bronze_360one():

    client = bigquery.Client(
        project=PROJECT_ID,
        location="us-east1",
    )

    query = f"""
        SELECT
            symbol,
            date,
            open,
            high,
            low,
            close,
            volume
        FROM `{BRONZE_TABLE}`
        WHERE symbol = '360ONE'
        ORDER BY date
    """

    print("\nReading 360ONE from Bronze...")

    df = client.query(query).to_dataframe()

    assert len(df) > 0

    print(f"Bronze rows: {len(df)}")

    # Match indicator input format
    df = df.rename(
        columns={
            "date": "timestamp"
        }
    )

    # Validate Bronze data
    valid_df = validate_ohlcv(df)

    print(
        f"Rows after validation: {len(valid_df)}"
    )

    assert len(valid_df) > 0

    # Calculate indicators
    result = calculate_indicators(valid_df)

    print(
        f"Rows after indicators: {len(result)}"
    )

    # Row count must remain unchanged
    assert len(result) == len(valid_df)

    # Required columns
    expected_columns = [
        "timestamp",
        "symbol",
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
    ]

    for column in expected_columns:

        assert column in result.columns, (
            f"Missing column: {column}"
        )

    # Basic range checks
    rsi = result["rsi_14"].dropna()

    assert (rsi >= 0).all()
    assert (rsi <= 100 + 1e-10).all()

    stoch_k = result["stoch_k"].dropna()

    assert (stoch_k >= 0).all()
    assert (stoch_k <= 100).all()

    stoch_d = result["stoch_d"].dropna()

    assert (stoch_d >= 0).all()
    assert (stoch_d <= 100).all()

    atr = result["atr_14"].dropna()

    assert (atr >= 0).all()

    adx = result["adx_14"].dropna()

    assert (adx >= 0).all()

    # Duplicate check
    duplicates = result.duplicated(
        subset=["symbol", "timestamp"]
    )

    assert duplicates.sum() == 0

    print("\nREAL BRONZE TEST PASSED")