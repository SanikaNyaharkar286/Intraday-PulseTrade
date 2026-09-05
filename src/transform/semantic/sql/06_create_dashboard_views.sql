CREATE SCHEMA IF NOT EXISTS `{{PROJECT_ID}}.{{DASHBOARD_DATASET}}`
OPTIONS (
    location = "{{BQ_LOCATION}}"
);

-- Fixed historical dashboard cutoff. The source data ends on 2026-02-27.

CREATE OR REPLACE VIEW
`{{PROJECT_ID}}.{{DASHBOARD_DATASET}}.vw_market_overview`
AS
WITH latest_stock AS (
    SELECT
        m.symbol,
        m.trade_date,
        m.timestamp,
        m.close,
        m.day_return_pct,
        m.volume,
        m.relative_volume,
        m.rsi_14,
        m.macd,
        m.macd_signal,
        m.ema_9,
        m.ema_20,
        m.vwap,
        m.price_vs_vwap,
        m.price_vs_ema20,
        m.price_vs_sma20,
        m.volume_status,
        m.trend,
        m.momentum_score,
        ROW_NUMBER() OVER (
            PARTITION BY m.symbol
            ORDER BY m.trade_date DESC, m.timestamp DESC
        ) AS row_number
    FROM `{{PROJECT_ID}}.{{GOLD_DATASET}}.fact_intraday_metrics` m
    WHERE m.timeframe = "1M"
        AND m.trade_date BETWEEN DATE_SUB(DATE("2026-02-27"), INTERVAL 90 DAY)
            AND DATE("2026-02-27")
)
SELECT
    m.symbol,
    s.company_name,
    s.sector,
    m.trade_date,
    m.timestamp,
    m.close,
    m.day_return_pct,
    m.volume,
    m.relative_volume,
    m.rsi_14,
    m.macd,
    m.macd_signal,
    m.ema_9,
    m.ema_20,
    m.vwap,
    m.price_vs_vwap,
    m.price_vs_ema20,
    m.price_vs_sma20,
    m.volume_status,
    m.trend,
    m.momentum_score
FROM latest_stock m
LEFT JOIN `{{PROJECT_ID}}.{{GOLD_DATASET}}.dim_stock` s
    ON s.symbol = m.symbol
WHERE m.row_number = 1;

CREATE OR REPLACE VIEW
`{{PROJECT_ID}}.{{DASHBOARD_DATASET}}.vw_symbol_intraday_chart`
AS
SELECT
    symbol,
    trade_date,
    timestamp,
    open,
    high,
    low,
    close,
    volume,
    rsi_14,
    macd,
    macd_signal,
    ema_9,
    ema_20,
    vwap,
    relative_volume
FROM `{{PROJECT_ID}}.{{GOLD_DATASET}}.fact_intraday_metrics`
WHERE timeframe = "5M"
    AND trade_date BETWEEN DATE_SUB(DATE("2026-02-27"), INTERVAL 90 DAY)
        AND DATE("2026-02-27");

CREATE OR REPLACE VIEW
`{{PROJECT_ID}}.{{DASHBOARD_DATASET}}.vw_signal_scanner`
AS
SELECT
    symbol,
    trade_date,
    timestamp,
    timeframe,
    signal_type,
    signal_value,
    reference_value
FROM `{{PROJECT_ID}}.{{GOLD_DATASET}}.fact_intraday_signals`
WHERE trade_date BETWEEN DATE_SUB(DATE("2026-02-27"), INTERVAL 90 DAY)
    AND DATE("2026-02-27");