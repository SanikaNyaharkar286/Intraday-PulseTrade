from tools.daily import analyze_daily_history


result = analyze_daily_history(
    intent="stock_performance",
    symbol="360ONE"
)

print(result)