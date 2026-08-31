from dotenv import load_dotenv
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

BRONZE_MAX_WORKERS = int(
    os.getenv(
        "BRONZE_MAX_WORKERS",
        "4"
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