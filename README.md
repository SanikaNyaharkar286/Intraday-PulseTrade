# Intraday-PulseTrade

Intraday-PulseTrade loads intraday stock market CSV files from Google Cloud Storage into BigQuery.

The pipeline has two paths:

- Historical backfill: run locally with `python main.py`.
- Incremental load: runs automatically when a new CSV is uploaded to the bucket.

Both paths load Bronze first, then run Silver, Gold, and Semantic automatically.

```text
CSV in GCS
  -> Bronze BigQuery load
  -> Silver stored procedure
  -> Silver analytics tables
  -> Gold stored procedure
  -> Gold business tables
  -> Semantic dashboard views
```

## Current Defaults

```text
Project ID: project-001658fa-3ce5-4746-980
Bucket: processed-intraday
BigQuery location: US
Bronze dataset: bronze_data
Bronze table: intraday_master
Silver dataset: silver_dataset_us
Gold dataset: pulse_trade_gold
Semantic dataset: pulse_trade_semantic
Audit dataset: audit_dataset_us
Audit table: pipeline_audit
Historical range: 2015-01 to 2026-02
Historical Silver mode: run after every Bronze month
Cloud Function: process-new-csv
Cloud Function region: us-east1
Function workers: 4
Function threads per worker: 1
```

## Repository Layout

```text
Intraday-PulseTrade/
|-- README.md
|-- architecture.md
|-- decision.md
|-- flow.md
|-- src/
|   |-- main.py
|   |-- requirements.txt
|   |-- historical/
|   |   `-- historical_loader.py
|   |-- incremental/
|   |   `-- incremental_loader.py
|   `-- transform/
|       |-- config.py
|       |-- bronze/
|       |   `-- bronze.py
|       |-- silver/
|       |   |-- silver.py
|       |   `-- sql/
|       |       |-- 01_create_silver_tables.sql
|       |       `-- 02_sp_bronze_to_silver.sql
|       |-- gold/
|       |   |-- gold.py
|       |   `-- sql/
|       |       |-- 01_create_gold_tables.sql
|       |       |-- 02_sp_silver_to_gold.sql
|       |       `-- 03_gold_validation.sql
|       `-- semantic/
|           `-- sql/
|               |-- 01_create_semantic_views.sql
|               |-- 02_stock_views.sql
|               |-- 03_scanner_views.sql
|               `-- 04_market_views.sql
`-- Terraform/
```

## Data Format

CSV header:

```csv
date,open,high,low,close,volume
```

Historical folder format:

```text
gs://processed-intraday/<year>/<MonthName>/<SYMBOL>.csv
```

Example:

```text
gs://processed-intraday/2026/March/3MINDIA.csv
```

Incremental files can also be uploaded like:

```text
gs://processed-intraday/2026/3MINDIA_2026-03-04.csv
```

The loader stores this symbol as:

```text
3MINDIA
```

CSV `date` values are treated as IST:

```sql
TIMESTAMP(SAFE_CAST(date AS DATETIME), "Asia/Kolkata")
```

## BigQuery Partitioning

Bronze is created as:

```text
PARTITION BY timestamp date
CLUSTER BY symbol, timestamp
```

Silver 1-minute and 5-minute are created as:

```text
PARTITION BY trade_date
CLUSTER BY symbol, timestamp
```

Silver daily is created as:

```text
PARTITION BY trade_date
CLUSTER BY symbol
```

Gold intraday facts are created as:

```text
PARTITION BY trade_date
CLUSTER BY symbol, timestamp
```

Gold daily facts are created as:

```text
PARTITION BY trade_date
CLUSTER BY symbol
```

Gold stock returns are created as:

```text
PARTITION BY as_of_date
CLUSTER BY symbol
```

Important: BigQuery cannot add partitioning to an existing non-partitioned Bronze table in place. New Bronze tables will be partitioned. If your current Bronze table already exists without partitioning, migrate it to a new partitioned table instead of deleting data.

## Setup

Run from `src/`:

```powershell
cd "D:\project\Intraday-PulseTrade (3)\Intraday-PulseTrade\src"
.\.venv\Scripts\Activate.ps1
```

Set environment variables:

