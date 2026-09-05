from typing import Optional, Literal

from config import PROJECT_ID, AI_DATASET
from tools.bigquery_client import execute_query


IntradayIntent = Literal[
    "intraday_history",
    "indicator_history",
    "timeframe_analysis"
]


def analyze_intraday_history(
    intent: IntradayIntent,
    symbol: Optional[str] = None,
    timeframe: Optional[str] = None,
    indicator: Optional[str] = None,
    limit: int = 100,
):

    """
    Analyze intraday historical price movement.

    Source:
    spot_ai_intraday_history_90d


    Supported intents:

    intraday_history:
        Fetch intraday OHLC history.

        Example:
        "Show RELIANCE intraday history"


    indicator_history:
        Analyze indicator movement.

        Example:
        "Show TCS RSI history"


    timeframe_analysis:
        Analyze specific timeframe.

        Example:
        "Show 5 minute data"


    Rules:
    - Only semantic intraday table.
    - Read only.
    - Never SELECT *.
    - Never access Gold/Silver/Bronze.
    """


    limit = max(1, min(limit, 200))


    table = (
        f"`{PROJECT_ID}.{AI_DATASET}."
        "spot_ai_intraday_history_90d`"
    )


    # -----------------------------
    # Intraday history
    # -----------------------------

    if intent == "intraday_history":

        if not symbol:
            raise ValueError(
                "symbol required for intraday_history"
            )


        sql = f"""
        SELECT
            symbol,
            trade_date,
            timestamp,
            timeframe,
            open,
            high,
            low,
            close,
            volume,
            relative_volume

        FROM {table}

        WHERE symbol = @symbol

        ORDER BY timestamp DESC

        LIMIT {limit}
        """


        return execute_query(
            sql,
            parameters={
                "symbol": symbol.upper()
            }
        )



    # -----------------------------
    # Indicator history
    # -----------------------------

    if intent == "indicator_history":

        if not symbol:
            raise ValueError(
                "symbol required for indicator_history"
            )


        allowed_indicators = {
            "rsi_14",
            "macd",
            "ema_9",
            "ema_20",
            "vwap",
            "relative_volume"
        }


        if indicator not in allowed_indicators:
            raise ValueError(
                f"Unsupported indicator: {indicator}"
            )


        sql = f"""
        SELECT
            symbol,
            trade_date,
            timestamp,
            timeframe,
            {indicator}

        FROM {table}

        WHERE symbol = @symbol

        ORDER BY timestamp DESC

        LIMIT {limit}
        """


        return execute_query(
            sql,
            parameters={
                "symbol": symbol.upper()
            }
        )



    # -----------------------------
    # Timeframe analysis
    # -----------------------------

    if intent == "timeframe_analysis":

        if not timeframe:
            raise ValueError(
                "timeframe required"
            )


        sql = f"""
        SELECT
            symbol,
            trade_date,
            timestamp,
            timeframe,
            close,
            rsi_14,
            macd,
            ema_9,
            ema_20,
            vwap,
            relative_volume

        FROM {table}

        WHERE timeframe = @timeframe

        ORDER BY timestamp DESC

        LIMIT {limit}
        """


        return execute_query(
            sql,
            parameters={
                "timeframe": timeframe.upper()
            }
        )


    raise ValueError(
        f"Unsupported intraday intent: {intent}"
    )