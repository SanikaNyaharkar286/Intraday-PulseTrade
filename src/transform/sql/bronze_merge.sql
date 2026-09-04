MERGE `{bronze_table}` AS T

USING `{staging_table}` AS S

ON
    T.symbol = S.symbol
    AND T.timestamp = S.timestamp

WHEN MATCHED THEN

UPDATE SET
    open = S.open,
    high = S.high,
    low = S.low,
    close = S.close,
    volume = S.volume

WHEN NOT MATCHED THEN

INSERT
(
    timestamp,
    open,
    high,
    low,
    close,
    volume,
    symbol
)

VALUES
(
    S.timestamp,
    S.open,
    S.high,
    S.low,
    S.close,
    S.volume,
    S.symbol
)