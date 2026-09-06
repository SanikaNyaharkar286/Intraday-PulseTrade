REQUIRED_COLUMNS = {
    "date",
    "open",
    "high",
    "low",
    "close",
    "volume"
}


def validate_schema(fieldnames):

    if not fieldnames:
        raise ValueError(
            "CSV does not contain a header."
        )

    cleaned = [
        column.strip().lower()
        for column in fieldnames
    ]

    if len(cleaned) != len(set(cleaned)):
        raise ValueError(
            "Duplicate column names detected."
        )

    available = set(cleaned)

    missing = (
        REQUIRED_COLUMNS - available
    )

    if missing:
        raise ValueError(
            f"Missing required columns: "
            f"{sorted(missing)}"
        )

    unexpected = (
        available - REQUIRED_COLUMNS
    )

    return {
        "missing": sorted(missing),
        "unexpected": sorted(unexpected)
    }