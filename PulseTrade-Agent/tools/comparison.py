from tools.bigquery_client import execute_query


def analyze_stock_comparison(
    symbol1: str,
    symbol2: str,
    metric: str = "performance",
    days: int = 30
):
    """
    Compare two stocks.

    Supported metrics:
    - performance
    - vwap deviation

    Example:
    Compare HDFCBANK and ICICIBANK on VWAP deviation
    """

    if not symbol1 or not symbol2:
        raise ValueError(
            "Two symbols are required"
        )


    # Normalize Gemini input
    metric = metric.lower().strip()


    # Normalize symbols
    symbol1 = symbol1.upper().strip()
    symbol2 = symbol2.upper().strip()


    table_daily = (
        "`pulse_trade_ai_semantic."
        "spot_ai_daily_history`"
    )


    table_vwap = (
        "`pulse_trade_ai_semantic."
        "spot_ai_intraday_behavior`"
    )


    # ----------------------------------
    # Performance comparison
    # ----------------------------------

    if metric == "performance":

        sql = f"""
        SELECT

            symbol,

            AVG(return_pct)
                AS avg_return_pct,

            AVG(relative_volume)
                AS avg_relative_volume,

            AVG(daily_range_pct)
                AS avg_daily_range_pct,

            AVG(rsi_14)
                AS avg_rsi


        FROM {table_daily}


        WHERE symbol IN UNNEST(@symbols)


        AND trade_date >= DATE_SUB(
        (
            SELECT MAX(trade_date)
            FROM {table_vwap}
        ),
        INTERVAL @days DAY
    )


        GROUP BY symbol

        ORDER BY avg_return_pct DESC

        """


    # ----------------------------------
    # VWAP deviation comparison
    # ----------------------------------

    elif metric in [
            "vwap",
            "vwap deviation",
            "vwap_deviation",
            "vwap deviation pct",
            "vwap deviation percentage"
    ]:
        sql = f"""
            SELECT

                symbol,

                AVG(
                    SAFE_DIVIDE(
                        (close_price - avg_vwap),
                        avg_vwap
                    ) * 100
                ) AS avg_vwap_deviation_pct


            FROM {table_vwap}


            WHERE symbol IN UNNEST(@symbols)


            AND trade_date >= DATE_SUB(
            (
                SELECT MAX(trade_date)
                FROM {table_vwap}
            ),
            INTERVAL @days DAY
        )


            GROUP BY symbol

            ORDER BY avg_vwap_deviation_pct DESC

            """


    else:

        raise ValueError(
            f"Unsupported comparison metric: {metric}"
        )


    params = {

        "symbols": [
            symbol1,
            symbol2
        ],

        "days": days

    }


    result = execute_query(
        sql,
        parameters=params
    )


    return {

        "intent": "stock_comparison",

        "symbols": [
            symbol1,
            symbol2
        ],

        "metric": metric,

        "days": days,

        "records": len(result),

        "data": result

    }