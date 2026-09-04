CREATE SCHEMA IF NOT EXISTS `{{PROJECT_ID}}.{{SILVER_DATASET}}`
OPTIONS (
    location = "{{BQ_LOCATION}}"
);

CREATE TABLE IF NOT EXISTS `{{PROJECT_ID}}.{{SILVER_DATASET}}.silver_intraday_1m`
(
    trade_date DATE NOT NULL,
    symbol STRING NOT NULL,
    timestamp DATETIME NOT NULL,
    open FLOAT64,
    high FLOAT64,
    low FLOAT64,
    close FLOAT64,
    volume FLOAT64,
    previous_close FLOAT64,
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
    silver_updated_at TIMESTAMP
)
PARTITION BY trade_date
CLUSTER BY symbol, timestamp;

CREATE TABLE IF NOT EXISTS `{{PROJECT_ID}}.{{SILVER_DATASET}}.silver_intraday_5m`
(
    trade_date DATE NOT NULL,
    symbol STRING NOT NULL,
    timestamp DATETIME NOT NULL,
    open FLOAT64,
    high FLOAT64,
    low FLOAT64,
    close FLOAT64,
    volume FLOAT64,
    previous_close FLOAT64,
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
    silver_updated_at TIMESTAMP
)
PARTITION BY trade_date
CLUSTER BY symbol, timestamp;

CREATE TABLE IF NOT EXISTS `{{PROJECT_ID}}.{{SILVER_DATASET}}.silver_daily_stock`
(
    trade_date DATE NOT NULL,
    symbol STRING NOT NULL,
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
    silver_updated_at TIMESTAMP
)
PARTITION BY trade_date
CLUSTER BY symbol;

CREATE TABLE IF NOT EXISTS `{{PROJECT_ID}}.{{SILVER_DATASET}}.silver_rejects`
(
    reject_date DATE NOT NULL,
    symbol STRING,
    timestamp DATETIME,
    open FLOAT64,
    high FLOAT64,
    low FLOAT64,
    close FLOAT64,
    volume FLOAT64,
    reject_reason STRING,
    reject_time TIMESTAMP
)
PARTITION BY reject_date
CLUSTER BY symbol, timestamp;

CREATE TABLE IF NOT EXISTS `{{PROJECT_ID}}.{{SILVER_DATASET}}.silver_audit`
(
    run_id STRING NOT NULL,
    run_start_time TIMESTAMP,
    run_end_time TIMESTAMP,
    status STRING,
    records_read INT64,
    records_processed INT64,
    records_inserted INT64,
    records_rejected INT64,
    records_duplicate INT64,
    error_message STRING
);
