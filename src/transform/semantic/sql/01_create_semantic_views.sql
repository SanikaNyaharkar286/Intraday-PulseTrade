CREATE SCHEMA IF NOT EXISTS `{{PROJECT_ID}}.{{SEMANTIC_DATASET}}`
OPTIONS (
    location = "{{BQ_LOCATION}}"
);

-- =====================================================
-- Current Intraday Snapshot
-- Purpose: Latest 1M row per stock from the latest trading date
-- =====================================================
CREATE OR REPLACE VIEW `{{PROJECT_ID}}.{{SEMANTIC_DATASET}}.vw_current_intraday` AS
WITH latest_trade_date AS (
    SELECT MAX(trade_date) AS trade_date
    FROM `{{PROJECT_ID}}.{{GOLD_DATASET}}.fact_intraday_metrics`
    WHERE timeframe = "1M"
),
ranked_rows AS (
    SELECT
        m.symbol,
        m.trade_date,
        m.timestamp,
        m.close,
        m.volume,
        m.day_return_pct,
        m.vwap,
        m.ema_9,
        m.ema_20,
        m.rsi_14,
        m.macd,
        m.macd_signal,
        m.relative_volume,
        m.price_vs_vwap,
        m.price_vs_ema20,
        m.price_vs_sma20,
        m.volume_status,
        m.trend,
        m.momentum_score,
        ROW_NUMBER() OVER (
            PARTITION BY m.symbol
            ORDER BY m.timestamp DESC
        ) AS row_number
    FROM `{{PROJECT_ID}}.{{GOLD_DATASET}}.fact_intraday_metrics` m
    INNER JOIN latest_trade_date d
        ON d.trade_date = m.trade_date
    WHERE m.timeframe = "1M"
)
SELECT * EXCEPT(row_number)
FROM ranked_rows
WHERE row_number = 1;

DROP VIEW IF EXISTS `{{PROJECT_ID}}.{{SEMANTIC_DATASET}}.vw_latest_intraday`;

-- =====================================================
-- Latest Daily Rows
-- Purpose: Latest daily market row per stock
-- =====================================================
CREATE OR REPLACE VIEW `{{PROJECT_ID}}.{{SEMANTIC_DATASET}}.vw_latest_daily` AS
SELECT * EXCEPT(row_number)
FROM (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY symbol
            ORDER BY trade_date DESC
        ) AS row_number
    FROM `{{PROJECT_ID}}.{{GOLD_DATASET}}.fact_daily_market`
)
WHERE row_number = 1;
