from concurrent.futures import (
    ThreadPoolExecutor,
    as_completed,
)

from datetime import datetime, timezone

from src.utils.config import (
    BRONZE_MAX_WORKERS,
    BRONZE_MAX_RETRIES,
)

from src.transform.bronze.bronze_loader import (
    load_one_file,
)

from src.transform.bronze.audit import (
    write_audit_record,
)

from src.messaging.publisher import (
    publish_bronze_batch_completed,
)


# ==========================================================
# PROCESS ONE FILE
# ==========================================================

def process_file(
    file_info,
    batch_id,
):

    uri = file_info["uri"]

    source_file = (
        file_info["source_file"]
    )

    symbol = (
        file_info["symbol"]
    )

    last_error = None

    # ======================================================
    # RETRY FILE LOAD
    # ======================================================

    for attempt in range(
        1,
        BRONZE_MAX_RETRIES + 1,
    ):

        started_at = (
            datetime.now(timezone.utc)
        )

        try:

            print(
                f"[{batch_id}] "
                f"[Attempt {attempt}] "
                f"Loading {source_file}"
            )

            # ==================================================
            # LOAD ONE GCS FILE -> BRONZE
            # ==================================================

            result = load_one_file(
                gcs_uri=uri,
                symbol=symbol,
            )

            completed_at = (
                datetime.now(timezone.utc)
            )

            # ==================================================
            # SUCCESS AUDIT
            # ==================================================

            write_audit_record(
                batch_id=batch_id,
                source_file=source_file,
                source_gcs_uri=uri,
                symbol=symbol,
                attempt_number=attempt,
                status="SUCCESS",
                row_count=result[
                    "row_count"
                ],
                started_at=started_at,
                completed_at=completed_at,
                error_message=None,
            )

            print(
                f"[{batch_id}] "
                f"SUCCESS: {source_file}"
            )

            # --------------------------------------------------
            # Ensure the result contains the information needed
            # later for the batch Pub/Sub message.
            # --------------------------------------------------

            result["status"] = "SUCCESS"
            result["symbol"] = symbol
            result["source_file"] = (
                source_file
            )
            result["gcs_uri"] = uri

            return result

        except Exception as exc:

            last_error = str(exc)

            completed_at = (
                datetime.now(timezone.utc)
            )

            # ==================================================
            # FAILURE AUDIT
            # ==================================================

            write_audit_record(
                batch_id=batch_id,
                source_file=source_file,
                source_gcs_uri=uri,
                symbol=symbol,
                attempt_number=attempt,
                status="FAILED",
                row_count=0,
                started_at=started_at,
                completed_at=completed_at,
                error_message=last_error,
            )

            print(
                f"[{batch_id}] "
                f"FAILED attempt "
                f"{attempt}: "
                f"{source_file}"
            )

            print(
                f"Reason: {last_error}"
            )

    # ======================================================
    # ALL RETRIES FAILED
    # ======================================================

    return {
        "status": "FAILED",
        "symbol": symbol,
        "source_file": source_file,
        "gcs_uri": uri,
        "row_count": 0,
        "error": last_error,
    }


# ==========================================================
# PROCESS ONE BATCH
# ==========================================================

