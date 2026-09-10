from src.utils.config import (
    GCP_PROJECT_ID,
    BQ_SILVER_DATASET,
    BQ_SILVER_1MIN_TABLE,
    BQ_SILVER_5MIN_TABLE,
    BQ_SILVER_15MIN_TABLE,
    BQ_SILVER_1HOUR_TABLE,
    BQ_SILVER_DAILY_TABLE,
)


def get_source_table(timeframe):

    routing = {

        "5min": BQ_SILVER_1MIN_TABLE,

        "15min": BQ_SILVER_5MIN_TABLE,

        "1hour": BQ_SILVER_15MIN_TABLE,

        "daily": BQ_SILVER_1HOUR_TABLE,

    }


    return routing.get(timeframe)



def print_source(timeframe):

    source = get_source_table(timeframe)

    print("==============================")
    print("TIMEFRAME:", timeframe)
    print("READ FROM:")
    print(
        f"{GCP_PROJECT_ID}.{BQ_SILVER_DATASET}.{source}"
    )
    print("==============================")



print_source("5min")

print_source("15min")

print_source("1hour")

print_source("daily")