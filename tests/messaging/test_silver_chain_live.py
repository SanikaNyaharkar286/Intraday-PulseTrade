import json

from google.cloud import pubsub_v1

from src.utils.config import GCP_PROJECT_ID
from src.messaging.topics import SILVER_TIMEFRAME_COMPLETED


publisher = pubsub_v1.PublisherClient()


topic_path = publisher.topic_path(
    GCP_PROJECT_ID,
    SILVER_TIMEFRAME_COMPLETED
)


message = {

    "event_type":
        "SILVER_TIMEFRAME_COMPLETED",

    "status":
        "SUCCESS",

    "batch_id":
        "test_chain_001",

    "symbols":
        [
            "INFY",
            "TCS"
        ],

    "timeframe":
        "1min",

    "load_type":
        "HISTORICAL",

    "start_date":
        "2025-01-01",

    "end_date":
        "2025-01-31"

}


future = publisher.publish(

    topic_path,

    json.dumps(message).encode("utf-8")

)


print(
    "Published:",
    future.result()
)