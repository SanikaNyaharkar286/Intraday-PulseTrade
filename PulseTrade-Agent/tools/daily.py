from typing import Optional, Literal

from config import PROJECT_ID, AI_DATASET
from tools.bigquery_client import execute_query


DailyIntent = Literal[
    "stock_performance",
    "stock_comparison",
    "return_ranking",
    "volatility_ranking",
    "price_history"
]


def analyze_daily_history(
        
    intent: DailyIntent,
    symbol: Optional[str] = None,
    symbols: Optional[list[str]] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 20,
):
    """
    Analyze historical daily stock performance.

    Source:
    spot_ai_daily_history


    Supported intents:

    stock_performance:
        Historical performance of one stock.

        Example:
        "How did <STOCK_SYMBOL> perform?"


    stock_comparison:
        Compare multiple stocks.

        Example:
        "Compare <STOCK_SYMBOL_1> and <STOCK_SYMBOL_2>"


    return_ranking:
        Rank stocks by return.

        Example:
        "Which stocks gave highest returns?"


    volatility_ranking:
        Rank stocks by volatility.

        Example:
        "Which stocks were most volatile?"


    price_history:
        Historical OHLC movement.

        Example:
        "Show price history of <STOCK_SYMBOL>"


    Rules:
    - Only semantic daily table.
    - Read only.
    - Never SELECT *
    - Never access Gold/Silver/Bronze.
    """


    limit = max(1, min(limit, 50))


    table = (
        f"`{PROJECT_ID}.{AI_DATASET}."
        "spot_ai_daily_history`"
    )


    # ---------------------------------
    # Single stock performance
    # ---------------------------------

    if intent == "stock_performance":

        if not symbol:
            raise ValueError(
                "symbol required"
            )


        sql = f"""
        SELECT
            symbol,
            trade_date,
            close,
            return_pct,
            gap_pct,
            daily_range_pct,
            relative_volume

        FROM {table}

        WHERE symbol = @symbol
        """


        if start_date:
            sql += """
            AND trade_date >= @start_date
            """


        if end_date:
            sql += """
            AND trade_date <= @end_date
            """


        sql += f"""
        ORDER BY trade_date DESC
        LIMIT {limit}
        """


        params = {
            "symbol": symbol.upper(),
            "limit": limit
        }


        if start_date:
            params["start_date"] = start_date

        if end_date:
            params["end_date"] = end_date


        result = execute_query(
            sql,
            parameters=params
        )
        if len(result) == 0:

            return {
                "error": "No historical data found",
                "symbol": symbol.upper(),
                "intent": intent,
                "action": "symbol_lookup_required"
            }

        return {
            "intent": intent,
            "source": "spot_ai_daily_history",
            "records": len(result),
            "data": result
        }


    # ---------------------------------
    # Compare stocks
    # ---------------------------------

    if intent == "stock_comparison":


        if not symbols:
            raise ValueError(
                "symbols required"
            )


        sql = f"""
        SELECT
            symbol,
            AVG(return_pct) AS avg_return_pct,
            AVG(daily_range_pct) AS avg_volatility,
            MAX(close) AS highest_close,
            MIN(close) AS lowest_close

        FROM {table}

        WHERE symbol IN UNNEST(@symbols)

        GROUP BY symbol

        ORDER BY avg_return_pct DESC

        """


        result = execute_query(
            sql,
            parameters=params
        )

        return {
            "intent": intent,
            "source": "spot_ai_daily_history",
            "records": len(result),
            "data": result
        }


    # ---------------------------------
    # Return ranking
    # ---------------------------------

    if intent == "return_ranking":


        sql = f"""
        SELECT
            symbol,
            AVG(return_pct) AS avg_return_pct,
            AVG(daily_range_pct) AS avg_daily_range

        FROM {table}

        GROUP BY symbol

        ORDER BY avg_return_pct DESC

        LIMIT {limit}
        """


        result = execute_query(
            sql,
            parameters=params
        )

        return {
            "intent": intent,
            "source": "spot_ai_daily_history",
            "records": len(result),
            "data": result
        }



    # ---------------------------------
    # Volatility ranking
    # ---------------------------------

    if intent == "volatility_ranking":


        sql = f"""
        SELECT
            symbol,
            AVG(daily_range_pct)
                AS avg_daily_range_pct,
            AVG(return_pct)
                AS avg_return_pct

        FROM {table}

        GROUP BY symbol

        ORDER BY avg_daily_range_pct DESC

        LIMIT {limit}
        """


        result = execute_query(
            sql,
            parameters=params
        )

        return {
            "intent": intent,
            "source": "spot_ai_daily_history",
            "records": len(result),
            "data": result
        }



    # ---------------------------------
    # Price history
    # ---------------------------------

    if intent == "price_history":


        if not symbol:
            raise ValueError(
                "symbol required"
            )


        sql = f"""
        SELECT
            symbol,
            trade_date,
            open,
            high,
            low,
            close,
            volume

        FROM {table}

        WHERE symbol = @symbol

        ORDER BY trade_date DESC

        LIMIT {limit}
        """


        result = execute_query(
            sql,
            parameters=params
        )
        if len(result) == 0:

            return {
                "error": "No data found for symbol",
                "symbol": symbol.upper(),
                "intent": intent,
                "action": "symbol_lookup_required"
            }

        return {
            "intent": intent,
            "source": "spot_ai_daily_history",
            "records": len(result),
            "data": result
        }

    raise ValueError(
        f"Unsupported daily intent: {intent}"
    )


