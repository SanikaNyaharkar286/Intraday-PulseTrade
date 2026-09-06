CREATE OR REPLACE PROCEDURE `{{PROJECT_ID}}.{{SILVER_DATASET}}.sp_bronze_to_silver`()
BEGIN
    DECLARE run_id STRING DEFAULT GENERATE_UUID();
    DECLARE run_start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP();
    DECLARE records_read INT64 DEFAULT 0;
    DECLARE records_processed INT64 DEFAULT 0;
    DECLARE records_inserted INT64 DEFAULT 0;
    DECLARE records_rejected INT64 DEFAULT 0;
    DECLARE records_duplicate INT64 DEFAULT 0;
---store the earlist changed bronze and latest changed 
    DECLARE impacted_start TIMESTAMP;
    DECLARE impacted_end TIMESTAMP;

    BEGIN
    --- create a temp table to check the bronze data for invalid row and reject reasoon
    ---validate the raw rows 
        CREATE TEMP TABLE bronze_checked AS
        SELECT
            symbol,
            timestamp AS bronze_timestamp,
            DATETIME(timestamp, "Asia/Kolkata") AS timestamp,
            open,
            high,
            low,
            close,
            volume,
            DATE(timestamp, "Asia/Kolkata") AS trade_date,
            ---checks for invalid rows and asgin the reject reason
            CASE
                WHEN symbol IS NULL
                    OR timestamp IS NULL
                    OR open IS NULL
                    OR high IS NULL
                    OR low IS NULL
                    OR close IS NULL
                    OR volume IS NULL
                    THEN "NULL required fields"
                WHEN open <= 0
                    OR high <= 0
                    OR low <= 0
                    OR close <= 0
                    THEN "Non-positive OHLC value"
                WHEN volume < 0
                    THEN "Negative volume"
                WHEN high < low
                    OR open < low
                    OR open > high
                    OR close < low
                    OR close > high
                    THEN "Invalid OHLC relationship"
                WHEN TIME(timestamp, "Asia/Kolkata") < TIME "09:15:00"
                    OR TIME(timestamp, "Asia/Kolkata") > TIME "15:30:00"
                    THEN "Outside market hours"
                --- if nothing match then reject reason will be null and it will be the vaild row 
                ELSE NULL
            END AS reject_reason
---this is read from the bronze dataset and filter data based on condition 
        FROM `{{PROJECT_ID}}.{{BRONZE_DATASET}}.{{BRONZE_TABLE}}`
        {{BRONZE_SOURCE_FILTER}};

---create a temp table to check bronze data with silver data and reject table to
--- find the valid and invalid rows 

        CREATE TEMP TABLE bronze_candidates AS
        SELECT
            b.*

        FROM bronze_checked b
---this check valid bronze data already exit in silver table or not and if it is invalid then check in reject table 
        LEFT JOIN `{{PROJECT_ID}}.{{SILVER_DATASET}}.silver_intraday_1m` s
            ON b.reject_reason IS NULL
            AND s.symbol = b.symbol
            AND s.timestamp = b.timestamp
---check if invalid data already exit in reject or not if not insert 
        LEFT JOIN `{{PROJECT_ID}}.{{SILVER_DATASET}}.silver_rejects` r
            ON b.reject_reason IS NOT NULL
            AND IFNULL(r.symbol, "") = IFNULL(b.symbol, "")
            AND IFNULL(r.timestamp, DATETIME "0001-01-01 00:00:00")
                = IFNULL(b.timestamp, DATETIME "0001-01-01 00:00:00")
            AND r.reject_reason = b.reject_reason

        WHERE
        ---filter bronze data based on the condition like date and symbol 
            {{BRONZE_CANDIDATE_FILTER}}
            AND
            (
                (
                    ---if row is valid theb check if it is present in silver or not if present then upate the change 
                    b.reject_reason IS NULL
                    AND (
                        s.timestamp IS NULL
                        OR IFNULL(s.open, -999999999999.0)
                            != IFNULL(b.open, -999999999999.0)
                        OR IFNULL(s.high, -999999999999.0)
                            != IFNULL(b.high, -999999999999.0)
                        OR IFNULL(s.low, -999999999999.0)
                            != IFNULL(b.low, -999999999999.0)
                        OR IFNULL(s.close, -999999999999.0)
                            != IFNULL(b.close, -999999999999.0)
                        OR IFNULL(s.volume, -999999999999.0)
                            != IFNULL(b.volume, -999999999999.0)
                    )
                )
                ---if row is invalid then check if it is already present in
                ---reject table or not if not insert new row 
                ---The Bronze row is invalid AND this invalid row does not already exist in Rejects.
                OR (
                    b.reject_reason IS NOT NULL
                    AND r.reject_time IS NULL
                )
            );
