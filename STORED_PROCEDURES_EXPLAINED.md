# Stored Procedures Explained

This file explains the stored procedures used in Intraday-PulseTrade in a simple way.

The pipeline uses stored procedures because the heavy work should run inside BigQuery:

```text
Bronze table
  -> sp_bronze_to_silver()
  -> Silver tables
  -> sp_silver_to_gold()
  -> Gold tables
  -> Semantic views
```

Python starts the pipeline, but SQL does the transformation work.

## Why Stored Procedures Are Used

Stored procedures are used for Silver and Gold because:

- BigQuery can process large historical data faster than Python loops.
- The same SQL can be reused for historical and incremental loads.
- For incremental uploads, Python renders symbol/date scope filters before creating the Silver and Gold procedures.
- A procedure keeps all transformation steps in one controlled sequence.
- Each procedure can be safely called again because tables use `MERGE`.
- The pipeline is easier to debug because each layer has one main procedure.

## Stored Procedure List

```text
sp_bronze_to_silver
  File: src/transform/silver/sql/02_sp_bronze_to_silver.sql
  Purpose: Bronze -> Silver

sp_silver_to_gold
  File: src/transform/gold/sql/02_sp_silver_to_gold.sql
  Purpose: Silver -> Gold
```

## Procedure 1: sp_bronze_to_silver

File:

```text
src/transform/silver/sql/02_sp_bronze_to_silver.sql
```

Purpose:

```text
Take raw Bronze rows, validate them, calculate indicators, and update Silver.
```

Output tables:

```text
silver_intraday_1m
silver_intraday_5m
silver_daily_stock
silver_rejects
silver_audit
```

### Lines 1-2: Create And Start The Procedure

```sql
CREATE OR REPLACE PROCEDURE `{{PROJECT_ID}}.{{SILVER_DATASET}}.sp_bronze_to_silver`()
BEGIN
```

What it does:

- Creates the procedure if it does not exist.
- Replaces the existing procedure if the SQL changed.
- Starts the SQL procedure body with `BEGIN`.

Why it is used:

- The project can update Silver logic by redeploying SQL.
- Python can simply call `CALL sp_bronze_to_silver()`.

### Lines 3-11: Declare Run Variables

```text
run_id
run_start_time
records_read
records_processed
records_inserted
records_rejected
records_duplicate
impacted_start
impacted_end
```

What they do:

- `run_id` gives every Silver run a unique ID.
- `run_start_time` records when the run started.
- `records_read` counts changed/new Bronze rows found by the procedure.
- `records_processed` counts valid rows processed into Silver.
- `records_inserted` counts new Silver 1-minute rows.
- `records_rejected` counts bad rows sent to rejects.
- `records_duplicate` counts rows that were read but not processed as new valid rows.
- `impacted_start` stores the earliest changed Bronze timestamp.
- `impacted_end` stores the latest changed Bronze timestamp.

Why they are used:

- They make audit logging possible.
- They limit recalculation to the affected time window instead of always recalculating everything.

### Lines 12-14: Start A Protected Work Block

The inner `BEGIN` starts the main work block.

Why it is used:

- It allows the `EXCEPTION WHEN ERROR` block near the end to catch failures.
- If anything fails, the procedure writes a failed audit row before raising the error.

### Lines 14-53: Create `bronze_checked`

This temporary table reads Bronze and adds validation results.

Important fields selected:

- `symbol`
- `bronze_timestamp`
- `timestamp` as IST `DATETIME`
- `open`
- `high`
- `low`
- `close`
- `volume`
- `trade_date`
- `reject_reason`

What it does:

- Reads from `bronze_data.intraday_master`.
- Converts Bronze `TIMESTAMP` into market-local `DATETIME`.
- Creates `trade_date` using `Asia/Kolkata`.
- Checks each row for data quality problems.

Validation rules:

