from google.cloud import bigquery

from src.transform.silver.timeframe.aggregator import (
    aggregate_timeframe
)

from src.utils.config import (
    GCP_PROJECT_ID,
    BQ_SILVER_DATASET,
    BQ_SILVER_1MIN_TABLE,
    BQ_SILVER_5MIN_TABLE,
)


import pandas as pd


client = bigquery.Client()


# ======================================================
# READ SOURCE DATA
# ======================================================

def read_symbol_data(
    table,
    symbol
):

    query = f"""

    SELECT

        date,
        open,
        high,
        low,
        close,
        volume,
        symbol

    FROM `{GCP_PROJECT_ID}.{BQ_SILVER_DATASET}.{table}`

    WHERE symbol=@symbol

    ORDER BY date

    LIMIT 1000

    """


    job_config = bigquery.QueryJobConfig(

        query_parameters=[

            bigquery.ScalarQueryParameter(
                "symbol",
                "STRING",
                symbol
            )

        ]

    )


    result = client.query(
        query,
        job_config=job_config
    ).result()


    return result.to_dataframe()



# ======================================================
# TEST 1MIN -> 5MIN
# ======================================================


print(
    "\n=============================="
)

print(
    "TEST 1MIN TO 5MIN AGGREGATION"
)

print(
    "=============================="
)


df_1min = read_symbol_data(

    BQ_SILVER_1MIN_TABLE,

    "360ONE"

)


print(
    "Input 1min rows:",
    len(df_1min)
)


df_5min = aggregate_timeframe(

    df_1min,

    "5min"

)


print(
    "Output 5min rows:",
    len(df_5min)
)


print(
    df_5min.head(10)
)



# ======================================================
# TEST 5MIN -> 15MIN
# ======================================================


print(
    "\n=============================="
)

print(
    "TEST 5MIN TO 15MIN AGGREGATION"
)

print(
    "=============================="
)



df_15min = aggregate_timeframe(

    df_5min,

    "15min"

)


print(
    "Output 15min rows:",
    len(df_15min)
)


print(
    df_15min.head(10)
)



# ======================================================
# TEST 15MIN -> 1HOUR
# ======================================================


print(
    "\n=============================="
)

print(
    "TEST 15MIN TO 1HOUR AGGREGATION"
)

print(
    "=============================="
)



df_1hour = aggregate_timeframe(

    df_15min,

    "1hour"

)


print(
    "Output 1hour rows:",
    len(df_1hour)
)


print(
    df_1hour.head(10)
)



# ======================================================
# TEST 1HOUR -> DAILY
# ======================================================


print(
    "\n=============================="
)

print(
    "TEST 1HOUR TO DAILY AGGREGATION"
)

print(
    "=============================="
)



df_daily = aggregate_timeframe(

    df_1hour,

    "daily"

)


print(
    "Output daily rows:",
    len(df_daily)
)


print(
    df_daily.head(10)
)