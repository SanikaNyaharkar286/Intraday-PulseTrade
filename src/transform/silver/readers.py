import pandas as pd

from google.cloud import bigquery

from src.utils.config import (
    GCP_PROJECT_ID,
    BQ_SILVER_DATASET,
)


def read_silver_timeframe_data(
    client: bigquery.Client,
    symbol: str,
    table_name: str,
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    """
    Read previous Silver timeframe data.

    Examples:

    silver_5min  -> reads silver_1min
    silver_15min -> reads silver_5min
    silver_1hour -> reads silver_15min
    silver_daily -> reads silver_1hour

    """

    if not symbol or not symbol.strip():
        raise ValueError(
            "symbol is required"
        )


    full_table_name = (
    f"{GCP_PROJECT_ID}."
    f"{BQ_SILVER_DATASET}."
    f"{table_name}"
)


    query = f"""
    SELECT
        date,
        open,
        high,
        low,
        close,
        volume,
        symbol

    FROM `{full_table_name}`

    WHERE symbol = @symbol
    """


    parameters = [

        bigquery.ScalarQueryParameter(
            "symbol",
            "STRING",
            symbol.strip()
        )

    ]


    if start_date:

        query += """
        AND DATE(date) >= @start_date
        """

        parameters.append(

            bigquery.ScalarQueryParameter(
                "start_date",
                "DATE",
                start_date
            )

        )


    if end_date:

        query += """
        AND DATE(date) <= @end_date
        """

        parameters.append(

            bigquery.ScalarQueryParameter(
                "end_date",
                "DATE",
                end_date
            )

        )


    query += """
    ORDER BY date
    """


    job_config = bigquery.QueryJobConfig(
        query_parameters=parameters
    )


    result = client.query(
        query,
        job_config=job_config
    ).result()


    return result.to_dataframe()