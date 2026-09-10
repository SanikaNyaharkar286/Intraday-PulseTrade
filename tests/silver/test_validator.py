import pandas as pd
import pytest

from src.transform.silver.validator import (
    validate_bronze_data,
)


def make_valid_row(**overrides):
    row = {
        "date": "2024-03-18T09:16:00",
        "open": 100.0,
        "high": 110.0,
        "low": 90.0,
        "close": 105.0,
        "volume": 1000.0,
        "symbol": "TEST",
    }

    row.update(overrides)

    return row


def test_valid_row_goes_to_valid_df():
    df = pd.DataFrame([
        make_valid_row()
    ])

    valid_df, rejected_df = validate_bronze_data(df)

    assert len(valid_df) == 1
    assert len(rejected_df) == 0


def test_invalid_date_is_rejected():
    df = pd.DataFrame([
        make_valid_row(
            date="invalid-date"
        )
    ])

    valid_df, rejected_df = validate_bronze_data(df)

    assert len(valid_df) == 0
    assert len(rejected_df) == 1

    assert (
        "INVALID_DATE"
        in rejected_df.iloc[0]["failure_reason"]
    )


def test_invalid_numeric_value_is_rejected():
    df = pd.DataFrame([
        make_valid_row(
            open="abc"
        )
    ])

    valid_df, rejected_df = validate_bronze_data(df)

    assert len(valid_df) == 0
    assert len(rejected_df) == 1

    assert (
        "INVALID_OPEN"
        in rejected_df.iloc[0]["failure_reason"]
    )


def test_high_less_than_low_is_rejected():
    df = pd.DataFrame([
        make_valid_row(
            high=80.0,
            low=90.0,
        )
    ])

    valid_df, rejected_df = validate_bronze_data(df)

    assert len(valid_df) == 0

    assert (
        "HIGH_LESS_THAN_LOW"
        in rejected_df.iloc[0]["failure_reason"]
    )


def test_high_less_than_open_is_rejected():
    df = pd.DataFrame([
        make_valid_row(
            open=120.0,
            high=110.0,
        )
    ])

    valid_df, rejected_df = validate_bronze_data(df)

    assert len(valid_df) == 0

    assert (
        "HIGH_LESS_THAN_OPEN"
        in rejected_df.iloc[0]["failure_reason"]
    )


def test_high_less_than_close_is_rejected():
    df = pd.DataFrame([
        make_valid_row(
            close=120.0,
            high=110.0,
        )
    ])

    valid_df, rejected_df = validate_bronze_data(df)

    assert len(valid_df) == 0

    assert (
        "HIGH_LESS_THAN_CLOSE"
        in rejected_df.iloc[0]["failure_reason"]
    )


def test_low_greater_than_open_is_rejected():
    df = pd.DataFrame([
        make_valid_row(
            open=80.0,
            low=90.0,
        )
    ])

    valid_df, rejected_df = validate_bronze_data(df)

    assert len(valid_df) == 0

    assert (
        "LOW_GREATER_THAN_OPEN"
        in rejected_df.iloc[0]["failure_reason"]
    )


def test_low_greater_than_close_is_rejected():
    df = pd.DataFrame([
        make_valid_row(
            close=80.0,
            low=90.0,
        )
    ])

    valid_df, rejected_df = validate_bronze_data(df)

    assert len(valid_df) == 0

    assert (
        "LOW_GREATER_THAN_CLOSE"
        in rejected_df.iloc[0]["failure_reason"]
    )


def test_negative_volume_is_rejected():
    df = pd.DataFrame([
        make_valid_row(
            volume=-100
        )
    ])

    valid_df, rejected_df = validate_bronze_data(df)

    assert len(valid_df) == 0

    assert (
        "NEGATIVE_VOLUME"
        in rejected_df.iloc[0]["failure_reason"]
    )


def test_zero_volume_is_allowed():
    df = pd.DataFrame([
        make_valid_row(
            volume=0
        )
    ])

    valid_df, rejected_df = validate_bronze_data(df)

    assert len(valid_df) == 1
    assert len(rejected_df) == 0


