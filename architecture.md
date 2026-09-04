# Architecture

Intraday-PulseTrade is a Google Cloud data pipeline for intraday stock market CSV files.

It has two ingestion paths:

- Historical backfill from existing GCS folders.
- Incremental processing from new GCS uploads.

Both paths write to Bronze first, then run Silver, Gold, and Semantic refreshes.

## High Level Architecture

```text
                    Historical command
                    python main.py
                           |
                           v
GCS historical folders -> Bronze loader
                           |
                           v
                    Bronze BigQuery table
                           |
                           v
                    Silver stored procedure
                           |
                           v
                    Silver BigQuery tables
                           |
                           v
                    Gold stored procedure
                           |
                           v
                    Gold business tables
                           |
                           v
                    Semantic views


New CSV upload -> Cloud Storage Eventarc trigger
                           |
                           v
                    Cloud Function process_new_csv
                           |
                           v
                    Incremental Bronze loader
                           |
                           v
                    Bronze BigQuery table
                           |
                           v
                    Silver stored procedure
                           |
                           v
                    Silver BigQuery tables
                           |
                           v
                    Gold stored procedure
                           |
                           v
                    Gold business tables
                           |
                           v
                    Semantic views
```

## Layers

### Source Layer

Source files are CSV files in Cloud Storage.

Expected header:

```csv
date,open,high,low,close,volume
```

Historical folder style:

```text
gs://processed-intraday/<year>/<MonthName>/<SYMBOL>.csv
```

Incremental files can also be uploaded directly under a year folder:

```text
gs://processed-intraday/2026/3MINDIA_2026-03-04.csv
```

### Bronze Layer

Bronze is the raw normalized BigQuery layer.

Table:

```text
project-001658fa-3ce5-4746-980.bronze_data.intraday_master
```

Columns:

```text
timestamp, open, high, low, close, volume, symbol
```

Responsibilities:

- Read CSV through a BigQuery external table.
- Convert CSV `date` as IST.
- Extract the stock symbol from the file name.
- Merge rows by `symbol + timestamp`.
- Keep only one latest row for each business key.
- Partition new Bronze tables by `timestamp`.
- Cluster Bronze by `symbol, timestamp`.

### Silver Layer

Silver is the trusted analytics layer.

Dataset:

```text
project-001658fa-3ce5-4746-980.silver_dataset_us
```

Tables:

```text
silver_intraday_1m
silver_intraday_5m
silver_daily_stock
silver_rejects
silver_audit
```

Responsibilities:

- Validate Bronze records.
- Store invalid records in rejects.
- Deduplicate by business key.
- Store Silver intraday timestamps as IST `DATETIME`.
- Calculate reusable technical indicators.
- Build 5-minute candles from trusted Silver 1-minute rows.
- Build daily stock rows from trusted Silver intraday data.
- Record Silver execution audit.

### Gold Layer

Gold is the business and trading-ready layer.

Dataset:

```text
project-001658fa-3ce5-4746-980.pulse_trade_gold
```

Tables:

```text
dim_stock
dim_date
dim_timeframe
fact_intraday_metrics
fact_intraday_signals
fact_daily_market
fact_stock_returns
```

Responsibilities:

- Read trusted Silver tables.
- Keep reusable Silver indicators.
- Add business fields such as trend, volume status, and momentum score.
- Store deterministic trading events in `fact_intraday_signals`.
- Store daily market facts and multi-year returns.

### Semantic Layer

Semantic is the dashboard and chatbot-friendly view layer.

Dataset:

```text
project-001658fa-3ce5-4746-980.pulse_trade_semantic
```

Responsibilities:

- Expose views only.
- Read from Gold tables.
- Provide latest stock metrics, scanner views, breakouts, gainers, losers, returns, and market overview.

## BigQuery Design

Bronze business key:

```text
symbol + timestamp
```

Daily business key:

```text
symbol + trade_date
```

Bronze:

```text
PARTITION BY timestamp date
CLUSTER BY symbol, timestamp
```

Silver 1-minute and Silver 5-minute:

```text
PARTITION BY trade_date
CLUSTER BY symbol, timestamp
```

Silver rejects:

```text
CLUSTER BY symbol, timestamp
```

Silver daily table:

```text
PARTITION BY trade_date
CLUSTER BY symbol
```

Reason:

- Date partitioning reduces scanned data.
- Symbol and timestamp clustering speeds company-wise time-series queries.
- `MERGE` makes repeated file processing idempotent.

BigQuery does not guarantee displayed row order unless the query uses `ORDER BY`.

## Silver Validation

Rows are rejected when:

```text
symbol is null
timestamp is null
open/high/low/close/volume is null
open/high/low/close <= 0
volume < 0
high < low
open outside low-high
close outside low-high
timestamp outside 09:15 to 15:30 IST
```

Rejected rows are written to:

```text
silver_dataset_us.silver_rejects
```

## Silver Intraday Indicators

Silver 1-minute and 5-minute calculate:

```text
previous_close
return_pct
gap_pct
sma_20
ema_9
ema_20
rsi_14
macd
macd_signal
vwap
avg_volume_20
relative_volume
```

Silver does not create buy/sell signals.

## Runtime Components

### Local Historical Runtime

Used for backfill:

```text
python main.py
```

Runs on the developer machine and uses local Google authentication.

Historical checkpoint:

```text
src/.pipeline_state/historical_checkpoint.json
```

The checkpoint is written after each month completes. If the process stops, the next `python main.py` run resumes from the next uncompleted month.

### Cloud Function Runtime

Used for incremental files:

```text
process_new_csv
```

Runs in Google Cloud when a CSV is uploaded to the bucket.

Function service account:

```text
527618877818-compute@developer.gserviceaccount.com
```

Required permissions:

```text
roles/bigquery.jobUser
roles/bigquery.dataEditor
roles/storage.objectViewer
```

## Location Rule

BigQuery location must be consistent.

Current config:

```text
BQ_LOCATION=US
```

Datasets used by the pipeline:

```text
bronze_data
silver_dataset_us
audit_dataset_us
```

Do not mix `US` and `us-east1` datasets in the same BigQuery query path.
