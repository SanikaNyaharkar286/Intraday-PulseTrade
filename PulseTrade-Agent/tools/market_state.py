from typing import Optional, Literal, get_args

from config import PROJECT_ID, AI_DATASET
from tools.bigquery_client import execute_query

MarketIntent = Literal[
    "symbol_overview",
    "rsi_screening",
    "momentum_ranking",
    "trend_screening",
    "volume_screening",
    "vwap_screening"
]

def analyze_current_market(
    intent: MarketIntent,
    symbol: Optional[str] = None,
    threshold: Optional[float] = None,
    direction: Optional[str] = None,
    limit: int = 20,
):

    allowed_intents = {
        "symbol_overview",
        "rsi_screening",
        "momentum_ranking",
        "trend_screening",
        "volume_screening",
        "vwap_screening"
    }

    if intent not in allowed_intents:
        raise ValueError(
            f"Unsupported intent: {intent}"
        )
    
    """
    Analyze the latest available market state.

    Use this tool ONLY for current/latest market questions.

    Supported intents:

    1. symbol_overview
       Use when user asks about one stock's current condition.
       Examples:
       Examples:
        - "What is <STOCK_SYMBOL> doing today?"
        - "What is the current RSI of <STOCK_SYMBOL>?"
        - "Is <STOCK_SYMBOL> above VWAP?"

    2. rsi_screening
       Use when user asks for stocks filtered by RSI.
       Examples:
       - "Which stocks have RSI below 30?"
       - "Find overbought stocks above RSI 70."

    3. momentum_ranking
       Use for strongest/weakest momentum ranking.
       Examples:
       - "Top 10 momentum stocks."
       - "Which stocks have the strongest momentum?"

    4. trend_screening
       Use for bullish/bearish/neutral stock screening.
       Examples:
       - "Which stocks are bullish today?"
       - "Show bearish stocks."

    5. volume_screening
       Use for current unusual/high/low volume questions.
       Examples:
       - "Which stocks have unusual volume?"
       - "Show high-volume stocks."

    6. vwap_screening
       Use for stocks above/below VWAP.
       Examples:
       - "Which stocks are above VWAP?"
       - "Show stocks below VWAP."

    Parameters:
        intent:
            One supported intent listed above.

        symbol:
            Optional stock symbol such as RELIANCE, TCS, INFY.

        threshold:
            Optional numeric threshold.
            Used mainly for RSI questions.

        direction:
            Optional categorical direction.
            Examples:
            BULLISH, BEARISH, ABOVE, BELOW,
            HIGH_VOLUME, LOW_VOLUME.

        limit:
            Maximum rows to return.
            Must remain reasonably small.

    Important:
    - This tool uses only the AI semantic current-state table.
    - It never queries Gold, Silver, Bronze, or dashboard views.
    - It never uses SELECT *.
    - It never executes write operations.
    """

    limit = max(1,min(limit,50))

    table = (
        f"`{PROJECT_ID}.{AI_DATASET}."
        "spot_ai_current_market_state`"
    )

    if intent == "symbol_overview":
        if not symbol:
            raise ValueError(
                "symbol is required for symbol_overview"
            )

        sql = f"""
        SELECT
            symbol,
            company_name,
            sector,
            trade_date,
            timestamp,
            close,
            day_return_pct,
            volume,
            relative_volume,
            rsi_14,
            macd,
            macd_signal,
            ema_9,
            ema_20,
            vwap,
            price_vs_vwap,
            price_vs_ema20,
            price_vs_sma20,
            volume_status,
            trend,
            momentum_score
        FROM {table}

        WHERE symbol = @symbol

        AND trade_date = (
            SELECT MAX(trade_date)
            FROM {table}
        )

        ORDER BY timestamp DESC

        LIMIT 1
        """

        result = execute_query(
            sql,
            parameters={
                "symbol": symbol.strip().upper()
            }
        )

        if not result:
            return {
                "status": "NO_DATA",
                "message": f"No market data found for {symbol.strip().upper()}",
                "data": []
            }

        return result

    if intent == "rsi_screening":
        if threshold is None:
            raise ValueError(
                "threshold is required for rsi_screening"
            )

        normalized_direction = (
            direction or "BELOW"
        ).upper()

        if normalized_direction == "BELOW":
            comparator = "<"
            order = "ASC"

        elif normalized_direction == "ABOVE":
            comparator = ">"
            order = "DESC"

        else:
            raise ValueError(
                "direction for RSI must be ABOVE or BELOW"
            )

        sql = f"""
        SELECT
            symbol,
            close,
            rsi_14,
            day_return_pct,
            trend,
            relative_volume
        FROM {table}
        WHERE rsi_14 {comparator} @threshold
        ORDER BY rsi_14 {order}
        LIMIT {limit}
        """

        return execute_query(
            sql,
            parameters={
                "threshold": threshold
            }
        )

    if intent == "momentum_ranking":
        normalized_direction = (
            direction or "HIGHEST"
        ).upper()

        order = (
            "DESC"
            if normalized_direction
            in ("HIGHEST", "STRONGEST", "TOP")
            else "ASC"
        )

        sql = f"""
            SELECT
                symbol,
                close,
                rsi_14,
                momentum_score,
                trend,
                relative_volume,
                volume_status
            FROM {table}
            ORDER BY momentum_score {order}
            LIMIT {limit}
        """
        return execute_query(sql)

    if intent == "trend_screening":
        normalized_direction = (
            direction or "BULLISH"
        ).upper()

        allowed = {
            "BULLISH",
            "BEARISH",
            "NEUTRAL",
        }

        if normalized_direction not in allowed:
            raise ValueError(
                "direction must be BULLISH, "
                "BEARISH, or NEUTRAL"
            )

        sql = f"""
        SELECT
            symbol,
            close,
            day_return_pct,
            rsi_14,
            trend,
            momentum_score,
            price_vs_vwap
        FROM {table}
        WHERE trend = @trend
        ORDER BY momentum_score DESC
        LIMIT {limit}
        """

        return execute_query(
            sql,
            parameters={
                "trend": normalized_direction
            }
        )

    if intent == "volume_screening":
        normalized_direction = (
            direction or "HIGH_VOLUME"
        ).upper()

        allowed = {
            "HIGH_VOLUME",
            "NORMAL_VOLUME",
            "LOW_VOLUME",
        }

        if normalized_direction not in allowed:
            raise ValueError(
                "direction must be HIGH_VOLUME, "
                "NORMAL_VOLUME, or LOW_VOLUME"
            )

        sql = f"""
        SELECT
            symbol,
            close,
            volume,
            relative_volume,
            volume_status,
            day_return_pct,
            trend
        FROM {table}
        WHERE volume_status = @volume_status
        ORDER BY relative_volume DESC
        LIMIT {limit}
        """

        return execute_query(
            sql,
            parameters={
                "volume_status": normalized_direction
            }
        )

    if intent == "vwap_screening":
        normalized_direction = (
            direction or "ABOVE"
        ).upper()

        allowed = {
            "ABOVE",
            "BELOW",
        }

        if normalized_direction not in allowed:
            raise ValueError(
                "direction must be ABOVE or BELOW"
            )

        sql = f"""
        SELECT
            symbol,
            close,
            vwap,
            price_vs_vwap,
            rsi_14,
            trend,
            momentum_score
        FROM {table}
        WHERE price_vs_vwap = @price_vs_vwap
        ORDER BY momentum_score DESC
        LIMIT {limit}
        """

        return execute_query(
            sql,
            parameters={
                "price_vs_vwap": normalized_direction
            }
        )

    raise ValueError(
        f"Unsupported market intent: {intent}"
    )



