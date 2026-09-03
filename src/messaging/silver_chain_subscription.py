from google.cloud import pubsub_v1

from src.messaging.silver_subscriber import (
    handle_silver_completed,
)

from src.utils.config import (
    GCP_PROJECT_ID,
)


SUBSCRIPTION_NAME = (
    "silver-timeframe-chain-sub"
)


def callback(
    message: pubsub_v1.subscriber.message.Message,
):

    print(
        "\n======================================"
    )

    print(
        "Silver timeframe event received"
    )

    print(
        f"Message ID: {message.message_id}"
    )

    print(
        "======================================"
    )


    try:

        handle_silver_completed(
            message.data
        )

        message.ack()


        print(
            f"Message ACKED: {message.message_id}"
        )


    except Exception as exc:

        print(
            "Silver chain failed"
        )

        print(exc)

        message.nack()



def start_silver_chain_subscriber():

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
        "Starting Silver chain subscriber..."
    )


    streaming_pull_future = (
    subscriber.subscribe(
        subscription_path,
        callback=callback,
        flow_control=pubsub_v1.types.FlowControl(
            max_messages=1
        ),
    )
)


    try:

        streaming_pull_future.result()

    except KeyboardInterrupt:

        streaming_pull_future.cancel()

    finally:

        subscriber.close()

if __name__ == "__main__":

    start_silver_chain_subscriber()