from google.cloud import bigquery

PROJECT_ID = "project-001658fa-3ce5-4746-980"
DATASET = "migration_bronze_v2"
TABLE = "market_prices"
SYMBOL = "360ONE"
TABLE_REF = f"{PROJECT_ID}.{DATASET}.{TABLE}"


def run_check(client, title, query):
    job = client.query(
        query,
        location="us-east1",
        job_config=bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("symbol", "STRING", SYMBOL)
            ]
        ),
    )
    rows = list(job.result())

    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)

    if not rows:
        print("No rows returned.")
        return

    for row in rows:
        print(dict(row))


def validate_basic_ohlcv(client):
    query = f"""
    SELECT
      COUNT(*) AS total_rows,
      COUNTIF(date IS NULL) AS null_date,
      COUNTIF(symbol IS NULL OR TRIM(symbol) = '') AS null_symbol,
      COUNTIF(open IS NULL) AS null_open,
      COUNTIF(high IS NULL) AS null_high,
      COUNTIF(low IS NULL) AS null_low,
      COUNTIF(close IS NULL) AS null_close,
      COUNTIF(volume IS NULL) AS null_volume,
      COUNTIF(open < 0) AS negative_open,
      COUNTIF(high < 0) AS negative_high,
      COUNTIF(low < 0) AS negative_low,
      COUNTIF(close < 0) AS negative_close,
      COUNTIF(volume < 0) AS negative_volume,
      COUNTIF(open = 0) AS zero_open,
      COUNTIF(high = 0) AS zero_high,
      COUNTIF(low = 0) AS zero_low,
      COUNTIF(close = 0) AS zero_close,
      COUNTIF(volume = 0) AS zero_volume,
      COUNTIF(high < low) AS high_less_than_low,
      COUNTIF(open > high) AS open_above_high,
      COUNTIF(open < low) AS open_below_low,
      COUNTIF(close > high) AS close_above_high,
      COUNTIF(close < low) AS close_below_low,
      COUNTIF(
        open > 0 AND high > 0 AND low > 0 AND close > 0
        AND (
          high < open OR high < close
          OR low > open OR low > close
        )
      ) AS invalid_ohlc_relationship,
      COUNTIF(
        open = 0 AND high = 0 AND low = 0
        AND close = 0 AND volume = 0
      ) AS completely_zero_rows,
      COUNTIF(
        volume = 0
        AND open > 0 AND high > 0
        AND low > 0 AND close > 0
      ) AS zero_volume_valid_price_rows
    FROM `{TABLE_REF}`
    WHERE symbol = @symbol
    """
    run_check(client, "BASIC OHLCV VALIDATION", query)


def validate_duplicates(client):
    query = f"""
    SELECT
      COUNT(*) AS duplicate_symbol_timestamp_groups,
      COALESCE(SUM(row_count - 1), 0) AS duplicate_extra_rows
    FROM (
      SELECT symbol, date, COUNT(*) AS row_count
      FROM `{TABLE_REF}`
      WHERE symbol = @symbol
      GROUP BY symbol, date
      HAVING COUNT(*) > 1
    )
    """
    run_check(client, "DUPLICATE VALIDATION", query)


def validate_timestamp_precision(client):
    query = f"""
    SELECT
      COUNT(*) AS total_rows,
      COUNTIF(EXTRACT(SECOND FROM date) != 0) AS rows_with_seconds,
      COUNTIF(EXTRACT(MILLISECOND FROM date) != 0)
        AS rows_with_milliseconds,
      MIN(EXTRACT(SECOND FROM date)) AS min_second,
      MAX(EXTRACT(SECOND FROM date)) AS max_second
    FROM `{TABLE_REF}`
    WHERE symbol = @symbol
    """
    run_check(client, "TIMESTAMP PRECISION VALIDATION", query)


def validate_minute_collisions(client):
    query = f"""
    SELECT
      TIMESTAMP_TRUNC(date, MINUTE) AS minute_bucket,
      COUNT(*) AS rows_in_minute,
      MIN(date) AS first_timestamp,
      MAX(date) AS last_timestamp
    FROM `{TABLE_REF}`
    WHERE symbol = @symbol
    GROUP BY minute_bucket
    HAVING COUNT(*) > 1
    ORDER BY minute_bucket
    """
    run_check(client, "1-MINUTE BUCKET COLLISIONS", query)


def validate_timestamp_order(client):
    query = f"""
    WITH ordered AS (
      SELECT
        symbol,
        date,
        LAG(date) OVER (
          PARTITION BY symbol
          ORDER BY date
        ) AS previous_date
      FROM `{TABLE_REF}`
      WHERE symbol = @symbol
    )
    SELECT
      COUNTIF(
        previous_date IS NOT NULL
        AND date <= previous_date
      ) AS non_increasing_timestamps
    FROM ordered
    """
    run_check(client, "TIMESTAMP ORDER VALIDATION", query)


def validate_timestamp_gaps(client):
    query = f"""
    WITH ordered AS (
      SELECT
        symbol,
        date,
        LAG(date) OVER (
          PARTITION BY symbol
          ORDER BY date
        ) AS previous_date
      FROM `{TABLE_REF}`
      WHERE symbol = @symbol
    )
    SELECT
      COUNTIF(
        previous_date IS NOT NULL
        AND TIMESTAMP_DIFF(date, previous_date, MINUTE) > 1
      ) AS timestamp_gaps
    FROM ordered
    """
    run_check(client, "TIMESTAMP GAP VALIDATION", query)


def validate_zero_price_period(client):
    query = f"""
    SELECT
      MIN(date) AS first_zero_price,
      MAX(date) AS last_zero_price,
      COUNT(*) AS zero_price_rows
    FROM `{TABLE_REF}`
    WHERE symbol = @symbol
      AND (
        open = 0 OR high = 0
        OR low = 0 OR close = 0
      )
    """
    run_check(client, "ZERO-PRICE PERIOD VALIDATION", query)


def validate_nonzero_seconds(client):
    query = f"""
    SELECT
      date, symbol, open, high, low, close, volume
    FROM `{TABLE_REF}`
    WHERE symbol = @symbol
      AND EXTRACT(SECOND FROM date) != 0
    ORDER BY date
    LIMIT 100
    """
    run_check(client, "NON-ZERO-SECOND TIMESTAMP EXAMPLES", query)


def main():
    print("=" * 80)
    print("PULSETRADE BRONZE OHLCV EDGE-CASE VALIDATION")
    print("=" * 80)
    print(f"Project : {PROJECT_ID}")
    print(f"Table   : {TABLE_REF}")
    print(f"Symbol  : {SYMBOL}")

    client = bigquery.Client(
        project=PROJECT_ID,
        location="us-east1",
    )

    validate_basic_ohlcv(client)
    validate_duplicates(client)
    validate_timestamp_precision(client)
    validate_minute_collisions(client)
    validate_timestamp_order(client)
    validate_timestamp_gaps(client)
    validate_zero_price_period(client)
    validate_nonzero_seconds(client)

    print("\n" + "=" * 80)
    print("VALIDATION COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
