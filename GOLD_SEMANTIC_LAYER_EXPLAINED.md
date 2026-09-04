# Gold And Semantic Layer Explained

This file explains where the Gold logic and Semantic layer are implemented, what each file does, why we use it, and how the data moves step by step.

## Where The Gold Logic Is Implemented

Gold orchestration file:

```text
src/transform/gold/gold.py
```

Gold SQL files:

```text
src/transform/gold/sql/01_create_gold_tables.sql
src/transform/gold/sql/02_sp_silver_to_gold.sql
src/transform/gold/sql/03_gold_validation.sql
```

Semantic SQL files:

```text
src/transform/semantic/sql/01_create_semantic_views.sql
src/transform/semantic/sql/02_stock_views.sql
src/transform/semantic/sql/03_scanner_views.sql
src/transform/semantic/sql/04_market_views.sql
```

Pipeline connection:

```text
src/transform/silver/silver.py
```

After Silver finishes, `silver.py` calls Gold when this config is true:

```text
RUN_GOLD_AFTER_SILVER=true
```

## Simple Full Flow

```text
CSV files in GCS bucket
  -> Bronze table
  -> Silver stored procedure
  -> Silver tables
  -> Gold stored procedure
  -> Gold tables
  -> Semantic views
  -> Dashboard or chatbot
```

## Current Implementation Notes

- Incremental uploads pass `scope_symbol`, `scope_start`, and `scope_end` from Bronze to Silver and Gold.
- Gold intraday metrics now expose `bar_return_pct` for previous-bar return and `day_return_pct` for previous-trading-day return.
- Intraday `relative_volume` in Gold is calculated against the previous 20 bars, excluding the current bar.
- `VOLUME_BREAKOUT` is a crossing event: previous relative volume at or below 2 and current relative volume above 2.
- `dim_stock` does not invent metadata; `company_name`, `sector`, `industry`, and `exchange` remain `NULL` unless real reference data is added.
- Semantic views are dashboard-ready read-only views.

## Why We Have A Gold Layer

Silver already has clean rows and technical indicators.

Gold is used for business-ready logic:

- trend classification
- momentum score
- volume category
- VWAP/EMA/SMA position
- bar and day return fields
- intraday breakout signals
- crossover signals
- daily market facts
- stock return facts

Reason:

- Silver should stay clean and reusable.
- Gold can contain trading/business logic.
- Dashboards should read simple Gold fields instead of recalculating rules.

## Why We Have A Semantic Layer

Semantic layer contains views only.

Reason:

- Views do not duplicate Gold data.
- Dashboards and chatbot queries get simple names.
- Latest-record logic is kept in one place.
- Users can ask simple questions like "which stocks are above VWAP?"

## File: src/transform/gold/gold.py

This Python file does not contain transformation logic.

It only runs SQL files and procedures.

### Step 1: Import Config

It imports:

```text
BQ_LOCATION
GOLD_DATASET
PROJECT_ID
SEMANTIC_DATASET
SILVER_DATASET
```

Why:

- The same code can run in different projects or datasets.
- SQL templates can use config placeholders like `{{PROJECT_ID}}`.

### Step 2: Create BigQuery Client

Function:

```text
get_bq_client()
```

What it does:

- Creates one BigQuery client.
- Reuses that client for Gold and Semantic SQL.

Why:

- Avoids creating a new connection for every SQL file.
- Keeps BigQuery execution in one place.

### Step 3: Render SQL

Function:

```text
_render_sql(sql)
```

What it does:

- Replaces placeholders in SQL files.

Example:

```text
{{PROJECT_ID}} -> project-001658fa-3ce5-4746-980
{{GOLD_DATASET}} -> pulse_trade_gold
{{SEMANTIC_DATASET}} -> pulse_trade_semantic
```

Why:

- SQL files stay reusable.
- Dataset names are controlled from `config.py`.

### Step 4: Run One SQL File

Function:

```text
_run_sql_file(sql_path)
```

