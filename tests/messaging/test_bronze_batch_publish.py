from src.ingestion.batch_manager import (
    create_batches
)


def test_bronze_batch_creation():

    symbols = [
        "360ONE",
        "TCS",
        "INFY",
        "RELIANCE",
        "HDFCBANK",
        "ICICIBANK",
        "SBIN",
        "AXISBANK",
        "WIPRO",
        "LT",
        "MARUTI",
        "ITC"
    ]


    batches = create_batches(
        symbols,
        batch_size=10
    )


    print("\nGenerated batches:")

    for index, batch in enumerate(
        batches,
        start=1
    ):

        print(
            f"Batch {index}: {batch}"
        )


    assert len(batches) == 2

    assert len(batches[0]) == 10

    assert len(batches[1]) == 2