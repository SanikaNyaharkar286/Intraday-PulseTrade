import json
from unittest.mock import patch


from src.messaging.silver_subscriber import (
    handle_bronze_batch_completed,
    handle_silver_completed,
)



# ======================================================
# Mock Silver Pipeline
# ======================================================

def mock_pipeline(
    client,
    symbol,
    load_type,
    start_date=None,
    end_date=None,
    timeframe="1min",
):

    print(
        f"RUNNING SILVER PIPELINE "
        f"| {symbol} | {timeframe}"
    )


    return {

        "symbol": symbol,

        "timeframe": timeframe,

        "status": "SUCCESS"

    }



# ======================================================
# Mock Publisher
# ======================================================

def mock_publish(
    topic_name,
    batch_id,
    symbols,
    timeframe,
    load_type,
    start_date=None,
    end_date=None,
):

    event = {

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


    print(
        "\nPUBLISHED EVENT"
    )

    print(
        json.dumps(
            event,
            indent=4
        )
    )


    return event



# ======================================================
# Full Flow Test
# ======================================================


def test_full_pubsub_flow():


    bronze_event = {


        "event_type":
            "BRONZE_BATCH_COMPLETED",


        "status":
            "SUCCESS",


        "batch_id":
            "batch_demo_001",


        "symbols":[

            "360ONE",

            "TCS",

            "INFY"

        ],


        "load_type":
            "HISTORICAL",


        "start_date":
            "2025-01-01",


        "end_date":
            "2025-01-31"

    }



    print(
        "\n========== BRONZE EVENT =========="
    )

    print(
        json.dumps(
            bronze_event,
            indent=4
        )
    )



    with patch(
        "src.messaging.silver_subscriber.run_silver_pipeline",
        side_effect=mock_pipeline
    ), patch(
        "src.messaging.silver_subscriber.publish_silver_completed",
        side_effect=mock_publish
    ), patch(
        "src.messaging.publisher.publish_silver_completed",
        side_effect=mock_publish
    ):


        # ----------------------------------
        # Bronze -> Silver 1min
        # ----------------------------------

        silver_event = (
            handle_bronze_batch_completed(
                json.dumps(
                    bronze_event
                ).encode("utf-8")
            )
        )



        print(
            "\n========== SILVER 1MIN RESULT =========="
        )

        print(
            json.dumps(
                silver_event,
                indent=4
            )
        )



        # ----------------------------------
        # Simulate receiving 1min completed
        # ----------------------------------

        next_event = {


            "event_type":
                "SILVER_TIMEFRAME_COMPLETED",


            "status":
                "SUCCESS",


            "batch_id":
                "batch_demo_001",


            "symbols":[

                "360ONE",

                "TCS",

                "INFY"

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
        current_event = next_event


        while current_event:


            current_event = handle_silver_completed(

                json.dumps(
                    current_event
                ).encode("utf-8")

            )

if __name__ == "__main__":

    test_full_pubsub_flow()