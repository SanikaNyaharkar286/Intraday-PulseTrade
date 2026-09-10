from src.messaging.publisher import (
    publish_silver_completed
)

from src.messaging.topics import (
    SILVER_TIMEFRAME_COMPLETED
)


symbols = [
    "FORCEMOT",
    "FORTIS",
    "FSL",
    "GABRIEL",
    "GAIL",
    "GALLANTT",
    "GESHIP",
    "GICRE",
    "GILLETTE",
    "GLAND",
    "GLAXO",
    "GLENMARK",
    "GMDCLTD",
    "GMRAIRPORT",
    "GODFRYPHLP",
    "GODIGIT",
    "GODREJAGRO",
    "GODREJCP",
    "GODREJIND",
    "GODREJPROP"
]


TIMEFRAME_FLOW = {

    "1min": "5min",
    "5min": "15min",
    "15min": "1hr",
    "1hr": "daily",
    "daily": None

}


def publish_next_timeframe(
    current_timeframe
):

    next_timeframe = TIMEFRAME_FLOW.get(
        current_timeframe
    )


    if not next_timeframe:

        print(
            "No next timeframe available"
        )

        return


    print("==============================")
    print("Publishing timeframe rebuild")
    print(f"Completed timeframe : {current_timeframe}")
    print(f"Next timeframe     : {next_timeframe}")
    print(f"Symbol count       : {len(symbols)}")
    print("==============================")


    message_id = publish_silver_completed(

        topic_name=SILVER_TIMEFRAME_COMPLETED,

        batch_id=f"TIMEFRAME_REBUILD_{next_timeframe}_45_SYMBOLS",

        symbols=symbols,

        timeframe=current_timeframe,

        load_type="HISTORICAL",

        start_date=None,

        end_date=None
    )


    print(
        "Published message:"
    )

    print(
        message_id
    )



# Start from where previous processing completed
publish_next_timeframe(
    "1min"
)