What it does:

- Reads a SQL file.
- Renders config values.
- Sends the SQL to BigQuery.
- Waits until BigQuery finishes.

Why:

- Python should only orchestrate.
- BigQuery should do the actual transformations.

### Step 5: Ensure Gold Objects

Function:

```text
ensure_gold_objects()
```

What it does:

- Runs `01_create_gold_tables.sql`.
- Runs `02_sp_silver_to_gold.sql`.

Why:

- Gold tables must exist before loading data.
- The stored procedure must exist before calling it.
- `CREATE OR REPLACE PROCEDURE` keeps procedure logic updated.

### Step 6: Ensure Semantic Views

Function:

```text
ensure_semantic_views()
```

What it does:

- Runs all semantic SQL files.
- Creates or replaces dashboard/chatbot views.

Why:

- Views depend on Gold tables.
- Replacing views is safe because views do not store copied data.

### Step 7: Run Gold Pipeline

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

Why:

- This is the one function to refresh Gold and Semantic.
- It can be run after Silver or manually if Gold was deleted.

Manual command:

```powershell
python -c "from transform.gold.gold import run_gold_pipeline; run_gold_pipeline()"
```

## File: 01_create_gold_tables.sql

This file creates all Gold tables.

It does not load data.

Reason:

- Table structure is separated from transformation logic.
- It is easy to see what Gold contains.

### Gold Dataset

Creates:

```text
pulse_trade_gold
```

Why:

- Gold should be separate from Silver.
- Business-ready tables should have their own dataset.

### Table: dim_stock

Purpose:

```text
One row per stock symbol.
```

Columns:

```text
stock_key
symbol
company_name
sector
industry
exchange
processed_at
```

Why:

- Facts can use `stock_key`.
- Symbol is the current main identifier.
- Company, sector, and industry are left ready for future reference data.

Clustering:

```text
CLUSTER BY symbol
```

Why:

- Stock lookup is usually done by symbol.

### Table: dim_date

Purpose:

```text
Calendar dimension for trade dates.
```

Columns:

```text
date_key
date
day
month
quarter
year
processed_at
```

Why:

- Dashboards can filter by month, quarter, and year.
- Facts can use a consistent date key.

Clustering:

```text
CLUSTER BY date
```

Why:

- Date filters are common in market analysis.

### Table: dim_timeframe

Purpose:

```text
Supported timeframes.
```

Initial values:

```text
1M
5M
```

Why:

- Intraday facts can support multiple timeframes with one table.
- New timeframes like `15M` can be added later.

### Table: fact_intraday_metrics

Purpose:

```text
Business-ready intraday metrics from Silver 1M and 5M.
```

Grain:

```text
one symbol + one timestamp + one timeframe
```

Contains:

- OHLCV data
- Silver indicators
- Gold business fields

Gold fields added:

```text
price_vs_vwap
price_vs_ema20
price_vs_sma20
volume_status
trend
momentum_score
```

Why:

- Dashboards need ready-to-query trading context.
- Chatbot queries can answer in simple words like `BULLISH` or `ABOVE_VWAP`.

Partitioning and clustering:

```text
PARTITION BY trade_date
CLUSTER BY symbol, timestamp
```

Why:

- Most queries filter by date and symbol.
- Intraday queries often sort by timestamp.

### Table: fact_intraday_signals

Purpose:

```text
Stores deterministic intraday events.
```

Signals:

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

Why:

- Trading events belong in Gold, not Silver.
- Signals can be queried directly by dashboards.

Partitioning and clustering:

```text
PARTITION BY trade_date
CLUSTER BY symbol, timestamp
```

Why:

- Signal queries usually ask for recent events by symbol/date.

### Table: fact_daily_market

Purpose:

```text
Daily stock performance facts.
```

Contains:

```text
open
high
low
close
volume
previous_close
return_pct
gap_pct
daily_range_pct
avg_volume_20
relative_volume
```

Why:

- Supports top gainers.
- Supports top losers.
- Supports daily market performance.
- Supports long-term return calculations.

Partitioning and clustering:

```text
PARTITION BY trade_date
CLUSTER BY symbol
```

Why:

- Daily queries mostly filter by date and symbol.

### Table: fact_stock_returns

Purpose:

```text
Stores latest 1Y, 2Y, 3Y, and 5Y returns.
```

Contains:

```text
return_1y
return_2y
return_3y
return_5y
```

Why:

- Dashboards can show long-term performance quickly.
- Missing history stays `NULL` instead of inventing values.

Partitioning and clustering:

```text
PARTITION BY as_of_date
CLUSTER BY symbol
```

Why:

- Return snapshots are queried by latest date and symbol.

## File: 02_sp_silver_to_gold.sql

This is the main Gold stored procedure.

Procedure:

```text
sp_silver_to_gold()
```

Purpose:

```text
Read Silver tables and update all Gold tables.
```

### Step 1: Prepare Silver Intraday Source

Temporary table:

```text
silver_intraday_source
```

What it does:

- Reads `silver_intraday_1m`.
- Reads `silver_intraday_5m`.
- Adds `timeframe = 1M` or `5M`.
- Adds `timeframe_key = 1` or `5`.
- Combines both tables with `UNION ALL`.

Why:

- Gold can process both intraday timeframes with one common structure.
- We do not duplicate transformation logic.

### Step 2: Update dim_stock

What it does:

- Finds distinct symbols from Silver intraday and daily tables.
- Creates a stable `stock_key` using `FARM_FINGERPRINT(symbol)`.
- Inserts new symbols only.

Why:

- Gold facts need a stable stock key.
- Current Silver data has symbol but not company/sector/industry.
- The table is ready for a future stock master.

### Step 3: Update dim_date

What it does:

- Finds distinct trade dates from Silver.
- Creates `date_key` as `YYYYMMDD`.
- Stores day, month, quarter, year.

Why:

- Dashboards can filter by date parts easily.
- Facts can join to one shared date table.

### Step 4: Update dim_timeframe

What it does:

- Inserts:
  - `1M`
  - `5M`
- Removes unsupported timeframe rows left by older deployments.

Why:

- Fact tables can use a clear timeframe key.
- More timeframes can be added later without redesign.

### Step 5: Update fact_intraday_metrics

What it does:

- Reads from `silver_intraday_source`.
- Keeps Silver OHLCV and indicators.
- Adds Gold business fields.
- Uses `MERGE` on `symbol + timestamp + timeframe_key`.

Why:

- If Silver changes, Gold updates.
- If new Silver rows arrive, Gold inserts them.
- Re-running the procedure is safe.

Business logic:

`price_vs_vwap`

```text
close > vwap  -> ABOVE_VWAP
close < vwap  -> BELOW_VWAP
else          -> AT_VWAP
```

Why:

- VWAP is important intraday reference price.

`price_vs_ema20`

```text
close > ema_20 -> ABOVE_EMA20
close < ema_20 -> BELOW_EMA20
```

Why:

- EMA20 is a short/medium trend reference.

`price_vs_sma20`

```text
close > sma_20 -> ABOVE_SMA20
close < sma_20 -> BELOW_SMA20
```

Why:

- SMA20 gives a simple trend comparison.

`volume_status`

```text
relative_volume > 1.5  -> HIGH_VOLUME
relative_volume < 0.75 -> LOW_VOLUME
else                   -> NORMAL_VOLUME
```

Why:

- Dashboards and chatbot answers need simple volume categories.

`trend`

```text
BULLISH:
close > vwap
close > ema_20
ema_9 > ema_20
rsi_14 > 50

BEARISH:
close < vwap
close < ema_20
ema_9 < ema_20
rsi_14 < 50

Otherwise:
NEUTRAL
```

Why:

- Gives a deterministic direction label.
- It is not a guaranteed buy/sell signal.

`momentum_score`

