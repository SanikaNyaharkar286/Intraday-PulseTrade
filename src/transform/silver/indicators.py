import pandas as pd
import pandas_ta as ta


# ==========================================================
# CONFIGURATION
# ==========================================================

INDICATOR_VERSION = "v2.0"


# ==========================================================
# HELPER FUNCTIONS
# ==========================================================

def _empty_series(index):
    """
    Return a float NaN Series matching the input index.

    Used when pandas_ta cannot calculate an indicator
    because there is not enough historical data.
    """
    return pd.Series(
        float("nan"),
        index=index,
        dtype="float64",
    )


def _assign_series(
    group: pd.DataFrame,
    column_name: str,
    result,
):
    """
    Safely assign a pandas_ta Series to a dataframe column.
    """

    if result is None:
        group[column_name] = _empty_series(
            group.index
        )
    else:
        group[column_name] = result.to_numpy()


def _find_indicator_column(
    indicator_df: pd.DataFrame,
    prefix: str,
):
    """
    Find a pandas_ta output column by prefix.

    This makes the code more tolerant of small naming
    differences between pandas_ta versions.
    """

    if indicator_df is None:
        return None

    matching_columns = [
        column
        for column in indicator_df.columns
        if column.startswith(prefix)
    ]

    if not matching_columns:
        return None

    return matching_columns[0]


# ==========================================================
# CALCULATE INDICATORS FOR ONE SYMBOL
# ==========================================================

