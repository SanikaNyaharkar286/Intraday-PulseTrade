-- =====================================================
-- Top Gainers
-- Purpose: Latest daily leaders by return percentage
-- =====================================================
CREATE OR REPLACE VIEW `{{PROJECT_ID}}.{{SEMANTIC_DATASET}}.vw_top_gainers` AS
WITH ranked_rows AS (
    SELECT
        ROW_NUMBER() OVER (ORDER BY return_pct DESC, symbol) AS rank,
        symbol,
        close,
        return_pct,
        volume,
        relative_volume
    FROM `{{PROJECT_ID}}.{{SEMANTIC_DATASET}}.vw_latest_daily`
)
SELECT *
FROM ranked_rows;

-- =====================================================
-- Top Losers
-- Purpose: Latest daily laggards by return percentage
-- =====================================================
CREATE OR REPLACE VIEW `{{PROJECT_ID}}.{{SEMANTIC_DATASET}}.vw_top_losers` AS
WITH ranked_rows AS (
    SELECT
        ROW_NUMBER() OVER (ORDER BY return_pct ASC, symbol) AS rank,
        symbol,
        close,
        return_pct,
        volume,
        relative_volume
    FROM `{{PROJECT_ID}}.{{SEMANTIC_DATASET}}.vw_latest_daily`
)
SELECT *
FROM ranked_rows;

-- =====================================================
-- Stock Returns
-- Purpose: Multi-year return view for dashboards
-- =====================================================
CREATE OR REPLACE VIEW `{{PROJECT_ID}}.{{SEMANTIC_DATASET}}.vw_stock_returns` AS
SELECT
    symbol,
    as_of_date,
    return_1y,
    return_2y,
    return_3y,
    return_5y
FROM `{{PROJECT_ID}}.{{GOLD_DATASET}}.fact_stock_returns`;

-- =====================================================
-- Market Overview
-- Purpose: Summary counts from latest intraday data
-- =====================================================
CREATE OR REPLACE VIEW `{{PROJECT_ID}}.{{SEMANTIC_DATASET}}.vw_market_overview` AS
SELECT
    COUNT(*) AS total_stocks,
    COUNTIF(trend = "BULLISH") AS bullish_stocks,
    COUNTIF(trend = "BEARISH") AS bearish_stocks,
    COUNTIF(trend = "NEUTRAL") AS neutral_stocks,
    COUNTIF(price_vs_vwap = "ABOVE_VWAP") AS stocks_above_vwap,
    COUNTIF(price_vs_vwap = "BELOW_VWAP") AS stocks_below_vwap,
    COUNTIF(volume_status = "HIGH_VOLUME") AS stocks_with_high_volume
FROM `{{PROJECT_ID}}.{{AI_DATASET}}.ai_current_intraday_snapshot`;