- Reject if required fields are null.
- Reject if OHLC prices are zero or negative.
- Reject if volume is negative.
- Reject if high/low/open/close relationship is impossible.
- Reject if timestamp is outside market hours `09:15` to `15:30` IST.

Why it is used:

- Bronze is raw, so bad records may exist.
- Silver should contain trusted records only.
- Reject reason is stored so bad data can be debugged later.

### Lines 55-94: Create `bronze_candidates`

This temporary table keeps only rows that need work.

What it does for valid rows:

- Compares Bronze rows with existing `silver_intraday_1m`.
- Keeps a valid row if it is new.
- Keeps a valid row if OHLCV values changed.

What it does for invalid rows:

- Compares the rejected row with `silver_rejects`.
- Keeps the rejected row only if the same reject is not already stored.

Why it is used:

- Avoids processing rows that already exist unchanged.
- Makes repeated runs faster.
- Keeps the procedure idempotent.

### Lines 96-98: Set `records_read`

Counts rows in `bronze_candidates`.

Why it is used:

- Shows how many rows the Silver procedure decided to handle in this run.
- Stored later in `silver_audit`.

### Lines 100-118: Create `invalid_rows`

This temporary table contains rejected records.

What it does:

- Adds `reject_date`.
- Keeps the bad row fields.
- Keeps `reject_reason`.
- Adds `reject_time`.

Why it is used:

- Keeps rejected data separate from trusted Silver facts.
- Makes bad source data visible instead of silently dropping it.

### Lines 121-153: Merge Into `silver_rejects`

What it does:

- Inserts invalid rows into `silver_rejects`.
- Does not insert the same rejected row twice.

Why `MERGE` is used:

- If a file is reprocessed, duplicate reject rows are avoided.
- The reject table remains clean and auditable.

### Lines 155-179: Create `valid_updates`

This temporary table keeps only valid rows.

What it does:

- Filters out rejected rows.
- Uses `ROW_NUMBER()` by `symbol + timestamp`.
- Keeps only the first row for each `symbol + timestamp`.

Why it is used:

- Silver should have one trusted row for each stock and timestamp.
- Duplicate source rows should not create duplicate Silver rows.

### Lines 181-187: Count Processed And Duplicate Rows

What it does:

- `records_processed` counts rows that will update Silver.
- `records_duplicate` is calculated from read, rejected, and processed counts.

Why it is used:

- Gives the audit table useful run statistics.

### Lines 189-190: Only Continue If Valid Rows Exist

```sql
IF records_processed > 0 THEN
```

What it does:

- Runs indicator calculations only when there are valid updates.

Why it is used:

- Avoids expensive BigQuery work when there is nothing new to process.

### Lines 191-207: Find Impacted Time Range, Symbols, And Dates

What it does:

- Finds the earliest changed Bronze timestamp.
- Finds the latest changed Bronze timestamp.
- Stores impacted symbols.
- Stores impacted trade dates.

Why it is used:

- Indicators need historical lookback.
- The procedure can recalculate only affected symbols and dates.

### Lines 208-236: Create `calc_input`

This is the input set for 1-minute indicator calculation.

What it does:

- Reads clean rows from `bronze_checked`.
- Includes only impacted symbols.
- Includes a 100-day lookback before the impacted start.
- Deduplicates again by `symbol + timestamp`.

Why 100-day lookback is used:

- Moving averages and EMAs need previous rows.
- Without lookback, the first changed rows would have weak or wrong indicator values.

### Lines 238-334: Create `windowed_rows`

This temporary table calculates simple window-based metrics.

Indicators created here:

- `previous_close`
- `return_pct`
- `gap_pct`
- `sma_20`
- `avg_volume_20`
- `avg_gain_14`
- `avg_loss_14`
- `vwap`

Why each indicator is used:

- `previous_close`: needed for returns, gaps, and RSI.
- `return_pct`: shows candle-to-candle percentage movement.
- `gap_pct`: shows open versus previous close.
- `sma_20`: short moving average trend reference.
- `avg_volume_20`: normal volume baseline.
- `avg_gain_14`: RSI gain input.
- `avg_loss_14`: RSI loss input.
- `vwap`: volume-weighted average price for intraday context.

