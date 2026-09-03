"""from dotenv import load_dotenv
import os


load_dotenv()


# ==========================================================
# COMMON / GCP
# ==========================================================

GCP_PROJECT_ID = os.getenv(
    "GCP_PROJECT_ID"
)

GCP_REGION = os.getenv(
    "GCP_REGION",
    "us-east1"
)


# ==========================================================
# LOCAL → GCS INGESTION
# ==========================================================

GCS_BUCKET_NAME = os.getenv(
    "GCS_BUCKET_NAME"
)

INPUT_PATH = os.getenv(
    "INPUT_PATH",
    r"D:\PulseTrade\market_data.zip"
)

MAX_WORKERS = int(
    os.getenv(
        "MAX_WORKERS",
        "4"
    )
)

UPLOAD_MODE = os.getenv(
    "UPLOAD_MODE",
    "SKIP"
).upper()

MAX_OPEN_FILES = int(
    os.getenv(
        "MAX_OPEN_FILES",
        "24"
    )
)


if UPLOAD_MODE not in {
    "SKIP",
    "FAIL",
    "OVERWRITE"
}:

    raise ValueError(
        "UPLOAD_MODE must be "
        "SKIP, FAIL or OVERWRITE"
    )


# ==========================================================
# GCS → BIGQUERY BRONZE
# ==========================================================

BQ_BRONZE_DATASET = os.getenv(
    "BQ_BRONZE_DATASET",
    "migration_bronze"
)

BQ_BRONZE_TABLE = os.getenv(
    "BQ_BRONZE_TABLE",
    "market_prices"
)

BQ_AUDIT_DATASET = os.getenv(
    "BQ_AUDIT_DATASET",
    "migration_audit"
)

BQ_AUDIT_TABLE = os.getenv(
    "BQ_AUDIT_TABLE",
    "ingestion_audit"
)


# ==========================================================
# BRONZE PROCESSING
# ==========================================================

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

BRONZE_BATCH_SIZE = int(
    os.getenv(
        "BRONZE_BATCH_SIZE",
        "500"
    )
)


# ==========================================================
# HISTORICAL DATA RANGE
# ==========================================================

BRONZE_HISTORICAL_END_YEAR = int(
    os.getenv(
        "BRONZE_HISTORICAL_END_YEAR",
        "2026"
    )
)

BRONZE_HISTORICAL_END_MONTH = int(
    os.getenv(
        "BRONZE_HISTORICAL_END_MONTH",
        "2"
    )
)


# ==========================================================
# LAPTOP BATCH ASSIGNMENT
#
# Each laptop gets a fixed range of batches.
#
# Laptop 1 → 1 to 37
# Laptop 2 → 38 to 74
# Laptop 3 → 75 to 111
#
# Change these values in .env on each laptop.
# ==========================================================

BRONZE_START_BATCH = int(
    os.getenv(
        "BRONZE_START_BATCH",
        "1"
    )
)

BRONZE_END_BATCH = int(
    os.getenv(
        "BRONZE_END_BATCH",
        "111"
    )
)"""

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