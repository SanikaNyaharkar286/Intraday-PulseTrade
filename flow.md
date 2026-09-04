# Execution Flow

This file traces exactly how execution moves between files and functions.

## Historical Flow

Command:

```powershell
python main.py
```

Execution path:

```text
src/main.py
  main()
    -> historical.run_historical()

src/historical/historical_loader.py
  run_historical()
    -> reads HISTORICAL_START_YEAR
    -> reads HISTORICAL_START_MONTH
    -> reads HISTORICAL_END_YEAR
    -> reads HISTORICAL_END_MONTH
    -> reads src/.pipeline_state/historical_checkpoint.json if it exists
    -> starts from the next month after the last completed month
    -> loops month by month
    -> calls process_historical_month(year, month)

src/transform/bronze/bronze.py
  process_historical_month(year, month)
    -> ensure_audit_table()
    -> ensure_bronze_table()
    -> builds GCS path:
       gs://processed-intraday/<year>/<MonthName>/*.csv
    -> creates temporary BigQuery external table over monthly CSV files
    -> creates temporary staging table
    -> converts CSV date from IST local time to BigQuery TIMESTAMP
    -> extracts symbol from CSV file name
    -> merges staging rows into Bronze using symbol + timestamp
    -> writes Bronze audit record
    -> deletes temporary external/staging tables
    -> calls _run_silver_pipeline()

src/transform/bronze/bronze.py
  _run_silver_pipeline()
    -> imports run_silver_pipeline()
    -> calls run_silver_pipeline()

src/transform/silver/silver.py
  run_silver_pipeline()
    -> ensure_silver_objects()
    -> CALL `<project>.<silver_dataset>.sp_bronze_to_silver`()
    -> calls run_gold_pipeline()

src/transform/silver/silver.py
  ensure_silver_objects()
    -> runs 01_create_silver_tables.sql
    -> runs 02_sp_bronze_to_silver.sql

src/transform/silver/sql/01_create_silver_tables.sql
  Creates Silver dataset and tables:
    -> silver_intraday_1m
    -> silver_intraday_5m
    -> silver_daily_stock
    -> silver_rejects
    -> silver_audit

src/transform/silver/sql/02_sp_bronze_to_silver.sql
  sp_bronze_to_silver()
    -> reads Bronze
    -> validates rows
    -> writes rejects
    -> deduplicates valid rows
    -> gets historical lookback
    -> calculates 1-minute indicators
    -> merges Silver 1-minute rows
    -> builds finalized 5-minute rows with indicators
    -> builds daily stock rows
    -> writes Silver audit row

src/transform/gold/gold.py
  run_gold_pipeline()
    -> runs 01_create_gold_tables.sql
    -> runs 02_sp_silver_to_gold.sql
    -> CALL `<project>.<gold_dataset>.sp_silver_to_gold`()
    -> refreshes Semantic views
```

End result:

```text
One historical month loaded to Bronze
Silver, Gold, and Semantic updated for that month
Checkpoint updated for that month
Next month starts
```

## Incremental Cloud Function Flow

Trigger:

```text
Upload CSV to gs://processed-intraday
```

Example:

```text
gs://processed-intraday/2026/3MINDIA_2026-03-04.csv
```

Execution path:

```text
src/main.py
  process_new_csv(cloud_event)
    -> reads cloud_event.data
    -> gets bucket from data["bucket"]
    -> gets file path from data["name"]
    -> ignores non-CSV files
    -> calls run_incremental(file_path)

src/incremental/incremental_loader.py
  run_incremental(file_path)
    -> validates file_path
    -> skips non-CSV files
    -> calls process_new_file(file_path)

src/transform/bronze/bronze.py
  process_new_file(file_path)
    -> ensure_audit_table()
    -> ensure_bronze_table()
    -> builds GCS URI:
       gs://processed-intraday/<file_path>
    -> creates temporary BigQuery external table over that one CSV
    -> creates temporary staging table
    -> converts CSV date from IST local time to BigQuery TIMESTAMP
    -> extracts symbol from CSV file name
    -> removes trailing _YYYY-MM-DD from symbol names when present
    -> merges staging rows into Bronze using symbol + timestamp
    -> reads staged symbol and timestamp range
    -> writes Bronze audit record
    -> deletes temporary external/staging tables
    -> calls _run_silver_pipeline(scope_symbol, scope_start, scope_end)

src/transform/silver/silver.py
  run_silver_pipeline(scope_symbol, scope_start, scope_end)
    -> deletes old generated Silver timestamp tables if they still use UTC TIMESTAMP
    -> creates or updates Silver tables/procedure
    -> renders scoped Bronze filters for incremental uploads
    -> calls sp_bronze_to_silver()
    -> calls run_gold_pipeline(scope_symbol, scope_start, scope_end)

src/transform/gold/gold.py
  run_gold_pipeline(scope_symbol, scope_start, scope_end)
    -> creates or updates Gold tables/procedure
    -> renders scoped Silver/Gold filters for incremental uploads
    -> calls sp_silver_to_gold()
    -> creates or updates Semantic views
```