---count how many record 
        SET records_read = (
            SELECT COUNT(*)
            FROM bronze_candidates
        );
---it take only invlaid row and insert into the reject table 
        CREATE TEMP TABLE invalid_rows AS
        SELECT
            IFNULL(trade_date, CURRENT_DATE("Asia/Kolkata")) AS reject_date,
            symbol,
            timestamp,
            open,
            high,
            low,
            close,
            volume,
            reject_reason,
            CURRENT_TIMESTAMP() AS reject_time

        FROM bronze_candidates
        WHERE reject_reason IS NOT NULL;
---reject row count 
        SET records_rejected = (
            SELECT COUNT(*)
            FROM invalid_rows
        );
---add to the reejct table if it is present then it will not add and if it is not then insert 
        --- need to comment this logic because we are already checking in bronze_canditate 
        MERGE `{{PROJECT_ID}}.{{SILVER_DATASET}}.silver_rejects` t
        USING invalid_rows s
        ON IFNULL(t.symbol, "") = IFNULL(s.symbol, "")
            AND IFNULL(t.timestamp, DATETIME "0001-01-01 00:00:00")
                = IFNULL(s.timestamp, DATETIME "0001-01-01 00:00:00")
            AND t.reject_reason = s.reject_reason
            ---when not matched then insert the row 
        WHEN NOT MATCHED THEN
            INSERT
            (
                reject_date,
                symbol,
                timestamp,
                open,
                high,
                low,
                close,
                volume,
                reject_reason,
                reject_time
            )
            VALUES
            (
                s.reject_date,
                s.symbol,
                s.timestamp,
                s.open,
                s.high,
                s.low,
                s.close,
                s.volume,
                s.reject_reason,
                s.reject_time
            );
---this temp table will take only valid row where the reject reason is null 
        CREATE TEMP TABLE valid_updates AS
        SELECT
            * EXCEPT(row_number)

        FROM (
            SELECT
                symbol,
                bronze_timestamp,
                timestamp,
                open,
                high,
                low,
                close,
                volume,
                trade_date,
    ---if same symbol timestamp present in bronze then it will take only lastest row 
                ROW_NUMBER() OVER (
                    PARTITION BY symbol, timestamp
                    ORDER BY bronze_timestamp
                ) AS row_number

            FROM bronze_candidates
            WHERE reject_reason IS NULL
        )
        ---take only lastest row for same symbol 
        WHERE row_number = 1;
---valid unique row count 
        SET records_processed = (
            SELECT COUNT(*)
            FROM valid_updates
        );
---count the duplilcate row which is already present in silver table 
        SET records_duplicate = records_read
            - records_rejected
            - records_processed;
---only process the valid updates if there are any records to process 
        IF records_processed > 0 THEN
            SET impacted_start = (
                SELECT MIN(bronze_timestamp)
                FROM valid_updates
            );
----impated end is max timestamp same for impacted start is min timestamp
            SET impacted_end = (
                SELECT MAX(bronze_timestamp)
                FROM valid_updates
            );
----impatecd symbol unique symbol which present in valid same for trade date 
            CREATE TEMP TABLE impacted_symbols AS
            SELECT DISTINCT symbol
            FROM valid_updates;

            CREATE TEMP TABLE impacted_dates AS
            SELECT DISTINCT trade_date
            FROM valid_updates;
