from pathlib import Path
from datetime import datetime, timezone
import time

from google.cloud import bigquery

from transform.config import (
    AI_DATASET,
    AI_SEMANTIC_DATASET,
    AI_SNAPSHOT_LOOKBACK_DAYS,
    BQ_LOCATION,
    GOLD_DATASET,
    PROJECT_ID,
    SEMANTIC_DATASET,
    SILVER_DATASET,
)


_bq_client = None


def _format_int(value):
    if value is None:
        return "0"

    return f"{int(value):,}"


def _format_ts(value):
    if value is None:
        return "N/A"

    return str(value)


def get_bq_client():
    global _bq_client

    if _bq_client is None:
        _bq_client = bigquery.Client(
            project=PROJECT_ID,
            location=BQ_LOCATION
        )

    return _bq_client


def _sql_string(value):
    return "'" + str(value).replace("'", "''") + "'"


def _render_sql(
    sql,
    scope_symbol=None,
    scope_start=None,
    scope_end=None
):
    if scope_symbol and scope_start and scope_end:
        source_start = _sql_string(scope_start)
        source_end = _sql_string(scope_end)
        symbol = _sql_string(scope_symbol)

        silver_1m_source_filter = f"""
        WHERE symbol = {symbol}
            AND timestamp BETWEEN
                DATETIME(TIMESTAMP({source_start}), "Asia/Kolkata")
                AND DATETIME(TIMESTAMP({source_end}), "Asia/Kolkata")
        """

        silver_5m_source_filter = f"""
        WHERE symbol = {symbol}
            AND trade_date BETWEEN
                DATE(DATETIME(TIMESTAMP({source_start}), "Asia/Kolkata"))
                AND DATE(DATETIME(TIMESTAMP({source_end}), "Asia/Kolkata"))
        """

        gold_signal_scope_filter = f"""
        symbol = {symbol}
            AND trade_date BETWEEN
                DATE(DATETIME(TIMESTAMP({source_start}), "Asia/Kolkata"))
                AND DATE(DATETIME(TIMESTAMP({source_end}), "Asia/Kolkata"))
        """

        gold_signal_delete_scope_filter = f"""
        t.symbol = {symbol}
            AND t.trade_date BETWEEN
                DATE(DATETIME(TIMESTAMP({source_start}), "Asia/Kolkata"))
                AND DATE(DATETIME(TIMESTAMP({source_end}), "Asia/Kolkata"))
        """

        silver_daily_source_filter = f"""
        WHERE symbol = {symbol}
            AND trade_date BETWEEN
                DATE(DATETIME(TIMESTAMP({source_start}), "Asia/Kolkata"))
                AND DATE(DATETIME(TIMESTAMP({source_end}), "Asia/Kolkata"))
        """

        silver_daily_join_filter = f"""
            AND d.symbol = {symbol}
            AND d.trade_date BETWEEN
                DATE(DATETIME(TIMESTAMP({source_start}), "Asia/Kolkata"))
                AND DATE(DATETIME(TIMESTAMP({source_end}), "Asia/Kolkata"))
        """

        silver_daily_alias_source_filter = f"""
        s.symbol = {symbol}
            AND s.trade_date BETWEEN
                DATE(DATETIME(TIMESTAMP({source_start}), "Asia/Kolkata"))
                AND DATE(DATETIME(TIMESTAMP({source_end}), "Asia/Kolkata"))
        """

        gold_ai_intraday_scope_filter = f"""
        m.symbol = {symbol}
            AND m.trade_date BETWEEN
                DATE(DATETIME(TIMESTAMP({source_start}), "Asia/Kolkata"))
                AND DATE(DATETIME(TIMESTAMP({source_end}), "Asia/Kolkata"))
        """
        gold_ai_daily_scope_filter = f"""
        symbol = {symbol}
            AND trade_date BETWEEN
                DATE(DATETIME(TIMESTAMP({source_start}), "Asia/Kolkata"))
                AND DATE(DATETIME(TIMESTAMP({source_end}), "Asia/Kolkata"))
        """
        gold_ai_signal_scope_filter = f"""
        s.symbol = {symbol}
            AND s.trade_date BETWEEN
                DATE(DATETIME(TIMESTAMP({source_start}), "Asia/Kolkata"))
                AND DATE(DATETIME(TIMESTAMP({source_end}), "Asia/Kolkata"))
        """
        ai_signal_delete_scope_filter = f"t.symbol = {symbol}"

    else:
        silver_1m_source_filter = ""
        silver_5m_source_filter = ""
        gold_signal_scope_filter = "TRUE"
        gold_signal_delete_scope_filter = "TRUE"
        silver_daily_source_filter = ""
        silver_daily_join_filter = ""
        silver_daily_alias_source_filter = "TRUE"
        gold_ai_intraday_scope_filter = "TRUE"
        gold_ai_daily_scope_filter = "TRUE"
        gold_ai_signal_scope_filter = "TRUE"
        ai_signal_delete_scope_filter = "TRUE"

    values = {
        "PROJECT_ID": PROJECT_ID,
        "BQ_LOCATION": BQ_LOCATION,
        "SILVER_DATASET": SILVER_DATASET,
        "GOLD_DATASET": GOLD_DATASET,
        "AI_DATASET": AI_DATASET,
        "AI_SEMANTIC_DATASET": AI_SEMANTIC_DATASET,
        "AI_SNAPSHOT_LOOKBACK_DAYS": str(AI_SNAPSHOT_LOOKBACK_DAYS),
        "SEMANTIC_DATASET": SEMANTIC_DATASET,
        "SILVER_1M_SOURCE_FILTER": silver_1m_source_filter,
        "SILVER_5M_SOURCE_FILTER": silver_5m_source_filter,
        "GOLD_SIGNAL_SCOPE_FILTER": gold_signal_scope_filter,
        "GOLD_SIGNAL_DELETE_SCOPE_FILTER": gold_signal_delete_scope_filter,
        "SILVER_DAILY_SOURCE_FILTER": silver_daily_source_filter,
        "SILVER_DAILY_JOIN_FILTER": silver_daily_join_filter,
        "SILVER_DAILY_ALIAS_SOURCE_FILTER": silver_daily_alias_source_filter,
        "GOLD_AI_INTRADAY_SCOPE_FILTER": gold_ai_intraday_scope_filter,
        "GOLD_AI_DAILY_SCOPE_FILTER": gold_ai_daily_scope_filter,
        "GOLD_AI_SIGNAL_SCOPE_FILTER": gold_ai_signal_scope_filter,
        "AI_SIGNAL_DELETE_SCOPE_FILTER": ai_signal_delete_scope_filter,
    }

    for key, value in values.items():
        sql = sql.replace(
            "{{" + key + "}}",
            value
        )

    return sql


