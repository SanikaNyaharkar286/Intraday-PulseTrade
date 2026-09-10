import pandas as pd

from src.transform.silver.timeframe.aggregator import (
    aggregate_timeframe,
)


def test_5min_aggregation():

    df = pd.DataFrame(
        {
            "symbol": [
                "360ONE",
                "360ONE",
                "360ONE",
                "360ONE",
                "360ONE",
            ],
            "date": [
                "2026-04-09 09:15:00",
                "2026-04-09 09:16:00",
                "2026-04-09 09:17:00",
                "2026-04-09 09:18:00",
                "2026-04-09 09:19:00",
            ],
            "open": [
                100,
                101,
                102,
                103,
                104,
            ],
            "high": [
                101,
                102,
                103,
                104,
                105,
            ],
            "low": [
                99,
                100,
                101,
                102,
                103,
            ],
            "close": [
                100.5,
                101.5,
                102.5,
                103.5,
                104.5,
            ],
            "volume": [
                100,
                200,
                300,
                400,
                500,
            ],
        }
    )


    result = aggregate_timeframe(
        df,
        "5min",
    )


    assert len(result) == 1


    row = result.iloc[0]


    # first open
    assert row["open"] == 100


    # maximum high
    assert row["high"] == 105


    # minimum low
    assert row["low"] == 99


    # last close
    assert row["close"] == 104.5


    # volume sum
    assert row["volume"] == 1500