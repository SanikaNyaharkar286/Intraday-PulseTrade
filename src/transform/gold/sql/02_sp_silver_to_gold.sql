CREATE OR REPLACE PROCEDURE `{{PROJECT_ID}}.{{GOLD_DATASET}}.sp_silver_to_gold`()
BEGIN
    -- =====================================================
    -- Prepare Silver Intraday Source
    -- Source: Silver 1-minute and 5-minute tables
    -- Purpose: Keep Gold logic focused on business fields
    -- =====================================================
    CREATE TEMP TABLE silver_intraday_source AS
    SELECT
        1 AS timeframe_key,
        "1M" AS timeframe,
        trade_date,
        symbol,
        timestamp,
        open,
        high,
        low,
        close,
        volume,
        previous_close,
        return_pct,
        gap_pct,
        sma_20,
        ema_9,
        ema_20,
        rsi_14,
        macd,
        macd_signal,
        vwap,
        avg_volume_20,
        relative_volume,
        silver_updated_at
    FROM `{{PROJECT_ID}}.{{SILVER_DATASET}}.silver_intraday_1m`
    {{SILVER_1M_SOURCE_FILTER}}

    UNION ALL

    SELECT
        5 AS timeframe_key,
        "5M" AS timeframe,
        trade_date,
        symbol,
        timestamp,
        open,
        high,
        low,
        close,
        volume,
        previous_close,
        return_pct,
        gap_pct,
        sma_20,
        ema_9,
        ema_20,
        rsi_14,
        macd,
        macd_signal,
        vwap,
        avg_volume_20,
        relative_volume,
        silver_updated_at
    FROM `{{PROJECT_ID}}.{{SILVER_DATASET}}.silver_intraday_5m`
    {{SILVER_5M_SOURCE_FILTER}};

    -- =====================================================
    -- Prepare Intraday Return And Volume Semantics
    -- Source: Silver intraday + Silver daily previous close
    -- Purpose:
    --   bar_return_pct = current bar close vs previous intraday close
    --   day_return_pct = current bar close vs previous trading-day close
    --   relative_volume = current volume vs previous 20 bars, excluding current bar
    -- Note: Silver provides simplified EMA/RSI/MACD values; Gold reuses them.
    -- =====================================================
    CREATE TEMP TABLE silver_intraday_enriched AS
    SELECT
        * EXCEPT(previous_20_bar_avg_volume),
        previous_20_bar_avg_volume AS avg_volume_20,
        SAFE_DIVIDE(volume, previous_20_bar_avg_volume) AS relative_volume
    FROM (
        SELECT
            s.* EXCEPT(avg_volume_20, relative_volume),
            s.return_pct AS bar_return_pct,
            SAFE_DIVIDE(
                s.close - d.previous_close,
                d.previous_close
            ) * 100 AS day_return_pct,
            AVG(s.volume) OVER (
                PARTITION BY s.symbol, s.timeframe_key
                ORDER BY s.timestamp
                ROWS BETWEEN 20 PRECEDING AND 1 PRECEDING
            ) AS previous_20_bar_avg_volume
        FROM silver_intraday_source s
        LEFT JOIN `{{PROJECT_ID}}.{{SILVER_DATASET}}.silver_daily_stock` d
            ON d.symbol = s.symbol
            AND d.trade_date = s.trade_date
            {{SILVER_DAILY_JOIN_FILTER}}
    );

    -- =====================================================
    -- Update Stock Dimension
    -- Source: Silver stock symbols
    -- Purpose: Add missing stocks without inventing metadata
    -- =====================================================
    MERGE `{{PROJECT_ID}}.{{GOLD_DATASET}}.dim_stock` t
    USING (
        SELECT DISTINCT
            FARM_FINGERPRINT(symbol) AS stock_key,
            symbol
        FROM (
            SELECT symbol
            FROM silver_intraday_source

            UNION DISTINCT

            SELECT symbol
            FROM `{{PROJECT_ID}}.{{SILVER_DATASET}}.silver_daily_stock`
            {{SILVER_DAILY_SOURCE_FILTER}}
        )
        WHERE symbol IS NOT NULL
    ) s
    ON t.symbol = s.symbol
    WHEN NOT MATCHED THEN
        INSERT
        (
            stock_key,
            symbol,
            company_name,
            sector,
            industry,
            exchange,
            processed_at
        )
        VALUES
        (
            s.stock_key,
            s.symbol,
            NULL,
            NULL,
            NULL,
            NULL,
            CURRENT_TIMESTAMP()
        );

    -- =====================================================
    -- Update Date Dimension
    -- Source: Silver trade dates
    -- Purpose: Add calendar rows used by Gold facts
    -- =====================================================
    MERGE `{{PROJECT_ID}}.{{GOLD_DATASET}}.dim_date` t
    USING (
        SELECT DISTINCT
            CAST(FORMAT_DATE("%Y%m%d", trade_date) AS INT64) AS date_key,
            trade_date AS date,
            EXTRACT(DAY FROM trade_date) AS day,
            EXTRACT(MONTH FROM trade_date) AS month,
            EXTRACT(QUARTER FROM trade_date) AS quarter,
            EXTRACT(YEAR FROM trade_date) AS year
        FROM (
            SELECT trade_date
            FROM silver_intraday_source

            UNION DISTINCT

            SELECT trade_date
            FROM `{{PROJECT_ID}}.{{SILVER_DATASET}}.silver_daily_stock`
            {{SILVER_DAILY_SOURCE_FILTER}}
        )
        WHERE trade_date IS NOT NULL
    ) s
    ON t.date_key = s.date_key
    WHEN NOT MATCHED THEN
        INSERT
        (
            date_key,
            date,
            day,
            month,
            quarter,
            year,
            processed_at
        )
        VALUES
        (
            s.date_key,
            s.date,
            s.day,
            s.month,
            s.quarter,
            s.year,
            CURRENT_TIMESTAMP()
        );

    -- =====================================================
    -- Update Timeframe Dimension
    -- Source: Supported Gold timeframes
    -- Purpose: Keep timeframe keys stable
    -- =====================================================
    MERGE `{{PROJECT_ID}}.{{GOLD_DATASET}}.dim_timeframe` t
    USING (
        SELECT 1 AS timeframe_key, "1M" AS timeframe
        UNION ALL
        SELECT 5 AS timeframe_key, "5M" AS timeframe
    ) s
    ON t.timeframe_key = s.timeframe_key
    WHEN NOT MATCHED THEN
        INSERT
        (
            timeframe_key,
            timeframe,
            processed_at
        )
        VALUES
        (
            s.timeframe_key,
            s.timeframe,
            CURRENT_TIMESTAMP()
        );

    DELETE FROM `{{PROJECT_ID}}.{{GOLD_DATASET}}.dim_timeframe`
    WHERE timeframe NOT IN ("1M", "5M");

    -- =====================================================
    -- Update Intraday Metrics
    -- Source: Silver intraday indicators
    -- Purpose: Add simple trading-ready business fields
    -- =====================================================
    MERGE `{{PROJECT_ID}}.{{GOLD_DATASET}}.fact_intraday_metrics` t
    USING (
        SELECT
            FARM_FINGERPRINT(s.symbol) AS stock_key,
            CAST(FORMAT_DATE("%Y%m%d", s.trade_date) AS INT64) AS date_key,
            s.timeframe_key,
            s.symbol,
            s.trade_date,
            s.timestamp,
            s.timeframe,
            s.open,
            s.high,
            s.low,
            s.close,
            s.volume,
            s.previous_close,
            s.bar_return_pct,
            s.day_return_pct,
            s.bar_return_pct AS return_pct,
            s.gap_pct,
            s.sma_20,
            s.ema_9,
            s.ema_20,
            s.rsi_14,
            s.macd,
            s.macd_signal,
            s.vwap,
            s.avg_volume_20,
            s.relative_volume,
            CASE
                WHEN s.close > s.vwap THEN "ABOVE_VWAP"
                WHEN s.close < s.vwap THEN "BELOW_VWAP"
                ELSE "AT_VWAP"
            END AS price_vs_vwap,
            CASE
                WHEN s.close > s.ema_20 THEN "ABOVE_EMA20"
                WHEN s.close < s.ema_20 THEN "BELOW_EMA20"
                ELSE NULL
            END AS price_vs_ema20,
            CASE
                WHEN s.close > s.sma_20 THEN "ABOVE_SMA20"
                WHEN s.close < s.sma_20 THEN "BELOW_SMA20"
                ELSE NULL
            END AS price_vs_sma20,
            CASE
                WHEN s.relative_volume > 1.5 THEN "HIGH_VOLUME"
                WHEN s.relative_volume < 0.75 THEN "LOW_VOLUME"
                ELSE "NORMAL_VOLUME"
            END AS volume_status,
            CASE
                WHEN
                    s.close > s.vwap
                    AND s.close > s.ema_20
                    AND s.ema_9 > s.ema_20
                    AND s.rsi_14 > 50
                    THEN "BULLISH"
                WHEN
                    s.close < s.vwap
                    AND s.close < s.ema_20
                    AND s.ema_9 < s.ema_20
                    AND s.rsi_14 < 50
                    THEN "BEARISH"
                ELSE "NEUTRAL"
            END AS trend,
            (
                IF(s.close > s.vwap, 1, 0)
                + IF(s.close > s.ema_20, 1, 0)
                + IF(s.ema_9 > s.ema_20, 1, 0)
                + IF(s.rsi_14 > 50, 1, 0)
                + IF(s.macd > s.macd_signal, 1, 0)
                + IF(s.relative_volume > 1.5, 1, 0)
            ) AS momentum_score
        FROM silver_intraday_enriched s
        LEFT JOIN `{{PROJECT_ID}}.{{GOLD_DATASET}}.fact_intraday_metrics` t
            ON t.symbol = s.symbol
            AND t.timestamp = s.timestamp
            AND t.timeframe_key = s.timeframe_key
        WHERE
            s.symbol IS NOT NULL
            AND s.timestamp IS NOT NULL
            AND (
                t.symbol IS NULL
                OR s.silver_updated_at > t.processed_at
                OR t.bar_return_pct IS NULL
                OR t.day_return_pct IS NULL
                OR t.avg_volume_20 IS DISTINCT FROM s.avg_volume_20
                OR t.relative_volume IS DISTINCT FROM s.relative_volume
            )
    ) s
    ON
        t.symbol = s.symbol
        AND t.timestamp = s.timestamp
        AND t.timeframe_key = s.timeframe_key
    WHEN MATCHED THEN
        UPDATE SET
            stock_key = s.stock_key,
            date_key = s.date_key,
            trade_date = s.trade_date,
            timeframe = s.timeframe,
            open = s.open,
            high = s.high,
            low = s.low,
            close = s.close,
            volume = s.volume,
            previous_close = s.previous_close,
            bar_return_pct = s.bar_return_pct,
            day_return_pct = s.day_return_pct,
            return_pct = s.return_pct,
            gap_pct = s.gap_pct,
            sma_20 = s.sma_20,
            ema_9 = s.ema_9,
            ema_20 = s.ema_20,
            rsi_14 = s.rsi_14,
            macd = s.macd,
            macd_signal = s.macd_signal,
            vwap = s.vwap,
            avg_volume_20 = s.avg_volume_20,
            relative_volume = s.relative_volume,
            price_vs_vwap = s.price_vs_vwap,
            price_vs_ema20 = s.price_vs_ema20,
            price_vs_sma20 = s.price_vs_sma20,
            volume_status = s.volume_status,
            trend = s.trend,
            momentum_score = s.momentum_score,
            processed_at = CURRENT_TIMESTAMP()
    WHEN NOT MATCHED THEN
        INSERT
        (
            stock_key,
            date_key,
            timeframe_key,
            symbol,
            trade_date,
            timestamp,
            timeframe,
            open,
            high,
            low,
            close,
            volume,
            previous_close,
            bar_return_pct,
            day_return_pct,
            return_pct,
            gap_pct,
            sma_20,
            ema_9,
            ema_20,
            rsi_14,
            macd,
            macd_signal,
            vwap,
            avg_volume_20,
            relative_volume,
            price_vs_vwap,
            price_vs_ema20,
            price_vs_sma20,
            volume_status,
            trend,
            momentum_score,
            processed_at
        )
        VALUES
        (
            s.stock_key,
            s.date_key,
            s.timeframe_key,
            s.symbol,
            s.trade_date,
            s.timestamp,
            s.timeframe,
            s.open,
            s.high,
            s.low,
            s.close,
            s.volume,
            s.previous_close,
            s.bar_return_pct,
            s.day_return_pct,
            s.return_pct,
            s.gap_pct,
            s.sma_20,
            s.ema_9,
            s.ema_20,
            s.rsi_14,
            s.macd,
            s.macd_signal,
            s.vwap,
            s.avg_volume_20,
            s.relative_volume,
            s.price_vs_vwap,
            s.price_vs_ema20,
            s.price_vs_sma20,
            s.volume_status,
            s.trend,
            s.momentum_score,
            CURRENT_TIMESTAMP()
        );

    -- =====================================================
    -- Update Intraday Signals
    -- Source: Gold intraday metrics
    -- Purpose: Store deterministic breakout and crossover events
    -- =====================================================
    CREATE TEMP TABLE signal_candidates AS
    WITH metric_windows AS (
        SELECT
            *,
            MAX(high) OVER (
                PARTITION BY symbol, trade_date, timeframe_key
                ORDER BY timestamp
                ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
            ) AS previous_intraday_high,
            MIN(low) OVER (
                PARTITION BY symbol, trade_date, timeframe_key
                ORDER BY timestamp
                ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
            ) AS previous_intraday_low,
            LAG(vwap) OVER (
                PARTITION BY symbol, trade_date, timeframe_key
                ORDER BY timestamp
            ) AS previous_vwap,
            LAG(close) OVER (
                PARTITION BY symbol, trade_date, timeframe_key
                ORDER BY timestamp
            ) AS previous_close_row,
            LAG(ema_9) OVER (
                PARTITION BY symbol, trade_date, timeframe_key
                ORDER BY timestamp
            ) AS previous_ema_9,
            LAG(ema_20) OVER (
                PARTITION BY symbol, trade_date, timeframe_key
                ORDER BY timestamp
            ) AS previous_ema_20,
            LAG(macd) OVER (
                PARTITION BY symbol, trade_date, timeframe_key
                ORDER BY timestamp
            ) AS previous_macd,
            LAG(macd_signal) OVER (
                PARTITION BY symbol, trade_date, timeframe_key
                ORDER BY timestamp
            ) AS previous_macd_signal,
            LAG(relative_volume) OVER (
                PARTITION BY symbol, trade_date, timeframe_key
                ORDER BY timestamp
            ) AS previous_relative_volume
        FROM `{{PROJECT_ID}}.{{GOLD_DATASET}}.fact_intraday_metrics`
        WHERE {{GOLD_SIGNAL_SCOPE_FILTER}}
    ),
    signals AS (
        SELECT
            stock_key,
            date_key,
            timeframe_key,
            symbol,
            trade_date,
            timestamp,
            timeframe,
            "DAY_HIGH_BREAKOUT" AS signal_type,
            high AS signal_value,
            previous_intraday_high AS reference_value
        FROM metric_windows
        WHERE previous_intraday_high IS NOT NULL
            AND high > previous_intraday_high

        UNION ALL

        SELECT
            stock_key,
            date_key,
            timeframe_key,
            symbol,
            trade_date,
            timestamp,
            timeframe,
            "DAY_LOW_BREAKDOWN" AS signal_type,
            low AS signal_value,
            previous_intraday_low AS reference_value
        FROM metric_windows
        WHERE previous_intraday_low IS NOT NULL
            AND low < previous_intraday_low

        UNION ALL

        SELECT
            stock_key,
            date_key,
            timeframe_key,
            symbol,
            trade_date,
            timestamp,
            timeframe,
            "VWAP_CROSS_UP" AS signal_type,
            close AS signal_value,
            vwap AS reference_value
        FROM metric_windows
        WHERE previous_close_row <= previous_vwap
            AND close > vwap

        UNION ALL

        SELECT
            stock_key,
            date_key,
            timeframe_key,
            symbol,
            trade_date,
            timestamp,
            timeframe,
            "VWAP_CROSS_DOWN" AS signal_type,
            close AS signal_value,
            vwap AS reference_value
        FROM metric_windows
        WHERE previous_close_row >= previous_vwap
            AND close < vwap

        UNION ALL

        SELECT
            stock_key,
            date_key,
            timeframe_key,
            symbol,
            trade_date,
            timestamp,
            timeframe,
            "EMA_BULLISH_CROSSOVER" AS signal_type,
            ema_9 AS signal_value,
            ema_20 AS reference_value
        FROM metric_windows
        WHERE previous_ema_9 <= previous_ema_20
            AND ema_9 > ema_20

        UNION ALL

        SELECT
            stock_key,
            date_key,
            timeframe_key,
            symbol,
            trade_date,
            timestamp,
            timeframe,
            "EMA_BEARISH_CROSSOVER" AS signal_type,
            ema_9 AS signal_value,
            ema_20 AS reference_value
        FROM metric_windows
        WHERE previous_ema_9 >= previous_ema_20
            AND ema_9 < ema_20

        UNION ALL

        SELECT
            stock_key,
            date_key,
            timeframe_key,
            symbol,
            trade_date,
            timestamp,
            timeframe,
            "MACD_BULLISH_CROSSOVER" AS signal_type,
            macd AS signal_value,
            macd_signal AS reference_value
        FROM metric_windows
        WHERE previous_macd <= previous_macd_signal
            AND macd > macd_signal

        UNION ALL

        SELECT
            stock_key,
            date_key,
            timeframe_key,
            symbol,
            trade_date,
            timestamp,
            timeframe,
            "MACD_BEARISH_CROSSOVER" AS signal_type,
            macd AS signal_value,
            macd_signal AS reference_value
        FROM metric_windows
        WHERE previous_macd >= previous_macd_signal
            AND macd < macd_signal

        UNION ALL

        SELECT
            stock_key,
            date_key,
            timeframe_key,
            symbol,
            trade_date,
            timestamp,
            timeframe,
            "VOLUME_BREAKOUT" AS signal_type,
            relative_volume AS signal_value,
            2.0 AS reference_value
        FROM metric_windows
        WHERE IFNULL(previous_relative_volume, 0) <= 2
            AND relative_volume > 2
    )
    SELECT
        TO_HEX(
            MD5(
                CONCAT(
                    symbol,
                    "|",
                    CAST(timestamp AS STRING),
                    "|",
                    timeframe,
                    "|",
                    signal_type
                )
            )
        ) AS signal_id,
        *
    FROM signals;

    DELETE FROM `{{PROJECT_ID}}.{{GOLD_DATASET}}.fact_intraday_signals` t
    WHERE t.signal_type = "VOLUME_BREAKOUT"
        AND {{GOLD_SIGNAL_DELETE_SCOPE_FILTER}}
        AND NOT EXISTS (
            SELECT 1
            FROM signal_candidates s
            WHERE s.signal_id = t.signal_id
        );

    MERGE `{{PROJECT_ID}}.{{GOLD_DATASET}}.fact_intraday_signals` t
    USING signal_candidates s
    ON t.signal_id = s.signal_id
    WHEN NOT MATCHED THEN
        INSERT
        (
            signal_id,
            stock_key,
            date_key,
            timeframe_key,
            symbol,
            trade_date,
            timestamp,
            timeframe,
            signal_type,
            signal_value,
            reference_value,
            processed_at
        )
        VALUES
        (
            s.signal_id,
            s.stock_key,
            s.date_key,
            s.timeframe_key,
            s.symbol,
            s.trade_date,
            s.timestamp,
            s.timeframe,
            s.signal_type,
            s.signal_value,
            s.reference_value,
            CURRENT_TIMESTAMP()
        );

    -- =====================================================
    -- Update Daily Market
    -- Source: Silver daily table
    -- Purpose: Daily market performance facts
    -- =====================================================
    MERGE `{{PROJECT_ID}}.{{GOLD_DATASET}}.fact_daily_market` t
    USING (
        SELECT
            FARM_FINGERPRINT(s.symbol) AS stock_key,
            CAST(FORMAT_DATE("%Y%m%d", s.trade_date) AS INT64) AS date_key,
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
            s.relative_volume
        FROM `{{PROJECT_ID}}.{{SILVER_DATASET}}.silver_daily_stock` s
        LEFT JOIN `{{PROJECT_ID}}.{{GOLD_DATASET}}.fact_daily_market` t
            ON t.symbol = s.symbol
            AND t.trade_date = s.trade_date
        WHERE
            {{SILVER_DAILY_ALIAS_SOURCE_FILTER}}
            AND
            s.symbol IS NOT NULL
            AND s.trade_date IS NOT NULL
            AND (
                t.symbol IS NULL
                OR s.silver_updated_at > t.processed_at
            )
    ) s
    ON t.symbol = s.symbol
        AND t.trade_date = s.trade_date
    WHEN MATCHED THEN
        UPDATE SET
            stock_key = s.stock_key,
            date_key = s.date_key,
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
            processed_at = CURRENT_TIMESTAMP()
    WHEN NOT MATCHED THEN
        INSERT
        (
            stock_key,
            date_key,
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
            processed_at
        )
        VALUES
        (
            s.stock_key,
            s.date_key,
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
            CURRENT_TIMESTAMP()
        );

    -- =====================================================
    -- Update Stock Returns
    -- Source: Gold daily market fact
    -- Purpose: Calculate simple multi-year cumulative returns
    -- =====================================================
    MERGE `{{PROJECT_ID}}.{{GOLD_DATASET}}.fact_stock_returns` t
    USING (
        WITH latest_daily AS (
            SELECT
                *,
                ROW_NUMBER() OVER (
                    PARTITION BY symbol
                    ORDER BY trade_date DESC
                ) AS row_number
            FROM `{{PROJECT_ID}}.{{GOLD_DATASET}}.fact_daily_market`
        ),
        current_daily AS (
            SELECT
                stock_key,
                symbol,
                trade_date,
                close
            FROM latest_daily
            WHERE row_number = 1
        ),
        return_1y_base AS (
            SELECT
                cur.symbol,
                hist.close,
                ROW_NUMBER() OVER (
                    PARTITION BY cur.symbol
                    ORDER BY hist.trade_date DESC
                ) AS row_number
            FROM current_daily cur
            INNER JOIN `{{PROJECT_ID}}.{{GOLD_DATASET}}.fact_daily_market` hist
                ON hist.symbol = cur.symbol
                AND hist.trade_date <= DATE_SUB(cur.trade_date, INTERVAL 1 YEAR)
        ),
        return_2y_base AS (
            SELECT
                cur.symbol,
                hist.close,
                ROW_NUMBER() OVER (
                    PARTITION BY cur.symbol
                    ORDER BY hist.trade_date DESC
                ) AS row_number
            FROM current_daily cur
            INNER JOIN `{{PROJECT_ID}}.{{GOLD_DATASET}}.fact_daily_market` hist
                ON hist.symbol = cur.symbol
                AND hist.trade_date <= DATE_SUB(cur.trade_date, INTERVAL 2 YEAR)
        ),
        return_3y_base AS (
            SELECT
                cur.symbol,
                hist.close,
                ROW_NUMBER() OVER (
                    PARTITION BY cur.symbol
                    ORDER BY hist.trade_date DESC
                ) AS row_number
            FROM current_daily cur
            INNER JOIN `{{PROJECT_ID}}.{{GOLD_DATASET}}.fact_daily_market` hist
                ON hist.symbol = cur.symbol
                AND hist.trade_date <= DATE_SUB(cur.trade_date, INTERVAL 3 YEAR)
        ),
        return_5y_base AS (
            SELECT
                cur.symbol,
                hist.close,
                ROW_NUMBER() OVER (
                    PARTITION BY cur.symbol
                    ORDER BY hist.trade_date DESC
                ) AS row_number
            FROM current_daily cur
            INNER JOIN `{{PROJECT_ID}}.{{GOLD_DATASET}}.fact_daily_market` hist
                ON hist.symbol = cur.symbol
                AND hist.trade_date <= DATE_SUB(cur.trade_date, INTERVAL 5 YEAR)
        )
        SELECT
            cur.stock_key,
            cur.symbol,
            cur.trade_date AS as_of_date,
            SAFE_DIVIDE(
                cur.close,
                r1.close
            ) - 1 AS return_1y,
            SAFE_DIVIDE(
                cur.close,
                r2.close
            ) - 1 AS return_2y,
            SAFE_DIVIDE(
                cur.close,
                r3.close
            ) - 1 AS return_3y,
            SAFE_DIVIDE(
                cur.close,
                r5.close
            ) - 1 AS return_5y
        FROM current_daily cur
        LEFT JOIN return_1y_base r1
            ON r1.symbol = cur.symbol
            AND r1.row_number = 1
        LEFT JOIN return_2y_base r2
            ON r2.symbol = cur.symbol
            AND r2.row_number = 1
        LEFT JOIN return_3y_base r3
            ON r3.symbol = cur.symbol
            AND r3.row_number = 1
        LEFT JOIN return_5y_base r5
            ON r5.symbol = cur.symbol
            AND r5.row_number = 1
    ) s
    ON t.symbol = s.symbol
        AND t.as_of_date = s.as_of_date
    WHEN MATCHED THEN
        UPDATE SET
            stock_key = s.stock_key,
            return_1y = s.return_1y,
            return_2y = s.return_2y,
            return_3y = s.return_3y,
            return_5y = s.return_5y,
            processed_at = CURRENT_TIMESTAMP()
    WHEN NOT MATCHED THEN
        INSERT
        (
            stock_key,
            symbol,
            as_of_date,
            return_1y,
            return_2y,
            return_3y,
            return_5y,
            processed_at
        )
        VALUES
        (
            s.stock_key,
            s.symbol,
            s.as_of_date,
            s.return_1y,
            s.return_2y,
            s.return_3y,
            s.return_5y,
            CURRENT_TIMESTAMP()
        );
END;
