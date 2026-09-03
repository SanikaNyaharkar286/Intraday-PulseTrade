import pandas as pd


# ==========================================================
# REQUIRED BRONZE COLUMNS
# ==========================================================

REQUIRED_COLUMNS = [
    "symbol",
    "date",
    "open",
    "high",
    "low",
    "close",
    "volume",
]

NUMERIC_COLUMNS = [
    "open",
    "high",
    "low",
    "close",
    "volume",
]


# ==========================================================
# SILVER VALIDATION
# ==========================================================

def validate_bronze_data(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Validate Bronze market data before Silver indicator calculation.

    Returns:
        valid_df:
            Valid records that can continue to indicator calculation.

        rejected_df:
            Invalid records with failure_reason.

    Validation rules:
        1. Required columns must exist.
        2. symbol must not be null/blank.
        3. date must be a valid timestamp.
        4. OHLCV values must be numeric.
        5. OHLC prices must be greater than 0.
        6. OHLC values must follow valid price relationships.
        7. volume cannot be negative.
        8. volume = 0 is allowed.
        9. Duplicate symbol + date rows are rejected.
        10. Valid data is sorted by symbol + date.
    """

    # ======================================================
    # EMPTY DATAFRAME
    # ======================================================

    if df is None or df.empty:

        return (
            pd.DataFrame(
                columns=REQUIRED_COLUMNS
            ),
            pd.DataFrame(
                columns=(
                    REQUIRED_COLUMNS
                    + ["failure_reason"]
                )
            ),
        )

    df = df.copy()

    # ======================================================
    # REQUIRED COLUMN VALIDATION
    # ======================================================

    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:

        raise ValueError(
            "Missing required Bronze columns: "
            + ", ".join(missing_columns)
        )

    # ======================================================
    # FAILURE REASON
    # ======================================================

    df["failure_reason"] = pd.NA

    # ======================================================
    # SYMBOL VALIDATION
    # ======================================================

    invalid_symbol = (
        df["symbol"].isna()
        |
        df["symbol"]
        .astype("string")
        .str.strip()
        .eq("")
    )

    _append_failure_reason(
        df,
        invalid_symbol,
        "INVALID_SYMBOL",
    )

    # ------------------------------------------------------
    # Normalize symbol
    # ------------------------------------------------------

    df["symbol"] = (
        df["symbol"]
        .astype("string")
        .str.strip()
    )

    # ======================================================
    # DATE / TIMESTAMP VALIDATION
    # ======================================================

    original_date = (
        df["date"].copy()
    )

    df["date"] = pd.to_datetime(
        df["date"],
        errors="coerce",
    )

    invalid_date = (
        df["date"].isna()
    )

    _append_failure_reason(
        df,
        invalid_date,
        "INVALID_DATE",
    )

    # ======================================================
    # NUMERIC CONVERSION
    # ======================================================

    for column in NUMERIC_COLUMNS:

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

        invalid_numeric = (
            df[column].isna()
        )

        _append_failure_reason(
            df,
            invalid_numeric,
            f"INVALID_{column.upper()}",
        )

    # ======================================================
    # VALID NUMERIC OHLC MASK
    #
    # Only perform OHLC validations where all four
    # price fields converted successfully.
    # ======================================================

    valid_ohlc_numbers = (
        df[
            [
                "open",
                "high",
                "low",
                "close",
            ]
        ]
        .notna()
        .all(axis=1)
    )

    # ======================================================
    # ZERO / NEGATIVE OHLC VALIDATION
    #
    # Prices must always be greater than zero.
    #
    # Examples rejected:
    #
    # open  = 0
    # high  = 0
    # low   = 0
    # close = 0
    #
    # Negative prices are also rejected.
    # ======================================================

    invalid_price = (
        valid_ohlc_numbers
        &
        (
            (df["open"] <= 0)
            |
            (df["high"] <= 0)
            |
            (df["low"] <= 0)
            |
            (df["close"] <= 0)
        )
    )

    _append_failure_reason(
        df,
        invalid_price,
        "NON_POSITIVE_OHLC",
    )

    # ======================================================
    # OHLC RELATIONSHIP VALIDATION
    # ======================================================

    invalid_high_low = (
        valid_ohlc_numbers
        &
        (df["high"] < df["low"])
    )

    _append_failure_reason(
        df,
        invalid_high_low,
        "HIGH_LESS_THAN_LOW",
    )

    # ------------------------------------------------------

    invalid_high_open = (
        valid_ohlc_numbers
        &
        (df["high"] < df["open"])
    )

    _append_failure_reason(
        df,
        invalid_high_open,
        "HIGH_LESS_THAN_OPEN",
    )

    # ------------------------------------------------------

    invalid_high_close = (
        valid_ohlc_numbers
        &
        (df["high"] < df["close"])
    )

    _append_failure_reason(
        df,
        invalid_high_close,
        "HIGH_LESS_THAN_CLOSE",
    )

    # ------------------------------------------------------

    invalid_low_open = (
        valid_ohlc_numbers
        &
        (df["low"] > df["open"])
    )

    _append_failure_reason(
        df,
        invalid_low_open,
        "LOW_GREATER_THAN_OPEN",
    )

    # ------------------------------------------------------

    invalid_low_close = (
        valid_ohlc_numbers
        &
        (df["low"] > df["close"])
    )

    _append_failure_reason(
        df,
        invalid_low_close,
        "LOW_GREATER_THAN_CLOSE",
    )

    # ======================================================
    # VOLUME VALIDATION
    #
    # volume < 0  -> rejected
    # volume = 0  -> allowed
    # volume > 0  -> allowed
    # ======================================================

    negative_volume = (
        df["volume"].notna()
        &
        (df["volume"] < 0)
    )

    _append_failure_reason(
        df,
        negative_volume,
        "NEGATIVE_VOLUME",
    )

    # ======================================================
    # DUPLICATE VALIDATION
    #
    # Business key:
    #
    #     symbol + date
    #
    # Reject every occurrence of a duplicate key.
    # ======================================================

    duplicate_mask = (
        df["symbol"].notna()
        &
        df["date"].notna()
        &
        df.duplicated(
            subset=[
                "symbol",
                "date",
            ],
            keep=False,
        )
    )

    _append_failure_reason(
        df,
        duplicate_mask,
        "DUPLICATE_SYMBOL_DATE",
    )

    # ======================================================
    # SPLIT VALID / REJECTED
    # ======================================================

    rejected_df = (
        df[
            df[
                "failure_reason"
            ].notna()
        ]
        .copy()
        .reset_index(drop=True)
    )

    valid_df = (
        df[
            df[
                "failure_reason"
            ].isna()
        ]
        .copy()
    )

    # ------------------------------------------------------
    # failure_reason belongs only to rejected/quarantine data
    # ------------------------------------------------------

    valid_df = valid_df.drop(
        columns=[
            "failure_reason"
        ]
    )

    # ======================================================
    # SORT VALID DATA
    # ======================================================

    valid_df = (
        valid_df
        .sort_values(
            [
                "symbol",
                "date",
            ]
        )
        .reset_index(drop=True)
    )

    return (
        valid_df,
        rejected_df,
    )


# ==========================================================
# FAILURE REASON HELPER
# ==========================================================

def _append_failure_reason(
    df: pd.DataFrame,
    mask: pd.Series,
    reason: str,
) -> None:
    """
    Add validation failure reasons without overwriting
    any existing reason.

    A record may contain multiple reasons.

    Example:

        NON_POSITIVE_OHLC;HIGH_LESS_THAN_CLOSE
    """

    if not mask.any():
        return

    existing_reason = (
        df.loc[
            mask,
            "failure_reason",
        ]
        .fillna("")
        .astype(str)
    )

    df.loc[
        mask,
        "failure_reason",
    ] = existing_reason.apply(
        lambda current:
            reason
            if not current
            else f"{current};{reason}"
    )