Why window functions are used:

- They calculate values over ordered stock history.
- They avoid Python row loops.
- They keep calculations inside BigQuery.

### Lines 336-371: Create `ema_rows`

This temporary table calculates:

- `ema_9`
- `ema_20`
- `macd`

What it does:

- Uses BigQuery window functions instead of a row-to-prior-rows self join.
- Calculates fast rolling-window approximations for `ema_9` and `ema_20`.
- Calculates MACD as a fast rolling average difference.

Why these indicators are used:

- `ema_9`: fast moving average, useful for short-term momentum.
- `ema_20`: medium moving average, useful for trend and Gold crossovers.
- `macd`: momentum indicator based on EMA difference.

### Lines 373-389: Create `macd_signal_rows`

This temporary table calculates `macd_signal`.

What it does:

- Uses a rolling average over MACD values.
- Avoids the expensive MACD self join used by the earlier version.

Why it is used:

- `macd_signal` is needed to compare against MACD.
- Gold later uses MACD crossing the signal line as deterministic events.

### Lines 391-453: Create Final `silver_rows`

This combines all 1-minute calculations into final Silver rows.

What it adds:

- `rsi_14`
- `relative_volume`
- `silver_updated_at`

Why each field is used:

- `rsi_14`: momentum strength.
- `relative_volume`: current volume compared with average volume.
- `silver_updated_at`: lets Gold detect changed Silver rows.

### Lines 455-461: Count New 1-Minute Rows

What it does:

- Counts final Silver rows that do not already exist in `silver_intraday_1m`.

Why it is used:

- Gives audit visibility into new row inserts.

### Lines 463-566: Merge Into `silver_intraday_1m`

What it does:

- Updates existing `symbol + timestamp` rows.
- Inserts new `symbol + timestamp` rows.
- Stores OHLCV and all 1-minute indicators.

Why `MERGE` is used:

- Reprocessing a month or file is safe.
- Existing rows get corrected if source OHLCV changes.
- No duplicate 1-minute records are created.

### Lines 568-603: Create `base_candles_5m`

This builds 5-minute candles from trusted 1-minute Silver rows.

What it does:

- Rounds each timestamp down to a 5-minute bucket.
- Uses first open in the bucket.
- Uses max high.
- Uses min low.
- Uses last close.
- Sums volume.
- Keeps only buckets with exactly 5 one-minute candles.

Why it is used:

- 5-minute data should be derived from trusted 1-minute Silver data.
- Requiring 5 rows avoids incomplete 5-minute candles.

### Lines 605-701: Create `windowed_5m_rows`

This calculates the same window-based indicators for 5-minute candles.

Indicators:

- `previous_close`
- `return_pct`
- `gap_pct`
- `sma_20`
- `avg_volume_20`
- `avg_gain_14`
- `avg_loss_14`
- `vwap`

Why it is used:

- 5-minute dashboards need the same lean indicators as 1-minute dashboards.
- The procedure does not need separate source files for 5-minute data.

### Lines 703-756: Create 5-Minute EMA And MACD Tables

What it does:

- Calculates `ema_9`, `ema_20`, and `macd` for 5-minute rows.
- Calculates `macd_signal` for 5-minute rows.

Why it is used:

- Gold can create 5-minute EMA/MACD crossover signals.
- 5-minute trend context is smoother than 1-minute context.

### Lines 758-822: Create Final `silver_5m_rows`

This combines all 5-minute calculations into final Silver 5-minute rows.

What it adds:

- RSI
- Relative volume
- Silver update timestamp

Why it is used:

- Produces a complete trusted 5-minute analytics table.

### Lines 824-927: Merge Into `silver_intraday_5m`

What it does:

- Updates existing 5-minute rows.
- Inserts new 5-minute rows.
- Uses `symbol + timestamp` as the business key.

