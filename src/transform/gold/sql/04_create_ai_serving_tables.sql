CREATE SCHEMA IF NOT EXISTS `{{PROJECT_ID}}.{{AI_DATASET}}`
OPTIONS (
    location = "{{BQ_LOCATION}}"
);

-- =====================================================
-- AI Current Intraday Snapshot
-- Purpose: One latest 1M row per stock for low-cost AI/dashboard reads
-- =====================================================
CREATE TABLE IF NOT EXISTS `{{PROJECT_ID}}.{{AI_DATASET}}.ai_current_intraday_snapshot`
(
    symbol STRING NOT NULL,
    trade_date DATE NOT NULL,
    timestamp DATETIME NOT NULL,
    timeframe STRING NOT NULL,
    close FLOAT64,
    volume FLOAT64,
    bar_return_pct FLOAT64,
    day_return_pct FLOAT64,
    vwap FLOAT64,
    ema_9 FLOAT64,
    ema_20 FLOAT64,
    rsi_14 FLOAT64,
    macd FLOAT64,
    macd_signal FLOAT64,
    relative_volume FLOAT64,
    price_vs_vwap STRING,
    price_vs_ema20 STRING,
    price_vs_sma20 STRING,
    volume_status STRING,
    trend STRING,
    momentum_score INT64,
    snapshot_at TIMESTAMP
)
PARTITION BY trade_date
CLUSTER BY symbol;

-- =====================================================
-- AI Current Signal Snapshot
-- Purpose: Current/recent signal events for low-cost AI/dashboard reads
-- =====================================================
CREATE TABLE IF NOT EXISTS `{{PROJECT_ID}}.{{AI_DATASET}}.ai_current_signal_snapshot`
(
    signal_id STRING NOT NULL,
    symbol STRING NOT NULL,
    trade_date DATE NOT NULL,
    timestamp DATETIME NOT NULL,
    timeframe STRING NOT NULL,
    signal_type STRING NOT NULL,
    signal_value FLOAT64,
    reference_value FLOAT64,
    snapshot_at TIMESTAMP
)
PARTITION BY trade_date
CLUSTER BY symbol, timestamp;

-- =====================================================
-- AI Latest Daily Snapshot
-- Purpose: One latest daily row per stock for gainers/losers/current state
-- =====================================================
CREATE TABLE IF NOT EXISTS `{{PROJECT_ID}}.{{AI_DATASET}}.ai_latest_daily_snapshot`
(
    symbol STRING NOT NULL,
    trade_date DATE NOT NULL,
    open FLOAT64,
    high FLOAT64,
    low FLOAT64,
    close FLOAT64,
    volume FLOAT64,
    previous_close FLOAT64,
    return_pct FLOAT64,
    gap_pct FLOAT64,
    daily_range_pct FLOAT64,
    avg_volume_20 FLOAT64,
    relative_volume FLOAT64,
    snapshot_at TIMESTAMP
)
PARTITION BY trade_date
CLUSTER BY symbol;