----create a temp calculate for historical data fro last 100 days
            CREATE TEMP TABLE calc_input AS
            SELECT
                * EXCEPT(row_number)

            FROM (
                SELECT
                    b.symbol,
                    b.bronze_timestamp,
                    b.timestamp,
                    b.open,
                    b.high,
                    b.low,
                    b.close,
                    b.volume,
                    b.trade_date,
                    ROW_NUMBER() OVER (
                        PARTITION BY b.symbol, b.timestamp
                        ORDER BY b.timestamp
                    ) AS row_number

                FROM bronze_checked b
                INNER JOIN impacted_symbols i
                    ON i.symbol = b.symbol
                WHERE b.reject_reason IS NULL
                    AND b.bronze_timestamp BETWEEN
                --- it get data for last 100 days form start date to end date for impacted symbol 
                 ---beacuse indicator need histroical data to calculate values 
                        TIMESTAMP_SUB(impacted_start, INTERVAL 100 DAY)
                        AND impacted_end
            )
            WHERE row_number = 1;

            CREATE TEMP TABLE windowed_rows AS
            WITH lagged AS (
                SELECT
                    *,
                    ROW_NUMBER() OVER (
                        PARTITION BY symbol
                        ORDER BY timestamp
                    ) AS row_number,
                    --- gets the previous close value for each symbol to calculate returm and gap precentage
                    LAG(close) OVER (
                        PARTITION BY symbol
                        ORDER BY timestamp
                    ) AS previous_close

                FROM calc_input
            )

            SELECT
                *,
                SAFE_DIVIDE(
                    close - previous_close,
                    previous_close
                ) * 100 AS return_pct,
                SAFE_DIVIDE(
                    open - previous_close,
                    previous_close
                ) * 100 AS gap_pct,
                ---sma20 simple moviing avg for last 20 days for each symbol 
                AVG(close) OVER (
                    PARTITION BY symbol
                    ORDER BY timestamp
                    ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
                ) AS sma_20,
                AVG(volume) OVER (
                    PARTITION BY symbol
                    ORDER BY timestamp
                    ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
                ) AS avg_volume_20,
                AVG(GREATEST(close - previous_close, 0)) OVER (
                    PARTITION BY symbol
                    ORDER BY timestamp
                    ROWS BETWEEN 13 PRECEDING AND CURRENT ROW
                ) AS avg_gain_14,
                AVG(GREATEST(previous_close - close, 0)) OVER (
                    PARTITION BY symbol
                    ORDER BY timestamp
                    ROWS BETWEEN 13 PRECEDING AND CURRENT ROW
                ) AS avg_loss_14,
                SAFE_DIVIDE(
                    SUM(((high + low + close) / 3) * volume) OVER (
                        PARTITION BY symbol, trade_date
                        ORDER BY timestamp
                        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                    ),
                    SUM(volume) OVER (
                        PARTITION BY symbol, trade_date
                        ORDER BY timestamp
                        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                    )
                ) AS vwap

            FROM lagged;

            CREATE TEMP TABLE ema_rows AS
            SELECT
                symbol,
                timestamp,
                row_number,
                AVG(close) OVER (
                    PARTITION BY symbol
                    ORDER BY timestamp
                    ROWS BETWEEN 8 PRECEDING AND CURRENT ROW
                ) AS ema_9,
                AVG(close) OVER (
                    PARTITION BY symbol
                    ORDER BY timestamp
                    ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
                ) AS ema_20,
                AVG(close) OVER (
                    PARTITION BY symbol
                    ORDER BY timestamp
                    ROWS BETWEEN 11 PRECEDING AND CURRENT ROW
                )
                - AVG(close) OVER (
                    PARTITION BY symbol
                    ORDER BY timestamp
                    ROWS BETWEEN 25 PRECEDING AND CURRENT ROW
                ) AS macd

            FROM windowed_rows;

            CREATE TEMP TABLE macd_signal_rows AS
            SELECT
                symbol,
                timestamp,
                AVG(macd) OVER (
                    PARTITION BY symbol
                    ORDER BY row_number
                    ROWS BETWEEN 8 PRECEDING AND CURRENT ROW
                ) AS macd_signal

            FROM ema_rows;
---here all the calulated value are joined to create final silver talbe 

            CREATE TEMP TABLE silver_rows AS
            SELECT
                w.trade_date,
                w.symbol,
                w.timestamp,
                w.open,
                w.high,
                w.low,
                w.close,
                w.volume,
                w.previous_close,
                w.return_pct,
                w.gap_pct,
                w.sma_20,
                e.ema_9,
                e.ema_20,
                CASE
                    WHEN w.avg_loss_14 = 0 THEN 100
                    ELSE 100 - (
                        100 / (
                            1 + SAFE_DIVIDE(
                                w.avg_gain_14,
                                w.avg_loss_14
                            )
                        )
                    )
                END AS rsi_14,
                e.macd,
                m.macd_signal,
                w.vwap,
                w.avg_volume_20,
                SAFE_DIVIDE(
                    w.volume,
                    w.avg_volume_20
                ) AS relative_volume,
                ---stores the current timestamp when silver updated 
                CURRENT_TIMESTAMP() AS silver_updated_at
