-- =====================================================
-- Scanner
-- Purpose: Current deterministic stock screening fields
-- =====================================================
CREATE OR REPLACE VIEW `{{PROJECT_ID}}.{{SEMANTIC_DATASET}}.vw_scanner` AS
SELECT
    symbol,
    trade_date,
    close,
    day_return_pct,
    vwap,
    ema_20,
    rsi_14,
    macd,
    macd_signal,
    relative_volume,
    trend,
    momentum_score,
    close > vwap AS above_vwap,
    close > ema_20 AS above_ema20,
    rsi_14 > 50 AS rsi_bullish,
    relative_volume > 1.5 AS high_volume,
    macd > macd_signal AS macd_bullish
FROM `{{PROJECT_ID}}.{{SEMANTIC_DATASET}}.vw_current_intraday`;

-- =====================================================
-- Current Breakouts
-- Purpose: Latest-date intraday breakout and crossover events
-- =====================================================
CREATE OR REPLACE VIEW `{{PROJECT_ID}}.{{SEMANTIC_DATASET}}.vw_current_breakouts` AS
WITH latest_trade_date AS (
    SELECT MAX(trade_date) AS trade_date
    FROM `{{PROJECT_ID}}.{{GOLD_DATASET}}.fact_intraday_metrics`
)
SELECT
    s.symbol,
    s.trade_date,
    s.timestamp,
    s.timeframe,
    s.signal_type,
    s.signal_value,
    s.reference_value
FROM `{{PROJECT_ID}}.{{GOLD_DATASET}}.fact_intraday_signals` s
INNER JOIN latest_trade_date d
    ON d.trade_date = s.trade_date
WHERE s.signal_type IN (
    "DAY_HIGH_BREAKOUT",
    "DAY_LOW_BREAKDOWN",
    "VWAP_CROSS_UP",
    "VWAP_CROSS_DOWN",
    "EMA_BULLISH_CROSSOVER",
    "EMA_BEARISH_CROSSOVER",
    "MACD_BULLISH_CROSSOVER",
    "MACD_BEARISH_CROSSOVER",
    "VOLUME_BREAKOUT"
);

DROP VIEW IF EXISTS `{{PROJECT_ID}}.{{SEMANTIC_DATASET}}.vw_breakouts`;
