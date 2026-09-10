import tempfile

from concurrent.futures import (
    ThreadPoolExecutor,
    as_completed
)

from pathlib import Path

from src.ingestion.source_reader import (
    get_csv_members,
    extract_member
)

from src.ingestion.csv_processor import (
    process_stock_csv
)

from src.utils.config import (
    INPUT_PATH,
    MAX_WORKERS
)

from src.utils.logger import (
    get_logger
)


logger = get_logger(
    "pulsetrade"
)


def process_zip_member(
    zip_path: Path,
    member: str
):

    with tempfile.TemporaryDirectory() as temp:

        temp_dir = Path(
            temp
        )

        csv_file = extract_member(
            zip_path,
            member,
            temp_dir
        )

        return process_stock_csv(
            csv_file
        )


def process_zip(
    zip_path: Path
):

    members = get_csv_members(
        zip_path
    )

    logger.info(
        "Found %s stock CSV files",
        len(members)
    )

    reports = []

    with ThreadPoolExecutor(
        max_workers=MAX_WORKERS
    ) as executor:

        futures = {
            executor.submit(
                process_zip_member,
                zip_path,
                member
            ): member
            for member in members
        }

        for future in as_completed(
            futures
        ):

            member = futures[
                future
            ]

            try:

                report = future.result()

                reports.append(
                    report
                )

            except Exception as exc:

                logger.exception(
                    "Stock failed: %s | %s",
                    member,
                    exc
                )

                reports.append({
                    "source_file": member,
                    "status": "FAILED",
                    "error": str(exc)
                })

    return reports


def main():

    source = Path(
        INPUT_PATH
    )

    if not source.exists():

        raise FileNotFoundError(
            f"Input path does not exist: "
            f"{source}"
        )

    if source.suffix.lower() != ".zip":

        raise ValueError(
            "Current implementation expects "
            "a ZIP file."
        )

    reports = process_zip(
        source
    )

    failed = [
        report
        for report in reports
        if (
            report.get("status")
            == "FAILED"
            or report.get(
                "failed_objects",
                0
            ) > 0
        )
    ]

    logger.info(
        "===================================="
    )

    logger.info(
        "Migration complete"
    )

    logger.info(
        "Total stocks: %s",
        len(reports)
    )

    logger.info(
        "Stocks with failures: %s",
        len(failed)
    )

    for report in failed:

        logger.error(
            "FAILED: %s",
            report.get(
                "source_file"
            )
        )


if __name__ == "__main__":
    main()