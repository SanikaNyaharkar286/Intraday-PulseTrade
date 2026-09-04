CREATE SCHEMA IF NOT EXISTS `{{PROJECT_ID}}.{{GOLD_DATASET}}`
OPTIONS (
    location = "{{BQ_LOCATION}}"
);

-- =====================================================
-- Stock Dimension
-- Purpose: Store one business row per stock symbol
-- =====================================================
CREATE TABLE IF NOT EXISTS `{{PROJECT_ID}}.{{GOLD_DATASET}}.dim_stock`
(
    stock_key INT64 NOT NULL,
    symbol STRING NOT NULL,
    company_name STRING,
    sector STRING,
    industry STRING,
    exchange STRING,
    processed_at TIMESTAMP
)
CLUSTER BY symbol;

-- =====================================================
-- Date Dimension
-- Purpose: Store calendar attributes used by facts
-- =====================================================
CREATE TABLE IF NOT EXISTS `{{PROJECT_ID}}.{{GOLD_DATASET}}.dim_date`
(
    date_key INT64 NOT NULL,
    date DATE NOT NULL,
    day INT64,
    month INT64,
    quarter INT64,
    year INT64,
    processed_at TIMESTAMP
)
CLUSTER BY date;

-- =====================================================
-- Timeframe Dimension
-- Purpose: Keep supported market timeframes extensible
-- =====================================================
CREATE TABLE IF NOT EXISTS `{{PROJECT_ID}}.{{GOLD_DATASET}}.dim_timeframe`
(
    timeframe_key INT64 NOT NULL,
    timeframe STRING NOT NULL,
    processed_at TIMESTAMP
)
CLUSTER BY timeframe;

-- =====================================================
-- Intraday Metrics Fact
-- Purpose: Trading-ready metrics from Silver 1M and 5M
-- =====================================================
CREATE TABLE IF NOT EXISTS `{{PROJECT_ID}}.{{GOLD_DATASET}}.fact_intraday_metrics`
(
    stock_key INT64 NOT NULL,
    date_key INT64 NOT NULL,
    timeframe_key INT64 NOT NULL,
    symbol STRING NOT NULL,
    trade_date DATE NOT NULL,
    timestamp DATETIME NOT NULL,
    timeframe STRING NOT NULL,
    open FLOAT64,
    high FLOAT64,
    low FLOAT64,
    close FLOAT64,
    volume FLOAT64,
    previous_close FLOAT64,
    bar_return_pct FLOAT64,
    day_return_pct FLOAT64,
    return_pct FLOAT64,
    gap_pct FLOAT64,
    sma_20 FLOAT64,
    ema_9 FLOAT64,
    ema_20 FLOAT64,
    rsi_14 FLOAT64,
    macd FLOAT64,
    macd_signal FLOAT64,
    vwap FLOAT64,
    avg_volume_20 FLOAT64,
    relative_volume FLOAT64,
    price_vs_vwap STRING,
    price_vs_ema20 STRING,
    price_vs_sma20 STRING,
    volume_status STRING,
    trend STRING,
    momentum_score INT64,
    processed_at TIMESTAMP
)
PARTITION BY trade_date
CLUSTER BY symbol, timestamp;

ALTER TABLE `{{PROJECT_ID}}.{{GOLD_DATASET}}.fact_intraday_metrics`
ADD COLUMN IF NOT EXISTS bar_return_pct FLOAT64;

ALTER TABLE `{{PROJECT_ID}}.{{GOLD_DATASET}}.fact_intraday_metrics`
ADD COLUMN IF NOT EXISTS day_return_pct FLOAT64;

-- =====================================================
-- Intraday Signals Fact
-- Purpose: Deterministic trading events from Gold metrics
-- =====================================================
CREATE TABLE IF NOT EXISTS `{{PROJECT_ID}}.{{GOLD_DATASET}}.fact_intraday_signals`
(
    signal_id STRING NOT NULL,
    stock_key INT64 NOT NULL,
    date_key INT64 NOT NULL,
    timeframe_key INT64 NOT NULL,
    symbol STRING NOT NULL,
    trade_date DATE NOT NULL,
    timestamp DATETIME NOT NULL,
    timeframe STRING NOT NULL,
    signal_type STRING NOT NULL,
    signal_value FLOAT64,
    reference_value FLOAT64,
    processed_at TIMESTAMP
)
PARTITION BY trade_date
CLUSTER BY symbol, timestamp;

-- =====================================================
-- Daily Market Fact
-- Purpose: Daily market-ready performance and volume data
-- =====================================================
CREATE TABLE IF NOT EXISTS `{{PROJECT_ID}}.{{GOLD_DATASET}}.fact_daily_market`
(
    stock_key INT64 NOT NULL,
    date_key INT64 NOT NULL,
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
    processed_at TIMESTAMP
)
PARTITION BY trade_date
CLUSTER BY symbol;

-- =====================================================
-- Stock Returns Fact
-- Purpose: Multi-year cumulative return snapshots
-- =====================================================
CREATE TABLE IF NOT EXISTS `{{PROJECT_ID}}.{{GOLD_DATASET}}.fact_stock_returns`
(
    stock_key INT64 NOT NULL,
    symbol STRING NOT NULL,
    as_of_date DATE NOT NULL,
    return_1y FLOAT64,
    return_2y FLOAT64,
    return_3y FLOAT64,
    return_5y FLOAT64,
    processed_at TIMESTAMP
)
PARTITION BY as_of_date
CLUSTER BY symbol;