def process_batch(
    files,
    batch_number,
    load_type="HISTORICAL",
    start_date=None,
    end_date=None,
):
    """
    Process one Bronze batch.

    After ALL files in the batch finish successfully,
    publish one Pub/Sub message for Silver.

    Parameters:

        files:
            Files belonging to this Bronze batch.

        batch_number:
            Numeric Bronze batch number.

        load_type:
            HISTORICAL or INCREMENTAL.

        start_date / end_date:
            Optional date range Silver should process.

    Important:
        Pub/Sub is published once per completed batch,
        NOT once per file.
    """

    batch_id = (
        f"BATCH_{batch_number:05d}"
    )

    print(
        "\n"
        + "=" * 70
    )

    print(
        f"Starting {batch_id}"
    )

    print(
        f"Files: {len(files)}"
    )

    print(
        f"Workers: "
        f"{BRONZE_MAX_WORKERS}"
    )

    print(
        f"Load type: "
        f"{load_type}"
    )

    print(
        "=" * 70
    )

    reports = []

    # ======================================================
    # PROCESS FILES IN PARALLEL
    # ======================================================

    with ThreadPoolExecutor(
        max_workers=BRONZE_MAX_WORKERS
    ) as executor:

        futures = {

            executor.submit(
                process_file,
                file_info,
                batch_id,
            ): file_info

            for file_info in files
        }

        for future in as_completed(
            futures
        ):

            file_info = futures[
                future
            ]

            try:

                result = (
                    future.result()
                )

                reports.append(
                    result
                )

            except Exception as exc:

                print(
                    f"Unexpected failure: "
                    f"{file_info['source_file']}: "
                    f"{exc}"
                )

                reports.append(
                    {
                        "status": "FAILED",
                        "symbol": (
                            file_info[
                                "symbol"
                            ]
                        ),
                        "source_file": (
                            file_info[
                                "source_file"
                            ]
                        ),
                        "gcs_uri": (
                            file_info[
                                "uri"
                            ]
                        ),
                        "row_count": 0,
                        "error": str(exc),
                    }
                )

    # ======================================================
    # BATCH SUMMARY
    # ======================================================

    successful = sum(
        1
        for report in reports
        if report.get("status")
        == "SUCCESS"
    )

    failed = sum(
        1
        for report in reports
        if report.get("status")
        == "FAILED"
    )

    # ======================================================
    # GET SUCCESSFUL SYMBOLS
    # ======================================================

    successful_symbols = sorted(
        {
            report["symbol"]
            for report in reports
            if (
                report.get("status")
                == "SUCCESS"
                and report.get("symbol")
            )
        }
    )

    print(
        f"{batch_id}: "
        f"Successful symbols: "
        f"{len(successful_symbols)}"
    )

    # ======================================================
    # PUB/SUB NOTIFICATION
    # ======================================================

    # Silver starts ONLY when the full Bronze batch
    # has completed successfully.
    #
    # This prevents Silver from processing partially
    # loaded Bronze batches.

    if (
        failed == 0
        and successful > 0
        and successful_symbols
    ):

        try:

            message_id = (
                publish_bronze_batch_completed(
                    batch_id=batch_id,
                    successful_files=successful,
                    failed_files=failed,
                    symbols=successful_symbols,
                    load_type=load_type,
                    start_date=start_date,
                    end_date=end_date,
                )
            )

            print(
                f"{batch_id}: "
                "Bronze batch completed "
                "successfully."
            )

            print(
                f"{batch_id}: "
                "Pub/Sub notification sent."
            )

            print(
                f"{batch_id}: "
                f"Message ID: {message_id}"
            )

        except Exception as exc:

            # --------------------------------------------------
            # Important:
            #
            # Bronze data is already successfully loaded.
            # Therefore we should NOT mark the Bronze files
            # themselves as failed just because Pub/Sub publish
            # failed.
            #
            # But the error must be visible so it can be retried.
            # --------------------------------------------------

            print(
                f"{batch_id}: "
                "Bronze completed, but "
                "Pub/Sub notification FAILED."
            )

            print(
                f"{batch_id}: "
                f"Pub/Sub error: {exc}"
            )

            raise

    else:

        print(
            f"{batch_id}: "
            "Pub/Sub notification NOT sent."
        )

        if failed > 0:

            print(
                f"{batch_id}: "
                f"{failed} Bronze file(s) failed."
            )

        elif not successful_symbols:

            print(
                f"{batch_id}: "
                "No successful symbols found."
            )

    # ======================================================
    # FINAL BATCH SUMMARY
    # ======================================================

    print(
        "\n"
        + "=" * 70
    )

    print(
        f"{batch_id} completed"
    )

    print(
        f"SUCCESS: {successful}"
    )

    print(
        f"FAILED : {failed}"
    )

    print(
        f"SYMBOLS: "
        f"{len(successful_symbols)}"
    )

    print(
        "=" * 70
    )

    return reports