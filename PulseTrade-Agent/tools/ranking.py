from typing import Optional, Literal

from config import PROJECT_ID, AI_DATASET
from tools.bigquery_client import execute_query


RankingIntent = Literal[
    "top_performers",
    "momentum_ranking",
    "volume_ranking",
    "trend_ranking"
]


def analyze_stock_ranking(
    intent: RankingIntent,
    direction: Optional[str] = None,
    limit: int = 20,
):

    """
    Analyze stock rankings.

    Source:
    spot_ai_stock_summary


    Supported intents:

    top_performers:
        Rank stocks by 90 day return.


    momentum_ranking:
        Rank stocks by momentum score.


    volume_ranking:
        Rank stocks by average volume.


    trend_ranking:
        Filter stocks by trend.


    Rules:
    - Only semantic summary table.
    - Read only.
    - Never SELECT *.
    """


    limit = max(1, min(limit, 50))


    table = (
        f"`{PROJECT_ID}.{AI_DATASET}."
        "spot_ai_stock_summary`"
    )


    # -----------------------------
    # Top performers
    # -----------------------------

    if intent == "top_performers":

        sql = f"""
        SELECT
            symbol,
            return_90d_pct,
            latest_close,
            latest_rsi,
            current_trend

        FROM {table}

        ORDER BY return_90d_pct DESC

        LIMIT {limit}
        """


        return execute_query(sql)



    # -----------------------------
    # Momentum ranking
    # -----------------------------

    if intent == "momentum_ranking":

        sql = f"""
        SELECT
            symbol,
            latest_momentum_score,
            latest_rsi,
            current_trend,
            return_90d_pct

        FROM {table}

        ORDER BY latest_momentum_score DESC

        LIMIT {limit}
        """


        return execute_query(sql)



    # -----------------------------
    # Volume ranking
    # -----------------------------

    if intent == "volume_ranking":

        sql = f"""
        SELECT
            symbol,
            avg_volume_90d,
            volume_status,
            current_trend

        FROM {table}

        ORDER BY avg_volume_90d DESC

        LIMIT {limit}
        """


        return execute_query(sql)



    # -----------------------------
    # Trend ranking
    # -----------------------------

    if intent == "trend_ranking":

        if not direction:
            direction = "BULLISH"


        sql = f"""
        SELECT
            symbol,
            current_trend,
            latest_momentum_score,
            return_90d_pct,
            latest_rsi

        FROM {table}

        WHERE current_trend = @trend

        ORDER BY latest_momentum_score DESC

        LIMIT {limit}
        """


        return execute_query(
            sql,
            parameters={
                "trend": direction.upper()
            }
        )


    raise ValueError(
        f"Unsupported ranking intent: {intent}"
    )