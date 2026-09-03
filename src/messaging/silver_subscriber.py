import json

from google.cloud import bigquery
from concurrent.futures import ThreadPoolExecutor, as_completed
from src.transform.silver.pipeline import (
    run_silver_pipeline,
)

from src.messaging.publisher import (
    publish_silver_completed,
)
from src.messaging.topics import (
    SILVER_TIMEFRAME_COMPLETED,
)
"""from src.messaging.topics import (
    SILVER_1MIN_COMPLETED,
    SILVER_5MIN_COMPLETED,
    SILVER_15MIN_COMPLETED,
    SILVER_1HR_COMPLETED,
    SILVER_DAILY_COMPLETED,
)
"""

# ==========================================================
# HANDLE BRONZE -> SILVER MESSAGE
# ==========================================================
def process_silver_symbol(
    symbol,
    batch_id,
    load_type,
    start_date,
    end_date,
):
    """
    Process one symbol independently for Silver 1min.
    """

    client = bigquery.Client()

    print(
        f"\n[{batch_id}] "
        f"Processing Silver 1min for {symbol}"
    )


    result = run_silver_pipeline(

        client=client,

        symbol=symbol,

        load_type=load_type,

        start_date=start_date,

        end_date=end_date,

        timeframe="1min",

    )


    print(
        f"[{batch_id}] "
        f"{symbol} completed"
    )


    return result

def process_silver_timeframe_symbol(
    symbol,
    batch_id,
    load_type,
    start_date,
    end_date,
    timeframe,
):
    """
    Process one symbol for next silver timeframe.
    """

    client = bigquery.Client()


    print(
        f"[{batch_id}] "
        f"Processing {timeframe} for {symbol}"
    )


    result = run_silver_pipeline(

        client=client,

        symbol=symbol,

        load_type=load_type,

        start_date=start_date,

        end_date=end_date,

        timeframe=timeframe,

    )


    print(
        f"[{batch_id}] "
        f"{symbol} {timeframe} completed"
    )


    return result
def handle_bronze_batch_completed(
    message_data: bytes,
) -> list[dict]:
    """
    Handle BRONZE_BATCH_COMPLETED Pub/Sub message.

    One Bronze batch may contain multiple symbols.

    The complete batch is processed first.
    Only after all symbols succeed,
    Silver completion event is published.
    """

    payload = json.loads(
        message_data.decode("utf-8")
    )

    print(
        "Received Bronze -> Silver message:"
    )

    print(payload)


    # ======================================================
    # VALIDATE EVENT TYPE
    # ======================================================

    event_type = payload.get(
        "event_type"
    )

    if event_type != "BRONZE_BATCH_COMPLETED":

        raise ValueError(
            f"Unsupported event_type: {event_type}"
        )


    # ======================================================
    # VALIDATE STATUS
    # ======================================================

    status = payload.get(
        "status"
    )

    if status != "SUCCESS":

        raise ValueError(
            f"Bronze batch failed. Status: {status}"
        )


    # ======================================================
    # MESSAGE VALUES
    # ======================================================

    batch_id = payload.get(
        "batch_id"
    )

    symbols = payload.get(
        "symbols",
        []
    )

    load_type = payload.get(
        "load_type"
    )

    start_date = payload.get(
        "start_date"
    )

    end_date = payload.get(
        "end_date"
    )


    # ======================================================
    # VALIDATION
    # ======================================================

    if not batch_id:

        raise ValueError(
            "batch_id is required"
        )


    if not symbols:

        raise ValueError(
            "symbols are required"
        )


    if not load_type:

        raise ValueError(
            "load_type is required"
        )


    # ======================================================
    # BIGQUERY CLIENT
    # ======================================================

    #client = bigquery.Client()


    results = []

    MAX_SILVER_WORKERS = 6


    with ThreadPoolExecutor(
        max_workers=MAX_SILVER_WORKERS
    ) as executor:


        futures = []


        for symbol in symbols:

            futures.append(

                executor.submit(

                    process_silver_symbol,

                    symbol,

                    batch_id,

                    load_type,

                    start_date,

                    end_date,

                )
            )


        for future in as_completed(futures):

            try:

                results.append(
                    future.result()
                )


            except Exception as exc:

                print(
                    f"[{batch_id}] "
                    f"Silver worker failed: {exc}"
                )

                raise



    # ======================================================
    # PUBLISH ONLY AFTER COMPLETE BATCH SUCCESS
    # ======================================================


    


    message_id = publish_silver_completed(

    topic_name=SILVER_TIMEFRAME_COMPLETED,

    batch_id=batch_id,

    symbols=symbols,

    timeframe="1min",

    load_type=load_type,

    start_date=start_date,

    end_date=end_date,

)
    print(
        "\nSILVER 1MIN COMPLETION EVENT PUBLISHED"
    )

    print(
    f"Message ID: {message_id}"
    )



    print(
        f"\n[{batch_id}] "
        f"Silver 1min batch completed "
        f"for {len(results)} symbols"
    )


    return results