```powershell
$env:GCP_PROJECT_ID="project-001658fa-3ce5-4746-980"
$env:GCP_REGION="us-east1"
$env:BQ_LOCATION="US"
$env:GCS_BUCKET="processed-intraday"
$env:BQ_BRONZE_DATASET="bronze_data"
$env:BQ_BRONZE_TABLE="intraday_master"
$env:BQ_SILVER_DATASET="silver_dataset_us"
$env:BQ_GOLD_DATASET="pulse_trade_gold"
$env:BQ_SEMANTIC_DATASET="pulse_trade_semantic"
$env:BQ_AUDIT_DATASET="audit_dataset_us"
$env:BQ_AUDIT_TABLE="pipeline_audit"
$env:RUN_GOLD_AFTER_SILVER="true"
$env:WORKERS="4"
$env:THREADS="1"
$env:HISTORICAL_START_YEAR="2015"
$env:HISTORICAL_START_MONTH="1"
$env:HISTORICAL_END_YEAR="2026"
$env:HISTORICAL_END_MONTH="2"
$env:HISTORICAL_CHECKPOINT_FILE="D:\project\Intraday-PulseTrade (3)\Intraday-PulseTrade\src\.pipeline_state\historical_checkpoint.json"
$env:HISTORICAL_RUN_SILVER_EACH_MONTH="true"
```

Install dependencies if needed:

```powershell
python -m pip install -r requirements.txt
```

## Run Historical Pipeline

Run:

```powershell
python main.py
```

What happens:

```text
main.py
  -> historical_loader.run_historical()
  -> bronze.process_historical_month()
  -> load one month into Bronze
  -> run Silver
  -> run Gold
  -> refresh Semantic views
  -> move to next month
```

With the current config, it runs:

```text
2015-01 through 2026-02
```

By default, Silver, Gold, and Semantic run after every completed historical Bronze month, so downstream tables update during the historical backfill.

If you want the faster behavior, set:

```powershell
$env:HISTORICAL_RUN_SILVER_EACH_MONTH="false"
```

Silver uses fast rolling-window EMA/MACD approximations during large historical builds. This avoids the expensive row-to-prior-rows self-join that made full Silver runs very slow.

After each month succeeds, the pipeline writes a checkpoint:

```text
src/.pipeline_state/historical_checkpoint.json
```

If you stop `python main.py` and run it again, it starts from the next uncompleted month.

Example:

```text
Last checkpoint: 2015-03
Next run starts: 2015-04
```

If the process stops during `2015-04`, the checkpoint stays at `2015-03`, so `2015-04` is retried.

If all Bronze months complete but the final Silver/Gold run fails, the checkpoint keeps `silver_completed=false`. The next `python main.py` run resumes by running the pending downstream pipeline instead of reloading every month.

## Run Silver, Gold, And Semantic Only

Use this when Bronze already has data and you only want to refresh downstream layers:

```powershell
python -c "from transform.silver.silver import run_silver_pipeline; run_silver_pipeline()"
```

## Run Gold And Semantic Only

Use this when Silver already has data and you only want to refresh Gold tables and Semantic views:

```powershell
python -c "from transform.gold.gold import run_gold_pipeline; run_gold_pipeline()"
```

## Test Incremental Locally

Start the local Cloud Function:

```powershell
functions-framework --target=process_new_csv --signature-type=cloudevent --port=8080
```

For a Linux/container multi-worker run, set the worker env vars before starting the framework:

```powershell
$env:WORKERS="4"
$env:THREADS="1"
functions-framework --target=process_new_csv --signature-type=cloudevent --port=8080
```

In another PowerShell terminal:

```powershell
$headers = @{
  "Content-Type" = "application/json"
  "Ce-Id" = "incremental-test-1"
  "Ce-Specversion" = "1.0"
  "Ce-Type" = "google.cloud.storage.object.v1.finalized"
  "Ce-Source" = "//storage.googleapis.com/projects/_/buckets/processed-intraday"
}

$body = @{
  bucket = "processed-intraday"
  name = "2026/3MINDIA_2026-03-04.csv"
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://127.0.0.1:8080/" -Method POST -Headers $headers -Body $body
```

Expected flow:

```text
CloudEvent POST
  -> process_new_csv()
  -> incremental_loader.run_incremental()
  -> bronze.process_new_file()
  -> Bronze MERGE
  -> Silver run
  -> Gold run
  -> Semantic views refresh
```

## Deploy Incremental Function

Deploy from `src/`:

```powershell
gcloud functions deploy process-new-csv `
  --gen2 `
  --runtime=python311 `
  --region=us-east1 `
  --source=. `
  --entry-point=process_new_csv `
  --concurrency=4 `
  --max-instances=10 `
  --trigger-event-filters=type=google.cloud.storage.object.v1.finalized `
  --trigger-event-filters=bucket=processed-intraday `
  --set-env-vars="GCP_PROJECT_ID=project-001658fa-3ce5-4746-980,GCP_REGION=us-east1,BQ_LOCATION=US,GCS_BUCKET=processed-intraday,BQ_BRONZE_DATASET=bronze_data,BQ_BRONZE_TABLE=intraday_master,BQ_SILVER_DATASET=silver_dataset_us,BQ_GOLD_DATASET=pulse_trade_gold,BQ_SEMANTIC_DATASET=pulse_trade_semantic,BQ_AUDIT_DATASET=audit_dataset_us,BQ_AUDIT_TABLE=pipeline_audit,RUN_GOLD_AFTER_SILVER=true,WORKERS=4,THREADS=1"
```

`--concurrency=4` lets one Gen2 function instance accept several file events at once, and `--max-instances=10` lets Google Cloud start more instances when many CSVs arrive together. Keep these numbers modest because every event can start BigQuery jobs and a Silver refresh.

After deploy, uploading a CSV to the bucket automatically runs:

```text
GCS upload -> Cloud Function -> Bronze -> Silver -> Gold -> Semantic
```

## Function Permissions

Find the Cloud Function service account:

```powershell
$SA = gcloud functions describe process-new-csv `
  --gen2 `
  --region=us-east1 `
  --format="value(serviceConfig.serviceAccountEmail)"

echo $SA
```

For this project the service account is:

```text
527618877818-compute@developer.gserviceaccount.com
```

Grant permissions:

```powershell
gcloud projects add-iam-policy-binding project-001658fa-3ce5-4746-980 `
  --member="serviceAccount:527618877818-compute@developer.gserviceaccount.com" `
  --role="roles/bigquery.jobUser"

gcloud projects add-iam-policy-binding project-001658fa-3ce5-4746-980 `
  --member="serviceAccount:527618877818-compute@developer.gserviceaccount.com" `
  --role="roles/bigquery.dataEditor"

gcloud storage buckets add-iam-policy-binding gs://processed-intraday `
  --member="serviceAccount:527618877818-compute@developer.gserviceaccount.com" `
  --role="roles/storage.objectViewer"
```

## Check Function Logs

```powershell
gcloud functions logs read process-new-csv `
  --gen2 `
  --region=us-east1 `
  --limit=50
```

Successful logs should include:

```text
Received Cloud Storage event
Incremental file received
Incremental completed
Silver pipeline completed
Gold and Semantic pipeline completed
Incremental processing finished
```

## Check Bronze

```sql
SELECT
  symbol,
  DATE(timestamp, "Asia/Kolkata") AS trade_date,
  COUNT(*) AS rows_loaded,
  MIN(TIME(timestamp, "Asia/Kolkata")) AS first_ist_time,
  MAX(TIME(timestamp, "Asia/Kolkata")) AS last_ist_time
FROM `project-001658fa-3ce5-4746-980.bronze_data.intraday_master`
WHERE symbol = '3MINDIA'
GROUP BY symbol, trade_date
ORDER BY trade_date DESC;
```

View Bronze company-wise and time-wise:

```sql
SELECT
  symbol,
  DATETIME(timestamp, "Asia/Kolkata") AS ist_timestamp,
  open,
  high,
  low,
  close,
  volume
FROM `project-001658fa-3ce5-4746-980.bronze_data.intraday_master`
WHERE symbol = '360ONE'
ORDER BY symbol ASC, ist_timestamp ASC;
```

## Check Silver

Silver 1-minute:

```sql
SELECT
  symbol,
  trade_date,
  COUNT(*) AS rows_loaded,
  MIN(TIME(timestamp)) AS first_ist_time,
  MAX(TIME(timestamp)) AS last_ist_time
FROM `project-001658fa-3ce5-4746-980.silver_dataset_us.silver_intraday_1m`
WHERE symbol = '3MINDIA'
GROUP BY symbol, trade_date
ORDER BY trade_date DESC;
```

View Silver 1-minute company-wise and time-wise:

```sql
SELECT
  symbol,
  timestamp AS ist_timestamp,
  open,
  high,
  low,
  close,
  volume
