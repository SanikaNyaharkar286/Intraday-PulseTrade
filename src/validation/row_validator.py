from datetime import datetime
from decimal import Decimal, InvalidOperation


DATE_FORMATS = [
    "%d-%m-%Y %H:%M",
    "%d-%m-%Y %H:%M:%S",
    "%d-%m-%Y %H:%M:%S.%f",

    "%Y-%m-%d %H:%M",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M:%S.%f",

    "%d/%m/%Y %H:%M",
    "%d/%m/%Y %H:%M:%S",

    "%Y/%m/%d %H:%M",
    "%Y/%m/%d %H:%M:%S",

    "%d-%m-%Y",
    "%Y-%m-%d",
    "%d/%m/%Y",
    "%Y/%m/%d",
]


def parse_timestamp(value):

    if value is None:
        return None

    text = str(value).strip()

    if not text:
        return None

    for date_format in DATE_FORMATS:

        try:
            return datetime.strptime(
                text,
                date_format
            )

        except ValueError:
            continue

    return None


def parse_decimal(value):

    if value is None:
        return None

    text = str(value).strip()

    if not text:
        return None

    try:
        return Decimal(text)

    except InvalidOperation:
        return None


def validate_row(row):

    timestamp = parse_timestamp(
        row.get("date")
    )

    if timestamp is None:

        return {
            "valid": False,
            "timestamp": None,
            "reason": (
                f"Invalid timestamp: "
                f"{row.get('date')}"
            )
        }

    numeric_columns = [
        "open",
        "high",
        "low",
        "close",
        "volume"
    ]

    numeric_values = {}

    for column in numeric_columns:

        numeric_value = parse_decimal(
            row.get(column)
        )

        if numeric_value is None:

            return {
                "valid": False,
                "timestamp": timestamp,
                "reason": (
                    f"Invalid numeric value "
                    f"for {column}: "
                    f"{row.get(column)}"
                )
            }

        numeric_values[column] = (
            numeric_value
        )

    open_price = numeric_values["open"]
    high = numeric_values["high"]
    low = numeric_values["low"]
    close = numeric_values["close"]
    volume = numeric_values["volume"]

    if min(
        open_price,
        high,
        low,
        close
    ) < 0:

        return {
            "valid": False,
            "timestamp": timestamp,
            "reason": "Negative OHLC price detected"
        }

    if volume < 0:

        return {
            "valid": False,
            "timestamp": timestamp,
            "reason": "Negative volume detected"
        }

    if high < max(
        open_price,
        close,
        low
    ):

        return {
            "valid": False,
            "timestamp": timestamp,
            "reason": (
                "High price is lower than "
                "another OHLC value"
            )
        }

    if low > min(
        open_price,
        close,
        high
    ):

        return {
            "valid": False,
            "timestamp": timestamp,
            "reason": (
                "Low price is higher than "
                "another OHLC value"
            )
        }

    return {
        "valid": True,
        "timestamp": timestamp,
        "reason": None
    }