def _run_sql_file(
    sql_path,
    scope_symbol=None,
    scope_start=None,
    scope_end=None
):
    sql = _render_sql(
        sql_path.read_text(encoding="utf-8"),
        scope_symbol=scope_symbol,
        scope_start=scope_start,
        scope_end=scope_end
    )

    get_bq_client().query(
        sql
    ).result()


def _print_gold_input_summary(
    scope_symbol=None,
    scope_start=None,
    scope_end=None
):
    if scope_symbol and scope_start and scope_end:
        source_start = _sql_string(scope_start)
        source_end = _sql_string(scope_end)
        symbol = _sql_string(scope_symbol)

        intraday_filter = f"""
        WHERE symbol = {symbol}
            AND timestamp BETWEEN
                DATETIME(TIMESTAMP({source_start}), "Asia/Kolkata")
                AND DATETIME(TIMESTAMP({source_end}), "Asia/Kolkata")
        """

        date_filter = f"""
        WHERE symbol = {symbol}
            AND trade_date BETWEEN
                DATE(DATETIME(TIMESTAMP({source_start}), "Asia/Kolkata"))
                AND DATE(DATETIME(TIMESTAMP({source_end}), "Asia/Kolkata"))
        """

    else:
        print(
            "Gold input Silver summary skipped because no incremental "
            "scope was provided. This avoids full Silver COUNT(*) scans."
        )
        return

    query = f"""
    SELECT
        "silver_intraday_1m" AS table_name,
        COUNT(*) AS rows_total,
        COUNT(DISTINCT symbol) AS symbols_total,
        COUNT(DISTINCT trade_date) AS trade_dates_total,
        MIN(trade_date) AS first_trade_date,
        MAX(trade_date) AS last_trade_date
    FROM `{PROJECT_ID}.{SILVER_DATASET}.silver_intraday_1m`
    {intraday_filter}

    UNION ALL

    SELECT
        "silver_intraday_5m" AS table_name,
        COUNT(*) AS rows_total,
        COUNT(DISTINCT symbol) AS symbols_total,
        COUNT(DISTINCT trade_date) AS trade_dates_total,
        MIN(trade_date) AS first_trade_date,
        MAX(trade_date) AS last_trade_date
    FROM `{PROJECT_ID}.{SILVER_DATASET}.silver_intraday_5m`
    {date_filter}

    UNION ALL

    SELECT
        "silver_daily_stock" AS table_name,
        COUNT(*) AS rows_total,
        COUNT(DISTINCT symbol) AS symbols_total,
        COUNT(DISTINCT trade_date) AS trade_dates_total,
        MIN(trade_date) AS first_trade_date,
        MAX(trade_date) AS last_trade_date
    FROM `{PROJECT_ID}.{SILVER_DATASET}.silver_daily_stock`
    {date_filter}
    """

    rows = (
        get_bq_client()
        .query(query)
        .result()
    )

    print("Gold input Silver summary")

    for row in rows:
        print(
            "  "
            f"{row['table_name']}: "
            f"rows_to_process={_format_int(row['rows_total'])}, "
            f"symbols={_format_int(row['symbols_total'])}, "
            f"dates={_format_int(row['trade_dates_total'])}, "
            f"range={_format_ts(row['first_trade_date'])} "
            f"to {_format_ts(row['last_trade_date'])}"
        )


