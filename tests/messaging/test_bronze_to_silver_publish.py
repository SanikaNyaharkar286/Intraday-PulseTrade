import json
from google.cloud import pubsub_v1

PROJECT_ID = "project-001658fa-3ce5-4746-980"

TOPIC = "bronze-v2-to-silver-v2"


publisher = pubsub_v1.PublisherClient()

topic_path = publisher.topic_path(
    PROJECT_ID,
    TOPIC
)


message = {

    "event_type": "BRONZE_BATCH_COMPLETED",

    "batch_id": "TEST_CHAIN_001",

    "status": "SUCCESS",

    "bronze_table":
        "project-001658fa-3ce5-4746-980.migration_bronze_v2.market_prices",

    "successful_files": 1,

    "failed_files": 0,

    "file_count": 1,

    "symbols": [
        "ABFRL"
    ],

    "load_type": "HISTORICAL",

    "start_date": None,

    "end_date": None
}


data = json.dumps(message).encode("utf-8")


future = publisher.publish(
    topic_path,
    data,
    batch_id="TEST_CHAIN_001"
)


print(
    "Published:",
    future.result()
)