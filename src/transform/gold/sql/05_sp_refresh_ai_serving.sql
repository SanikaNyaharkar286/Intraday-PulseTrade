CREATE OR REPLACE PROCEDURE `{{PROJECT_ID}}.{{AI_DATASET}}.sp_refresh_ai_serving`()
BEGIN
    DECLARE latest_snapshot_date DATE DEFAULT (
        SELECT MAX(trade_date)
        FROM `{{PROJECT_ID}}.{{GOLD_DATASET}}.fact_daily_market`
        WHERE {{GOLD_AI_DAILY_SCOPE_FILTER}}
    );

    -- =====================================================
    -- Resolve the latest daily date per stock first.
    -- Full refresh is limited to a recent partition window.
    -- Incremental refresh is already limited to the scoped file date.
    -- =====================================================
    CREATE TEMP TABLE latest_daily_keys AS
    SELECT
        symbol,
        MAX(trade_date) AS trade_date
    FROM `{{PROJECT_ID}}.{{GOLD_DATASET}}.fact_daily_market`
    WHERE {{GOLD_AI_DAILY_SCOPE_FILTER}}
        AND trade_date BETWEEN
            DATE_SUB(
                latest_snapshot_date,
                INTERVAL {{AI_SNAPSHOT_LOOKBACK_DAYS}} DAY
            )
            AND latest_snapshot_date
    GROUP BY symbol;

    -- =====================================================
    -- Refresh Current Intraday Snapshot
    -- Source: Gold intraday metrics
    -- Grain: One latest 1M row per stock
    -- =====================================================
    CREATE TEMP TABLE current_intraday_rows AS
    SELECT * EXCEPT(row_number)
    FROM (
        SELECT
            m.symbol,
            m.trade_date,
            m.timestamp,
            m.timeframe,
            m.close,
            m.volume,
            m.bar_return_pct,
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
            CURRENT_TIMESTAMP() AS snapshot_at,
            ROW_NUMBER() OVER (
                PARTITION BY m.symbol
                ORDER BY m.trade_date DESC, m.timestamp DESC
            ) AS row_number
        FROM `{{PROJECT_ID}}.{{GOLD_DATASET}}.fact_intraday_metrics` m
        INNER JOIN latest_daily_keys k
            ON m.symbol = k.symbol
            AND m.trade_date = k.trade_date
        WHERE m.timeframe = "1M"
            AND m.trade_date BETWEEN
                DATE_SUB(
                    latest_snapshot_date,
                    INTERVAL {{AI_SNAPSHOT_LOOKBACK_DAYS}} DAY
                )
                AND latest_snapshot_date
            AND {{GOLD_AI_INTRADAY_SCOPE_FILTER}}
    )
    WHERE row_number = 1;

    MERGE `{{PROJECT_ID}}.{{AI_DATASET}}.ai_current_intraday_snapshot` t
    USING current_intraday_rows s
    ON t.symbol = s.symbol
    WHEN MATCHED THEN
        UPDATE SET
            trade_date = s.trade_date,
            timestamp = s.timestamp,
            timeframe = s.timeframe,
            close = s.close,
            volume = s.volume,
            bar_return_pct = s.bar_return_pct,
            day_return_pct = s.day_return_pct,
            vwap = s.vwap,
            ema_9 = s.ema_9,
            ema_20 = s.ema_20,
            rsi_14 = s.rsi_14,
            macd = s.macd,
            macd_signal = s.macd_signal,
            relative_volume = s.relative_volume,
            price_vs_vwap = s.price_vs_vwap,
            price_vs_ema20 = s.price_vs_ema20,
            price_vs_sma20 = s.price_vs_sma20,
            volume_status = s.volume_status,
            trend = s.trend,
            momentum_score = s.momentum_score,
            snapshot_at = s.snapshot_at
    WHEN NOT MATCHED THEN
        INSERT
        (
            symbol,
            trade_date,
            timestamp,
            timeframe,
            close,
            volume,
            bar_return_pct,
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
            momentum_score,
            snapshot_at
        )
        VALUES
        (
            s.symbol,
            s.trade_date,
            s.timestamp,
            s.timeframe,
            s.close,
            s.volume,
            s.bar_return_pct,
            s.day_return_pct,
            s.vwap,
            s.ema_9,
            s.ema_20,
            s.rsi_14,
            s.macd,
            s.macd_signal,
            s.relative_volume,
            s.price_vs_vwap,
            s.price_vs_ema20,
            s.price_vs_sma20,
            s.volume_status,
            s.trend,
            s.momentum_score,
            s.snapshot_at
        );

    -- =====================================================
    -- Refresh Latest Daily Snapshot
    -- Source: Gold daily market
    -- Grain: One latest daily row per stock
    -- =====================================================
    CREATE TEMP TABLE latest_daily_rows AS
    SELECT * EXCEPT(row_number)
    FROM (
        SELECT
            d.symbol,
            d.trade_date,
            d.open,
            d.high,
            d.low,
            d.close,
            d.volume,
            d.previous_close,
            d.return_pct,
            d.gap_pct,
            d.daily_range_pct,
            d.avg_volume_20,
            d.relative_volume,
            CURRENT_TIMESTAMP() AS snapshot_at,
            ROW_NUMBER() OVER (
                PARTITION BY d.symbol
                ORDER BY d.trade_date DESC
            ) AS row_number
        FROM `{{PROJECT_ID}}.{{GOLD_DATASET}}.fact_daily_market` d
        INNER JOIN latest_daily_keys k
            ON d.symbol = k.symbol
            AND d.trade_date = k.trade_date
    )
    WHERE row_number = 1;

    MERGE `{{PROJECT_ID}}.{{AI_DATASET}}.ai_latest_daily_snapshot` t
    USING latest_daily_rows s
    ON t.symbol = s.symbol
    WHEN MATCHED THEN
        UPDATE SET
            trade_date = s.trade_date,
            open = s.open,
            high = s.high,
            low = s.low,
            close = s.close,
            volume = s.volume,
            previous_close = s.previous_close,
            return_pct = s.return_pct,
            gap_pct = s.gap_pct,
            daily_range_pct = s.daily_range_pct,
            avg_volume_20 = s.avg_volume_20,
            relative_volume = s.relative_volume,
            snapshot_at = s.snapshot_at
    WHEN NOT MATCHED THEN
        INSERT
        (
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
            snapshot_at
        )
        VALUES
        (
            s.symbol,
            s.trade_date,
            s.open,
            s.high,
            s.low,
            s.close,
            s.volume,
            s.previous_close,
            s.return_pct,
            s.gap_pct,
            s.daily_range_pct,
            s.avg_volume_20,
            s.relative_volume,
            s.snapshot_at
        );

    -- =====================================================
    -- Refresh Current Signal Snapshot
    -- Source: Gold intraday signals
    -- Grain: Current/recent signal event rows
    -- =====================================================
    CREATE TEMP TABLE current_signal_rows AS
    SELECT
        s.signal_id,
        s.symbol,
        s.trade_date,
        s.timestamp,
        s.timeframe,
        s.signal_type,
        s.signal_value,
        s.reference_value,
        CURRENT_TIMESTAMP() AS snapshot_at
    FROM `{{PROJECT_ID}}.{{GOLD_DATASET}}.fact_intraday_signals` s
    INNER JOIN latest_daily_keys k
        ON s.symbol = k.symbol
        AND s.trade_date = k.trade_date
    WHERE s.trade_date BETWEEN
            DATE_SUB(
                latest_snapshot_date,
                INTERVAL {{AI_SNAPSHOT_LOOKBACK_DAYS}} DAY
            )
            AND latest_snapshot_date
        AND {{GOLD_AI_SIGNAL_SCOPE_FILTER}};

    DELETE FROM `{{PROJECT_ID}}.{{AI_DATASET}}.ai_current_signal_snapshot` t
    WHERE {{AI_SIGNAL_DELETE_SCOPE_FILTER}};

    INSERT INTO `{{PROJECT_ID}}.{{AI_DATASET}}.ai_current_signal_snapshot`
    (
        signal_id,
        symbol,
        trade_date,
        timestamp,
        timeframe,
        signal_type,
        signal_value,
        reference_value,
        snapshot_at
    )
    SELECT
        signal_id,
        symbol,
        trade_date,
        timestamp,
        timeframe,
        signal_type,
        signal_value,
        reference_value,
        snapshot_at
    FROM current_signal_rows;
END;
