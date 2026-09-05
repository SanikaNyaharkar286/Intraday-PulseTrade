from tools.intraday import analyze_intraday_history


result = analyze_intraday_history(
    intent="intraday_history",
    symbol="RELIANCE",
    limit=10
)


print(result)