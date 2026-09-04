import re

from agent.semantic_loader import (
    load_intents,
    load_metrics
)


class IntentRouter:

    def __init__(self):

        self.intents = load_intents()
        self.metrics = load_metrics()


    def route(self, question: str):

        question_lower = question.lower()


        # -------------------------
        # MARKET OVERVIEW
        # -------------------------

        if any(keyword in question_lower for keyword in [
            "market today",
            "market summary",
            "market sentiment",
            "how is market"
        ]):

            return {
                "intent": "MARKET_OVERVIEW",
                "view": "ai_vw_market_overview",
                "filters": []
            }



        # -------------------------
        # TOP GAINERS
        # -------------------------

        if any(keyword in question_lower for keyword in [
            "top gainers",
            "best stocks",
            "highest return"
        ]):

            return {
                "intent": "TOP_GAINERS",
                "view": "ai_vw_top_gainers",
                "filters": []
            }



        # -------------------------
        # TOP LOSERS
        # -------------------------

        if any(keyword in question_lower for keyword in [
            "top losers",
            "worst stocks",
            "lowest return"
        ]):

            return {
                "intent": "TOP_LOSERS",
                "view": "ai_vw_top_losers",
                "filters": []
            }



        # -------------------------
        # RSI SCANNER
        # -------------------------

        if "rsi" in question_lower:


            filters = []


            if (
                "below 30" in question_lower
                or "oversold" in question_lower
            ):

                filters.append(
                    {
                        "column": "rsi_oversold",
                        "operator": "=",
                        "value": True
                    }
                )


            elif (
                "above 70" in question_lower
                or "overbought" in question_lower
            ):

                filters.append(
                    {
                        "column": "rsi_overbought",
                        "operator": "=",
                        "value": True
                    }
                )


            return {
                "intent": "STOCK_SCREEN",
                "view": "ai_vw_scanner",
                "filters": filters
            }



        # -------------------------
        # VWAP SCANNER
        # -------------------------

        if "vwap" in question_lower:


            filters=[]


            if (
                "above" in question_lower
                or "breakout" in question_lower
            ):

                filters.append(
                    {
                        "column":"above_vwap",
                        "operator":"=",
                        "value":True
                    }
                )


            return {
                "intent":"STOCK_SCREEN",
                "view":"ai_vw_scanner",
                "filters":filters
            }



        # -------------------------
        # MACD SCANNER
        # -------------------------

        if "macd" in question_lower:


            filters=[]


            if (
                "bullish" in question_lower
                or "positive" in question_lower
            ):

                filters.append(
                    {
                        "column":"macd_bullish",
                        "operator":"=",
                        "value":True
                    }
                )


            return {
                "intent":"STOCK_SCREEN",
                "view":"ai_vw_scanner",
                "filters":filters
            }



        # -------------------------
        # STOCK ANALYSIS
        # -------------------------

        if any(symbol_word in question_lower for symbol_word in [
            "analyze",
            "analysis",
            "details",
            "technical"
        ]):

            return {
                "intent":"STOCK_ANALYSIS",
                "view":"ai_vw_stock_metrics",
                "filters":[]
            }



        # -------------------------
        # FALLBACK
        # -------------------------

        return {
            "intent":"UNKNOWN",
            "view":None,
            "filters":[]
        }