Why it is used:

- Keeps the 5-minute table safe to rerun.
- Avoids duplicate candles.

### Lines 929-1009: Create Daily Rows

This builds daily OHLCV and daily indicators from `silver_intraday_1m`.

What it does:

- Uses first intraday open as daily open.
- Uses max high as daily high.
- Uses min low as daily low.
- Uses last intraday close as daily close.
- Sums intraday volume.
- Calculates daily previous close.
- Calculates daily return percentage.
- Calculates daily gap percentage.
- Calculates daily range percentage.
- Calculates 20-day average volume.
- Calculates daily relative volume.

Why it is used:

- Daily analytics should come from trusted Silver intraday rows.
- Top gainers, top losers, and returns need daily data.

### Lines 1011-1063: Merge Into `silver_daily_stock`

What it does:

- Updates daily rows if they already exist.
- Inserts daily rows if they are new.
- Uses `symbol + trade_date` as the business key.

Why it is used:

- Daily data remains safe to rebuild.
- Reprocessing intraday data updates the daily summary.

### Line 1064: End The Valid-Rows Block

This closes:

```sql
IF records_processed > 0 THEN
```

If there were no valid updates, the procedure skips all indicator calculations and goes straight to audit logging.

### Lines 1066-1091: Insert Success Audit

What it does:

- Inserts a success record into `silver_audit`.
- Stores start time, end time, counts, and no error message.

Why it is used:

- Makes every Silver run traceable.
- Helps measure how much data was processed.

### Lines 1093-1119: Insert Failure Audit

What it does:

- Catches SQL errors.
- Inserts a failed audit row.
- Stores `@@error.message`.
- Raises the error again.

Why it is used:

- Failures are visible in BigQuery.
- Python still receives the error and stops the pipeline safely.

### Lines 1122-1123: End The Procedure

What it does:

- Ends the inner protected block.
- Ends the stored procedure.

## Procedure 2: sp_silver_to_gold

File:

```text
src/transform/gold/sql/02_sp_silver_to_gold.sql
```

Purpose:

```text
Take trusted Silver data and create business-ready Gold tables.
```

Output tables:

```text
dim_stock
dim_date
dim_timeframe
fact_intraday_metrics
fact_intraday_signals
fact_daily_market
fact_stock_returns
```

### Lines 1-2: Create And Start The Procedure

```sql
CREATE OR REPLACE PROCEDURE `{{PROJECT_ID}}.{{GOLD_DATASET}}.sp_silver_to_gold`()
BEGIN
```

What it does:

- Creates or replaces the Gold procedure.
- Starts the procedure body.

Why it is used:

- Gold logic can be updated by changing one SQL file.
- Python only needs to call `CALL sp_silver_to_gold()`.

### Lines 8-86: Create `silver_intraday_source`

This temporary table combines Silver 1-minute and 5-minute data.

What it does:

- Reads from `silver_intraday_1m`.
- Adds `timeframe_key = 1`.
- Adds `timeframe = "1M"`.
- Reads from `silver_intraday_5m`.
- Adds `timeframe_key = 5`.
- Adds `timeframe = "5M"`.
- Uses `UNION ALL` to stack both sources.

Why it is used:

- Gold intraday metrics have one common structure for multiple timeframes.
- The business logic can be written once for both 1M and 5M.

### Lines 88-130: Merge Into `dim_stock`

What it does:

- Finds all distinct symbols from Silver intraday and daily tables.
- Creates a stable `stock_key` using `FARM_FINGERPRINT(symbol)`.
- Inserts new symbols into `dim_stock`.
- Leaves company, sector, and industry as `NULL`.
- Leaves exchange as `NULL` until a real reference table is added.

Why it is used:

- Gold fact tables need a stock dimension.
- The project currently has symbols but no stock master table.
- The design is ready for future company/sector data without inventing it now.

### Lines 132-178: Merge Into `dim_date`

What it does:

