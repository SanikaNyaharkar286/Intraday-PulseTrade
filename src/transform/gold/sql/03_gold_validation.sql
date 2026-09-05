-- =====================================================
-- 1. Gold Row Counts
-- Purpose: Confirm Gold tables contain expected data
-- =====================================================
"""SELECT "dim_stock" AS table_name, COUNT(*) AS row_count
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
FROM `{{PROJECT_ID}}.{{GOLD_DATASET}}.fact_stock_returns`;"""

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
-- 4. AI Current Market State
-- Purpose: One latest 1M row per stock
-- =====================================================
SELECT
    (SELECT MAX(trade_date)
     FROM `{{PROJECT_ID}}.{{GOLD_DATASET}}.fact_intraday_metrics`
     WHERE timeframe = "1M") AS latest_intraday_trade_date,
    (SELECT MAX(trade_date)
FROM `{{PROJECT_ID}}.{{AI_SEMANTIC_DATASET}}.spot_ai_current_market_state`;

-- =====================================================
-- 5. AI Signal History
-- Purpose: Signal events available to the agent
-- =====================================================
SELECT
    signal_type,
    COUNT(*) AS signal_count
FROM `{{PROJECT_ID}}.{{AI_SEMANTIC_DATASET}}.spot_ai_signal_history_90d`
GROUP BY signal_type
ORDER BY signal_count DESC;
    MIN(trade_date) AS min_trade_date,
    MAX(trade_date) AS max_trade_date
-- 6. AI Intraday History
-- Purpose: Confirm the fixed historical intraday range
-- =====================================================
SELECT
    COUNT(*) AS candle_rows,
    COUNT(DISTINCT symbol) AS symbols,
    MIN(trade_date) AS first_trade_date,
    MAX(trade_date) AS last_trade_date
FROM `{{PROJECT_ID}}.{{AI_SEMANTIC_DATASET}}.spot_ai_intraday_history_90d`;
SELECT *
FROM `{{PROJECT_ID}}.{{SEMANTIC_DATASET}}.vw_top_gainers`
-- 7. AI Daily History
-- Purpose: Confirm the daily historical table
-- =====================================================
SELECT
    COUNT(*) AS daily_rows,
    COUNT(DISTINCT symbol) AS symbols,
    MIN(trade_date) AS first_trade_date,
    MAX(trade_date) AS last_trade_date
FROM `{{PROJECT_ID}}.{{AI_SEMANTIC_DATASET}}.spot_ai_daily_history`;
-- =====================================================
SELECT *
-- 8. AI Behavior And Summary Tables
-- Purpose: Confirm derived tables are populated

-- =====================================================
    (SELECT COUNT(*) FROM `{{PROJECT_ID}}.{{AI_SEMANTIC_DATASET}}.spot_ai_intraday_behavior`)
        AS behavior_rows,
    (SELECT COUNT(*) FROM `{{PROJECT_ID}}.{{AI_SEMANTIC_DATASET}}.spot_ai_stock_summary`)
        AS summary_rows;
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
