import pandas as pd
from google.cloud import bigquery

from src.utils.config import (
    GCP_PROJECT_ID,
    BQ_BRONZE_DATASET,
    BQ_BRONZE_TABLE,
)


# ==========================================================
# BRONZE TABLE
# ==========================================================

BRONZE_TABLE = (
    f"{GCP_PROJECT_ID}."
    f"{BQ_BRONZE_DATASET}."
    f"{BQ_BRONZE_TABLE}"
)


# ==========================================================
# READ BRONZE DATA
# ==========================================================

def read_bronze_data(
    client: bigquery.Client,
    symbol: str,
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    """
    Read Bronze market data for one symbol.

    Optional:
        start_date
        end_date

    Example:
        symbol = "360ONE"
        start_date = "2024-03-18"
        end_date = "2024-03-19"

    Returns:
        Pandas DataFrame containing:

        date
        open
        high
        low
        close
        volume
        symbol
    """

    if not symbol or not symbol.strip():
        raise ValueError(
            "symbol is required"
        )

    symbol = symbol.strip()

    # ======================================================
    # QUERY
    # ======================================================

    query = f"""
    SELECT
        date,
        open,
        high,
        low,
        close,
        volume,
        symbol
    FROM `{BRONZE_TABLE}`
    WHERE symbol = @symbol
    """

    query_parameters = [
        bigquery.ScalarQueryParameter(
            "symbol",
            "STRING",
            symbol,
        )
    ]

    # ======================================================
    # OPTIONAL START DATE
    # ======================================================

    if start_date:

        query += """
        AND DATE(date) >= @start_date
        """

        query_parameters.append(
            bigquery.ScalarQueryParameter(
                "start_date",
                "DATE",
                start_date,
            )
        )

    # ======================================================
    # OPTIONAL END DATE
    # ======================================================

    if end_date:

        query += """
        AND DATE(date) <= @end_date
        """

        query_parameters.append(
            bigquery.ScalarQueryParameter(
                "end_date",
                "DATE",
                end_date,
            )
        )

    # ======================================================
    # ORDER DATA
    # ======================================================

    query += """
    ORDER BY
        symbol,
        date
    """

    # ======================================================
    # BIGQUERY JOB CONFIG
    # ======================================================

    job_config = bigquery.QueryJobConfig(
        query_parameters=query_parameters
    )

    # ======================================================
    # EXECUTE
    # ======================================================

    query_job = client.query(
        query,
        job_config=job_config,
    )

    result = query_job.result()

    # ======================================================
    # BIGQUERY → PANDAS
    # ======================================================

    df = result.to_dataframe()

    return df