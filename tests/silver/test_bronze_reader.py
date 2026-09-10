import pandas as pd

from src.transform.silver.bronze_reader import (
    read_bronze_data,
)


class FakeResult:

    def to_dataframe(self):

        return pd.DataFrame(
            [
                {
                    "date": pd.Timestamp(
                        "2024-03-18 09:16:00"
                    ),
                    "open": 689.65,
                    "high": 691.35,
                    "low": 682.35,
                    "close": 684.05,
                    "volume": 2577.0,
                    "symbol": "360ONE",
                }
            ]
        )


class FakeQueryJob:

    def result(self):
        return FakeResult()


class FakeBigQueryClient:

    def query(
        self,
        query,
        job_config=None,
    ):
        return FakeQueryJob()


def test_read_bronze_data_returns_dataframe():

    client = FakeBigQueryClient()

    df = read_bronze_data(
        client=client,
        symbol="360ONE",
    )

    assert isinstance(
        df,
        pd.DataFrame,
    )

    assert len(df) == 1

    assert (
        df.iloc[0]["symbol"]
        == "360ONE"
    )


def test_expected_bronze_columns_exist():

    client = FakeBigQueryClient()

    df = read_bronze_data(
        client=client,
        symbol="360ONE",
    )

    expected_columns = [
        "date",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "symbol",
    ]

    assert (
        df.columns.tolist()
        == expected_columns
    )


def test_blank_symbol_is_not_allowed():

    client = FakeBigQueryClient()

    try:

        read_bronze_data(
            client=client,
            symbol="   ",
        )

        assert False

    except ValueError as exc:

        assert (
            "symbol is required"
            in str(exc)
        )