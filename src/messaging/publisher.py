import json

from google.cloud import pubsub_v1

from src.utils.config import (
    GCP_PROJECT_ID,
    PUBSUB_BRONZE_TO_SILVER_TOPIC,
)

from src.messaging.topics import (
    SILVER_TIMEFRAME_COMPLETED,
)
publisher = pubsub_v1.PublisherClient()

def get_next_timeframe(current_timeframe):

    chain = {
        "1min": "5min",
        "5min": "15min",
        "15min": "1hour",
        "1hour": "daily",
        "daily": "COMPLETED"
    }

    return chain.get(
        current_timeframe,
        "UNKNOWN"
    )
def publish_bronze_batch_completed(
    batch_id: str,
    successful_files: int,
    failed_files: int,
    symbols: list[str],
    load_type: str,
    start_date: str | None = None,
    end_date: str | None = None,
):

    topic_path = publisher.topic_path(
        GCP_PROJECT_ID,
        PUBSUB_BRONZE_TO_SILVER_TOPIC,
    )

    message = {
        "event_type": "BRONZE_BATCH_COMPLETED",
        "batch_id": batch_id,
        "status": "SUCCESS",

        "bronze_table": (
            f"{GCP_PROJECT_ID}."
            "migration_bronze_v2.market_prices"
        ),

        "successful_files": successful_files,
        "failed_files": failed_files,
        "file_count": len(symbols),

        # Required by Silver
        "symbols": symbols,
        "load_type": load_type,
        "start_date": start_date,
        "end_date": end_date,
    }

    data = json.dumps(
        message
    ).encode("utf-8")

    future = publisher.publish(
        topic_path,
        data,
        batch_id=batch_id,
    )

    message_id = future.result()

    print(
        f"Pub/Sub message published: "
        f"{message_id}"
    )

    return message_id

"""def publish_silver_completed(
    topic_name,
    batch_id: str,
    symbols: list[str],
    timeframe: str,
    load_type: str,
    start_date: str | None = None,
    end_date: str | None = None,
):

    topic_path = publisher.topic_path(
    GCP_PROJECT_ID,
    SILVER_TIMEFRAME_COMPLETED,
    )


    message = {

        "event_type":
            "SILVER_TIMEFRAME_COMPLETED",

        "status":
            "SUCCESS",

        "batch_id":
            batch_id,

        "symbols":
            symbols,

        "timeframe":
            timeframe,

        "load_type":
            load_type,

        "start_date":
            start_date,

        "end_date":
            end_date,

    }


    data = json.dumps(
        message
    ).encode("utf-8")


    print("==============================")
    print("PUBLISHING NEXT SILVER EVENT")
    print(f"TIMEFRAME: {timeframe}")
    print(f"SYMBOL COUNT: {len(symbols)}")
    print(f"SYMBOLS: {symbols}")
    print("==============================")


    future = publisher.publish(
        topic_path,
        data,
        batch_id=batch_id,
    )


    message_id = future.result()


    print(
        f"Silver Pub/Sub message published: "
        f"{message_id}"
    )


    return message_id"""

def publish_silver_completed(
    topic_name,
    batch_id: str,
    symbols: list[str],
    timeframe: str,
    load_type: str,
    start_date: str | None = None,
    end_date: str | None = None,
):

    topic_path = publisher.topic_path(
        GCP_PROJECT_ID,
        SILVER_TIMEFRAME_COMPLETED,
    )


    message = {

        "event_type":
            "SILVER_TIMEFRAME_COMPLETED",

        "status":
            "SUCCESS",

        "batch_id":
            batch_id,

        "symbols":
            symbols,

        "timeframe":
            timeframe,

        "load_type":
            load_type,

        "start_date":
            start_date,

        "end_date":
            end_date,

    }


    data = json.dumps(
        message
    ).encode("utf-8")


    print("==============================")
    print("PUBLISHING SILVER TIMEFRAME EVENT")
    print(f"BATCH ID       : {batch_id}")
    print(f"COMPLETED      : {timeframe}")
    print(f"NEXT CHAIN     : {get_next_timeframe(timeframe)}")
    print(f"SYMBOL COUNT   : {len(symbols)}")
    print("==============================")


    future = publisher.publish(
        topic_path,
        data,
        batch_id=batch_id,
    )


    message_id = future.result()


    print(
        f"Silver Pub/Sub message published: {message_id}"
    )


    return message_id