-- =====================================================
-- Stock Metrics
-- Purpose: Latest 1M stock metrics for dashboard cards
-- =====================================================
CREATE OR REPLACE VIEW `{{PROJECT_ID}}.{{SEMANTIC_DATASET}}.vw_stock_metrics` AS
SELECT
    symbol,
    trade_date,
    timestamp,
    "1M" AS timeframe,
    close,
    volume,
    day_return_pct,
    vwap,
    rsi_14,
    ema_9,
    ema_20,
    macd,
    macd_signal,
    relative_volume,
    price_vs_vwap,
    price_vs_ema20,
    price_vs_sma20,
    volume_status,
    trend,
    momentum_score
FROM `{{PROJECT_ID}}.{{SEMANTIC_DATASET}}.vw_current_intraday`;
