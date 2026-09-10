import pandas as pd

from src.transform.silver.silver_loader import (
    load_silver_data,
)


class FakeJob:

    def result(self):
        return None


class FakeClient:

    def __init__(self):
        self.loaded = False
        self.queried = False
        self.deleted = False

    def load_table_from_dataframe(
        self,
        df,
        table,
        job_config=None,
    ):
        self.loaded = True
        return FakeJob()

    def query(
        self,
        query,
    ):
        self.queried = True
        return FakeJob()

    def delete_table(
        self,
        table,
        not_found_ok=False,
    ):
        self.deleted = True


def create_silver_df():

    return pd.DataFrame(
        [
            {
                "symbol": "360ONE",
                "timestamp": (
                    "2024-03-18 09:15:00"
                ),
                "open": 705.0,
                "high": 710.0,
                "low": 688.0,
                "close": 691.5,
                "volume": 2259.0,
                "sma_20": None,
                "ema_9": None,
                "ema_20": None,
                "rsi_14": None,
                "macd": None,
                "macd_signal": None,
                "macd_histogram": None,
                "stoch_k": None,
                "stoch_d": None,
                "atr_14": None,
                "atr_pct": None,
                "bollinger_lower": None,
                "bollinger_upper": None,
                "volume_sma_20": None,
                "relative_volume_20": None,
                "obv": 2259.0,
                "vwap": 696.5,
                "vwap_deviation_pct": -0.717875,
                "previous_session_close": None,
                "gap_pct": None,
                "adx_14": None,
                "price_change_pct": -1.914894,
                "indicator_version": "v2.0",
                "processed_at": pd.Timestamp.now(
                    tz="UTC"
                ),
            }
        ]
    )


def test_loader_runs_staging_merge_cleanup():

    client = FakeClient()

    df = create_silver_df()

    rows = load_silver_data(
        client,
        df,
    )

    assert rows == 1
    assert client.loaded is True
    assert client.queried is True
    assert client.deleted is True


def test_empty_dataframe_returns_zero():

    client = FakeClient()

    rows = load_silver_data(
        client,
        pd.DataFrame(),
    )

    assert rows == 0

    assert client.loaded is False