from typing import Optional, Literal

from config import PROJECT_ID, AI_DATASET
from tools.bigquery_client import execute_query


SignalIntent = Literal[
    "latest_signal",
    "signal_screening",
    "stock_signal_history",
    "timeframe_signal_analysis"
]


VALID_SIGNALS = {
    "DAY_HIGH_BREAKOUT",
    "EMA_BEARISH_CROSSOVER",
    "VOLUME_BREAKOUT",
    "EMA_BULLISH_CROSSOVER",
    "MACD_BEARISH_CROSSOVER",
    "MACD_BULLISH_CROSSOVER",
    "VWAP_CROSS_DOWN",
    "DAY_LOW_BREAKDOWN",
    "VWAP_CROSS_UP"
}


def analyze_signals(
    intent: SignalIntent,
    symbol: Optional[str] = None,
    signal_type: Optional[str] = None,
    timeframe: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 20,
):
    """
    Analyze technical trading signals.

    Source:
    spot_ai_signal_history_90d


    Supported intents:

    latest_signal:
        Latest signal for a stock.

        Example:
        "What is the latest signal for <STOCK_SYMBOL>?"


    signal_screening:
        Find stocks having a specific signal.

        Example:
        "Which stocks have MACD bullish crossover?"


    stock_signal_history:
        Historical signals for one stock.

        Example:
        "Show <STOCK_SYMBOL> breakout signals last month"


    timeframe_signal_analysis:
        Analyze signals for specific timeframe.

        Example:
        "Show 5 minute EMA crossovers"


    Rules:
    - Only semantic signal table is used.
    - Never query gold/silver/bronze.
    - Never use SELECT *.
    - Read only.
    """


    limit = max(1, min(limit, 50))


    table = (
        f"`{PROJECT_ID}.{AI_DATASET}."
        "spot_ai_signal_history_90d`"
    )


    # -------------------------------
    # Input validation
    # -------------------------------

    if signal_type:

        signal_type = signal_type.upper()

        if signal_type not in VALID_SIGNALS:
            raise ValueError(
                f"Unsupported signal type: {signal_type}"
            )


    # -------------------------------
    # Latest signal
    # -------------------------------

    if intent == "latest_signal":

        if not symbol:
            raise ValueError(
                "symbol is required"
            )


        sql = f"""
        SELECT
            symbol,
            trade_date,
            timestamp,
            timeframe,
            signal_type,
            signal_value,
            reference_value

        FROM {table}

        WHERE symbol = @symbol

        ORDER BY
            trade_date DESC,
            timestamp DESC

        LIMIT 1
        """


        return execute_query(
            sql,
            parameters={
                "symbol": symbol.strip().upper()
            }
        )


    # -------------------------------
    # Signal screening
    # -------------------------------

    if intent == "signal_screening":

        if not signal_type:
            raise ValueError(
                "signal_type is required"
            )


        sql = f"""
        SELECT
            symbol,
            trade_date,
            timestamp,
            timeframe,
            signal_type,
            signal_value,
            reference_value

        FROM {table}

        WHERE signal_type = @signal_type

        AND trade_date = (
            SELECT MAX(trade_date)
            FROM {table}
        )

        ORDER BY timestamp DESC

        LIMIT 20
        """


        return execute_query(
            sql,
            parameters={
                "signal_type": signal_type
            }
        )


    # -------------------------------
    # Stock signal history
    # -------------------------------

    if intent == "stock_signal_history":

        if not symbol:
            raise ValueError(
                "symbol is required"
            )


        conditions = [
            "symbol = @symbol"
        ]


        parameters = {
            "symbol": symbol.strip().upper()
        }


        if signal_type:

            conditions.append(
                "signal_type = @signal_type"
            )

            parameters["signal_type"] = signal_type


        if start_date:

            conditions.append(
                "trade_date >= @start_date"
            )

            parameters["start_date"] = start_date


        if end_date:

            conditions.append(
                "trade_date <= @end_date"
            )

            parameters["end_date"] = end_date


        where_clause = " AND ".join(
            conditions
        )


        sql = f"""
        SELECT
            symbol,
            trade_date,
            timestamp,
            timeframe,
            signal_type,
            signal_value,
            reference_value

        FROM {table}

        WHERE {where_clause}

        ORDER BY timestamp DESC

        LIMIT {limit}
        """


        return execute_query(
            sql,
            parameters=parameters
        )


    # -------------------------------
    # Timeframe analysis
    # -------------------------------

    if intent == "timeframe_signal_analysis":

        if not timeframe:
            raise ValueError(
                "timeframe is required"
            )


        if not signal_type:
            raise ValueError(
                "signal_type is required"
            )


        sql = f"""
        SELECT
            symbol,
            trade_date,
            timestamp,
            timeframe,
            signal_type,
            signal_value

        FROM {table}

        WHERE timeframe = @timeframe

        AND signal_type = @signal_type

        ORDER BY timestamp DESC

        LIMIT {limit}
        """


        return execute_query(
            sql,
            parameters={
                "timeframe": timeframe,
                "signal_type": signal_type
            }
        )


    raise ValueError(
        f"Unsupported signal intent: {intent}"
    )