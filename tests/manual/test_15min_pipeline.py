import sys
from pathlib import Path

sys.path.append(
    str(
        Path(__file__)
        .resolve()
        .parents[2]
    )
)
from google.cloud import bigquery

from src.transform.silver.pipeline import (
    run_silver_pipeline
)

from src.utils.config import (
    GCP_PROJECT_ID
)


client = bigquery.Client(
    project=GCP_PROJECT_ID
)


result = run_silver_pipeline(
    client=client,
    symbol="360ONE",
    load_type="HISTORICAL",
    timeframe="15min"
)


print("==========================")
print(result)
print("==========================")