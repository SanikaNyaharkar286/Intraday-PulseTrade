import pandas as pd


def _normalize_resample_rule(timeframe):

    if isinstance(timeframe, int):

        if timeframe == 1440:
            return "1D"

        return f"{timeframe}min"


    timeframe = (
        str(timeframe)
        .strip()
        .lower()
    )


    mapping = {

        "5min": "5min",

        "15min": "15min",

        "1hour": "1h",

        "hour": "1h",

        "daily": "1D",

        "day": "1D",

    }


    return mapping.get(
        timeframe,
        timeframe
    )



def aggregate_timeframe(
    df: pd.DataFrame,
    timeframe: str,
) -> pd.DataFrame:


    if df.empty:
        return df


    df = df.copy()


    df["date"] = pd.to_datetime(
        df["date"]
    )


    df = (
        df
        .sort_values(
            [
                "symbol",
                "date"
            ]
        )
    )


    rule = _normalize_resample_rule(
        timeframe
    )


    # ======================================================
    # Market session alignment
    # Only hourly candles need offset.
    #
    # 09:15 -> 10:15 -> 11:15
    #
    # 5min and 15min already align correctly.
    # Daily should start from midnight.
    # ======================================================

    resample_config = {

        "label": "left",

        "closed": "left"

    }


    if rule == "1h":

        resample_config.update(

            {

                "origin": "start_day",

                "offset": "15min"

            }

        )


    result = (

        df

        .set_index("date")

        .groupby("symbol")

        .resample(
            rule,
            **resample_config
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