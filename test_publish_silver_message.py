from src.messaging.publisher import (
    publish_bronze_batch_completed,
)


message_id = publish_bronze_batch_completed(
    batch_id="LIVE_TEST_BATCH_001",
    successful_files=1,
    failed_files=0,
    symbols=[
        "360ONE",
    ],
    load_type="HISTORICAL",
    start_date="2024-03-18",
    end_date="2024-03-18",
)


print(
    "Published message ID:",
    message_id,
)