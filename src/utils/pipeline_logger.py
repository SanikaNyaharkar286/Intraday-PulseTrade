from datetime import datetime


def pipeline_log(
    stage,
    batch_id=None,
    symbol=None,
    status="INFO",
    message=""
):

    print("\n" + "=" * 60)

    print("PIPELINE STATUS")

    print("=" * 60)

    print(
        f"Stage      : {stage}"
    )

    print(
        f"Batch ID   : {batch_id}"
    )

    print(
        f"Symbol     : {symbol}"
    )

    print(
        f"Status     : {status}"
    )

    print(
        f"Time       : {datetime.utcnow()}"
    )

    if message:
        print(
            f"Message    : {message}"
        )

    print("=" * 60)