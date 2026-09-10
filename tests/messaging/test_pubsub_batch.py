import json


def create_bronze_event():

    return {

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



def test_batch_flow():


    event = create_bronze_event()


    print(
        "\nBronze Event:"
    )

    print(
        json.dumps(
            event,
            indent=4
        )
    )


    symbols = event["symbols"]


    results=[]


    for symbol in symbols:


        result = {

            "symbol":symbol,

            "timeframe":"1min",

            "status":"SUCCESS"

        }


        results.append(
            result
        )


    print(
        "\nSilver 1min Completed:"
    )


    print(
        json.dumps(
            results,
            indent=4
        )
    )



if __name__ == "__main__":

    test_batch_flow()