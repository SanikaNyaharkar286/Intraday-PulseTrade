from datetime import datetime
from pathlib import Path

from google.cloud import storage
"""
Monthly local CSV
→ choose GCS bucket
→ create month name
→ build cloud file path
→ check whether file already exists
→ apply upload rule: SKIP / FAIL / OVERWRITE
→ upload file
→ compare local and cloud file sizes
→ return UPLOADED, SKIPPED, or error
"""
from src.utils.config import (
    GCP_PROJECT_ID,
    GCS_BUCKET_NAME,
    UPLOAD_MODE
)

"""Creates a connection to Google Cloud Storage using the configured project."""
client = storage.Client(
    project=GCP_PROJECT_ID
)



def upload_month_file(
    local_file: Path, #zip
    symbol: str, #file name
    year: int, 
    month: int
):

    bucket = client.bucket(
        GCS_BUCKET_NAME
    )

    # Convert month number to month name.
    # Example:
    # 1  -> January
    # 2  -> February
    # 8  -> August
    month_name = datetime(
        year,
        month,
        1
    ).strftime("%B")

    # Final GCS path:
    #
    # 2011/January/ABBOTINDIA.csv
    # 2011/February/ABBOTINDIA.csv
    # 2026/August/RELIANCE.csv

    object_name = (
        f"{year:04d}/"
        f"{month_name}/"
        f"{symbol}.csv"
    )

    blob = bucket.blob(
        object_name
    )#2026/August/RELIANCE.csv

    exists = blob.exists()

    if exists:

        if UPLOAD_MODE == "SKIP":

            return {
                "status": "SKIPPED",
                "object": object_name
            }

        if UPLOAD_MODE == "FAIL":

            raise FileExistsError(
                f"GCS object already exists: "
                f"gs://{GCS_BUCKET_NAME}/"
                f"{object_name}"
            )

    generation_condition = (
        None
        if UPLOAD_MODE == "OVERWRITE"
        else 0
    )

    blob.upload_from_filename(
        str(local_file),
        content_type="text/csv",
        if_generation_match=(
            generation_condition
        )
    )

    blob.reload()

    local_size = (
        local_file.stat().st_size
    )

    remote_size = int(
        blob.size
    )

    if local_size != remote_size:

        raise RuntimeError(
            "Upload verification failed: "
            f"{object_name}. "
            f"Local size={local_size}, "
            f"GCS size={remote_size}"
        )

    return {
        "status": "UPLOADED",
        "object": object_name,
        "bytes": remote_size
    }