Adds 1 point for each condition:

```text
close > vwap
close > ema_20
ema_9 > ema_20
rsi_14 > 50
macd > macd_signal
relative_volume > 1.5
```

Why:

- Gives a simple sortable strength score from 0 to 6.

Return fields:

```text
bar_return_pct = current close versus previous intraday close
day_return_pct = current close versus previous trading-day close
```

Why:

- Intraday previous-bar movement and daily stock performance are different concepts.
- Dashboards use `day_return_pct` for current intraday daily gain/loss.

### Step 6: Create signal_candidates

What it does:

- Reads `fact_intraday_metrics`.
- Adds previous row values with window functions.
- Creates signal rows when a deterministic event happens.

Why:

- Signals need current and previous values.
- Window functions let BigQuery compare each row with prior rows.

Signal logic:

`DAY_HIGH_BREAKOUT`

```text
current high > previous intraday high
```

Why:

- Detects when price breaks above the earlier high of the same day.

`DAY_LOW_BREAKDOWN`

```text
current low < previous intraday low
```

Why:

- Detects when price breaks below the earlier low of the same day.

`VWAP_CROSS_UP`

```text
previous close <= previous VWAP
current close > current VWAP
```

Why:

- Detects price crossing from below VWAP to above VWAP.

`VWAP_CROSS_DOWN`

```text
previous close >= previous VWAP
current close < current VWAP
```

Why:

- Detects price crossing from above VWAP to below VWAP.

`EMA_BULLISH_CROSSOVER`

```text
previous ema_9 <= previous ema_20
current ema_9 > current ema_20
```

Why:

- Detects fast EMA crossing above medium EMA.

`EMA_BEARISH_CROSSOVER`

```text
previous ema_9 >= previous ema_20
current ema_9 < current ema_20
```

Why:

- Detects fast EMA crossing below medium EMA.

`MACD_BULLISH_CROSSOVER`

```text
previous macd <= previous macd_signal
current macd > current macd_signal
```

Why:

- Detects MACD momentum turning positive versus signal line.

`MACD_BEARISH_CROSSOVER`

```text
previous macd >= previous macd_signal
current macd < current macd_signal
```

Why:

- Detects MACD momentum turning negative versus signal line.

`VOLUME_BREAKOUT`

```text
previous relative_volume <= 2
current relative_volume > 2
```

Why:

- Detects unusually high trading volume.
- Avoids repeated breakout signals on every row above the threshold.

### Step 7: Merge Into fact_intraday_signals

What it does:

- Creates `signal_id` from:

```text
symbol + timestamp + timeframe + signal_type
```

- Inserts only new signal IDs.

Why:

- The same signal will not duplicate if the procedure runs again.

### Step 8: Update fact_daily_market

What it does:

- Reads `silver_daily_stock`.
- Writes daily OHLCV and daily indicators into Gold.
- Uses `MERGE` on `symbol + trade_date`.

Why:

- Daily dashboards should read from Gold.
- Re-running Gold updates changed daily rows safely.

### Step 9: Update fact_stock_returns

What it does:

- Finds the latest daily close for each symbol.
- Finds historical close values about 1Y, 2Y, 3Y, and 5Y back.
- Calculates:

```text
current_close / historical_close - 1
```

Why:

- Makes long-term return queries fast.
- Keeps missing return values as `NULL` when history is not available.

## File: 03_gold_validation.sql

This file contains validation queries for Gold.

It checks:

- Gold row counts.
- Duplicate intraday rows.
- Null symbols.
- Null timestamps.
- Invalid prices.
- Invalid volume.
- Signal counts.
- Daily market records.
- Stock returns.

Why:

- After running Gold, we need simple checks to confirm data quality.
- It is a manual validation file, not part of the automatic pipeline.

## Semantic Layer Files

Semantic views read from Gold.

They do not store duplicate table data.

## File: 01_create_semantic_views.sql

Creates common base views.

### View: vw_current_intraday

Purpose:

