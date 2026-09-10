"""
Batch creation utility.

Responsible for splitting incoming files/symbols
into manageable Pub/Sub batches.
"""


DEFAULT_BATCH_SIZE = 10


def create_batches(
    items: list[str],
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> list[list[str]]:
    """
    Split items into batches.

    Example:

    Input:
        [
          AAPL,
          MSFT,
          TSLA,
          GOOG,
          AMZN
        ]

    batch_size=2


    Output:

    [
      [
        AAPL,
        MSFT
      ],
      [
        TSLA,
        GOOG
      ],
      [
        AMZN
      ]
    ]

    """

    if not items:
        return []


    if batch_size <= 0:
        raise ValueError(
            "Batch size must be greater than zero"
        )


    batches = []


    for index in range(
        0,
        len(items),
        batch_size
    ):

        batches.append(
            items[
                index:index + batch_size
            ]
        )


    return batches