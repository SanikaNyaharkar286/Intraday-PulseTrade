from datetime import datetime, timezone
import re    #used for regex operation
import uuid     #unique batch id for each run 

from google.cloud import bigquery

from transform.config import (
    PROJECT_ID,
    BQ_LOCATION,
    BUCKET_NAME,
    BRONZE_DATASET,
    BRONZE_TABLE,
    AUDIT_DATASET,
    AUDIT_TABLE,
)


_bq_client = None
_bq_location = None


def get_bq_location():
    global _bq_location

    if _bq_location is None:
        metadata_client = bigquery.Client(
            project=PROJECT_ID
        )

        try:
            dataset = metadata_client.get_dataset(
                f"{PROJECT_ID}.{BRONZE_DATASET}"
            )

            _bq_location = dataset.location

        except Exception:
            _bq_location = BQ_LOCATION

    return _bq_location


def get_bq_client():
    global _bq_client

    if _bq_client is None:
        _bq_client = bigquery.Client(
            project=PROJECT_ID,
            location=get_bq_location()
        )

    return _bq_client


def _table_id(dataset, table):
    return (
        f"{PROJECT_ID}."
        f"{dataset}."
        f"{table}"
    )


def _quoted_table_id(dataset, table):
    return f"`{_table_id(dataset, table)}`"

#bigquery table name should not have special char so this function will repalce 
def _safe_table_suffix(value):
    return re.sub(
        r"[^A-Za-z0-9_]",
        "_",
        value
    )

#want to normalize the symbol by removing the data 
def _normalize_symbol(symbol):
    return re.sub(
        r"_[0-9]{4}-[0-9]{2}-[0-9]{2}$",
        "",
        str(symbol)
    )

#after processing the month we can delete the temp table which create the stging 
def _delete_temp_tables(*table_ids):
    client = get_bq_client()

    for table_id in table_ids:
        if table_id:
            client.delete_table(
                table_id,
                not_found_ok=True
            )

#count the rows in the table and return the total count 
def _rows_in_table(table_id):
    query = f"""
    SELECT COUNT(*) AS total
    FROM `{table_id}`
    """

    count_result = (
        get_bq_client()
        .query(query)
        .result()
    )

    return list(count_result)[0]["total"]


def _merge_to_bronze(staging_table):
    #merge the staging table to bronze table if record is already there update or insert 
    merge_query = f"""
    
    MERGE {_quoted_table_id(BRONZE_DATASET, BRONZE_TABLE)} T

    USING `{staging_table}` S

    ON
        T.symbol = S.symbol
        AND T.timestamp = S.timestamp

    WHEN MATCHED THEN

        UPDATE SET
            open = S.open,
            high = S.high,
            low = S.low,
            close = S.close,
            volume = S.volume

    WHEN NOT MATCHED THEN

        INSERT
        (
            timestamp,
            open,
            high,
            low,
            close,
            volume,
            symbol
        )

        VALUES
        (
            S.timestamp,
            S.open,
            S.high,
            S.low,
            S.close,
            S.volume,
            S.symbol
        )
    """

    get_bq_client().query(
        merge_query
    ).result()


def _run_silver_pipeline(
    scope_symbol=None,
    scope_start=None,
    scope_end=None
):
    from transform.silver.silver import run_silver_pipeline

    run_silver_pipeline(
        scope_symbol=scope_symbol,
        scope_start=scope_start,
        scope_end=scope_end
    )


def _incremental_scope_from_table(staging_table):
    query = f"""
    SELECT
        COUNT(DISTINCT symbol) AS symbols_total,
        ARRAY_AGG(DISTINCT symbol IGNORE NULLS LIMIT 2) AS symbols,
        MIN(timestamp) AS scope_start,
        MAX(timestamp) AS scope_end
    FROM `{staging_table}`
    """

    rows = (
        get_bq_client()
        .query(query)
        .result()
    )

    row = next(iter(rows), None)

    if (
        not row
        or row["symbols_total"] != 1
        or not row["symbols"]
        or row["scope_start"] is None
        or row["scope_end"] is None
    ):
        return None

    return {
        "symbol": _normalize_symbol(row["symbols"][0]),
        "start": row["scope_start"].isoformat(),
        "end": row["scope_end"].isoformat(),
    }


