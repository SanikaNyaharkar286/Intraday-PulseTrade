from typing import Optional, Literal

from config import PROJECT_ID, AI_DATASET
from tools.bigquery_client import execute_query


BehaviorIntent = Literal[
    "gap_screening",
    "vwap_hold_analysis",
    "breakout_screening",
    "breakdown_screening",
    "trend_behavior"
]


def analyze_intraday_behavior(
    intent: BehaviorIntent,
    threshold: Optional[float] = None,
    direction: Optional[str] = None,
    limit: int = 20,
):
    """
    Analyze intraday stock behavior.

    Source:
    spot_ai_intraday_behavior

    Supported intents:

    gap_screening:
        Find stocks with large gap movements.

    vwap_hold_analysis:
        Find stocks maintaining above VWAP.

    breakout_screening:
        Find stocks breaking daily highs.

    breakdown_screening:
        Find stocks breaking daily lows.

    trend_behavior:
        Analyze intraday trend.

    Rules:
    - Only semantic behavior table.
    - Read only.
    - Never SELECT *.
    - Never access Gold/Silver/Bronze.
    """

    limit = max(1, min(limit, 50))

    table = (
        f"`{PROJECT_ID}.{AI_DATASET}."
        "spot_ai_intraday_behavior`"
    )


    # -----------------------------
    # Gap Screening
    # -----------------------------

    if intent == "gap_screening":

        threshold = threshold or 3

        sql = f"""
        SELECT
            symbol,
            trade_date,
            gap_pct,
            open_price,
            previous_close,
            close_price,
            day_trend

        FROM {table}

        WHERE gap_pct >= @threshold

        ORDER BY gap_pct DESC

        LIMIT {limit}
        """

        return execute_query(
            sql,
            parameters={
                "threshold": threshold
            }
        )


    # -----------------------------
    # VWAP Hold Analysis
    # -----------------------------

    if intent == "vwap_hold_analysis":

        sql = f"""
        SELECT
            symbol,
            trade_date,
            vwap_hold_percentage,
            avg_vwap,
            close_price,
            day_trend

        FROM {table}

        WHERE trade_date = (
            SELECT MAX(trade_date)
            FROM {table}
        )

        ORDER BY vwap_hold_percentage DESC

        LIMIT {limit}
        """

        return execute_query(
            sql,
            parameters={}
        )


    # -----------------------------
    # Breakout Screening
    # -----------------------------

    if intent == "breakout_screening":

        sql = f"""
        SELECT
            symbol,
            trade_date,
            day_high,
            close_price,
            gap_pct,
            day_trend

        FROM {table}

        WHERE high_breakout_flag = TRUE

        ORDER BY trade_date DESC

        LIMIT {limit}
        """

        return execute_query(
            sql,
            parameters={}
        )


    # -----------------------------
    # Breakdown Screening
    # -----------------------------

    if intent == "breakdown_screening":

        sql = f"""
        SELECT
            symbol,
            trade_date,
            day_low,
            close_price,
            gap_pct,
            day_trend

        FROM {table}

        WHERE low_breakdown_flag = TRUE

        ORDER BY trade_date DESC

        LIMIT {limit}
        """

        return execute_query(
            sql,
            parameters={}
        )


    # -----------------------------
    # Trend Behavior
    # -----------------------------

    if intent == "trend_behavior":

        direction = (
            direction.upper()
            if direction
            else "BULLISH"
        )

        sql = f"""
        SELECT
            symbol,
            trade_date,
            day_trend,
            close_price,
            intraday_range_pct,
            vwap_hold_percentage

        FROM {table}

        WHERE day_trend = @trend

        AND trade_date = (
            SELECT MAX(trade_date)
            FROM {table}
        )

        ORDER BY intraday_range_pct DESC

        LIMIT {limit}
        """

        return execute_query(
            sql,
            parameters={
                "trend": direction
            }
        )


    raise ValueError(
        f"Unsupported behavior intent: {intent}"
    )