def _print_gold_output_summary():
    query = f"""
    SELECT "dim_stock" AS table_name, COUNT(*) AS rows_total
    FROM `{PROJECT_ID}.{GOLD_DATASET}.dim_stock`
    UNION ALL
    SELECT "dim_date", COUNT(*)
    FROM `{PROJECT_ID}.{GOLD_DATASET}.dim_date`
    UNION ALL
    SELECT "dim_timeframe", COUNT(*)
    FROM `{PROJECT_ID}.{GOLD_DATASET}.dim_timeframe`
    UNION ALL
    SELECT "fact_intraday_metrics", COUNT(*)
    FROM `{PROJECT_ID}.{GOLD_DATASET}.fact_intraday_metrics`
    UNION ALL
    SELECT "fact_intraday_signals", COUNT(*)
    FROM `{PROJECT_ID}.{GOLD_DATASET}.fact_intraday_signals`
    UNION ALL
    SELECT "fact_daily_market", COUNT(*)
    FROM `{PROJECT_ID}.{GOLD_DATASET}.fact_daily_market`
    UNION ALL
    SELECT "fact_stock_returns", COUNT(*)
    FROM `{PROJECT_ID}.{GOLD_DATASET}.fact_stock_returns`
    """

    rows = (
        get_bq_client()
        .query(query)
        .result()
    )

    print("Gold output summary")

    for row in rows:
        print(
            "  "
            f"{row['table_name']}: "
            f"rows_processed={_format_int(row['rows_total'])}"
        )


def _print_ai_serving_summary():
    query = f"""
    SELECT "ai_current_intraday_snapshot" AS table_name, COUNT(*) AS rows_total
    FROM `{PROJECT_ID}.{AI_DATASET}.ai_current_intraday_snapshot`
    UNION ALL
    SELECT "ai_current_signal_snapshot", COUNT(*)
    FROM `{PROJECT_ID}.{AI_DATASET}.ai_current_signal_snapshot`
    UNION ALL
    SELECT "ai_latest_daily_snapshot", COUNT(*)
    FROM `{PROJECT_ID}.{AI_DATASET}.ai_latest_daily_snapshot`
    """

    rows = (
        get_bq_client()
        .query(query)
        .result()
    )

    print("AI serving snapshot summary")

    for row in rows:
        print(
            "  "
            f"{row['table_name']}: "
            f"rows={_format_int(row['rows_total'])}"
        )


def _print_semantic_summary():
    query = f"""
    SELECT "spot_ai_current_market_state" AS table_name, COUNT(*) AS rows_total
    FROM `{PROJECT_ID}.{AI_SEMANTIC_DATASET}.spot_ai_current_market_state`
    UNION ALL
    SELECT "spot_ai_signal_history_90d", COUNT(*)
    FROM `{PROJECT_ID}.{AI_SEMANTIC_DATASET}.spot_ai_signal_history_90d`
    UNION ALL
    SELECT "spot_ai_intraday_history_90d", COUNT(*)
    FROM `{PROJECT_ID}.{AI_SEMANTIC_DATASET}.spot_ai_intraday_history_90d`
    UNION ALL
    SELECT "spot_ai_daily_history", COUNT(*)
    FROM `{PROJECT_ID}.{AI_SEMANTIC_DATASET}.spot_ai_daily_history`
    UNION ALL
    SELECT "spot_ai_intraday_behavior", COUNT(*)
    FROM `{PROJECT_ID}.{AI_SEMANTIC_DATASET}.spot_ai_intraday_behavior`
    UNION ALL
    SELECT "spot_ai_stock_summary", COUNT(*)
    FROM `{PROJECT_ID}.{AI_SEMANTIC_DATASET}.spot_ai_stock_summary`
    """

    rows = (
        get_bq_client()
        .query(query)
        .result()
    )

    print("Semantic view summary")

    for row in rows:
        print(
            "  "
            f"{row['table_name']}: "
            f"rows={_format_int(row['rows_total'])}"
        )


