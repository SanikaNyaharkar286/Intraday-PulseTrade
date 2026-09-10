from google.cloud import bigquery

from src.transform.silver.pipeline import (
    run_silver_pipeline,
)


client = bigquery.Client()


result = run_silver_pipeline(
    client=client,
    symbol="360ONE",
    load_type="HISTORICAL",
    start_date="2024-03-18",
    end_date="2024-03-18",
)


print("\nPIPELINE RESULT")
print(result)