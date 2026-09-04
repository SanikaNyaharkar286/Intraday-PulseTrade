-- =====================================================
-- 1. Gold Row Counts
-- Purpose: Confirm Gold tables contain expected data
-- =====================================================
SELECT "dim_stock" AS table_name, COUNT(*) AS row_count
FROM `{{PROJECT_ID}}.{{GOLD_DATASET}}.dim_stock`
UNION ALL
SELECT "dim_date", COUNT(*)
FROM `{{PROJECT_ID}}.{{GOLD_DATASET}}.dim_date`
UNION ALL
SELECT "dim_timeframe", COUNT(*)
FROM `{{PROJECT_ID}}.{{GOLD_DATASET}}.dim_timeframe`
UNION ALL
SELECT "fact_intraday_metrics", COUNT(*)
FROM `{{PROJECT_ID}}.{{GOLD_DATASET}}.fact_intraday_metrics`
UNION ALL
SELECT "fact_intraday_signals", COUNT(*)
FROM `{{PROJECT_ID}}.{{GOLD_DATASET}}.fact_intraday_signals`
UNION ALL
SELECT "fact_daily_market", COUNT(*)
FROM `{{PROJECT_ID}}.{{GOLD_DATASET}}.fact_daily_market`
UNION ALL
SELECT "fact_stock_returns", COUNT(*)
FROM `{{PROJECT_ID}}.{{GOLD_DATASET}}.fact_stock_returns`;

-- =====================================================
-- 2. Duplicate Detection
-- Purpose: Fact tables must keep their declared grain
-- =====================================================
SELECT
    "fact_intraday_metrics" AS table_name,
    symbol,
    trade_date,
    timestamp,
    timeframe,
    COUNT(*) AS duplicate_count
FROM `{{PROJECT_ID}}.{{GOLD_DATASET}}.fact_intraday_metrics`
GROUP BY symbol, trade_date, timestamp, timeframe
HAVING COUNT(*) > 1
UNION ALL
SELECT
    "fact_daily_market" AS table_name,
    symbol,
    trade_date,
    CAST(NULL AS DATETIME) AS timestamp,
    CAST(NULL AS STRING) AS timeframe,
    COUNT(*) AS duplicate_count
FROM `{{PROJECT_ID}}.{{GOLD_DATASET}}.fact_daily_market`
GROUP BY symbol, trade_date
HAVING COUNT(*) > 1;

-- =====================================================
-- 3. Latest Trading Date
-- Purpose: Check latest dates used by daily and intraday views
-- =====================================================
SELECT
    (SELECT MAX(trade_date)
     FROM `{{PROJECT_ID}}.{{GOLD_DATASET}}.fact_intraday_metrics`
     WHERE timeframe = "1M") AS latest_intraday_trade_date,
    (SELECT MAX(trade_date)
     FROM `{{PROJECT_ID}}.{{GOLD_DATASET}}.fact_daily_market`) AS latest_daily_trade_date;

-- =====================================================
-- 4. Current Intraday Snapshot
-- Purpose: One latest 1M row per stock
-- =====================================================
SELECT
    COUNT(*) AS current_snapshot_rows,
    COUNT(DISTINCT symbol) AS current_snapshot_symbols,
    MIN(trade_date) AS min_trade_date,
    MAX(trade_date) AS max_trade_date
FROM `{{PROJECT_ID}}.{{SEMANTIC_DATASET}}.vw_current_intraday`;

-- =====================================================
-- 5. Top 10 Gainers
-- Purpose: Latest-date gainers ranked by daily return
-- =====================================================
SELECT *
FROM `{{PROJECT_ID}}.{{SEMANTIC_DATASET}}.vw_top_gainers`
ORDER BY rank;

-- =====================================================
-- 6. Top 10 Losers
-- Purpose: Latest-date losers ranked by daily return
-- =====================================================
SELECT *
FROM `{{PROJECT_ID}}.{{SEMANTIC_DATASET}}.vw_top_losers`
ORDER BY rank;

-- =====================================================
-- 7. Market Overview
-- Purpose: Current market breadth summary
-- =====================================================
SELECT *
FROM `{{PROJECT_ID}}.{{SEMANTIC_DATASET}}.vw_market_overview`;

-- =====================================================
-- 8. Current Breakouts
-- Purpose: Current-date deterministic signals
-- =====================================================
SELECT
    signal_type,
    COUNT(*) AS signal_count
FROM `{{PROJECT_ID}}.{{SEMANTIC_DATASET}}.vw_current_breakouts`
GROUP BY signal_type
ORDER BY signal_count DESC;

-- =====================================================
-- 9. Stock Returns
-- Purpose: Confirm simple 1Y/2Y/3Y/5Y return snapshots
-- =====================================================
SELECT
    symbol,
    as_of_date,
    return_1y,
    return_2y,
    return_3y,
    return_5y
FROM `{{PROJECT_ID}}.{{SEMANTIC_DATASET}}.vw_stock_returns`
ORDER BY as_of_date DESC, symbol
LIMIT 50;

-- =====================================================
-- 10. Signal Duplicates
-- Purpose: One stock + timestamp + timeframe + signal type
-- =====================================================
SELECT
    symbol,
    trade_date,
    timestamp,
    timeframe,
    signal_type,
    COUNT(*) AS duplicate_count
FROM `{{PROJECT_ID}}.{{GOLD_DATASET}}.fact_intraday_signals`
GROUP BY symbol, trade_date, timestamp, timeframe, signal_type
HAVING COUNT(*) > 1;
