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


# ==========================================================
# PROCESS ONE FILE
# ==========================================================

def process_file(
    file_info,
    batch_id
):

    uri = file_info["uri"]

    source_file = (
        file_info["source_file"]
    )

    symbol = (
        file_info["symbol"]
    )

    last_error = None

    for attempt in range(
        1,
        BRONZE_MAX_RETRIES + 1
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

            result = load_one_file(
                gcs_uri=uri,
                symbol=symbol
            )

            completed_at = (
                datetime.now(timezone.utc)
            )

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

            return result

        except Exception as exc:

            last_error = str(exc)

            completed_at = (
                datetime.now(timezone.utc)
            )

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

    return {

        "status": "FAILED",

        "symbol":
            symbol,

        "gcs_uri":
            uri,

        "row_count":
            0,

        "error":
            last_error,

    }


# ==========================================================
# PROCESS ONE BATCH
# ==========================================================

def process_batch(
    files,
    batch_number
):

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
        "=" * 70
    )

    reports = []

    with ThreadPoolExecutor(
        max_workers=BRONZE_MAX_WORKERS
    ) as executor:

        futures = {

            executor.submit(
                process_file,
                file_info,
                batch_id
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

                result = future.result()

                reports.append(
                    result
                )

            except Exception as exc:

                print(
                    f"Unexpected failure: "
                    f"{file_info['source_file']}: "
                    f"{exc}"
                )

                reports.append({

                    "status":
                        "FAILED",

                    "symbol":
                        file_info[
                            "symbol"
                        ],

                    "gcs_uri":
                        file_info[
                            "uri"
                        ],

                    "row_count":
                        0,

                    "error":
                        str(exc),

                })

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
        "=" * 70
    )

    return reports