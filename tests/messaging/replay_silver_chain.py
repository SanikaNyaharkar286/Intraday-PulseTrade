from src.messaging.publisher import (
    publish_silver_completed
)

from src.messaging.topics import (
    SILVER_TIMEFRAME_COMPLETED
)


publish_silver_completed(

    topic_name=SILVER_TIMEFRAME_COMPLETED,

    batch_id="BATCH_00001",

    symbols=[
        "3MINDIA",
        "AADHARHFC",
        "AARTIIND",
        "AAVAS",
        "ABB",
        "ABBOTINDIA",
        "ABCAPITAL",
        "ABDL"
    ],

    timeframe="1min",

    load_type="HISTORICAL",

    start_date=None,

    end_date=None,
)


print(
    "Silver 1min replay event published"
)