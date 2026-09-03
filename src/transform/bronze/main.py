from src.transform.bronze.bronze_loader import (
    create_bronze_table,
)

from src.transform.bronze.audit import (
    create_audit_table,
)


def main():

    print(
        "=" * 70
    )

    print(
        "Starting PulseTrade Bronze V2 setup..."
    )

    print(
        "=" * 70
    )

    # ======================================================
    # BRONZE TABLE
    # ======================================================

    bronze_table = create_bronze_table()

    print(
        "\nBronze table ready:"
    )

    print(
        bronze_table.full_table_id
    )

    # ======================================================
    # AUDIT TABLE
    # ======================================================

    audit_table = create_audit_table()

    print(
        "\nBronze audit table ready:"
    )

    print(
        audit_table.full_table_id
    )

    print(
        "\n"
        + "=" * 70
    )

    print(
        "Bronze V2 infrastructure setup complete."
    )

    print(
        "=" * 70
    )


if __name__ == "__main__":

    main()