def ensure_audit_table():
    client = get_bq_client()

    dataset_id = f"{PROJECT_ID}.{AUDIT_DATASET}"
    table_id = _table_id(
        AUDIT_DATASET,
        AUDIT_TABLE
    )

    dataset = bigquery.Dataset(dataset_id)
    dataset.location = get_bq_client().location

    client.create_dataset(
        dataset,
        exists_ok=True
    )

    schema = [
        bigquery.SchemaField(
            "batch_id",
            "STRING",
            mode="REQUIRED"
        ),
        bigquery.SchemaField(
            "pipeline_type",
            "STRING",
            mode="REQUIRED"
        ),
        bigquery.SchemaField(
            "process_date",
            "TIMESTAMP",
            mode="REQUIRED"
        ),
        bigquery.SchemaField(
            "year",
            "INT64"
        ),
        bigquery.SchemaField(
            "month",
            "INT64"
        ),
        bigquery.SchemaField(
            "file_name",
            "STRING"
        ),
        bigquery.SchemaField(
            "status",
            "STRING",
            mode="REQUIRED"
        ),
        bigquery.SchemaField(
            "rows_processed",
            "INT64"
        ),
        bigquery.SchemaField(
            "message",
            "STRING"
        ),
    ]

    table = bigquery.Table(
        table_id,
        schema=schema
    )

    client.create_table(
        table,
        exists_ok=True
    )

    print(
        f"Audit table ready: {table_id}"
    )


