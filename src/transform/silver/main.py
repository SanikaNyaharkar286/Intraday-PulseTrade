from src.transform.silver.silver_loader import (
    load_symbol_to_silver_1min,
)


def main():

    print(
        "Starting Silver 1-minute test..."
    )

    load_symbol_to_silver_1min(
        "360ONE"
    )

    print(
        "Silver test completed."
    )


if __name__ == "__main__":
    main()