TIMEFRAME_CONFIG = {

    "1min": {

        "target_table": "silver_1min",

        "aggregation_required": False,

        "aggregation": 1,

        "source_table": "bronze_market_prices",

    },


    "5min": {

        "target_table": "silver_5min",

        "aggregation_required": True,

        "aggregation": 5,

        "source_table": "silver_1min",

    },


    "15min": {

        "target_table": "silver_15min",

        "aggregation_required": True,

        "aggregation": 15,

        "source_table": "silver_5min",

    },


    "1hr": {

        "target_table": "silver_1hour",

        "aggregation_required": True,

        "aggregation": 60,

        "source_table": "silver_15min",

    },


    "daily": {

        "target_table": "silver_daily",

        "aggregation_required": True,

        "aggregation": 1440,

        "source_table": "silver_1hour",

    }

}


def get_timeframe_config(timeframe: str) -> dict:

    timeframe = (
        timeframe
        .strip()
        .lower()
    )

    if timeframe not in TIMEFRAME_CONFIG:

        raise ValueError(
            f"Unsupported timeframe: {timeframe}"
        )

    return TIMEFRAME_CONFIG[timeframe]