---we have read historical data for last 100 but we only need to update the impacted data in silver 
            FROM windowed_rows w
            INNER JOIN ema_rows e
                ON e.symbol = w.symbol
                AND e.timestamp = w.timestamp
            INNER JOIN macd_signal_rows m
                ON m.symbol = w.symbol
                AND m.timestamp = w.timestamp
            WHERE w.bronze_timestamp BETWEEN impacted_start AND impacted_end;
---check how many od the calulated rows are already in silver table 
            SET records_inserted = (
                SELECT COUNT(*)
                FROM silver_rows s
                LEFT JOIN `{{PROJECT_ID}}.{{SILVER_DATASET}}.silver_intraday_1m` t
                    ON t.symbol = s.symbol
                    AND t.timestamp = s.timestamp
                WHERE t.timestamp IS NULL
            );
--merge into the silver 1m table 
            MERGE `{{PROJECT_ID}}.{{SILVER_DATASET}}.silver_intraday_1m` t
            USING silver_rows s
            ON t.symbol = s.symbol
                AND t.timestamp = s.timestamp
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
                    sma_20 = s.sma_20,
                    ema_9 = s.ema_9,
                    ema_20 = s.ema_20,
                    rsi_14 = s.rsi_14,
                    macd = s.macd,
                    macd_signal = s.macd_signal,
                    vwap = s.vwap,
                    avg_volume_20 = s.avg_volume_20,
                    relative_volume = s.relative_volume,
                    silver_updated_at = s.silver_updated_at
            WHEN NOT MATCHED THEN
                INSERT
                (
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
                )
                VALUES
                (
                    s.trade_date,
                    s.symbol,
                    s.timestamp,
                    s.open,
                    s.high,
                    s.low,
                    s.close,
                    s.volume,
                    s.previous_close,
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
                    s.silver_updated_at
                );
