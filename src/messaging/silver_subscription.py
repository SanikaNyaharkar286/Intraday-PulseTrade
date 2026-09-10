from google.cloud import pubsub_v1

from src.messaging.silver_subscriber import (
    handle_bronze_batch_completed,
)

from src.utils.config import (
    GCP_PROJECT_ID,
)


# ==========================================================
# CONFIGURATION
# ==========================================================

SUBSCRIPTION_NAME = (
    "bronze-v2-to-silver-v2-sub"
)


# ==========================================================
# PUB/SUB CALLBACK
# ==========================================================

def callback(
    message: pubsub_v1.subscriber.message.Message,
):
    """
    Handle one Pub/Sub message.

    ACK:
        only after Silver processing succeeds.

    NACK:
        when processing fails so Pub/Sub
        can redeliver the message.
    """

    print(
        "\n======================================"
    )
    print(
        "Pub/Sub message received"
    )
    print(
        f"Message ID: {message.message_id}"
    )
    print(
        "======================================"
    )

    try:

        # Existing tested handler
        handle_bronze_batch_completed(
            message.data
        )

        # Only acknowledge when the entire
        # Silver processing finishes successfully.

        message.ack()

        print(
            f"Message ACKED: "
            f"{message.message_id}"
        )

    except Exception as exc:

        print(
            f"Message FAILED: "
            f"{message.message_id}"
        )

        print(
            f"Error: {exc}"
        )

        # Do not ACK a failed message.
        #
        # NACK allows Pub/Sub to redeliver it.

        message.nack()

        raise


# ==========================================================
# START SUBSCRIBER
# ==========================================================

def start_silver_subscriber():
    """
    Start listening for Bronze -> Silver
    Pub/Sub messages.
    """

    subscriber = (
        pubsub_v1.SubscriberClient()
    )

    subscription_path = (
        subscriber.subscription_path(
            GCP_PROJECT_ID,
            SUBSCRIPTION_NAME,
        )
    )

    print(
        "Starting Silver subscriber..."
    )

    print(
        f"Project: {GCP_PROJECT_ID}"
    )

    print(
        f"Subscription: "
        f"{SUBSCRIPTION_NAME}"
    )

    streaming_pull_future = (
    subscriber.subscribe(
        subscription_path,
        callback=callback,
        flow_control=pubsub_v1.types.FlowControl(
            max_messages=1
            )
        )
    )

    print(
        "\nWaiting for Bronze completion "
        "messages..."
    )

    try:

        streaming_pull_future.result()

    except KeyboardInterrupt:

        print(
            "\nStopping Silver subscriber..."
        )

        streaming_pull_future.cancel()

        streaming_pull_future.result()

    finally:

        subscriber.close()

if __name__ == "__main__":
    start_silver_subscriber()