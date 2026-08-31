"""from src.transform.bronze.gcs_reader import (
    get_historical_files
)
from src.transform.bronze.gcs_reader import (
    get_test_file
)
from src.transform.bronze.bronze_loader import (
    create_bronze_table
)


def main():

    print(
        "Starting Bronze setup..."
    )

    # ------------------------------------------------------
    # Create Bronze table
    # ------------------------------------------------------

    table = create_bronze_table()

    print(
        "Bronze table ready:"
    )

    print(
        table.full_table_id
    )

    # ------------------------------------------------------
    # Discover historical GCS files
    # ------------------------------------------------------

    #files = get_historical_files()
    files = get_test_file()
    print(
        f"Historical CSV files found: "
        f"{len(files)}"
    )

    # ------------------------------------------------------
    # Show first few files for verification
    # ------------------------------------------------------

    for file_info in files[:10]:

        print(
            file_info["uri"]
        )


if __name__ == "__main__":
    main()"""


"""
from src.transform.bronze.gcs_reader import (
    get_test_file
)

from src.transform.bronze.bronze_loader import (
    create_bronze_table
)


def main():

    print(
        "Starting Bronze test..."
    )

    # ------------------------------------------------------
    # Create Bronze table
    # ------------------------------------------------------

    table = create_bronze_table()

    print(
        "Bronze table ready:"
    )

    print(
        table.full_table_id
    )

    # ------------------------------------------------------
    # ONE FILE TEST
    # ------------------------------------------------------

    files = get_test_file()

    print(
        f"Test files found: "
        f"{len(files)}"
    )

    for file_info in files:

        print(
            file_info["uri"]
        )


if __name__ == "__main__":
    main()"""


"""from src.transform.bronze.gcs_reader import (
    get_test_file
)

from src.transform.bronze.bronze_loader import (
    create_bronze_table,
    load_one_file
)


def main():

    print(
        "Starting Bronze one-file test..."
    )

    # ------------------------------------------------------
    # Make sure Bronze table exists
    # ------------------------------------------------------

    table = create_bronze_table()

    print(
        "Bronze table ready:"
    )

    print(
        table.full_table_id
    )

    # ------------------------------------------------------
    # Get exactly ONE test file
    # ------------------------------------------------------

    files = get_test_file()

    print(
        f"Files to process: {len(files)}"
    )

    for file_info in files:

        print(
            f"Loading: {file_info['uri']}"
        )

        try:

            result = load_one_file(
                gcs_uri=file_info["uri"],
                symbol=file_info["symbol"]
            )

            print(
                "Load completed:"
            )

            print(
                result
            )

        except Exception as exc:

            print(
                f"Load failed: {exc}"
            )

            raise


if __name__ == "__main__":

    main()"""


"""from src.transform.bronze.bronze_loader import (
    create_bronze_table,
)

from src.transform.bronze.audit import (
    create_audit_table,
)


def main():

    print(
        "Starting Bronze infrastructure setup..."
    )

    # ------------------------------------------------------
    # Bronze table
    # ------------------------------------------------------

    bronze_table = create_bronze_table()

    print(
        "Bronze table ready:"
    )

    print(
        bronze_table.full_table_id
    )

    # ------------------------------------------------------
    # Audit table
    # ------------------------------------------------------

    audit_table = create_audit_table()

    print(
        "Audit table ready:"
    )

    print(
        audit_table.full_table_id
    )


if __name__ == "__main__":

    main()"""

from src.utils.config import (
    BRONZE_BATCH_SIZE,
)

from src.transform.bronze.gcs_reader import (
    get_historical_files,
)

from src.transform.bronze.bronze_loader import (
    create_bronze_table,
)

from src.transform.bronze.audit import (
    create_audit_table,
    get_successful_files,
)

from src.transform.bronze.batch_processor import (
    process_batch,
)


def main():

    print(
        "Starting Historical Bronze Load..."
    )

    # ======================================================
    # INFRASTRUCTURE
    # ======================================================

    bronze_table = (
        create_bronze_table()
    )

    print(
        "Bronze table ready:"
    )

    print(
        bronze_table.full_table_id
    )

    audit_table = (
        create_audit_table()
    )

    print(
        "Audit table ready:"
    )

    print(
        audit_table.full_table_id
    )

    # ======================================================
    # DISCOVER FILES
    # ======================================================

    print(
        "Discovering historical files..."
    )

    all_files = (
        get_historical_files()
    )

    print(
        f"Historical files found: "
        f"{len(all_files)}"
    )

    # ======================================================
    # RESUME SUPPORT
    # ======================================================

    successful_files = (
        get_successful_files()
    )

    print(
        f"Already successful: "
        f"{len(successful_files)}"
    )

    files_to_process = [

        file_info

        for file_info in all_files

        if file_info["uri"]
        not in successful_files
    ]

    print(
        f"Files remaining: "
        f"{len(files_to_process)}"
    )

    if not files_to_process:

        print(
            "No files require processing."
        )

        return

    # ======================================================
    # BATCH CREATION
    # ======================================================

    batches = [

        files_to_process[i:i + BRONZE_BATCH_SIZE]

        for i in range(
            0,
            len(files_to_process),
            BRONZE_BATCH_SIZE
        )
    ]

    print(
        f"Total batches: "
        f"{len(batches)}"
    )

    # ======================================================
    # PROCESS BATCHES
    # ======================================================

    total_success = 0
    total_failed = 0

    for index, batch in enumerate(
        batches,
        start=1
    ):

        reports = process_batch(
            batch,
            index
        )

        total_success += sum(

            1

            for report in reports

            if report.get(
                "status"
            ) == "SUCCESS"
        )

        total_failed += sum(

            1

            for report in reports

            if report.get(
                "status"
            ) == "FAILED"
        )

        print(
            "\nHistorical progress:"
        )

        print(
            f"Batch: "
            f"{index}/{len(batches)}"
        )

        print(
            f"Successful this run: "
            f"{total_success}"
        )

        print(
            f"Failed this run: "
            f"{total_failed}"
        )

    # ======================================================
    # FINAL SUMMARY
    # ======================================================

    print(
        "\n"
        + "=" * 70
    )

    print(
        "Historical Bronze Load Complete"
    )

    print(
        f"Successful: "
        f"{total_success}"
    )

    print(
        f"Failed: "
        f"{total_failed}"
    )

    print(
        "=" * 70
    )


if __name__ == "__main__":

    main()