----create a 5min temp table from 1min data 
            CREATE TEMP TABLE base_candles_5m AS
            SELECT
                trade_date,
                symbol,
                ---create the group of timestamp for 5min 
                DATETIME_ADD(
                    DATETIME_TRUNC(timestamp, HOUR),
                    INTERVAL (5 * DIV(EXTRACT(MINUTE FROM timestamp), 5)) MINUTE
                ) AS timestamp,
                ARRAY_AGG(open ORDER BY timestamp LIMIT 1)[OFFSET(0)] AS open,
                MAX(high) AS high,
                MIN(low) AS low,
                ARRAY_AGG(close ORDER BY timestamp DESC LIMIT 1)[OFFSET(0)] AS close,
                SUM(volume) AS volume

            FROM `{{PROJECT_ID}}.{{SILVER_DATASET}}.silver_intraday_1m`
            WHERE trade_date BETWEEN
                    DATE_SUB(
                        (
                            SELECT MIN(trade_date)
                            FROM impacted_dates
                        ),
                        INTERVAL 100 DAY
                    )
                    AND (
                        SELECT MAX(trade_date)
                        FROM impacted_dates
                    )
                AND symbol IN (
                    SELECT symbol
                    FROM impacted_symbols
                )
            GROUP BY
                trade_date,
                symbol,
                timestamp
                -- check if we have 5 rw for each 5min candele if not then it will not calculate
            HAVING COUNT(*) = 5;

            CREATE TEMP TABLE windowed_5m_rows AS
            WITH lagged AS (
                SELECT
                    *,
                    ROW_NUMBER() OVER (
                        PARTITION BY symbol
                        ORDER BY timestamp
                    ) AS row_number,
                    LAG(close) OVER (
                        PARTITION BY symbol
                        ORDER BY timestamp
                    ) AS previous_close

                FROM base_candles_5m
            )

            SELECT
                *,
                SAFE_DIVIDE(
                    close - previous_close,
                    previous_close
                ) * 100 AS return_pct,
                SAFE_DIVIDE(
                    open - previous_close,
                    previous_close
                ) * 100 AS gap_pct,
                AVG(close) OVER (
                    PARTITION BY symbol
                    ORDER BY timestamp
                    ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
                ) AS sma_20,
                AVG(volume) OVER (
                    PARTITION BY symbol
                    ORDER BY timestamp
                    ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
                ) AS avg_volume_20,
                AVG(GREATEST(close - previous_close, 0)) OVER (
                    PARTITION BY symbol
                    ORDER BY timestamp
                    ROWS BETWEEN 13 PRECEDING AND CURRENT ROW
                ) AS avg_gain_14,
                AVG(GREATEST(previous_close - close, 0)) OVER (
                    PARTITION BY symbol
                    ORDER BY timestamp
                    ROWS BETWEEN 13 PRECEDING AND CURRENT ROW
                ) AS avg_loss_14,
                SAFE_DIVIDE(
                    SUM(((high + low + close) / 3) * volume) OVER (
                        PARTITION BY symbol, trade_date
                        ORDER BY timestamp
                        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                    ),
                    SUM(volume) OVER (
                        PARTITION BY symbol, trade_date
                        ORDER BY timestamp
                        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                    )
                ) AS vwap

            FROM lagged;

            CREATE TEMP TABLE ema_5m_rows AS
            SELECT
                symbol,
                timestamp,
                row_number,
                AVG(close) OVER (
                    PARTITION BY symbol
                    ORDER BY timestamp
                    ROWS BETWEEN 8 PRECEDING AND CURRENT ROW
                ) AS ema_9,
                AVG(close) OVER (
                    PARTITION BY symbol
                    ORDER BY timestamp
                    ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
                ) AS ema_20,
                AVG(close) OVER (
                    PARTITION BY symbol
                    ORDER BY timestamp
                    ROWS BETWEEN 11 PRECEDING AND CURRENT ROW
                )
                - AVG(close) OVER (
                    PARTITION BY symbol
                    ORDER BY timestamp
                    ROWS BETWEEN 25 PRECEDING AND CURRENT ROW
                ) AS macd

            FROM windowed_5m_rows;

            CREATE TEMP TABLE macd_5m_signal_rows AS
            SELECT
                symbol,
                timestamp,
                AVG(macd) OVER (
                    PARTITION BY symbol
                    ORDER BY row_number
                    ROWS BETWEEN 8 PRECEDING AND CURRENT ROW
                ) AS macd_signal

            FROM ema_5m_rows;

            CREATE TEMP TABLE silver_5m_rows AS
            SELECT
                w.trade_date,
                w.symbol,
                w.timestamp,
                w.open,
                w.high,
                w.low,
                w.close,
                w.volume,
                w.previous_close,
                w.return_pct,
                w.gap_pct,
                w.sma_20,
                e.ema_9,
                e.ema_20,
                CASE
                    WHEN w.avg_loss_14 = 0 THEN 100
                    ELSE 100 - (
                        100 / (
                            1 + SAFE_DIVIDE(
                                w.avg_gain_14,
                                w.avg_loss_14
                            )
                        )
                    )
                END AS rsi_14,
                e.macd,
                m.macd_signal,
                w.vwap,
                w.avg_volume_20,
                SAFE_DIVIDE(
                    w.volume,
                    w.avg_volume_20
                ) AS relative_volume,
                CURRENT_TIMESTAMP() AS silver_updated_at

            FROM windowed_5m_rows w
            INNER JOIN ema_5m_rows e
                ON e.symbol = w.symbol
                AND e.timestamp = w.timestamp
            INNER JOIN macd_5m_signal_rows m
                ON m.symbol = w.symbol
                AND m.timestamp = w.timestamp
            WHERE w.trade_date IN (
                SELECT trade_date
                FROM impacted_dates
            );

            MERGE `{{PROJECT_ID}}.{{SILVER_DATASET}}.silver_intraday_5m` t
            USING silver_5m_rows s
            ON t.symbol = s.symbol
                AND t.timestamp = s.timestamp
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
                    sma_20 = s.sma_20,
                    ema_9 = s.ema_9,
                    ema_20 = s.ema_20,
                    rsi_14 = s.rsi_14,
                    macd = s.macd,
                    macd_signal = s.macd_signal,
                    vwap = s.vwap,
                    avg_volume_20 = s.avg_volume_20,
                    relative_volume = s.relative_volume,
                    silver_updated_at = s.silver_updated_at
            WHEN NOT MATCHED THEN
                INSERT
                (
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
                )
                VALUES
                (
                    s.trade_date,
                    s.symbol,
                    s.timestamp,
                    s.open,
                    s.high,
                    s.low,
                    s.close,
                    s.volume,
                    s.previous_close,
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
                    s.silver_updated_at
                );
