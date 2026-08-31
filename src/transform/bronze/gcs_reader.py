"""import re

from google.cloud import storage

from src.utils.config import (
    GCP_PROJECT_ID,
    GCS_BUCKET_NAME,
)


# ==========================================================
# EXPECTED GCS STRUCTURE
#
# YYYY/Month/file.csv
#
# Example:
#
# 2015/January/ABB.csv
# 2026/February/LTIM.csv
# ==========================================================

GCS_PATH_PATTERN = re.compile(
    r"^(\d{4})/"
    r"(January|February|March|April|May|June|"
    r"July|August|September|October|November|December)/"
    r"([^/]+\.csv)$",
    re.IGNORECASE
)


storage_client = storage.Client(
    project=GCP_PROJECT_ID
)

def get_historical_files():

    bucket = storage_client.bucket(
        GCS_BUCKET_NAME
    )

    blobs = bucket.list_blobs()

    historical_files = []

    for blob in blobs:

        match = GCS_PATH_PATTERN.match(
            blob.name
        )

        if not match:
            continue

        year = int(
            match.group(1)
        )

        month_name = match.group(2)

        month_number = (
            __import__("datetime")
            .datetime.strptime(
                month_name,
                "%B"
            )
            .month
        )

        # --------------------------------------------------
        # Historical cutoff
        # --------------------------------------------------

        if year > 2026:
            continue

        if (
            year == 2026
            and month_number > 2
        ):
            continue

        historical_files.append(
            {
                "blob_name": blob.name,
                "uri": (
                    f"gs://{GCS_BUCKET_NAME}/"
                    f"{blob.name}"
                ),
                "year": year,
                "month": month_name,
                "symbol": (
                    match.group(3)
                    .replace(".csv", "")
                ),
            }
        )

    return historical_files

def get_test_file():

    return [
        {
            "blob_name": "2015/April/360ONE.csv",

            "uri": (
                f"gs://{GCS_BUCKET_NAME}/"
                "2015/April/360ONE.csv"
            ),

            "year": 2015,

            "month": "April",

            "symbol": "360ONE",
        }
    ]"""

import re

from google.cloud import storage

from src.utils.config import (
    GCP_PROJECT_ID,
    GCS_BUCKET_NAME,
    BRONZE_HISTORICAL_END_YEAR,
    BRONZE_HISTORICAL_END_MONTH,
)


client = storage.Client(
    project=GCP_PROJECT_ID
)


MONTHS = {
    "January": 1,
    "February": 2,
    "March": 3,
    "April": 4,
    "May": 5,
    "June": 6,
    "July": 7,
    "August": 8,
    "September": 9,
    "October": 10,
    "November": 11,
    "December": 12,
}


# ==========================================================
# VALID HISTORICAL GCS PATH
# ==========================================================

PATH_PATTERN = re.compile(
    r"^(\d{4})/([A-Za-z]+)/([^/]+)\.csv$"
)


def is_historical_path(
    object_name: str
) -> bool:

    match = PATH_PATTERN.match(
        object_name
    )

    if not match:
        return False

    year = int(
        match.group(1)
    )

    month_name = match.group(2)

    month = MONTHS.get(
        month_name
    )

    if month is None:
        return False

    # Only process through February 2026.
    if year > BRONZE_HISTORICAL_END_YEAR:
        return False

    if (
        year == BRONZE_HISTORICAL_END_YEAR
        and month >
        BRONZE_HISTORICAL_END_MONTH
    ):
        return False

    return True


# ==========================================================
# SYMBOL FROM GCS OBJECT
# ==========================================================

def get_symbol(
    object_name: str
) -> str:

    filename = (
        object_name
        .split("/")[-1]
    )

    return filename.rsplit(
        ".",
        1
    )[0]


# ==========================================================
# DISCOVER HISTORICAL FILES
# ==========================================================

def get_historical_files():

    bucket = client.bucket(
        GCS_BUCKET_NAME
    )

    files = []

    for blob in bucket.list_blobs():

        object_name = blob.name

        if not is_historical_path(
            object_name
        ):
            continue

        symbol = get_symbol(
            object_name
        )

        files.append({

            "uri": (
                f"gs://{GCS_BUCKET_NAME}/"
                f"{object_name}"
            ),

            "object_name":
                object_name,

            "source_file":
                object_name.split("/")[-1],

            "symbol":
                symbol,

        })

    files.sort(
        key=lambda x: x["object_name"]
    )

    return files