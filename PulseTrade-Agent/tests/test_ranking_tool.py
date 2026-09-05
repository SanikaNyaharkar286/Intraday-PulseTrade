from tools.ranking import analyze_stock_ranking


result = analyze_stock_ranking(
    intent="momentum_ranking",
    limit=10
)


print(result)