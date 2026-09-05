from tools.market_state import analyze_current_market


result = analyze_current_market(
    intent="symbol_overview",
    symbol="RELIANCE"
)


print(result)