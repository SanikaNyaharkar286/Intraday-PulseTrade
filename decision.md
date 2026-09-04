# Project Decisions

This file records the main design decisions for the Intraday-PulseTrade pipeline.

## 1. Pipeline Uses Bronze, Silver, Gold, And Semantic Layers

The current pipeline is:

```text
GCS CSV files
  -> Bronze
  -> Silver
  -> Gold
  -> Semantic views
```

Reason:

- Bronze keeps raw normalized market data.
- Silver keeps trusted, validated data and reusable technical indicators.
- Gold keeps business-ready metrics, trends, signals, and return facts.
- Semantic views make the data easy for dashboards and chatbot-style questions.

## 2. No Scheduled Historical Batch

Historical data is loaded manually with:

```powershell
python main.py
```

Incremental data is loaded automatically when a new CSV is uploaded to the GCS bucket.

Reason:

- Historical backfill from 2015 to 2026 is a one-time or occasional operation.
- Incremental loads should react to new files immediately.
- The pipeline stays simple because data runs only when a backfill starts or a file arrives.

Scheduler can still be added later for timed checks, but it is not required for the GCS upload flow.

## 3. Historical Runs Month By Month

Historical processing runs one month at a time.

Example range:

```text
2015-01 to 2026-02
```

Default flow for every month:

```text
Load monthly CSV files to Bronze -> Run Silver -> Run Gold -> Refresh Semantic -> Move to next month
```

Fast backfill flow:

```powershell
$env:HISTORICAL_RUN_SILVER_EACH_MONTH="false"
python main.py
```

Fast mode does:

```text
Load all Bronze months -> Run Silver once -> Run Gold once -> Refresh Semantic views
```

Reason:

- Month-sized BigQuery jobs are easier to debug.
- If one month fails, the pipeline stops at that month.
- The default mode updates Silver and Gold during the backfill.
- The fast mode avoids running heavy Silver and Gold transformations after every month.
- Silver EMA/MACD uses fast rolling-window approximation to avoid expensive row-to-prior-row self joins on large historical builds.

## 4. Historical Resume Uses A Checkpoint

After each historical month completes successfully, the pipeline writes:

```text
src/.pipeline_state/historical_checkpoint.json
```

The checkpoint stores:

```text
last_completed_year
last_completed_month
silver_completed
```

On the next `python main.py` run:

- If the checkpoint says `2015-03` completed, the pipeline starts from `2015-04`.
- If the previous run stopped during `2015-04`, the checkpoint still says `2015-03`, so `2015-04` is retried.
- If Bronze is complete but downstream processing failed in fast mode, `silver_completed=false` allows the next run to refresh Silver/Gold without reloading all months.

Reason:

- Restarting `main.py` should not scan from `2015-01` every time.
- The checkpoint advances only after the month has safely completed.
- Bronze uses `MERGE`, so retrying a partially loaded month does not create duplicate business rows.

## 5. Incremental Is Event Driven

Incremental processing runs from the Cloud Function `process_new_csv`.

Trigger:

```text
New CSV uploaded to gs://processed-intraday
```

Flow:

```text
GCS upload -> Cloud Function -> Bronze -> Silver -> Gold -> Semantic views
```

Reason:

- New files are processed automatically.
- No manual command is needed after the Cloud Function is deployed.
- Re-uploading a CSV safely re-runs the pipeline because Bronze and downstream facts use deterministic keys or merges.
- Incremental uploads pass the staged symbol and timestamp range into Silver and Gold so only the uploaded symbol/date scope is recalculated.
- The Cloud Function runs with one instance and one concurrent request to avoid overlapping generated procedure deployments and BigQuery jobs.

## 6. Why The Main Python Functions Exist

`main.py`

- Provides the local historical entry point.
- Provides the Cloud Function entry point `process_new_csv`.

Reason:

- One file controls both execution paths without duplicating pipeline logic.

`historical_loader.run_historical()`

- Reads the configured start/end range.
- Reads and writes the historical checkpoint.
- Calls `process_historical_month()` for each month.

Reason:

- Historical backfill needs resume behavior and month-by-month control.

`incremental_loader.run_incremental()`

- Validates one uploaded file path.
- Calls `process_new_file()`.

Reason:

- Incremental load is file-based, not month-based.

`bronze.process_historical_month()`

- Creates a BigQuery external table over one month of CSV files.
- Creates a staging table.
- Merges rows into Bronze.

Reason:

- BigQuery can read the monthly wildcard path efficiently.
- Staging keeps raw file reads separate from the final Bronze table.
- Merge makes retry and reprocessing safe.

`bronze.process_new_file()`

- Creates a BigQuery external table over one uploaded CSV.
- Creates a staging table.
- Merges rows into Bronze.

Reason:

- Incremental files should process immediately and independently.