def _calculate_symbol_indicators(
    group: pd.DataFrame,
) -> pd.DataFrame:
    """
    Calculate indicators for one symbol only.

    Keeping calculation symbol-specific prevents rolling
    indicators from leaking between different stocks.
    """

    group = (
        group.copy()
        .sort_values("timestamp")
        .reset_index(drop=True)
    )

    # ======================================================
    # 1. SMA 20
    # ======================================================

    sma_20 = ta.sma(
        group["close"],
        length=20,
    )

    _assign_series(
        group,
        "sma_20",
        sma_20,
    )

    # ======================================================
    # 2. EMA 9
    # ======================================================

    ema_9 = ta.ema(
        group["close"],
        length=9,
    )

    _assign_series(
        group,
        "ema_9",
        ema_9,
    )

    # ======================================================
    # 3. EMA 20
    # ======================================================

    ema_20 = ta.ema(
        group["close"],
        length=20,
    )

    _assign_series(
        group,
        "ema_20",
        ema_20,
    )

    # ======================================================
    # 4. RSI 14
    # ======================================================

    rsi_14 = ta.rsi(
        group["close"],
        length=14,
    )

    _assign_series(
        group,
        "rsi_14",
        rsi_14,
    )

    # ======================================================
    # 5-7. MACD
    # ======================================================

    macd_result = ta.macd(
        group["close"],
        fast=12,
        slow=26,
        signal=9,
    )

    if macd_result is not None:

        macd_column = _find_indicator_column(
            macd_result,
            "MACD_",
        )

        signal_column = _find_indicator_column(
            macd_result,
            "MACDs_",
        )

        histogram_column = _find_indicator_column(
            macd_result,
            "MACDh_",
        )

        if macd_column:
            group["macd"] = (
                macd_result[
                    macd_column
                ].to_numpy()
            )
        else:
            group["macd"] = _empty_series(
                group.index
            )

        if signal_column:
            group["macd_signal"] = (
                macd_result[
                    signal_column
                ].to_numpy()
            )
        else:
            group["macd_signal"] = (
                _empty_series(
                    group.index
                )
            )

        if histogram_column:
            group["macd_histogram"] = (
                macd_result[
                    histogram_column
                ].to_numpy()
            )
        else:
            group["macd_histogram"] = (
                group["macd"]
                - group["macd_signal"]
            )

    else:

        group["macd"] = _empty_series(
            group.index
        )

        group["macd_signal"] = _empty_series(
            group.index
        )

        group["macd_histogram"] = _empty_series(
            group.index
        )

    # ======================================================
    # 8-9. STOCHASTIC
    # ======================================================

    stochastic_result = ta.stoch(
        group["high"],
        group["low"],
        group["close"],
        k=14,
        d=3,
        smooth_k=3,
    )

    if stochastic_result is not None:

        stoch_k_column = (
            _find_indicator_column(
                stochastic_result,
                "STOCHk_",
            )
        )

        stoch_d_column = (
            _find_indicator_column(
                stochastic_result,
                "STOCHd_",
            )
        )

        if stoch_k_column:
            group["stoch_k"] = (
                stochastic_result[
                    stoch_k_column
                ].to_numpy()
            )
        else:
            group["stoch_k"] = (
                _empty_series(
                    group.index
                )
            )

        if stoch_d_column:
            group["stoch_d"] = (
                stochastic_result[
                    stoch_d_column
                ].to_numpy()
            )
        else:
            group["stoch_d"] = (
                _empty_series(
                    group.index
                )
            )

    else:

        group["stoch_k"] = _empty_series(
            group.index
        )

        group["stoch_d"] = _empty_series(
            group.index
        )

    # ======================================================
    # 10. ATR 14
    # ======================================================

    atr_14 = ta.atr(
        group["high"],
        group["low"],
        group["close"],
        length=14,
    )

    _assign_series(
        group,
        "atr_14",
        atr_14,
    )

    # ======================================================
    # 11. ATR %
    # ======================================================

    group["atr_pct"] = (
        group["atr_14"]
        .div(
            group["close"].replace(
                0,
                pd.NA,
            )
        )
        * 100
    )

    # ======================================================
    # 12-13. BOLLINGER BANDS
    # ======================================================

    bollinger_result = ta.bbands(
        group["close"],
        length=20,
        std=2,
    )

    if bollinger_result is not None:

        lower_column = (
            _find_indicator_column(
                bollinger_result,
                "BBL_",
            )
        )

        upper_column = (
            _find_indicator_column(
                bollinger_result,
                "BBU_",
            )
        )

        if lower_column:
            group["bollinger_lower"] = (
                bollinger_result[
                    lower_column
                ].to_numpy()
            )
        else:
            group["bollinger_lower"] = (
                _empty_series(
                    group.index
                )
            )

        if upper_column:
            group["bollinger_upper"] = (
                bollinger_result[
                    upper_column
                ].to_numpy()
            )
        else:
            group["bollinger_upper"] = (
                _empty_series(
                    group.index
                )
            )

    else:

        group["bollinger_lower"] = (
            _empty_series(
                group.index
            )
        )

        group["bollinger_upper"] = (
            _empty_series(
                group.index
            )
        )

    # ======================================================
    # 14. VOLUME SMA 20
    # ======================================================

    volume_sma_20 = ta.sma(
        group["volume"],
        length=20,
    )

    _assign_series(
        group,
        "volume_sma_20",
        volume_sma_20,
    )

    # ======================================================
    # 15. RELATIVE VOLUME
    # ======================================================

    group["relative_volume_20"] = (
        group["volume"]
        .div(
            group[
                "volume_sma_20"
            ].replace(
                0,
                pd.NA,
            )
        )
    )

    # ======================================================
    # 16. OBV
    # ======================================================

    obv = ta.obv(
        group["close"],
        group["volume"],
    )

    _assign_series(
        group,
        "obv",
        obv,
    )

    # ======================================================
    # TRADING DATE HELPER
    # ======================================================

    group["trading_date"] = (
        group["timestamp"].dt.date
    )

    # ======================================================
    # 17. VWAP
    # ======================================================

    typical_price = (
        group["high"]
        + group["low"]
        + group["close"]
    ) / 3

    price_volume = (
        typical_price
        * group["volume"]
    )

    cumulative_price_volume = (
        price_volume
        .groupby(
            group["trading_date"]
        )
        .cumsum()
    )

    cumulative_volume = (
        group["volume"]
        .groupby(
            group["trading_date"]
        )
        .cumsum()
    )

    group["vwap"] = (
        cumulative_price_volume
        .div(
            cumulative_volume.replace(
                0,
                pd.NA,
            )
        )
    )

    # ======================================================
    # 18. VWAP DEVIATION %
    # ======================================================

    group["vwap_deviation_pct"] = (
        (
            group["close"]
            - group["vwap"]
        )
        .div(
            group["vwap"].replace(
                0,
                pd.NA,
            )
        )
        * 100
    )

    # ======================================================
    # 19. PREVIOUS SESSION CLOSE
    # ======================================================

    daily_close = (
        group.groupby(
            "trading_date",
            as_index=False,
        )
        .agg(
            session_close=(
                "close",
                "last",
            )
        )
    )

    daily_close[
        "previous_session_close"
    ] = (
        daily_close[
            "session_close"
        ]
        .shift(1)
    )

    group = group.merge(
        daily_close[
            [
                "trading_date",
                "previous_session_close",
            ]
        ],
        on="trading_date",
        how="left",
    )

    # ======================================================
    # 20. GAP %
    # ======================================================

    session_open = (
        group.groupby(
            "trading_date"
        )["open"]
        .transform("first")
    )

    group["gap_pct"] = (
        (
            session_open
            - group[
                "previous_session_close"
            ]
        )
        .div(
            group[
                "previous_session_close"
            ].replace(
                0,
                pd.NA,
            )
        )
        * 100
    )

    # ======================================================
    # 21. ADX 14
    # ======================================================

    adx_result = ta.adx(
        group["high"],
        group["low"],
        group["close"],
        length=14,
    )

    if adx_result is not None:

        adx_column = (
            _find_indicator_column(
                adx_result,
                "ADX_",
            )
        )

        if adx_column:
            group["adx_14"] = (
                adx_result[
                    adx_column
                ].to_numpy()
            )
        else:
            group["adx_14"] = (
                _empty_series(
                    group.index
                )
            )

    else:

        group["adx_14"] = (
            _empty_series(
                group.index
            )
        )

    # ======================================================
    # 22. PRICE CHANGE %
    # ======================================================

    group["price_change_pct"] = (
        (
            group["close"]
            - group["open"]
        )
        .div(
            group["open"].replace(
                0,
                pd.NA,
            )
        )
        * 100
    )

    # ======================================================
    # REMOVE INTERNAL COLUMN
    # ======================================================

    group = group.drop(
        columns=["trading_date"],
        errors="ignore",
    )

    return group


