from google.cloud import bigquery

from src.utils.config import (
    GCP_PROJECT_ID,
    BQ_BRONZE_DATASET,
    BQ_BRONZE_TABLE,
)

from src.transform.bronze.schema import (
    BRONZE_SCHEMA,
)


# ==========================================================
# BIGQUERY CLIENT
# ==========================================================

client = bigquery.Client(
    project=GCP_PROJECT_ID
)


# ==========================================================
# BRONZE TABLE ID
# ==========================================================

def get_table_id():

    return (
        f"{GCP_PROJECT_ID}."
        f"{BQ_BRONZE_DATASET}."
        f"{BQ_BRONZE_TABLE}"
    )


# ==========================================================
# CREATE BRONZE TABLE
# ==========================================================

def create_bronze_table():

    table_id = get_table_id()

    table = bigquery.Table(
        table_id,
        schema=BRONZE_SCHEMA
    )

    # ------------------------------------------------------
    # Partition by market date
    # ------------------------------------------------------

    table.time_partitioning = (
        bigquery.TimePartitioning(
            type_=bigquery.TimePartitioningType.DAY,
            field="date"
        )
    )

    # ------------------------------------------------------
    # Cluster by stock symbol
    # ------------------------------------------------------

    table.clustering_fields = [
        "symbol"
    ]

    return client.create_table(
        table,
        exists_ok=True
    )


# ==========================================================
# LOAD ONE GCS FILE
# ==========================================================

def load_one_file(
    gcs_uri: str,
    symbol: str
):

    table_id = get_table_id()

    staging_table_id = (
        f"{GCP_PROJECT_ID}."
        f"{BQ_BRONZE_DATASET}."
        f"_staging_{symbol.lower()}"
    )

    print(
        f"Creating staging table: "
        f"{staging_table_id}"
    )

    try:

        # ==================================================
        # 1. GCS → STAGING
        # ==================================================

        staging_job_config = (
            bigquery.LoadJobConfig(

                schema=[

                    bigquery.SchemaField(
                        "date",
                        "STRING"
                    ),

                    bigquery.SchemaField(
                        "open",
                        "STRING"
                    ),

                    bigquery.SchemaField(
                        "high",
                        "STRING"
                    ),

                    bigquery.SchemaField(
                        "low",
                        "STRING"
                    ),

                    bigquery.SchemaField(
                        "close",
                        "STRING"
                    ),

                    bigquery.SchemaField(
                        "volume",
                        "STRING"
                    ),

                ],

                skip_leading_rows=1,

                source_format=(
                    bigquery.SourceFormat.CSV
                ),

                write_disposition=(
                    bigquery.WriteDisposition
                    .WRITE_TRUNCATE
                ),

                field_delimiter=",",

                allow_quoted_newlines=True,

                ignore_unknown_values=False,
            )
        )

        print(
            f"Loading GCS file into staging: "
            f"{gcs_uri}"
        )

        load_job = client.load_table_from_uri(
            gcs_uri,
            staging_table_id,
            job_config=staging_job_config,
        )

        load_job.result()

        print(
            "GCS → staging completed"
        )

        # ==================================================
        # 2. COUNT ONLY NEW ROWS
        # ==================================================

        count_query = f"""
            SELECT
                COUNT(*) AS row_count

            FROM `{staging_table_id}` AS source

            WHERE NOT EXISTS
            (
                SELECT 1

                FROM `{table_id}` AS target

                WHERE target.symbol = @symbol

                AND target.date =
                    PARSE_DATETIME(
                        '%Y-%m-%d %H:%M:%S',
                        TRIM(source.date)
                    )
            )
        """

        count_config = (
            bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter(
                        "symbol",
                        "STRING",
                        symbol
                    )
                ]
            )
        )

        print(
            "Checking for new rows..."
        )

        count_job = client.query(
            count_query,
            job_config=count_config
        )

        count_result = next(
            iter(
                count_job.result()
            )
        )

        new_row_count = int(
            count_result.row_count
        )

        print(
            f"New rows to insert: "
            f"{new_row_count}"
        )

        # ==================================================
        # 3. MERGE INTO BRONZE
        # ==================================================

        merge_query = f"""
            MERGE `{table_id}` AS target

            USING
            (
                SELECT

                    PARSE_DATETIME(
                        '%Y-%m-%d %H:%M:%S',
                        TRIM(date)
                    ) AS date,

                    SAFE_CAST(
                        TRIM(open)
                        AS FLOAT64
                    ) AS open,

                    SAFE_CAST(
                        TRIM(high)
                        AS FLOAT64
                    ) AS high,

                    SAFE_CAST(
                        TRIM(low)
                        AS FLOAT64
                    ) AS low,

                    SAFE_CAST(
                        TRIM(close)
                        AS FLOAT64
                    ) AS close,

                    SAFE_CAST(
                        TRIM(volume)
                        AS FLOAT64
                    ) AS volume

                FROM `{staging_table_id}`

                QUALIFY ROW_NUMBER() OVER
                (
                    PARTITION BY date
                    ORDER BY date
                ) = 1

            ) AS source

            ON
                target.symbol = @symbol
                AND target.date = source.date

            WHEN NOT MATCHED THEN

                INSERT
                (
                    date,
                    open,
                    high,
                    low,
                    close,
                    volume,
                    symbol
                )

                VALUES
                (
                    source.date,
                    source.open,
                    source.high,
                    source.low,
                    source.close,
                    source.volume,
                    @symbol
                )
        """

        merge_config = (
            bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter(
                        "symbol",
                        "STRING",
                        symbol
                    )
                ]
            )
        )

        print(
            "Merging data into Bronze..."
        )

        merge_job = client.query(
            merge_query,
            job_config=merge_config
        )

        merge_job.result()

        print(
            "Staging → Bronze completed"
        )

        # ==================================================
        # 4. RETURN RESULT
        # ==================================================

        return {

            "status":
                "SUCCESS",

            "symbol":
                symbol,

            "gcs_uri":
                gcs_uri,

            "row_count":
                new_row_count,

        }

    finally:

        # ==================================================
        # 5. ALWAYS CLEAN STAGING TABLE
        # ==================================================

        print(
            f"Cleaning staging table: "
            f"{staging_table_id}"
        )

        client.delete_table(
            staging_table_id,
            not_found_ok=True
        )

        print(
            "Staging table cleanup completed"
        )