import os
from pathlib import Path


def _int_env(name, default):
    value = os.getenv(name)

    if value is None or value == "":
        return default

    return int(value)


def _bool_env(name, default):
    value = os.getenv(name)

    if value is None or value == "":
        return default

    return value.strip().lower() in {
        "1",
        "true",
        "yes",
        "y",
        "on",
    }


PROJECT_ID = os.getenv(
    "GCP_PROJECT_ID",
    "project-001658fa-3ce5-4746-980"
)

REGION = os.getenv(
    "GCP_REGION",
    "us-east1"
)

BQ_LOCATION = os.getenv(
    "BQ_LOCATION",
    "US"
)

BUCKET_NAME = os.getenv(
    "GCS_BUCKET",
    "processed-intraday"
)

BRONZE_DATASET = os.getenv(
    "BQ_BRONZE_DATASET",
    "bronze_data"
)

BRONZE_TABLE = os.getenv(
    "BQ_BRONZE_TABLE",
    "intraday_master"
)

SILVER_DATASET = os.getenv(
    "BQ_SILVER_DATASET",
    "silver_dataset_us"
)

GOLD_DATASET = os.getenv(
    "BQ_GOLD_DATASET",
    "pulse_trade_gold"
)

AI_DATASET = os.getenv(
    "BQ_AI_DATASET",
    "pulse_trade_ai"
)

AI_SNAPSHOT_LOOKBACK_DAYS = _int_env(
    "AI_SNAPSHOT_LOOKBACK_DAYS",
    30
)

SEMANTIC_DATASET = os.getenv(
    "BQ_SEMANTIC_DATASET",
    "pulse_trade_semantic"
)

RUN_GOLD_AFTER_SILVER = _bool_env(
    "RUN_GOLD_AFTER_SILVER",
    True
)

AUDIT_DATASET = os.getenv(
    "BQ_AUDIT_DATASET",
    "audit_dataset_us"
)

AUDIT_TABLE = os.getenv(
    "BQ_AUDIT_TABLE",
    "pipeline_audit"
)

# =========================================================
# Historical test range
# =========================================================

HISTORICAL_START_YEAR = _int_env(
    "HISTORICAL_START_YEAR",
    2015
)

HISTORICAL_START_MONTH = _int_env(
    "HISTORICAL_START_MONTH",
    1
)

HISTORICAL_END_YEAR = _int_env(
    "HISTORICAL_END_YEAR",
    2026
)

HISTORICAL_END_MONTH = _int_env(
    "HISTORICAL_END_MONTH",
    2
)

HISTORICAL_CHECKPOINT_FILE = os.getenv(
    "HISTORICAL_CHECKPOINT_FILE",
    str(
        Path(__file__).resolve().parents[1]
        / ".pipeline_state"
        / "historical_checkpoint.json"
    )
)

HISTORICAL_RUN_SILVER_EACH_MONTH = _bool_env(
    "HISTORICAL_RUN_SILVER_EACH_MONTH",
    True
)
