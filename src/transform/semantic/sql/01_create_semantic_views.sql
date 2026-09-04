CREATE SCHEMA IF NOT EXISTS `{{PROJECT_ID}}.{{SEMANTIC_DATASET}}`
OPTIONS (
    location = "{{BQ_LOCATION}}"
);

-- =====================================================
-- Current Intraday Snapshot
-- Purpose: Latest 1M row per stock
-- =====================================================
CREATE OR REPLACE VIEW `{{PROJECT_ID}}.{{SEMANTIC_DATASET}}.vw_current_intraday` AS
SELECT
    symbol,
    trade_date,
    timestamp,
    close,
    volume,
    day_return_pct,
    vwap,
    ema_9,
    ema_20,
    rsi_14,
    macd,
    macd_signal,
    relative_volume,
    price_vs_vwap,
    price_vs_ema20,
    price_vs_sma20,
    volume_status,
    trend,
    momentum_score
FROM `{{PROJECT_ID}}.{{AI_DATASET}}.ai_current_intraday_snapshot`;

DROP VIEW IF EXISTS `{{PROJECT_ID}}.{{SEMANTIC_DATASET}}.vw_latest_intraday`;

-- =====================================================
-- Latest Daily Rows
-- Purpose: Latest daily market row per stock
-- =====================================================
CREATE OR REPLACE VIEW `{{PROJECT_ID}}.{{SEMANTIC_DATASET}}.vw_latest_daily` AS
SELECT
    symbol,
    trade_date,
    open,
    high,
    low,
    close,
    volume,
    previous_close,
    return_pct,
    gap_pct,
    daily_range_pct,
    avg_volume_20,
    relative_volume
FROM `{{PROJECT_ID}}.{{AI_DATASET}}.ai_latest_daily_snapshot`;
