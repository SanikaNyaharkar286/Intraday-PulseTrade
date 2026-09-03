from src.ingestion.batch_manager import (
    create_batches,
)


def test_single_batch():

    files = [
        "AAPL",
        "MSFT",
        "TSLA"
    ]

    result = create_batches(
        files,
        batch_size=10
    )


    assert len(result) == 1
    assert len(result[0]) == 3



def test_exact_batch_size():

    files = [
        str(i)
        for i in range(10)
    ]


    result = create_batches(
        files,
        batch_size=10
    )


    assert len(result) == 1



def test_multiple_batches():

    files = [
        str(i)
        for i in range(25)
    ]


    result = create_batches(
        files,
        batch_size=10
    )


    assert len(result) == 3

    assert len(result[0]) == 10
    assert len(result[1]) == 10
    assert len(result[2]) == 5



def test_empty_input():

    result = create_batches(
        [],
        batch_size=10
    )


    assert result == []



def test_invalid_batch_size():

    try:

        create_batches(
            ["AAPL"],
            0
        )

        assert False

    except ValueError:

        assert True