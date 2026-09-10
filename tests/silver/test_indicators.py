import pandas as pd

from src.transform.silver.indicators import (
    calculate_indicators,
)


# ==========================================================
# TEST DATA
# ==========================================================

def create_market_data(
    symbol="360ONE",
    start="2024-03-18 09:15:00",
    periods=60,
):
    timestamps = pd.date_range(
        start=start,
        periods=periods,
        freq="1min",
    )

    rows = []

    for i, timestamp in enumerate(timestamps):

        open_price = 100 + (i * 0.5)
        close_price = open_price + 0.25

        rows.append(
            {
                "symbol": symbol,
                "timestamp": timestamp,
                "open": open_price,
                "high": open_price + 1,
                "low": open_price - 1,
                "close": close_price,
                "volume": 1000 + (i * 10),
            }
        )

    return pd.DataFrame(rows)


# ==========================================================
# BASIC TESTS
# ==========================================================

def test_row_count_preserved():

    df = create_market_data()

    result = calculate_indicators(df)

    assert len(result) == len(df)


def test_all_indicator_columns_created():

    df = create_market_data()

    result = calculate_indicators(df)

    expected_columns = [
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

    for column in expected_columns:
        assert column in result.columns


# ==========================================================
# SMA
# ==========================================================

def test_sma_20():

    df = create_market_data(
        periods=30
    )

    result = calculate_indicators(df)

    # SMA 20 should not exist before 20 rows
    assert pd.isna(
        result.iloc[18]["sma_20"]
    )

    # 20th row should contain SMA
    assert pd.notna(
        result.iloc[19]["sma_20"]
    )

    expected = (
        result.iloc[0:20]["close"]
        .mean()
    )

    assert abs(
        result.iloc[19]["sma_20"]
        - expected
    ) < 0.000001


# ==========================================================
# EMA
# ==========================================================

def test_ema_9_created():

    df = create_market_data(
        periods=30
    )

    result = calculate_indicators(df)

    assert (
        result["ema_9"]
        .notna()
        .any()
    )


def test_ema_20_created():

    df = create_market_data(
        periods=30
    )

    result = calculate_indicators(df)

    assert (
        result["ema_20"]
        .notna()
        .any()
    )


# ==========================================================
# RSI
# ==========================================================

def test_rsi_14_created():

    df = create_market_data(
        periods=30
    )

    result = calculate_indicators(df)

    assert (
        result["rsi_14"]
        .notna()
        .any()
    )


# ==========================================================
# MACD
# ==========================================================

def test_macd_created():

    df = create_market_data(
        periods=60
    )

    result = calculate_indicators(df)

    assert (
        result["macd"]
        .notna()
        .any()
    )

    assert (
        result["macd_signal"]
        .notna()
        .any()
    )


def test_macd_histogram_formula():

    df = create_market_data(
        periods=60
    )

    result = calculate_indicators(df)

    valid_rows = result.dropna(
        subset=[
            "macd",
            "macd_signal",
            "macd_histogram",
        ]
    )

    assert len(valid_rows) > 0

    row = valid_rows.iloc[-1]

    expected = (
        row["macd"]
        - row["macd_signal"]
    )

    assert abs(
        row["macd_histogram"]
        - expected
    ) < 0.000001


# ==========================================================
# ATR %
# ==========================================================

def test_atr_pct_formula():

    df = create_market_data(
        periods=40
    )

    result = calculate_indicators(df)

    valid_rows = result.dropna(
        subset=[
            "atr_14",
            "atr_pct",
        ]
    )

    assert len(valid_rows) > 0

    row = valid_rows.iloc[-1]

    expected = (
        row["atr_14"]
        / row["close"]
        * 100
    )

    assert abs(
        row["atr_pct"]
        - expected
    ) < 0.000001


# ==========================================================
# RELATIVE VOLUME
# ==========================================================

def test_relative_volume_formula():

    df = create_market_data(
        periods=40
    )

    result = calculate_indicators(df)

    valid_rows = result.dropna(
        subset=[
            "volume_sma_20",
            "relative_volume_20",
        ]
    )

    row = valid_rows.iloc[-1]

    expected = (
        row["volume"]
        / row["volume_sma_20"]
    )

    assert abs(
        row["relative_volume_20"]
        - expected
    ) < 0.000001


# ==========================================================
# VWAP
# ==========================================================

def test_first_row_vwap():

    df = create_market_data(
        periods=30
    )

    result = calculate_indicators(df)

    first = result.iloc[0]

    expected = (
        first["high"]
        + first["low"]
        + first["close"]
    ) / 3

    assert abs(
        first["vwap"]
        - expected
    ) < 0.000001


# ==========================================================
# VWAP SESSION RESET
# ==========================================================

def test_vwap_resets_on_new_trading_day():

    day1 = create_market_data(
        start="2024-03-18 15:25:00",
        periods=5,
    )

    day2 = create_market_data(
        start="2024-03-19 09:15:00",
        periods=5,
    )

    df = pd.concat(
        [
            day1,
            day2,
        ],
        ignore_index=True,
    )

    result = calculate_indicators(df)

    day2_first = result[
        result["timestamp"].dt.date
        == pd.Timestamp(
            "2024-03-19"
        ).date()
    ].iloc[0]

    expected = (
        day2_first["high"]
        + day2_first["low"]
        + day2_first["close"]
    ) / 3

    assert abs(
        day2_first["vwap"]
        - expected
    ) < 0.000001


# ==========================================================
# PREVIOUS SESSION CLOSE
# ==========================================================

def test_previous_session_close():

    day1 = create_market_data(
        start="2024-03-18 15:25:00",
        periods=5,
    )

    day2 = create_market_data(
        start="2024-03-19 09:15:00",
        periods=5,
    )

    df = pd.concat(
        [
            day1,
            day2,
        ],
        ignore_index=True,
    )

    result = calculate_indicators(df)

    expected_previous_close = (
        day1.iloc[-1]["close"]
    )

    day2_result = result[
        result["timestamp"].dt.date
        == pd.Timestamp(
            "2024-03-19"
        ).date()
    ]

    assert (
        day2_result[
            "previous_session_close"
        ]
        == expected_previous_close
    ).all()


# ==========================================================
# GAP %
# ==========================================================

def test_gap_pct_formula():

    day1 = create_market_data(
        start="2024-03-18 15:25:00",
        periods=5,
    )

    day2 = create_market_data(
        start="2024-03-19 09:15:00",
        periods=5,
    )

    df = pd.concat(
        [
            day1,
            day2,
        ],
        ignore_index=True,
    )

    result = calculate_indicators(df)

    day2_result = result[
        result["timestamp"].dt.date
        == pd.Timestamp(
            "2024-03-19"
        ).date()
    ]

    row = day2_result.iloc[0]

    expected = (
        (
            row["open"]
            - row["previous_session_close"]
        )
        / row["previous_session_close"]
        * 100
    )

    assert abs(
        row["gap_pct"]
        - expected
    ) < 0.000001


# ==========================================================
# PRICE CHANGE %
# ==========================================================

def test_price_change_pct_formula():

    df = create_market_data()

    result = calculate_indicators(df)

    row = result.iloc[0]

    expected = (
        (
            row["close"]
            - row["open"]
        )
        / row["open"]
        * 100
    )

    assert abs(
        row["price_change_pct"]
        - expected
    ) < 0.000001


# ==========================================================
# METADATA
# ==========================================================

def test_indicator_version():

    df = create_market_data()

    result = calculate_indicators(df)

    assert (
        result["indicator_version"]
        == "v2.0"
    ).all()


def test_processed_at_created():

    df = create_market_data()

    result = calculate_indicators(df)

    assert (
        result["processed_at"]
        .notna()
        .all()
    )