def mock_run_silver_pipeline(
    symbol,
    timeframe
):

    print(
        f"Processing {symbol} -> {timeframe}"
    )

    return {

        "symbol": symbol,

        "timeframe": timeframe,

        "status": "SUCCESS"

    }