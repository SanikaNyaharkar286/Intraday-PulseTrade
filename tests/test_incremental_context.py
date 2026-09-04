from src.transform.silver.pipeline import (
    get_source_table_for_timeframe,
)


def test_incremental():

    symbol = "ABFRL"

    timeframes = [
        "1min",
        "5min",
        "15min",
        "1hour",
        "daily"
    ]


    print("==============================")
    print("INCREMENTAL CONTEXT TEST")
    print("==============================")


    for tf in timeframes:

        source = get_source_table_for_timeframe(tf)

        print()
        print(tf)
        print("SOURCE:")
        print(source)

        print("SYMBOL FILTER:")
        print(symbol)

        print("------------------------------")


if __name__ == "__main__":
    test_incremental()