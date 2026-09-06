from bigquery.bigquery_client import execute_query


def analyze_stock_comparison(
    symbol1: str,
    symbol2: str,
    metric: str = "performance",
    days: int = 30
):

    if not symbol1 or not symbol2:
        raise ValueError(
            "Two symbols are required"
        )


    if metric == "performance":

        sql = f"""
        SELECT

            symbol,
            AVG(return_pct) AS avg_return_pct,
            AVG(relative_volume) AS avg_relative_volume,
            AVG(daily_range_pct) AS avg_daily_range_pct,
            AVG(rsi_14) AS avg_rsi

        FROM pulse_trade_ai_semantic.spot_ai_daily_history

        WHERE symbol IN (@symbol1,@symbol2)

        AND trade_date >= DATE_SUB(
            CURRENT_DATE(),
            INTERVAL @days DAY
        )

        GROUP BY symbol

        """


    elif metric == "vwap":

        sql = f"""
        SELECT

            symbol,
            AVG(vwap_deviation_pct) AS avg_vwap_deviation_pct

        FROM pulse_trade_ai_semantic.spot_ai_intraday_behavior

        WHERE symbol IN (@symbol1,@symbol2)

        AND trade_date >= DATE_SUB(
            CURRENT_DATE(),
            INTERVAL @days DAY
        )

        GROUP BY symbol

        """


    params = {

        "symbol1": symbol1.upper(),
        "symbol2": symbol2.upper(),
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
        "data": result

    }