---daily intraday data is calculated from 1min data and stored in silver daily dataset
            CREATE TEMP TABLE daily_calc_input AS
            SELECT
                trade_date,
                symbol,
                ---day start time and end time is used to get open and close price fro day 
                ARRAY_AGG(open ORDER BY timestamp LIMIT 1)[OFFSET(0)] AS open,
                MAX(high) AS high,
                MIN(low) AS low,
                ARRAY_AGG(close ORDER BY timestamp DESC LIMIT 1)[OFFSET(0)] AS close,
                SUM(volume) AS volume

            FROM `{{PROJECT_ID}}.{{SILVER_DATASET}}.silver_intraday_1m`
            WHERE trade_date BETWEEN
                    DATE_SUB(
                        (
                            SELECT MIN(trade_date)
                            FROM impacted_dates
                        ),
                        INTERVAL 40 DAY
                    )
                    AND (
                        SELECT MAX(trade_date)
                        FROM impacted_dates
                    )
                AND symbol IN (
                    SELECT symbol
                    FROM impacted_symbols
                )
            GROUP BY
                trade_date,
                symbol;

            CREATE TEMP TABLE daily_rows AS
            WITH daily_windowed AS (
                SELECT
                    *,
                    ---get previous close price for each symbol 
                    LAG(close) OVER (
                        PARTITION BY symbol
                        ORDER BY trade_date
                    ) AS previous_close,
                    AVG(volume) OVER (
                        PARTITION BY symbol
                        ORDER BY trade_date
                        ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
                    ) AS avg_volume_20

                FROM daily_calc_input
            )

            SELECT
                trade_date,
                symbol,
                open,
                high,
                low,
                close,
                volume,
                previous_close,
                SAFE_DIVIDE(
                    close - previous_close,
                    previous_close
                ) * 100 AS return_pct,
                SAFE_DIVIDE(
                    open - previous_close,
                    previous_close
                ) * 100 AS gap_pct,
                SAFE_DIVIDE(
                    high - low,
                    open
                ) * 100 AS daily_range_pct,
                avg_volume_20,
                SAFE_DIVIDE(
                    volume,
                    avg_volume_20
                ) AS relative_volume,
                CURRENT_TIMESTAMP() AS silver_updated_at

            FROM daily_windowed
            WHERE trade_date IN (
                SELECT trade_date
                FROM impacted_dates
            );

            MERGE `{{PROJECT_ID}}.{{SILVER_DATASET}}.silver_daily_stock` t
            USING daily_rows s
            ON t.symbol = s.symbol
                AND t.trade_date = s.trade_date
            WHEN MATCHED THEN
                UPDATE SET
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
                    silver_updated_at = s.silver_updated_at
            WHEN NOT MATCHED THEN
                INSERT
                (
                    trade_date,
                    symbol,
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
                    silver_updated_at
                )
                VALUES
                (
                    s.trade_date,
                    s.symbol,
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
                    s.silver_updated_at
                );
        END IF;

        INSERT INTO `{{PROJECT_ID}}.{{SILVER_DATASET}}.silver_audit`
        (
            run_id,
            run_start_time,
            run_end_time,
            status,
            records_read,
            records_processed,
            records_inserted,
            records_rejected,
            records_duplicate,
            error_message
        )
        VALUES
        (
            run_id,
            run_start_time,
            CURRENT_TIMESTAMP(),
            "SUCCESS",
            records_read,
            records_processed,
            records_inserted,
            records_rejected,
            records_duplicate,
            NULL
        );

    EXCEPTION WHEN ERROR THEN
        INSERT INTO `{{PROJECT_ID}}.{{SILVER_DATASET}}.silver_audit`
        (
            run_id,
            run_start_time,
            run_end_time,
            status,
            records_read,
            records_processed,
            records_inserted,
            records_rejected,
            records_duplicate,
            error_message
        )
        VALUES
        (
            run_id,
            run_start_time,
            CURRENT_TIMESTAMP(),
            "FAILED",
            records_read,
            records_processed,
            records_inserted,
            records_rejected,
            records_duplicate,
            @@error.message
        );

        RAISE;
    END;
END;
