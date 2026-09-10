from google.cloud import bigquery

from src.transform.silver.pipeline import (
    run_silver_pipeline,
)


client = bigquery.Client()


result = run_silver_pipeline(
    client=client,
    symbol="360ONE",
    load_type="INCREMENTAL",
    start_date="2026-04-09",
    end_date="2026-04-09",
    timeframe="5min",
)


print("======================")
print(result)
print("======================")