# ==========================================================
# HANDLE SILVER TIMEFRAME COMPLETION
# ==========================================================

def handle_silver_completed(
    message_data: bytes
):

    """
    Handles:

    1min -> 5min
    5min -> 15min
    15min -> 1hr
    1hr -> daily

    Processing happens batch-wise.
    """


    payload = json.loads(
        message_data.decode("utf-8")
    )


    print(
        "Received Silver completion event:"
    )

    print(payload)



    batch_id = payload.get(
        "batch_id"
    )


    symbols = payload.get(
        "symbols",
        []
    )


    load_type = payload.get(
        "load_type"
    )


    start_date = payload.get(
        "start_date"
    )


    end_date = payload.get(
        "end_date"
    )


    timeframe = payload.get(
        "timeframe"
    )


    if not batch_id:
        raise ValueError(
            "batch_id is required"
        )


    if not symbols:
        raise ValueError(
            "symbols are required"
        )


    if not timeframe:
        raise ValueError(
            "timeframe is required"
        )
    
    next_timeframe = get_next_timeframe(
        timeframe
    )


    if next_timeframe is None:

        print(
            f"{batch_id} completed final timeframe"
        )

        return



    #client = bigquery.Client()



    results = []

    MAX_SILVER_WORKERS = 6


    with ThreadPoolExecutor(
        max_workers=MAX_SILVER_WORKERS
    ) as executor:


        futures = []


        for symbol in symbols:

            futures.append(

                executor.submit(

                    process_silver_timeframe_symbol,

                    symbol,

                    #client,

                    batch_id,

                    load_type,

                    start_date,

                    end_date,

                    next_timeframe,

                )

            )


        for future in as_completed(futures):

            try:

                results.append(
                    future.result()
                )


            except Exception as exc:

                print(
                    f"[{batch_id}] "
                    f"{next_timeframe} worker failed: {exc}"
                )

                raise

    print(
        f"[{batch_id}] "
        f"{next_timeframe} completed "
        f"for {len(results)} symbols"
    )



    # Publish next timeframe event

    return publish_next_timeframe_event(
    batch_id=batch_id,
    symbols=symbols,
    timeframe=next_timeframe,
    load_type=load_type,
    start_date=start_date,
    end_date=end_date,
    )





# ==========================================================
# TIMEFRAME ROUTING
# ==========================================================

def get_next_timeframe(
    timeframe: str
):

    flow = {

        "1min": "5min",

        "5min": "15min",

        "15min": "1hr",

        "1hr": "daily",

        "daily": None,

    }


    return flow.get(
        timeframe
    )





# ==========================================================
# PUBLISH NEXT EVENT
# ==========================================================

def publish_next_timeframe_event(
    batch_id,
    symbols,
    timeframe,
    load_type,
    start_date=None,
    end_date=None,
):

    topic_name = SILVER_TIMEFRAME_COMPLETED



    return publish_silver_completed(

        topic_name=topic_name,

        batch_id=batch_id,

        symbols=symbols,

        timeframe=timeframe,

        load_type=load_type,

        start_date=start_date,

        end_date=end_date,

    )
