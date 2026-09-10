from google.cloud import bigquery

from src.transform.silver.pipeline import (
    run_silver_pipeline
)


client = bigquery.Client()


result = run_silver_pipeline(

    client=client,

    symbol="360ONE",
    timeframe="daily",

    load_type="HISTORICAL",


    start_date=None,

    end_date=None

)


print(result)