# ==========================================================
# MAIN PRODUCTION FUNCTION
# ==========================================================

def calculate_indicators(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Calculate PulseTrade technical indicators.

    Expected input:

        symbol
        timestamp OR date
        open
        high
        low
        close
        volume

    The dataframe should already have passed
    validator.py.

    Returns:

        OHLCV
        +
        22 indicators
        +
        indicator_version
        processed_at
    """

    if df is None or df.empty:
        return df

    df = df.copy()

    # ======================================================
    # NORMALIZE BRONZE DATE COLUMN
    # ======================================================

    if (
        "timestamp" not in df.columns
        and "date" in df.columns
    ):
        df = df.rename(
            columns={
                "date": "timestamp"
            }
        )

    if "timestamp" not in df.columns:
        raise ValueError(
            "Indicator input must contain "
            "'timestamp' or 'date'."
        )

    # ======================================================
    # TIMESTAMP
    # ======================================================

    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        errors="coerce",
    )

    # ======================================================
    # NUMERIC TYPES
    # ======================================================

    numeric_columns = [
        "open",
        "high",
        "low",
        "close",
        "volume",
    ]

    for column in numeric_columns:

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    # ======================================================
    # DEFENSIVE VALIDATION
    #
    # validator.py should already have handled bad rows.
    # This prevents pandas_ta from crashing if this function
    # is accidentally called directly.
    # ======================================================

    df = df.dropna(
        subset=[
            "symbol",
            "timestamp",
            "open",
            "high",
            "low",
            "close",
            "volume",
        ]
    )

    if df.empty:
        return df

    # ======================================================
    # SORT DATA
    # ======================================================

    df = (
        df.sort_values(
            [
                "symbol",
                "timestamp",
            ]
        )
        .reset_index(drop=True)
    )

    # ======================================================
    # CALCULATE SYMBOL BY SYMBOL
    # ======================================================

    result_frames = []

    for _, symbol_df in df.groupby(
        "symbol",
        sort=False,
    ):

        result = (
            _calculate_symbol_indicators(
                symbol_df
            )
        )

        result_frames.append(
            result
        )

    result_df = pd.concat(
        result_frames,
        ignore_index=True,
    )

    # ======================================================
    # METADATA
    # ======================================================

    result_df[
        "indicator_version"
    ] = INDICATOR_VERSION

    result_df["processed_at"] = (
        pd.Timestamp.now(
            tz="UTC"
        )
    )

    # ======================================================
    # FINAL ORDER
    # ======================================================

    result_df = (
        result_df.sort_values(
            [
                "symbol",
                "timestamp",
            ]
        )
        .reset_index(drop=True)
    )

    return result_df