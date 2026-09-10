from google.cloud import bigquery

from src.transform.silver.pipeline import (
    get_source_table_for_timeframe,
)


PROJECT = "project-001658fa-3ce5-4746-980"


def test_timeframe_source_mapping():

    timeframes = [
        "1min",
        "5min",
        "15min",
        "1hour",
        "daily"
    ]


    print("\n==============================")
    print("TIMEFRAME SOURCE TEST")
    print("==============================\n")


    for timeframe in timeframes:

        source_table = get_source_table_for_timeframe(
            timeframe
        )


        print(
            f"{timeframe.upper()}"
        )

        print(
            f"READ FROM:"
        )

        print(
            source_table
        )

        print("------------------------------")


if __name__ == "__main__":

    test_timeframe_source_mapping()