def test_duplicate_symbol_date_is_rejected():
    row = make_valid_row()

    df = pd.DataFrame([
        row,
        row.copy(),
    ])

    valid_df, rejected_df = validate_bronze_data(df)

    assert len(valid_df) == 0
    assert len(rejected_df) == 2

    assert all(
        rejected_df["failure_reason"]
        .str.contains("DUPLICATE_SYMBOL_DATE")
    )


def test_blank_symbol_is_rejected():
    df = pd.DataFrame([
        make_valid_row(
            symbol="   "
        )
    ])

    valid_df, rejected_df = validate_bronze_data(df)

    assert len(valid_df) == 0

    assert (
        "INVALID_SYMBOL"
        in rejected_df.iloc[0]["failure_reason"]
    )


def test_missing_required_column_raises_error():
    df = pd.DataFrame([
        make_valid_row()
    ])

    df = df.drop(
        columns=["volume"]
    )

    with pytest.raises(
        ValueError,
        match="Missing required Bronze columns"
    ):
        validate_bronze_data(df)


def test_valid_data_is_sorted_by_symbol_and_date():
    df = pd.DataFrame([
        make_valid_row(
            symbol="BBB",
            date="2024-03-18T09:20:00",
        ),
        make_valid_row(
            symbol="AAA",
            date="2024-03-18T09:18:00",
        ),
        make_valid_row(
            symbol="AAA",
            date="2024-03-18T09:16:00",
        ),
    ])

    valid_df, rejected_df = validate_bronze_data(df)

    assert len(rejected_df) == 0

    assert valid_df["symbol"].tolist() == [
        "AAA",
        "AAA",
        "BBB",
    ]

    assert valid_df["date"].tolist() == [
        pd.Timestamp("2024-03-18 09:16:00"),
        pd.Timestamp("2024-03-18 09:18:00"),
        pd.Timestamp("2024-03-18 09:20:00"),
    ]

def test_zero_ohlc_goes_to_rejected():

    df = pd.DataFrame(
        {
            "symbol": ["TEST"],
            "date": [
                "2024-01-01 09:15:00"
            ],
            "open": [0],
            "high": [0],
            "low": [0],
            "close": [0],
            "volume": [100],
        }
    )

    valid_df, rejected_df = (
        validate_bronze_data(df)
    )

    assert len(valid_df) == 0
    assert len(rejected_df) == 1

    assert (
    "NON_POSITIVE_OHLC"
    in rejected_df.iloc[0][
        "failure_reason"
    ]
)
def test_any_zero_price_goes_to_rejected():

    df = pd.DataFrame(
        {
            "symbol": [
                "TEST1",
                "TEST2",
                "TEST3",
                "TEST4",
            ],
            "date": [
                "2024-01-01 09:15:00",
                "2024-01-01 09:16:00",
                "2024-01-01 09:17:00",
                "2024-01-01 09:18:00",
            ],
            "open": [
                0,
                100,
                100,
                100,
            ],
            "high": [
                101,
                0,
                101,
                101,
            ],
            "low": [
                99,
                99,
                0,
                99,
            ],
            "close": [
                100,
                100,
                100,
                0,
            ],
            "volume": [
                100,
                100,
                100,
                100,
            ],
        }
    )

    valid_df, rejected_df = (
        validate_bronze_data(df)
    )

    assert len(valid_df) == 0
    assert len(rejected_df) == 4
def test_zero_volume_is_allowed():

    df = pd.DataFrame(
        {
            "symbol": ["TEST"],
            "date": [
                "2024-01-01 09:15:00"
            ],
            "open": [100],
            "high": [101],
            "low": [99],
            "close": [100],
            "volume": [0],
        }
    )

    valid_df, rejected_df = (
        validate_bronze_data(df)
    )

    assert len(valid_df) == 1
    assert len(rejected_df) == 0