`silver.run_silver_pipeline()`

- Creates or updates Silver tables and procedure.
- Calls `sp_bronze_to_silver()`.
- Calls Gold when `RUN_GOLD_AFTER_SILVER=true`.

Reason:

- Historical and incremental paths share the same trusted transformation logic.

`gold.run_gold_pipeline()`

- Creates or updates Gold tables and procedure.
- Calls `sp_silver_to_gold()`.
- Creates or refreshes Semantic views.

Reason:

- Gold transformations stay in SQL.
- Python only orchestrates BigQuery objects and procedure calls.

## 7. Bronze Is The Raw Landing Layer

Bronze stores normalized OHLCV rows:

```text
timestamp, open, high, low, close, volume, symbol
```

Business key:

```text
symbol + timestamp
```

Bronze uses `MERGE`, so reprocessing the same file updates existing rows instead of creating duplicates.

New Bronze tables are created with:

```text
PARTITION BY timestamp date
CLUSTER BY symbol, timestamp
```

Reason:

- Timestamp partitioning reduces scanned data for date-range queries.
- Symbol/timestamp clustering speeds stock-wise time-series reads.
- Bronze should not contain business signals or derived trading logic.

BigQuery cannot add partitioning to an existing non-partitioned table in place. Existing Bronze data should not be deleted casually; migrate to a new partitioned table if needed.

## 8. CSV Date Values Are Treated As IST

CSV `date` values are read as strings and converted using:

```sql
TIMESTAMP(SAFE_CAST(date AS DATETIME), "Asia/Kolkata")
```

Reason:

- Market data timestamps are in IST.
- BigQuery `TIMESTAMP` is stored internally as UTC.
- Silver validates market hours by converting the timestamp back to `Asia/Kolkata`.

Example:

```text
CSV date: 2026-03-04 09:15:00
Stored timestamp: UTC equivalent of 09:15 IST
Silver check: TIME(timestamp, "Asia/Kolkata") = 09:15:00
```

## 9. Silver Is The Trusted Indicator Layer

Silver stores validated market rows and reusable indicators.

Silver intraday tables:

```text
silver_intraday_1m
silver_intraday_5m
```

Silver daily table:

```text
silver_daily_stock
```

Reason:

- Silver is clean enough for analytics.
- Silver indicators can be reused by many downstream tables.
- Trading signals do not belong in Silver.

## 10. Silver Stores Market Timestamp As IST DATETIME

BigQuery `TIMESTAMP` values are displayed as UTC. To make Silver show market time directly, Silver uses:

```text
timestamp DATETIME
```

The value comes from Bronze with:

```sql
DATETIME(timestamp, "Asia/Kolkata")
```

Reason:

- Traders and analytics should see `09:15:00` as `09:15:00`.
- Bronze can keep the precise UTC instant.
- Silver is the trusted market-local layer.

If older Silver tables still use `TIMESTAMP`, the Silver runner deletes and recreates the generated Silver timestamp tables. Bronze is not deleted.

## 11. Why These Silver Indicators Are Used

Silver now keeps only the indicators used by Gold and the semantic views. The heavier unused indicators were removed to reduce full historical runtime.

`previous_close`

- Needed to calculate returns, gaps, RSI gains/losses, and daily comparison.

`return_pct`

- In Silver intraday tables, measures price change from the previous intraday bar close.
- Gold exposes this as `bar_return_pct` and adds `day_return_pct` for current close versus previous trading-day close.
- Daily gainers and losers use daily `fact_daily_market.return_pct`, not intraday previous-bar return.

`gap_pct`

- Measures opening move versus previous close.
- Useful for gap-up/gap-down market analysis.

`sma_20`

- Simple moving average for short trend direction.
- Used by Gold for price versus SMA trend context.

`ema_9`, `ema_20`

- Exponential moving averages react faster than SMAs.
- `ema_9` and `ema_20` support crossover logic in Gold.
- The current Silver implementation uses rolling-window approximations so full historical builds run faster.

`rsi_14`

- Measures momentum strength.
- Used in Gold trend and scanner fields such as bullish/bearish momentum.

`macd`, `macd_signal`

- Measures trend momentum using EMA differences.
- Gold uses MACD crossovers as deterministic signal events.
- The MACD signal also uses a rolling-window approximation to keep the full Silver run practical.

`vwap`

- Shows the volume-weighted average trading price.
- Important for intraday trading context.

`avg_volume_20`

- Baseline volume average.
- Used to compare current volume against normal activity.

`relative_volume`

- Current volume divided by average volume.
- Gold uses it for `volume_status`, high-volume scans, and volume breakout events.

## 12. Silver Rejects Bad Rows

Silver rejects rows when:

- Required fields are null.
- OHLC values are non-positive.
- Volume is negative.
- OHLC relationships are invalid.
- Timestamp is outside `09:15` to `15:30` IST.

