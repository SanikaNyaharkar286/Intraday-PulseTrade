import json

from src.messaging.silver_subscriber import (
    handle_bronze_batch_completed,
)


message = {
    "event_type": "BRONZE_BATCH_COMPLETED",
    "batch_id": "TEST_BATCH_001",
    "status": "SUCCESS",
    "bronze_table": (
        "project-001658fa-3ce5-4746-980."
        "migration_bronze_v2.market_prices"
    ),
    "successful_files": 1,
    "failed_files": 0,
    "symbols": [
        "360ONE",
    ],
    "load_type": "HISTORICAL",
    "start_date": "2024-03-18",
    "end_date": "2024-03-18",
}


message_data = json.dumps(
    message
).encode("utf-8")


result = handle_bronze_batch_completed(
    message_data
)


print("\n====================================")
print("SUBSCRIBER RESULT")
print("====================================")

print(result)