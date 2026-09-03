import pandas as pd

from src.transform.silver.validator import (
    validate_bronze_data,
)


test_df = pd.DataFrame(
    [
        {
            "date": "2024-03-18T09:16:00",
            "open": 689.65,
            "high": 691.35,
            "low": 682.35,
            "close": 684.05,
            "volume": 2577.0,
            "symbol": "360ONE",
        },
        {
            "date": "bad-date",
            "open": 688.00,
            "high": 688.00,
            "low": 684.95,
            "close": 684.95,
            "volume": 1076.0,
            "symbol": "360ONE",
        },
        {
            "date": "2024-03-18T09:22:00",
            "open": 688.15,
            "high": 680.00,
            "low": 685.65,
            "close": 685.70,
            "volume": 91.0,
            "symbol": "360ONE",
        },
    ]
)


valid_df, rejected_df = validate_bronze_data(
    test_df
)


print("\nVALID:")
print(valid_df)

print("\nREJECTED:")
print(
    rejected_df[
        [
            "symbol",
            "date",
            "failure_reason",
        ]
    ]
)