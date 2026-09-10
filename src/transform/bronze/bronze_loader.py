from google.cloud import bigquery
import uuid
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
    # Cluster by symbol
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
import uuid
def load_one_file(
    gcs_uri: str,
    symbol: str
):

    table_id = get_table_id()

    # ------------------------------------------------------
    # Unique staging table for this symbol
    # ------------------------------------------------------

    staging_table_id = (
    f"{GCP_PROJECT_ID}."
    f"{BQ_BRONZE_DATASET}."
    f"_staging_{symbol.lower()}_"
    f"{uuid.uuid4().hex[:8]}"
    )

    print(
        f"Creating staging table: "
        f"{staging_table_id}"
    )

    try:

        # ==================================================
        # STAGE 1
        # GCS → BIGQUERY STAGING
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
        # STAGE 2
        # COUNT NEW RECORDS
        # ==================================================
        #
        # We calculate this BEFORE the MERGE.
        #
        # Existing:
        #   symbol + date already in Bronze
        #   → don't count
        #
        # New:
        #   symbol + date not in Bronze
        #   → count
        #
        # ==================================================

        count_query = f"""
    SELECT
        COUNT(*) AS new_row_count

    FROM
    (
        SELECT DISTINCT

            SAFE.PARSE_DATETIME(
                '%Y-%m-%d %H:%M:%S',
                TRIM(source.date)
            ) AS parsed_date

        FROM `{staging_table_id}` source

        WHERE SAFE.PARSE_DATETIME(
            '%Y-%m-%d %H:%M:%S',
            TRIM(source.date)
        ) IS NOT NULL
    ) source

    WHERE NOT EXISTS
    (
        SELECT 1

        FROM `{table_id}` target

        WHERE target.symbol = @symbol

        AND target.date =
            source.parsed_date
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
            count_result.new_row_count
        )

        print(
            f"New rows to insert: "
            f"{new_row_count}"
        )

        # ==================================================
        # STAGE 3
        # STAGING → BRONZE
        # ==================================================
        #
        # MERGE protects us from duplicate records.
        #
        # Unique business key:
        #
        #       symbol + date
        #
        # MATCHED:
        #       do nothing
        #
        # NOT MATCHED:
        #       insert
        #
        # ==================================================

        merge_query = f"""

    MERGE `{table_id}` AS target

    USING
    (
        SELECT
            date,
            open,
            high,
            low,
            close,
            volume,
            symbol

        FROM
        (
            SELECT

                SAFE.PARSE_DATETIME(
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
                ) AS volume,

                @symbol AS symbol,

                ROW_NUMBER() OVER
                (
                    PARTITION BY
                        SAFE.PARSE_DATETIME(
                            '%Y-%m-%d %H:%M:%S',
                            TRIM(date)
                        )

                    ORDER BY
                        SAFE.PARSE_DATETIME(
                            '%Y-%m-%d %H:%M:%S',
                            TRIM(date)
                        )
                ) AS row_num

            FROM `{staging_table_id}`

            WHERE SAFE.PARSE_DATETIME(
                '%Y-%m-%d %H:%M:%S',
                TRIM(date)
            ) IS NOT NULL
        )

        WHERE row_num = 1

    ) AS source

    ON target.symbol = source.symbol

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
            source.symbol
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
        # RESULT
        # ==================================================

        return {

            "status": "SUCCESS",

            "symbol": symbol,

            "gcs_uri": gcs_uri,

            "row_count": new_row_count,

        }

    finally:

        # ==================================================
        # CLEANUP STAGING TABLE
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