- Finds all distinct trade dates from Silver.
- Builds `date_key` in `YYYYMMDD` integer format.
- Stores day, month, quarter, and year.
- Inserts dates that do not already exist.

Why it is used:

- Facts can join to a reusable calendar dimension.
- Dashboards can filter by month, quarter, and year easily.

### Lines 180-202: Merge Into `dim_timeframe`

What it does:

- Inserts the supported timeframes:
  - `1M`
  - `5M`
- Deletes unsupported timeframe rows left by older runs.

Why it is used:

- Gold facts can use a stable timeframe key.
- The design can later add `15M` or `1H`.

### Lines 208-433: Merge Into `fact_intraday_metrics`

This is the main Gold intraday metrics table.

What it reads:

- `silver_intraday_source`

What it writes:

- OHLCV data.
- Silver technical indicators.
- `bar_return_pct`, which is current close versus previous intraday close.
- `day_return_pct`, which is current close versus previous trading-day close.
- Gold business fields.

Business fields added:

- `price_vs_vwap`
- `price_vs_ema20`
- `price_vs_sma20`
- `volume_status`
- `trend`
- `momentum_score`

Why these Gold fields are used:

- `price_vs_vwap` explains whether price is above, below, or at VWAP.
- `price_vs_ema20` gives short-term trend context.
- `price_vs_sma20` gives a simpler moving-average comparison.
- `volume_status` turns relative volume into a dashboard-friendly category.
- `trend` classifies each row as `BULLISH`, `BEARISH`, or `NEUTRAL`.
- `momentum_score` gives a simple 0-to-6 strength score.

How `trend` works:

```text
BULLISH when:
close > vwap
close > ema_20
ema_9 > ema_20
rsi_14 > 50

BEARISH when:
close < vwap
close < ema_20
ema_9 < ema_20
rsi_14 < 50

Otherwise:
NEUTRAL
```

How `momentum_score` works:

```text
+1 close > vwap
+1 close > ema_20
+1 ema_9 > ema_20
+1 rsi_14 > 50
+1 macd > macd_signal
+1 relative_volume > 1.5
```

Why `MERGE` is used:

- Existing Gold rows are updated when Silver changes.
- New Gold rows are inserted when new Silver rows arrive.
- The key is `symbol + timestamp + timeframe_key`.

### Lines 440-646: Create `signal_candidates`

This temporary table finds deterministic trading events.

It first creates `metric_windows`.

`metric_windows` adds:

- Previous intraday high for the day.
- Previous intraday low for the day.
- Previous VWAP.
- Previous close row.
- Previous EMA 9.
- Previous EMA 20.
- Previous MACD.
- Previous MACD signal.

Why previous values are needed:

- Crossovers need a before-and-after comparison.
- Breakouts must not compare a candle against itself.

Signals created:

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

Why each signal is used:

- `DAY_HIGH_BREAKOUT`: current high breaks the earlier high of the same day.
- `DAY_LOW_BREAKDOWN`: current low breaks the earlier low of the same day.
- `VWAP_CROSS_UP`: close moves from below VWAP to above VWAP.
- `VWAP_CROSS_DOWN`: close moves from above VWAP to below VWAP.
- `EMA_BULLISH_CROSSOVER`: EMA 9 crosses above EMA 20.
- `EMA_BEARISH_CROSSOVER`: EMA 9 crosses below EMA 20.
- `MACD_BULLISH_CROSSOVER`: MACD crosses above signal line.
- `MACD_BEARISH_CROSSOVER`: MACD crosses below signal line.
- `VOLUME_BREAKOUT`: relative volume crosses above 2 from a previous value at or below 2.

The procedure creates `signal_id` with:

```text
symbol + timestamp + timeframe + signal_type
```

Why `signal_id` is used:

- It makes each signal deterministic.
- The same signal will not be inserted twice on rerun.

Important note:

- These are deterministic events, not guaranteed buy/sell recommendations.