def _wait_for_job_with_progress(job, label):
    started_at = datetime.now(timezone.utc)

    print(f"{label} BigQuery job id: {job.job_id}")
    print(f"{label} start time: {started_at.isoformat()}")

    while not job.done():
        elapsed_minutes = (
            datetime.now(timezone.utc) - started_at
        ).total_seconds() / 60

        print(
            f"{label} still running: "
            f"{elapsed_minutes:.1f} minutes elapsed"
        )

        time.sleep(60)

        job.reload()

    result = job.result()
    ended_at = datetime.now(timezone.utc)
    elapsed_minutes = (
        ended_at - started_at
    ).total_seconds() / 60

    print(f"{label} end time: {ended_at.isoformat()}")
    print(f"{label} total time: {elapsed_minutes:.1f} minutes")

    return result


def ensure_gold_objects(
    scope_symbol=None,
    scope_start=None,
    scope_end=None
):
    sql_dir = Path(__file__).parent / "sql"

    _run_sql_file(
        sql_dir / "01_create_gold_tables.sql"
    )

    _run_sql_file(
        sql_dir / "02_sp_silver_to_gold.sql",
        scope_symbol=scope_symbol,
        scope_start=scope_start,
        scope_end=scope_end
    )


def ensure_ai_serving_objects(
    scope_symbol=None,
    scope_start=None,
    scope_end=None
):
    sql_dir = Path(__file__).parent / "sql"

    _run_sql_file(
        sql_dir / "04_create_ai_serving_tables.sql"
    )

    _run_sql_file(
        sql_dir / "05_sp_refresh_ai_serving.sql",
        scope_symbol=scope_symbol,
        scope_start=scope_start,
        scope_end=scope_end
    )


def refresh_ai_serving_snapshots():
    procedure_id = (
        f"`{PROJECT_ID}."
        f"{AI_DATASET}."
        "sp_refresh_ai_serving`"
    )

    job = get_bq_client().query(
        f"CALL {procedure_id}()"
    )

    _wait_for_job_with_progress(
        job,
        "AI serving refresh"
    )


def ensure_semantic_views():
    sql_dir = Path(__file__).parents[1] / "semantic" / "sql"

    _run_sql_file(
        sql_dir / "05_create_ai_semantic_tables.sql"
    )


def run_gold_pipeline(
    scope_symbol=None,
    scope_start=None,
    scope_end=None
):
    ensure_gold_objects(
        scope_symbol=scope_symbol,
        scope_start=scope_start,
        scope_end=scope_end
    )

    print("=" * 60)
    print("Gold pipeline starting")
    print("=" * 60)
    if scope_symbol and scope_start and scope_end:
        print("Gold incremental scope")
        print(f"  symbol: {scope_symbol}")
        print(f"  start: {scope_start}")
        print(f"  end: {scope_end}")

    _print_gold_input_summary(
        scope_symbol=scope_symbol,
        scope_start=scope_start,
        scope_end=scope_end
    )

    procedure_id = (
        f"`{PROJECT_ID}."
        f"{GOLD_DATASET}."
        "sp_silver_to_gold`"
    )

    job = get_bq_client().query(
        f"CALL {procedure_id}()"
    )

    _wait_for_job_with_progress(
        job,
        "Gold pipeline"
    )

    print(
        "Review changed BigQuery SQL and dry-run cost before running "
        "production refreshes."
    )

    # Disabled to avoid full-table COUNT(*) scans on large Gold tables.
    # _print_gold_output_summary()

    ensure_ai_serving_objects(
        scope_symbol=scope_symbol,
        scope_start=scope_start,
        scope_end=scope_end
    )

    refresh_ai_serving_snapshots()

    # AI snapshot tables are small, but keep summary counts disabled by default
    # while BigQuery spend is tight.
    # _print_ai_serving_summary()

    ensure_semantic_views()

    # Disabled to avoid full-view COUNT(*) scans over large Gold tables.
    # _print_semantic_summary()

    print(
        "Gold, AI serving, and Semantic pipeline completed"
    )
