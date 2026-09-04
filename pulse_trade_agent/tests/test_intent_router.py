from agent.intent_router import IntentRouter


router = IntentRouter()



questions = [

    "How is market today?",

    "Show RSI below 30 stocks",

    "Find stocks above VWAP",

    "Show MACD bullish stocks",

    "Top gainers today",

    "Top losers today",

    "Analyze HDFC technical indicators",

    "What is the weather today?"

]


for q in questions:

    result = router.route(q)

    print("\nQuestion:")
    print(q)

    print("Result:")
    print(result)