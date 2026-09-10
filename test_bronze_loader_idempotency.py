from google.cloud import bigquery

from src.transform.bronze.bronze_loader import (
    load_one_file,
)

from src.utils.config import (
    GCP_PROJECT_ID,
    BQ_BRONZE_DATASET,
    BQ_BRONZE_TABLE,
)


SYMBOL = "360ONE"

GCS_URI = (
    "gs://raw_data_20gb/"
    "360ONE_minute.csv"
)

BRONZE_TABLE = (
    f"{GCP_PROJECT_ID}."
    f"{BQ_BRONZE_DATASET}."
    f"{BQ_BRONZE_TABLE}"
)


def get_counts(client):

    query = f"""
    SELECT
        COUNT(*) AS total_rows,
        COUNT(
            DISTINCT CAST(date AS STRING)
        ) AS unique_rows
    FROM `{BRONZE_TABLE}`
    WHERE symbol = @symbol
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter(
                "symbol",
                "STRING",
                SYMBOL,
            )
        ]
    )

    row = next(
        iter(
            client.query(
                query,
                job_config=job_config,
            ).result()
        )
    )

    total_rows = int(
        row.total_rows
    )

    unique_rows = int(
        row.unique_rows
    )

    return (
        total_rows,
        unique_rows,
    )


def main():

    client = bigquery.Client(
        project=GCP_PROJECT_ID
    )

    # ======================================================
    # BEFORE
    # ======================================================

    before_total, before_unique = (
        get_counts(client)
    )

    print(
        "\nRows BEFORE rerun:"
    )

    print(
        f"Total rows : {before_total}"
    )

    print(
        f"Unique rows: {before_unique}"
    )

    print(
        f"Duplicates : "
        f"{before_total - before_unique}"
    )

    # ======================================================
    # RUN REAL PRODUCTION BRONZE LOADER AGAIN
    # ======================================================

    print(
        "\nRunning load_one_file again..."
    )

    result = load_one_file(
        gcs_uri=GCS_URI,
        symbol=SYMBOL,
    )

    print(
        "\nLoader result:"
    )

    print(
        result
    )

    # ======================================================
    # AFTER
    # ======================================================

    after_total, after_unique = (
        get_counts(client)
    )

    print(
        "\nRows AFTER rerun:"
    )

    print(
        f"Total rows : {after_total}"
    )

    print(
        f"Unique rows: {after_unique}"
    )

    print(
        f"Duplicates : "
        f"{after_total - after_unique}"
    )

    # ======================================================
    # VALIDATION
    # ======================================================

    if (
        after_total
        != before_total
    ):

        raise AssertionError(
            "FAIL: Bronze row count changed "
            "after loading the same file again."
        )

    if (
        after_total
        != after_unique
    ):

        raise AssertionError(
            "FAIL: Bronze contains duplicate "
            "symbol + date records."
        )

    if result["row_count"] != 0:

        raise AssertionError(
            "FAIL: Loader reported new rows "
            "for an already-loaded file."
        )

    print(
        "\n"
        + "=" * 70
    )

    print(
        "PASS: Bronze loader is idempotent."
    )

    print(
        "Same GCS file did not create duplicates."
    )

    print(
        "=" * 70
    )


if __name__ == "__main__":

    main()