### Lines 648-681: Merge Into `fact_intraday_signals`

What it does:

- Inserts new signal events.
- Removes stale `VOLUME_BREAKOUT` rows that no longer meet crossing logic.
- Does not update old signals.
- Does not insert duplicates because it matches on `signal_id`.

Why it is used:

- Signal history should be stable.
- Re-running Gold should not duplicate events.

### Lines 688-775: Merge Into `fact_daily_market`

What it reads:

- `silver_daily_stock`

What it writes:

- Daily OHLCV.
- Daily previous close.
- Daily return percentage.
- Daily gap percentage.
- Daily range percentage.
- Average volume.
- Relative volume.

Why it is used:

- Dashboards need top gainers, top losers, and daily market performance.
- Gold daily facts are easier to query than raw Silver daily fields.

Why `MERGE` is used:

- Updates changed daily rows.
- Inserts new daily rows.
- Uses `symbol + trade_date` as the key.

### Lines 781-918: Merge Into `fact_stock_returns`

This calculates multi-year stock returns.

What it does:

- Finds the latest daily row for each symbol.
- Finds the closest available historical close at least:
  - 1 year back
  - 2 years back
  - 3 years back
  - 5 years back
- Calculates:
  - `return_1y`
  - `return_2y`
  - `return_3y`
  - `return_5y`

Formula:

```text
current_close / historical_close - 1
```

Why joins and `ROW_NUMBER()` are used:

- BigQuery does not allow the older correlated subquery pattern in this procedure.
- Ranked joins find the nearest valid historical close cleanly.

Why returns can be `NULL`:

- If the table does not yet have enough history, the historical close is missing.
- Example: with only 1 year of loaded data, 2-year, 3-year, and 5-year returns can be `NULL`.

Why it is used:

- Dashboards can answer long-term return questions quickly.
- The calculation uses existing Gold daily facts instead of raw Bronze rows.

### Line 920: End The Procedure

This closes the Gold stored procedure.

## How Python Calls These Procedures

### Silver Call

File:

```text
src/transform/silver/silver.py
```

Function:

```text
run_silver_pipeline()
```

What it does:

```text
ensure_silver_objects()
CALL sp_bronze_to_silver()
if RUN_GOLD_AFTER_SILVER=true:
    run_gold_pipeline()
```

Why it is used:

- Every historical or incremental Bronze load gets the same Silver behavior.
- Gold can be turned on or off with `RUN_GOLD_AFTER_SILVER`.

### Gold Call

File:

```text
src/transform/gold/gold.py
```

Function:

```text
run_gold_pipeline()
```

What it does:

```text
ensure_gold_objects()
CALL sp_silver_to_gold()
ensure_semantic_views()
```

Why it is used:

- Gold transformations stay inside SQL.
- Semantic views are refreshed after Gold objects exist.

## Simple End-To-End Flow

For historical:

```text
python main.py
  -> historical_loader.run_historical()
  -> bronze.process_historical_month()
  -> bronze table MERGE
  -> silver.run_silver_pipeline()
  -> CALL sp_bronze_to_silver()
  -> gold.run_gold_pipeline()
  -> CALL sp_silver_to_gold()
  -> refresh semantic views
```

For incremental:

```text
CSV uploaded to bucket
  -> process_new_csv()
  -> incremental_loader.run_incremental()
  -> bronze.process_new_file()
  -> bronze table MERGE
  -> silver.run_silver_pipeline(scope_symbol, scope_start, scope_end)
  -> CALL sp_bronze_to_silver()
  -> gold.run_gold_pipeline(scope_symbol, scope_start, scope_end)
  -> CALL sp_silver_to_gold()
  -> refresh semantic views
```

## Simple Mental Model

```text
Bronze asks:
  What did the CSV say?

Silver asks:
  Is the data clean, deduplicated, and technically useful?

Gold asks:
  What does this mean for trading and business analysis?

Semantic asks:
  How can a dashboard or chatbot ask simple questions?
```
