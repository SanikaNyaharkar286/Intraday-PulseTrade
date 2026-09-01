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
    BRONZE_START_BATCH,
    BRONZE_END_BATCH,
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

    bronze_table = create_bronze_table()

    print(
        "Bronze table ready:"
    )

    print(
        bronze_table.full_table_id
    )

    audit_table = create_audit_table()

    print(
        "Audit table ready:"
    )

    print(
        audit_table.full_table_id
    )

    # ======================================================
    # DISCOVER ALL HISTORICAL FILES
    # ======================================================

    print(
        "Discovering historical files..."
    )

    all_files = get_historical_files()

    print(
        f"Historical files found: "
        f"{len(all_files)}"
    )

    # ======================================================
    # SORT FILES
    #
    # This is VERY IMPORTANT.
    #
    # Every laptop must create the exact same
    # file order.
    # ======================================================

    all_files = sorted(
        all_files,
        key=lambda x: x["uri"]
    )

    # ======================================================
    # CREATE FIXED BATCHES
    #
    # We create batches BEFORE removing successful files.
    #
    # Therefore:
    #
    # Batch 1 always means the same 500 files.
    # Batch 2 always means the same 500 files.
    #
    # This allows three laptops to work safely.
    # ======================================================

    batches = [

        all_files[i:i + BRONZE_BATCH_SIZE]

        for i in range(
            0,
            len(all_files),
            BRONZE_BATCH_SIZE
        )
    ]

    print(
        f"Total fixed batches: "
        f"{len(batches)}"
    )

    # ======================================================
    # SHOW LAPTOP ASSIGNMENT
    # ======================================================

    print(
        "\n"
        + "=" * 70
    )

    print(
        "THIS LAPTOP BATCH ASSIGNMENT"
    )

    print(
        f"Start batch: "
        f"{BRONZE_START_BATCH}"
    )

    print(
        f"End batch: "
        f"{BRONZE_END_BATCH}"
    )

    print(
        f"Batch size: "
        f"{BRONZE_BATCH_SIZE}"
    )

    print(
        "=" * 70
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

    # ======================================================
    # PROCESS ASSIGNED BATCHES
    # ======================================================

    total_success = 0
    total_failed = 0

    total_batches = len(batches)

    for index, original_batch in enumerate(
        batches,
        start=1
    ):

        # --------------------------------------------------
        # Skip batches assigned to another laptop
        # --------------------------------------------------

        if index < BRONZE_START_BATCH:

            continue

        if index > BRONZE_END_BATCH:

            break

        # --------------------------------------------------
        # Remove files already successfully processed
        # --------------------------------------------------

        batch = [

            file_info

            for file_info in original_batch

            if file_info["uri"]
            not in successful_files
        ]

        print(
            "\n"
            + "=" * 70
        )

        print(
            f"Starting BATCH_{index:05d}"
        )

        print(
            f"Original files: "
            f"{len(original_batch)}"
        )

        print(
            f"Files remaining: "
            f"{len(batch)}"
        )

        print(
            "=" * 70
        )

        # --------------------------------------------------
        # Entire batch already processed
        # --------------------------------------------------

        if not batch:

            print(
                f"BATCH_{index:05d} "
                f"already completed. Skipping."
            )

            continue

        # --------------------------------------------------
        # Process batch
        # --------------------------------------------------

        reports = process_batch(
            batch,
            index
        )

        # --------------------------------------------------
        # Count successful files
        # --------------------------------------------------

        batch_success = sum(

            1

            for report in reports

            if report.get(
                "status"
            ) == "SUCCESS"
        )

        # --------------------------------------------------
        # Count failed files
        # --------------------------------------------------

        batch_failed = sum(

            1

            for report in reports

            if report.get(
                "status"
            ) == "FAILED"
        )

        total_success += (
            batch_success
        )

        total_failed += (
            batch_failed
        )

        # --------------------------------------------------
        # Batch summary
        # --------------------------------------------------

        print(
            f"\nBATCH_{index:05d} completed"
        )

        print(
            f"Successful: "
            f"{batch_success}"
        )

        print(
            f"Failed: "
            f"{batch_failed}"
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
        f"Assigned batches: "
        f"{BRONZE_START_BATCH}"
        f" - "
        f"{BRONZE_END_BATCH}"
    )

    print(
        f"Successful this run: "
        f"{total_success}"
    )

    print(
        f"Failed this run: "
        f"{total_failed}"
    )

    print(
        "=" * 70
    )


if __name__ == "__main__":

    main()