```text
Latest 1M intraday row per stock.
```

How it works:

- Reads `fact_intraday_metrics`.
- Uses `ROW_NUMBER()`.
- Filters to `timeframe = 1M`.
- Uses the latest available `trade_date`.
- Orders each symbol by latest `timestamp`.
- Keeps row number 1.

Why:

- Each stock may have a different latest timestamp.
- We should not use one global `MAX(timestamp)`.

### View: vw_latest_daily

Purpose:

```text
Latest daily row per symbol.
```

How it works:

- Reads `fact_daily_market`.
- Uses `ROW_NUMBER()`.
- Partitions by symbol.
- Orders by `trade_date DESC`.
- Keeps row number 1.

Why:

- Top gainers, losers, and dashboard summaries need latest daily data.

## File: 02_stock_views.sql

### View: vw_stock_metrics

Purpose:

```text
Answer stock-specific questions.
```

Example questions:

```text
What is RELIANCE doing today?
Is RELIANCE above VWAP?
What is RELIANCE RSI?
Is RELIANCE bullish or bearish?
```

Fields returned:

```text
symbol
trade_date
timestamp
timeframe
close
volume
vwap
rsi_14
ema_9
ema_20
macd
macd_signal
relative_volume
price_vs_vwap
price_vs_ema20
volume_status
trend
momentum_score
```

Why:

- It gives one simple place for stock-level dashboard cards.
- Chatbot answers can read ready fields directly.

## File: 03_scanner_views.sql

### View: vw_scanner

Purpose:

```text
Support stock screening.
```

Boolean fields:

```text
above_vwap
above_ema20
rsi_bullish
high_volume
macd_bullish
```

Why:

- Screeners need true/false filters.
- Users can ask simple questions like "show high volume stocks".

### View: vw_current_breakouts

Purpose:

```text
Show latest trading-date Gold signal events.
```

Fields:

```text
symbol
trade_date
timestamp
timeframe
signal_type
signal_value
reference_value
```

Why:

- Dashboards can show breakouts and crossovers without reading the full metrics table.

## File: 04_market_views.sql

### View: vw_top_gainers

Purpose:

```text
Show latest daily stocks ordered by highest return_pct.
```

Why:

- Supports "top gainers" dashboard and chatbot queries.

### View: vw_top_losers

Purpose:

```text
Show latest daily stocks ordered by lowest return_pct.
```

Why:

- Supports "top losers" dashboard and chatbot queries.

### View: vw_stock_returns

Purpose:

```text
Show 1Y, 2Y, 3Y, and 5Y returns.
```

Why:

- Supports long-term return questions.

### View: vw_market_overview

Purpose:

```text
Show market summary counts from latest intraday rows.
```

Calculates:

```text
total_stocks
bullish_stocks
bearish_stocks
neutral_stocks
stocks_above_vwap
stocks_below_vwap
stocks_with_high_volume
```

Why:

- Dashboards need one quick market summary view.
- It avoids writing repeated summary SQL in every dashboard.

## How To Run Only Gold And Semantic

Use this when Silver already exists and Gold was deleted or changed:

```powershell
cd "D:\project\Intraday-PulseTrade (3)\Intraday-PulseTrade\src"
.\.venv\Scripts\Activate.ps1
python -c "from transform.gold.gold import run_gold_pipeline; run_gold_pipeline()"
```

This runs:

```text
Silver -> Gold -> Semantic views
```

## How To Run Full Pipeline

Use:

```powershell
cd "D:\project\Intraday-PulseTrade (3)\Intraday-PulseTrade\src"
.\.venv\Scripts\Activate.ps1
python main.py
```

This runs:

```text
Bronze -> Silver -> Gold -> Semantic views
```

## Simple Mental Model

```text
Silver says:
  Here are clean prices and technical indicators.

Gold says:
  Here are business-ready metrics, trends, signals, and returns.

Semantic says:
  Here are simple views for dashboards and chatbot questions.
```
