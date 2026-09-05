CREATE SCHEMA IF NOT EXISTS `{{PROJECT_ID}}.{{AI_SEMANTIC_DATASET}}`
OPTIONS (
    location = "{{BQ_LOCATION}}"
);

-- Fixed historical cutoff for the dashboard and AI agent dataset.
-- The source data ends on 2026-02-27.

CREATE OR REPLACE TABLE
`{{PROJECT_ID}}.{{AI_SEMANTIC_DATASET}}.spot_ai_current_market_state`
AS
WITH latest_stock AS (
    SELECT
        m.*,
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
    m.momentum_score,
    CURRENT_TIMESTAMP() AS processed_at
FROM latest_stock m
LEFT JOIN `{{PROJECT_ID}}.{{GOLD_DATASET}}.dim_stock` s
    ON s.symbol = m.symbol
WHERE m.row_number = 1;

CREATE OR REPLACE TABLE
`{{PROJECT_ID}}.{{AI_SEMANTIC_DATASET}}.spot_ai_signal_history_90d`
PARTITION BY trade_date
CLUSTER BY symbol, signal_type
AS
SELECT
    signal_id,
    symbol,
    trade_date,
    timestamp,
    timeframe,
    signal_type,
    signal_value,
    reference_value,
    CURRENT_TIMESTAMP() AS processed_at
FROM `{{PROJECT_ID}}.{{GOLD_DATASET}}.fact_intraday_signals`
WHERE trade_date BETWEEN DATE_SUB(DATE("2026-02-27"), INTERVAL 90 DAY)
    AND DATE("2026-02-27");

CREATE OR REPLACE TABLE
`{{PROJECT_ID}}.{{AI_SEMANTIC_DATASET}}.spot_ai_intraday_history_90d`
PARTITION BY trade_date
CLUSTER BY symbol, timestamp
AS
SELECT
    symbol,
    trade_date,
    timestamp,
    timeframe,
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
    relative_volume,
    CURRENT_TIMESTAMP() AS processed_at
FROM `{{PROJECT_ID}}.{{GOLD_DATASET}}.fact_intraday_metrics`
WHERE timeframe = "5M"
    AND trade_date BETWEEN DATE_SUB(DATE("2026-02-27"), INTERVAL 90 DAY)
        AND DATE("2026-02-27");

CREATE OR REPLACE TABLE
`{{PROJECT_ID}}.{{AI_SEMANTIC_DATASET}}.spot_ai_daily_history`
PARTITION BY trade_date
CLUSTER BY symbol
AS
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
    relative_volume,
    CURRENT_TIMESTAMP() AS processed_at
FROM `{{PROJECT_ID}}.{{GOLD_DATASET}}.fact_daily_market`
WHERE trade_date <= DATE("2026-02-27");

CREATE OR REPLACE TABLE
`{{PROJECT_ID}}.{{AI_SEMANTIC_DATASET}}.spot_ai_intraday_behavior`
PARTITION BY trade_date
CLUSTER BY symbol
AS
WITH intraday AS (
    SELECT
        symbol,
        trade_date,
        ARRAY_AGG(
            STRUCT(timestamp, open, close)
            ORDER BY timestamp
            LIMIT 1
        )[OFFSET(0)] AS first_candle,
        MAX(high) AS day_high,
        MIN(low) AS day_low,
        ARRAY_AGG(close ORDER BY timestamp DESC LIMIT 1)[OFFSET(0)]
            AS close_price,
        SUM(volume) AS total_volume,
        AVG(volume) AS avg_volume,
        AVG(vwap) AS avg_vwap,
        COUNT(*) AS total_candles,
        COUNTIF(close > vwap) AS candles_above_vwap
    FROM `{{PROJECT_ID}}.{{AI_SEMANTIC_DATASET}}.spot_ai_intraday_history_90d`
    GROUP BY symbol, trade_date
),
daily AS (
    SELECT symbol, trade_date, previous_close
    FROM `{{PROJECT_ID}}.{{AI_SEMANTIC_DATASET}}.spot_ai_daily_history`
)
SELECT
    i.symbol,
    i.trade_date,
    i.first_candle.open AS open_price,
    d.previous_close,
    i.day_high,
    i.day_low,
    i.close_price,
    SAFE_DIVIDE(
        i.first_candle.open - d.previous_close,
        d.previous_close
    ) * 100 AS gap_pct,
    SAFE_DIVIDE(i.day_high - i.day_low, i.day_low) * 100
        AS intraday_range_pct,
    i.total_volume,
    i.avg_volume,
    i.avg_vwap,
    SAFE_DIVIDE(i.candles_above_vwap, i.total_candles) * 100
        AS vwap_hold_percentage,
    i.day_high = i.close_price AS high_breakout_flag,
    i.day_low = i.close_price AS low_breakdown_flag,
    CASE
        WHEN i.close_price > i.avg_vwap THEN "BULLISH"
        WHEN i.close_price < i.avg_vwap THEN "BEARISH"
        ELSE "NEUTRAL"
    END AS day_trend,
    CURRENT_TIMESTAMP() AS processed_at
FROM intraday i
LEFT JOIN daily d
    ON d.symbol = i.symbol
    AND d.trade_date = i.trade_date;

CREATE OR REPLACE TABLE
`{{PROJECT_ID}}.{{AI_SEMANTIC_DATASET}}.spot_ai_stock_summary`
AS
WITH daily_metrics AS (
    SELECT
        symbol,
        ARRAY_AGG(
            STRUCT(trade_date, close)
            ORDER BY trade_date
            LIMIT 1
        )[OFFSET(0)] AS first_day,
        ARRAY_AGG(
            STRUCT(trade_date, close)
            ORDER BY trade_date DESC
            LIMIT 1
        )[OFFSET(0)] AS last_day,
        AVG(daily_range_pct) AS avg_daily_range_pct,
        AVG(volume) AS avg_volume_90d
    FROM `{{PROJECT_ID}}.{{AI_SEMANTIC_DATASET}}.spot_ai_daily_history`
    WHERE trade_date >= DATE_SUB(DATE("2026-02-27"), INTERVAL 90 DAY)
    GROUP BY symbol
)
SELECT
    d.symbol,
    SAFE_DIVIDE(
        d.last_day.close - d.first_day.close,
        d.first_day.close
    ) * 100 AS return_90d_pct,
    d.avg_daily_range_pct,
    d.avg_volume_90d,
    m.close AS latest_close,
    m.rsi_14 AS latest_rsi,
    m.momentum_score AS latest_momentum_score,
    m.trend AS current_trend,
    m.volume_status,
    CURRENT_TIMESTAMP() AS processed_at
FROM daily_metrics d
LEFT JOIN
`{{PROJECT_ID}}.{{AI_SEMANTIC_DATASET}}.spot_ai_current_market_state` m
    ON m.symbol = d.symbol;