End result:

```text
One uploaded CSV loaded to Bronze
Silver, Gold, and Semantic updated immediately after Bronze
```

## Important Function Calls

Main local entry:

```text
main.py -> main() -> run_historical()
```

Cloud Function entry:

```text
main.py -> process_new_csv(cloud_event) -> run_incremental(file_path)
```

Historical Bronze loader:

```text
historical_loader.py -> run_historical() -> process_historical_month()
```

Incremental Bronze loader:

```text
incremental_loader.py -> run_incremental() -> process_new_file()
```

Silver runner:

```text
bronze.py -> _run_silver_pipeline() -> silver.py -> run_silver_pipeline()
```

Gold runner:

```text
silver.py -> run_gold_pipeline() -> gold.py -> sp_silver_to_gold()
```

Silver SQL:

```text
silver.py -> 01_create_silver_tables.sql
silver.py -> 02_sp_bronze_to_silver.sql
silver.py -> CALL sp_bronze_to_silver()
```

Gold and Semantic SQL:

```text
gold.py -> 01_create_gold_tables.sql
gold.py -> 02_sp_silver_to_gold.sql
gold.py -> CALL sp_silver_to_gold()
gold.py -> semantic SQL view files
```

Historical checkpoint:

```text
historical_loader.py -> _get_start_month()
historical_loader.py -> _read_checkpoint()
historical_loader.py -> _write_checkpoint()
```

## Function Purpose

```text
main.py
  -> Starts historical locally
  -> Receives Cloud Function events for incremental files

historical_loader.py
  -> Controls month-by-month backfill and checkpoint resume

incremental_loader.py
  -> Validates one uploaded CSV event path

bronze.py
  -> Loads GCS CSV data into Bronze with external/staging tables and MERGE

silver.py
  -> Creates Silver objects and runs sp_bronze_to_silver()

gold.py
  -> Creates Gold objects, runs sp_silver_to_gold(), and refreshes Semantic views
```

## Data Movement

Historical:

```text
GCS month folder
  -> BigQuery external table
  -> BigQuery staging table
  -> bronze_data.intraday_master
  -> silver_dataset_us.silver_intraday_1m
  -> silver_dataset_us.silver_intraday_5m
  -> silver_dataset_us.silver_daily_stock
  -> pulse_trade_gold Gold tables
  -> pulse_trade_semantic Semantic views
```

Incremental:

```text
Single uploaded GCS CSV
  -> BigQuery external table
  -> BigQuery staging table
  -> bronze_data.intraday_master
  -> silver_dataset_us Silver tables for the uploaded symbol/date scope
  -> pulse_trade_gold Gold tables for the uploaded symbol/date scope
  -> pulse_trade_semantic Semantic views
```

Rejects:

```text
Bronze invalid rows
  -> silver_dataset_us.silver_rejects
```

Audit:

```text
Bronze run info
  -> audit_dataset_us.pipeline_audit

Silver run info
  -> silver_dataset_us.silver_audit
```

## Reading In Sorted Order

BigQuery does not guarantee row order when you open a table directly. To see company-wise time order, always query with:

```sql
ORDER BY symbol ASC, timestamp ASC
```

For Bronze, display IST time with:

```sql
DATETIME(timestamp, "Asia/Kolkata")
```

For Silver 1-minute and 5-minute, `timestamp` is already stored as IST `DATETIME`.