Rejected rows go to:

```text
silver_dataset_us.silver_rejects
```

Reason:

- Bad source rows should not enter trusted Silver tables.
- Rejects preserve evidence for debugging.

## 13. Gold Is The Business And Trading Layer

Gold reads from Silver and creates:

```text
dim_stock
dim_date
dim_timeframe
fact_intraday_metrics
fact_intraday_signals
fact_daily_market
fact_stock_returns
```

Reason:

- Gold keeps trading-ready data separate from reusable technical indicators.
- Dashboards can read business-friendly facts instead of raw Silver logic.
- Gold can contain trading signals without polluting Silver.

## 14. Why These Gold Fields And Signals Are Used

`price_vs_vwap`

- Shows whether price is above, below, or at VWAP.
- Useful for intraday bias.

`price_vs_ema20`

- Shows whether price is above or below the 20 EMA.
- Useful for short-term trend context.

`price_vs_sma20`

- Shows whether price is above or below the 20 SMA.
- Useful as a slower trend comparison.

`volume_status`

- Converts `relative_volume` into `HIGH_VOLUME`, `NORMAL_VOLUME`, or `LOW_VOLUME`.
- Easier for dashboards and chatbot answers.

`trend`

- Classifies rows as `BULLISH`, `BEARISH`, or `NEUTRAL`.
- Uses deterministic conditions from VWAP, EMA, and RSI.
- It is not a guaranteed buy/sell recommendation.

`momentum_score`

- Scores simple positive conditions from 0 to 6.
- Gives dashboards a sortable strength field.

`DAY_HIGH_BREAKOUT`

- Fires when current high breaks the previous intraday high for that symbol/day/timeframe.
- It does not compare the candle against itself.

`DAY_LOW_BREAKDOWN`

- Fires when current low breaks the previous intraday low for that symbol/day/timeframe.

`VWAP_CROSS_UP` and `VWAP_CROSS_DOWN`

- Fire when close crosses VWAP from the previous row to the current row.

`EMA_BULLISH_CROSSOVER` and `EMA_BEARISH_CROSSOVER`

- Fire when `ema_9` crosses `ema_20`.
- This uses Silver indicators instead of recalculating EMAs in Gold.

`MACD_BULLISH_CROSSOVER` and `MACD_BEARISH_CROSSOVER`

- Fire when MACD crosses the MACD signal line.

`VOLUME_BREAKOUT`

- Fires when `relative_volume` crosses above 2 from a previous value at or below 2.
- This avoids repeated breakout events on every high-volume row.

## 15. Semantic Layer Uses Views Only

Semantic dataset:

```text
pulse_trade_semantic
```

Views:

```text
vw_current_intraday
vw_stock_metrics
vw_scanner
vw_current_breakouts
vw_top_gainers
vw_top_losers
vw_latest_daily
vw_stock_returns
vw_market_overview
```

Reason:

- Views avoid duplicating Gold data.
- Dashboards and chatbot queries get simple names and ready fields.
- Latest-record logic is centralized.

## 16. Partitioning And Clustering

Bronze:

```text
PARTITION BY timestamp date
CLUSTER BY symbol, timestamp
```

Silver intraday:

```text
PARTITION BY trade_date
CLUSTER BY symbol, timestamp
```

Silver daily:

```text
PARTITION BY trade_date
CLUSTER BY symbol
```

Gold intraday facts:

```text
PARTITION BY trade_date
CLUSTER BY symbol, timestamp
```

Gold daily facts:

```text
PARTITION BY trade_date
CLUSTER BY symbol
```

Gold stock returns:

```text
PARTITION BY as_of_date
CLUSTER BY symbol
```

Reason:

- Date partitioning reduces BigQuery scan cost for time-window queries.
- Symbol clustering speeds stock-specific filtering and joins.
- Timestamp clustering helps ordered intraday analysis.

## 17. BigQuery Location Must Match

The project uses:

```text
BQ_LOCATION=US
```

Current datasets:

```text
bronze_data
silver_dataset_us
pulse_trade_gold
pulse_trade_semantic
audit_dataset_us
```

Reason:

- BigQuery jobs cannot freely join/create external tables across incompatible locations.
- Bronze, Silver, Gold, Semantic, and audit datasets should stay in the same BigQuery location.

## 18. Function Permissions Are Required

The deployed Cloud Function runs as:

```text
527618877818-compute@developer.gserviceaccount.com
```

It needs:

- `roles/bigquery.jobUser`
- `roles/bigquery.dataEditor`
- `roles/storage.objectViewer`

Reason:

- `bigquery.jobUser` allows the function to run BigQuery jobs.
- `bigquery.dataEditor` allows table, procedure, and view updates.
- `storage.objectViewer` allows CSV reads from the GCS bucket.