def insert_audit(
    batch_id,
    pipeline_type,
    year=None,
    month=None,
    file_name=None,
    status="SUCCESS",
    rows_processed=None,
    message=None
):
    audit_table = _quoted_table_id(
        AUDIT_DATASET,
        AUDIT_TABLE
    )

    query = f"""
    INSERT INTO {audit_table}
    (
        batch_id,
        pipeline_type,
        process_date,
        year,
        month,
        file_name,
        status,
        rows_processed,
        message
    )
    VALUES
    (
        @batch_id,
        @pipeline_type,
        CURRENT_TIMESTAMP(),
        @year,
        @month,
        @file_name,
        @status,
        @rows_processed,
        @message
    )
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter(
                "batch_id",
                "STRING",
                batch_id
            ),
            bigquery.ScalarQueryParameter(
                "pipeline_type",
                "STRING",
                pipeline_type
            ),
            bigquery.ScalarQueryParameter(
                "year",
                "INT64",
                year
            ),
            bigquery.ScalarQueryParameter(
                "month",
                "INT64",
                month
            ),
            bigquery.ScalarQueryParameter(
                "file_name",
                "STRING",
                file_name
            ),
            bigquery.ScalarQueryParameter(
                "status",
                "STRING",
                status
            ),
            bigquery.ScalarQueryParameter(
                "rows_processed",
                "INT64",
                rows_processed
            ),
            bigquery.ScalarQueryParameter(
                "message",
                "STRING",
                message
            ),
        ]
    )

    try:
        get_bq_client().query(
            query,
            job_config=job_config
        ).result()

    except Exception as e:
        print(
            f"Audit insert skipped: {e}"
        )

        return

    print(
        f"Audit inserted: {batch_id} | {status}"
    )


def ensure_bronze_table():
    client = get_bq_client()

    dataset_id = (
        f"{PROJECT_ID}.{BRONZE_DATASET}"
    )

    table_id = _table_id(
        BRONZE_DATASET,
        BRONZE_TABLE
    )

    dataset = bigquery.Dataset(
        dataset_id
    )

    dataset.location = get_bq_client().location

    client.create_dataset(
        dataset,
        exists_ok=True
    )

    schema = [
        bigquery.SchemaField(
            "timestamp",
            "TIMESTAMP",
            mode="REQUIRED"
        ),
        bigquery.SchemaField(
            "open",
            "FLOAT64"
        ),
        bigquery.SchemaField(
            "high",
            "FLOAT64"
        ),
        bigquery.SchemaField(
            "low",
            "FLOAT64"
        ),
        bigquery.SchemaField(
            "close",
            "FLOAT64"
        ),
        bigquery.SchemaField(
            "volume",
            "FLOAT64"
        ),
        bigquery.SchemaField(
            "symbol",
            "STRING",
            mode="REQUIRED"
        ),
    ]

    table = bigquery.Table(
        table_id,
        schema=schema
    )

    table.time_partitioning = bigquery.TimePartitioning(
        type_=bigquery.TimePartitioningType.DAY,
        field="timestamp"
    )
#clustring is used to sort the data based on the fields so that it can be queried faster 
    table.clustering_fields = [
        "symbol",
        "timestamp",
    ]

    client.create_table(
        table,
        exists_ok=True
    )

    try:
        existing_table = client.get_table(
            table_id
        )

        if not existing_table.time_partitioning:
            print(
                "Bronze table is not partitioned. "
                "BigQuery cannot add partitioning to an existing table. "
                "Create a new partitioned Bronze table and copy data if needed."
            )

        if existing_table.clustering_fields != [
            "symbol",
            "timestamp",
        ]:
            existing_table.clustering_fields = [
                "symbol",
                "timestamp",
            ]

            client.update_table(
                existing_table,
                [
                    "clustering_fields",
                ]
            )

    except Exception as e:
        print(
            f"Bronze clustering update skipped: {e}"
        )

    print(
        f"Bronze table ready: {table_id}"
    )


def process_historical_month(
    year,
    month,
    pipeline_type="HISTORICAL",
    batch_prefix="HIST",
    run_silver=True
):
    ensure_audit_table()
    ensure_bronze_table()

    batch_id = (
        f"{batch_prefix}_{year}_{month:02d}_"
        f"{uuid.uuid4().hex[:8]}"
    )

    suffix = _safe_table_suffix(batch_id)

    month_name = datetime(
        year,
        month,
        1
    ).strftime("%B")

    gcs_path = (
        f"gs://{BUCKET_NAME}/"
        f"{year}/{month_name}/*.csv"
    )

    external_table = _table_id(
        BRONZE_DATASET,
        f"_external_{suffix}"
    )

    staging_table = _table_id(
        BRONZE_DATASET,
        f"_staging_{suffix}"
    )

    bronze_loaded = False

    try:
        print("=" * 60)
        print(
            f"{pipeline_type} processing: "
            f"{year}-{month:02d}"
        )
        print(
            f"GCS: {gcs_path}"
        )
        print("=" * 60)

        create_external = f"""
        CREATE OR REPLACE EXTERNAL TABLE
        `{external_table}`
        (
            date STRING,
            open FLOAT64,
            high FLOAT64,
            low FLOAT64,
            close FLOAT64,
            volume FLOAT64
        )
        OPTIONS (
            format = 'CSV',
            uris = ['{gcs_path}'],
            skip_leading_rows = 1
        )
        """

        get_bq_client().query(
            create_external
        ).result()

        create_stage = f"""
        CREATE OR REPLACE TABLE
        `{staging_table}` AS

        SELECT
            TIMESTAMP(
                SAFE_CAST(date AS DATETIME),
                "Asia/Kolkata"
            ) AS timestamp,
            open,
            high,
            low,
            close,
            volume,

            REGEXP_REPLACE(
                REGEXP_EXTRACT(
                    _FILE_NAME,
                    r'/([^/]+)\\.csv$'
                ),
                r'_[0-9]{4}-[0-9]{2}-[0-9]{2}$',
                ''
            ) AS symbol

        FROM `{external_table}`
        """

        get_bq_client().query(
            create_stage
        ).result()

        rows_processed = _rows_in_table(
            staging_table
        )

        _merge_to_bronze(
            staging_table
        )

        insert_audit(
            batch_id=batch_id,
            pipeline_type=pipeline_type,
            year=year,
            month=month,
            status="SUCCESS",
            rows_processed=rows_processed,
            message=(
                f"{pipeline_type} month "
                f"{year}-{month:02d} completed"
            )
        )

        print(
            f"{pipeline_type} completed: "
            f"{year}-{month:02d}"
        )

        bronze_loaded = True

    except Exception as e:
        print(
            f"{pipeline_type} failed: "
            f"{year}-{month:02d}"
        )

        print(str(e))

        insert_audit(
            batch_id=batch_id,
            pipeline_type=pipeline_type,
            year=year,
            month=month,
            status="FAILED",
            rows_processed=0,
            message=str(e)
        )

        raise

    finally:
        _delete_temp_tables(
            external_table,
            staging_table
        )

    if bronze_loaded and run_silver:
        _run_silver_pipeline()


def process_new_file(file_path):
    ensure_audit_table()
    ensure_bronze_table()

    batch_id = (
        "INC_"
        f"{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_"
        f"{uuid.uuid4().hex[:8]}"
    )

    suffix = _safe_table_suffix(batch_id)

    print("=" * 60)
    print(
        f"Incremental file received: {file_path}"
    )
    print("=" * 60)

    file_name = file_path.split("/")[-1]

    if not file_name.lower().endswith(".csv"):
        print(
            f"Skipping non-CSV file: "
            f"{file_name}"
        )

        return

    parts = file_path.split("/")

    year = None
    month = None

    if len(parts) >= 3:
        try:
            year = int(parts[-3])

            month_name = parts[-2]

            month = datetime.strptime(
                month_name,
                "%B"
            ).month

        except (ValueError, IndexError):
            year = None
            month = None

    gcs_uri = (
        f"gs://{BUCKET_NAME}/"
        f"{file_path}"
        if not file_path.startswith("gs://")
        else file_path
    )

    external_table = _table_id(
        BRONZE_DATASET,
        f"_incremental_external_{suffix}"
    )

    staging_table = _table_id(
        BRONZE_DATASET,
        f"_incremental_staging_{suffix}"
    )

    bronze_loaded = False
    incremental_scope = None

    try:
        create_external = f"""
        CREATE OR REPLACE EXTERNAL TABLE
        `{external_table}`
        (
            date STRING,
            open FLOAT64,
            high FLOAT64,
            low FLOAT64,
            close FLOAT64,
            volume FLOAT64
        )
        OPTIONS (
            format = 'CSV',
            uris = ['{gcs_uri}'],
            skip_leading_rows = 1
        )
        """

        get_bq_client().query(
            create_external
        ).result()

        create_stage = f"""
        CREATE OR REPLACE TABLE
        `{staging_table}` AS

        SELECT
            TIMESTAMP(
                SAFE_CAST(date AS DATETIME),
                "Asia/Kolkata"
            ) AS timestamp,
            open,
            high,
            low,
            close,
            volume,

            REGEXP_REPLACE(
                REGEXP_EXTRACT(
                    _FILE_NAME,
                    r'/([^/]+)\\.csv$'
                ),
                r'_[0-9]{4}-[0-9]{2}-[0-9]{2}$',
                ''
            ) AS symbol

        FROM `{external_table}`
        """

        get_bq_client().query(
            create_stage
        ).result()

        rows_processed = _rows_in_table(
            staging_table
        )

        incremental_scope = _incremental_scope_from_table(
            staging_table
        )

        if incremental_scope:
            print("Incremental Silver scope")
            print(f"  symbol: {incremental_scope['symbol']}")
            print(f"  start: {incremental_scope['start']}")
            print(f"  end: {incremental_scope['end']}")

        _merge_to_bronze(
            staging_table
        )

        insert_audit(
            batch_id=batch_id,
            pipeline_type="INCREMENTAL",
            year=year,
            month=month,
            file_name=file_name,
            status="SUCCESS",
            rows_processed=rows_processed,
            message=(
                f"Incremental file "
                f"{file_name} processed successfully"
            )
        )

        print(
            f"Incremental completed: "
            f"{file_name}"
        )

        bronze_loaded = True

    except Exception as e:
        print(
            f"Incremental failed: "
            f"{file_path}"
        )

        print(str(e))

        insert_audit(
            batch_id=batch_id,
            pipeline_type="INCREMENTAL",
            year=year,
            month=month,
            file_name=file_name,
            status="FAILED",
            rows_processed=0,
            message=str(e)
        )

        raise

    finally:
        _delete_temp_tables(
            external_table,
            staging_table
        )

    if bronze_loaded:
        if incremental_scope:
            _run_silver_pipeline(
                scope_symbol=incremental_scope["symbol"],
                scope_start=incremental_scope["start"],
                scope_end=incremental_scope["end"]
            )

        else:
            _run_silver_pipeline()
