import sys
import os

sys.path.append(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

from tools.market_state import get_current_market_state

def main():

    print("Testing market state tool...\n")

    result = get_current_market_state()

    print(f"Rows returned: {len(result)}\n")

    for row in result:
        print(row)


if __name__ == "__main__":
    main()