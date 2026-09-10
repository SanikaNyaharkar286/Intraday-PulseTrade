from src.utils.config import (
    BRONZE_BATCH_SIZE,
    BRONZE_START_BATCH,
    BRONZE_END_BATCH,
)

from src.transform.bronze.gcs_reader import (
    get_historical_files,
)

from src.transform.bronze.audit import (
    get_successful_files,
)

from src.transform.bronze.batch_processor import (
    process_batch,
)


# ==========================================================
# HISTORICAL BRONZE RUNNER
# ==========================================================

def run_historical_load():

    print(
        "\n"
        + "=" * 70
    )

    print(
        "Starting Historical Bronze Load..."
    )

    print(
        "=" * 70
    )


    # ======================================================
    # 1. DISCOVER HISTORICAL FILES
    # ======================================================

    print(
        "\nDiscovering historical files..."
    )

    all_files = get_historical_files()


    print(
        f"Historical files found: {len(all_files)}"
    )


    if not all_files:

        print(
            "No historical files found."
        )

        return


    # ======================================================
    # 2. DETERMINISTIC ORDER
    #
    # Important:
    # Every laptop should generate the same batches
    # ======================================================

    all_files = sorted(
        all_files,
        key=lambda x: (
            x["symbol"],
            x["source_file"],
        ),
    )


    # ======================================================
    # 3. CREATE FIXED BATCHES
    # ======================================================

    batches = [

        all_files[i:i + BRONZE_BATCH_SIZE]

        for i in range(
            0,
            len(all_files),
            BRONZE_BATCH_SIZE,
        )

    ]


    total_batches = len(batches)


    print(
        f"Total fixed batches: {total_batches}"
    )


    # ======================================================
    # 4. LAPTOP BATCH ASSIGNMENT
    # ======================================================

    print(
        "\n"
        + "=" * 70
    )

    print(
        "LAPTOP BATCH ASSIGNMENT"
    )

    print(
        f"Start batch: {BRONZE_START_BATCH}"
    )

    print(
        f"End batch: {BRONZE_END_BATCH}"
    )

    print(
        f"Batch size: {BRONZE_BATCH_SIZE}"
    )

    print(
        "=" * 70
    )


    # ======================================================
    # 5. RESUME SUPPORT
    # ======================================================

    successful_files = (
        get_successful_files()
    )


    print(
        f"\nAlready successful files: "
        f"{len(successful_files)}"
    )


    # ======================================================
    # 6. TOTAL COUNTERS
    # ======================================================

    total_success = 0
    total_failed = 0

    processed_batches = 0
    skipped_batches = 0


    # ======================================================
    # 7. PROCESS ASSIGNED BATCHES
    # ======================================================

    for batch_number, original_batch in enumerate(
        batches,
        start=1,
    ):


        # --------------------------------------------------
        # Skip batches assigned to another laptop
        # --------------------------------------------------

        if batch_number < BRONZE_START_BATCH:
            continue


        if batch_number > BRONZE_END_BATCH:
            break



        # --------------------------------------------------
        # Remove already processed files
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
            f"Preparing BATCH_{batch_number:05d}"
        )


        print(
            f"Original files: {len(original_batch)}"
        )


        print(
            f"Files remaining: {len(batch)}"
        )


        print(
            "=" * 70
        )



        # ==================================================
        # ALREADY COMPLETED
        # ==================================================

        if not batch:

            print(
                f"BATCH_{batch_number:05d} "
                "already completed. Skipping."
            )

            skipped_batches += 1

            continue



        # ==================================================
        # PROCESS ONE BATCH
        #
        # batch_processor.py handles:
        #
        # GCS -> Bronze
        # Validation
        # Audit
        # Pub/Sub publish
        #
        # ==================================================

        reports = process_batch(

            files=batch,

            batch_number=batch_number,

            load_type="HISTORICAL",

        )


        processed_batches += 1



        # ==================================================
        # BATCH COUNTS
        # ==================================================

        batch_success = sum(

            1

            for report in reports

            if report.get("status")
            == "SUCCESS"

        )


        batch_failed = sum(

            1

            for report in reports

            if report.get("status")
            == "FAILED"

        )


        total_success += batch_success

        total_failed += batch_failed



        # ==================================================
        # BATCH SUMMARY
        # ==================================================

        print(
            "\n"
            + "-" * 70
        )

        print(
            f"BATCH_{batch_number:05d} SUMMARY"
        )

        print(
            f"Successful: {batch_success}"
        )

        print(
            f"Failed: {batch_failed}"
        )

        print(
            "-" * 70
        )



    # ======================================================
    # 8. FINAL SUMMARY
    # ======================================================

    print(
        "\n"
        + "=" * 70
    )

    print(
        "Historical Bronze Load Complete"
    )


    print(
        f"Processed batches: {processed_batches}"
    )


    print(
        f"Skipped batches: {skipped_batches}"
    )


    print(
        f"Successful files: {total_success}"
    )


    print(
        f"Failed files: {total_failed}"
    )


    print(
        "=" * 70
    )



# ==========================================================
# ENTRY POINT
# ==========================================================

if __name__ == "__main__":

    run_historical_load()