FROM `project-001658fa-3ce5-4746-980.silver_dataset_us.silver_intraday_1m`
WHERE symbol = '360ONE'
ORDER BY symbol ASC, timestamp ASC;
```

View Silver 5-minute company-wise and time-wise:

```sql
SELECT
  symbol,
  timestamp AS ist_timestamp,
  open,
  high,
  low,
  close,
  volume
FROM `project-001658fa-3ce5-4746-980.silver_dataset_us.silver_intraday_5m`
WHERE symbol = '360ONE'
ORDER BY symbol ASC, timestamp ASC;
```

Silver rejects:

```sql
SELECT
  reject_reason,
  COUNT(*) AS rejected_rows
FROM `project-001658fa-3ce5-4746-980.silver_dataset_us.silver_rejects`
WHERE symbol = '3MINDIA'
GROUP BY reject_reason
ORDER BY rejected_rows DESC;
```

Silver audit:

```sql
SELECT *
FROM `project-001658fa-3ce5-4746-980.silver_dataset_us.silver_audit`
ORDER BY run_start_time DESC
LIMIT 20;
```

## Silver Tables

```text
silver_intraday_1m
silver_intraday_5m
silver_daily_stock
silver_rejects
silver_audit
```

Silver is the trusted layer. It validates Bronze rows, rejects bad data, stores IST market timestamps as `DATETIME`, and calculates reusable technical indicators.

Silver 1-minute and 5-minute indicators:

```text
previous_close, return_pct, gap_pct, sma_20,
ema_9, ema_20, rsi_14, macd, macd_signal,
vwap, avg_volume_20, relative_volume
```

Silver does not create buy or sell signals.

Silver stores intraday `timestamp` as BigQuery `DATETIME`, not `TIMESTAMP`, so the value displays directly as IST market time.

Example:

```text
2026-03-04 09:15:00
```

If old Silver tables still have `timestamp TIMESTAMP` or the removed heavy indicator columns, the Silver runner deletes and recreates those generated Silver tables so they can be rebuilt from Bronze with IST `DATETIME` and the lean indicator schema.

## Gold Tables

```text
dim_stock
dim_date
dim_timeframe
fact_intraday_metrics
fact_intraday_signals
fact_daily_market
fact_stock_returns
```

Gold reads only from Silver. It keeps the Silver indicators and adds simple business fields like:

```text
price_vs_vwap
price_vs_ema20
price_vs_sma20
volume_status
trend
momentum_score
```

Trading events are stored in `fact_intraday_signals`, including:

```text
DAY_HIGH_BREAKOUT
DAY_LOW_BREAKDOWN
VWAP_CROSS_UP
VWAP_CROSS_DOWN
EMA_BULLISH_CROSSOVER
EMA_BEARISH_CROSSOVER
MACD_BULLISH_CROSSOVER
MACD_BEARISH_CROSSOVER
VOLUME_BREAKOUT
```

Gold is where trading/business logic belongs. Silver keeps indicators; Gold turns those indicators into dashboard-ready fields and deterministic signal events.

## Semantic Views

Semantic views read from Gold and are ready for dashboards or chatbot questions:

```text
vw_latest_intraday
vw_latest_daily
vw_stock_metrics
vw_scanner
vw_breakouts
vw_top_gainers
vw_top_losers
vw_stock_returns
vw_market_overview
```

## Troubleshooting

If all rows are rejected:

- Check `silver_rejects.reject_reason`.
- Most common cause is timestamp timezone.
- Bronze should show market times when queried with `TIME(timestamp, "Asia/Kolkata")`.

If the function triggers but does not load data:

- Check function logs.
- Confirm service account permissions.
- Confirm env vars are deployed correctly.

If BigQuery says dataset not found in location:

- Do not mix `US` and `us-east1` datasets in one query path.
- Keep Bronze, Silver, and audit datasets in `US` for this project.

If the function logs show unauthenticated requests:

- That can happen when manually opening the Cloud Run URL.
- Real GCS/Eventarc trigger logs will show `Received Cloud Storage event`.

## More Docs

- [Architecture](architecture.md)
- [Execution Flow](flow.md)
- [Decisions](decision.md)
- [Stored Procedures Explained](STORED_PROCEDURES_EXPLAINED.md)
- [Gold And Semantic Layer Explained](GOLD_SEMANTIC_LAYER_EXPLAINED.md)
