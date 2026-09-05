from dotenv import load_dotenv
import os


load_dotenv()

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

GCP_PROJECT_ID = os.getenv(
    "GCP_PROJECT_ID"
)

GCP_REGION = os.getenv(
    "GCP_REGION",
    "us-east1"
)
