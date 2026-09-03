import json


def mock_run_silver_pipeline(
    symbol,
    timeframe
):

    print(
        f"Processing {symbol} -> {timeframe}"
    )

    return {

        "symbol": symbol,

        "timeframe": timeframe,

        "status": "SUCCESS"

    }



def get_next_timeframe(timeframe):

    flow = {

        "1min": "5min",

        "5min": "15min",

        "15min": "1hr",

        "1hr": "daily",

        "daily": None

    }

    return flow.get(timeframe)




def process_silver_event(event):


    print(
        "\nReceived Event"
    )

    print(
        json.dumps(
            event,
            indent=4
        )
    )


    symbols = event["symbols"]

    current_timeframe = event["timeframe"]


    next_timeframe = get_next_timeframe(
        current_timeframe
    )


    if next_timeframe is None:

        print(
            "Pipeline completed"
        )

        return



    results=[]


    for symbol in symbols:


        result = mock_run_silver_pipeline(

            symbol,

            next_timeframe

        )


        results.append(
            result
        )


    next_event = {


        "event_type":
            "SILVER_TIMEFRAME_COMPLETED",


        "batch_id":
            event["batch_id"],


        "symbols":
            symbols,


        "timeframe":
            next_timeframe,


        "status":
            "SUCCESS"

    }


    print(
        "\nPublishing Next Event"
    )

    print(
        json.dumps(
            next_event,
            indent=4
        )
    )


    return next_event




def test_full_silver_chain():


    event = {


        "event_type":
            "SILVER_TIMEFRAME_COMPLETED",


        "batch_id":
            "batch_demo_001",


        "symbols":[

            "360ONE",

            "TCS",

            "INFY"

        ],


        "timeframe":
            "1min",


        "status":
            "SUCCESS"

    }


    while event:


        event = process_silver_event(
            event
        )



if __name__ == "__main__":

    test_full_silver_chain()