import pandas as pd


def _normalize_resample_rule(timeframe):
    """
    Convert timeframe configuration into pandas resample format.

    Examples:
        5      -> "5min"
        15     -> "15min"
        60     -> "60min"
        1440   -> "1D"
        "5min" -> "5min"
        "1D"   -> "1D"
    """

    if isinstance(timeframe, int):

        if timeframe == 1440:
            return "1D"

        return f"{timeframe}min"


    timeframe = (
        str(timeframe)
        .strip()
        .lower()
    )


    if timeframe in {"daily", "day"}:
        return "1D"


    return timeframe



def aggregate_timeframe(
    df: pd.DataFrame,
    timeframe: str,
) -> pd.DataFrame:
    """
    Convert 1 minute OHLCV data into higher timeframe candles.

    Input:
        1 minute bronze data

    Output:
        Aggregated OHLCV dataframe
    """

    if df.empty:
        return df


    df = df.copy()


    # Normalize pandas frequency
    timeframe = _normalize_resample_rule(
        timeframe
    )


    df["date"] = pd.to_datetime(
        df["date"]
    )


    df = (
        df
        .sort_values(
            [
                "symbol",
                "date",
            ]
        )
    )


    result = (
        df
        .set_index("date")
        .groupby("symbol")
        .resample(
            timeframe,
            label="left",
            closed="left"
        )
        .agg(
            {
                "open": "first",
                "high": "max",
                "low": "min",
                "close": "last",
                "volume": "sum",
            }
        )
        .dropna()
        .reset_index()
    )


    return result