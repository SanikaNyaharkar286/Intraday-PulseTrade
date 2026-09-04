import json

from google.cloud import pubsub_v1


PROJECT_ID = "project-001658fa-3ce5-4746-980"

TOPIC_NAME = "bronze-v2-to-silver-v2"


publisher = pubsub_v1.PublisherClient()


topic_path = publisher.topic_path(
    PROJECT_ID,
    TOPIC_NAME
)


# Missing symbols from validation query

symbols = [

    "APARINDS"

]


message = {


    "event_type":

        "BRONZE_BATCH_COMPLETED",


    "batch_id":

        "REPLAY_MISSING_SILVER_001",


    "status":

        "SUCCESS",


    "bronze_table":

        f"{PROJECT_ID}.migration_bronze_v2.market_prices",


    "successful_files":

        len(symbols),


    "failed_files":

        0,


    "file_count":

        len(symbols),


    "symbols":

        symbols,


    "load_type":

        "HISTORICAL",


    "start_date":

        None,


    "end_date":

        None

}



data = json.dumps(
    message
).encode("utf-8")



future = publisher.publish(

    topic_path,

    data,

    batch_id="REPLAY_MISSING_SILVER_001"

)



message_id = future.result()



print(
    "================================"
)

print(
    "Replay Bronze -> Silver Published"
)

print(
    f"Message ID: {message_id}"
)

print(
    f"Symbols: {len(symbols)}"
)

print(
    symbols
)

print(
    "================================"
)