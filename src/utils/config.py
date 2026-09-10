from dotenv import load_dotenv
import os


load_dotenv()


# ==========================================================
# GCP
# ==========================================================

GCP_PROJECT_ID = os.getenv(
    "GCP_PROJECT_ID"
)

GCP_REGION = os.getenv(
    "GCP_REGION",
    "us-east1"
)
PUBSUB_BRONZE_TO_SILVER_TOPIC = os.getenv(
    "PUBSUB_BRONZE_TO_SILVER_TOPIC",
    "bronze-v2-to-silver-v2"
)
PUBSUB_SILVER_TIMEFRAME_COMPLETED_TOPIC = os.getenv(
    "PUBSUB_SILVER_TIMEFRAME_COMPLETED_TOPIC",
    "silver-timeframe-completed"
)

# ==========================================================
# SOURCE GCS
# ==========================================================

GCS_BUCKET_NAME = os.getenv(
    "GCS_BUCKET_NAME",
    "raw_data_20gb"
)


# ==========================================================
# BIGQUERY DATASETS
# ==========================================================

BQ_BRONZE_DATASET = os.getenv(
    "BQ_BRONZE_DATASET",
    "migration_bronze"
)

BQ_SILVER_DATASET = os.getenv(
    "BQ_SILVER_DATASET",
    "migration_silver"
)

BQ_GOLD_DATASET = os.getenv(
    "BQ_GOLD_DATASET",
    "migration_gold"
)

BQ_AUDIT_DATASET = os.getenv(
    "BQ_AUDIT_DATASET",
    "migration_audit"
)


# ==========================================================
# BIGQUERY TABLES
# ==========================================================
BQ_SILVER_AUDIT_TABLE = os.getenv(
    "BQ_SILVER_AUDIT_TABLE",
    "silver_audit_log"
)
BQ_BRONZE_TABLE = os.getenv(
    "BQ_BRONZE_TABLE",
    "market_prices"
)

BQ_AUDIT_TABLE = os.getenv(
    "BQ_AUDIT_TABLE",
    "ingestion_audit"
)
BQ_SILVER_1MIN_TABLE = os.getenv(
    "BQ_SILVER_1MIN_TABLE"
)


BQ_SILVER_5MIN_TABLE = os.getenv(
    "BQ_SILVER_5MIN_TABLE"
)


BQ_SILVER_15MIN_TABLE = os.getenv(
    "BQ_SILVER_15MIN_TABLE"
)


BQ_SILVER_1HOUR_TABLE = os.getenv(
    "BQ_SILVER_1HOUR_TABLE"
)


BQ_SILVER_DAILY_TABLE = os.getenv(
    "BQ_SILVER_DAILY_TABLE"
)


# ==========================================================
# BRONZE PROCESSING
# ==========================================================
# ==========================================================
# HISTORICAL BRONZE BATCH RANGE
#
# Controls which fixed batches this machine processes.
#
# For testing:
#   start = 1
#   end   = 1
#
# Later different machines can use different ranges.
# ==========================================================

BRONZE_START_BATCH = int(
    os.getenv(
        "BRONZE_START_BATCH",
        "1",
    )
)

BRONZE_END_BATCH = int(
    os.getenv(
        "BRONZE_END_BATCH",
        "26",
    )
)
BRONZE_BATCH_SIZE = int(
    os.getenv(
        "BRONZE_BATCH_SIZE",
        "20"
    )
)

BRONZE_MAX_WORKERS = int(
    os.getenv(
        "BRONZE_MAX_WORKERS",
        "6"
    )
)

BRONZE_MAX_RETRIES = int(
    os.getenv(
        "BRONZE_MAX_RETRIES",
        "3"
    )
)


# ==========================================================
# SOURCE FILE RULES
# ==========================================================

SOURCE_FILE_SUFFIX = "_minute.csv"

NEW_FILE_SUFFIX = "_minute_new.csv"
