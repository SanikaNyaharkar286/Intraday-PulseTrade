import csv
import tempfile

from pathlib import Path
"""
Open one stock CSV
        |
Validate file and headers
        |
Read rows as dictionaries
        |
Takes each row
        |
Write rows into monthly CSV files
        |
Close temporary files
        |
Check row counts
        |
Upload monthly files to GCS
        |
Return processing report
"""
from src.ingestion.month_partitioner import (
    MonthlyPartitionWriter
)

from src.ingestion.gcs_uploader import (
    upload_month_file
)

from src.validation.file_validator import (
    validate_file
)

from src.validation.schema_validator import (
    validate_schema
)

from src.validation.row_validator import (
    validate_row
)

from src.validation.reconciliation import (
    validate_reconciliation
)

from src.utils.logger import get_logger


logger = get_logger(
    "csv_processor"
)


def extract_symbol(
    filename: str
):

    name = Path(
        filename
    ).stem

    if name.lower().endswith(
        "_minute"
    ):
        name = name[:-7]

    symbol = (
        name.strip().upper()
    )

    if not symbol:
        raise ValueError(
            f"Unable to identify stock "
            f"from {filename}"
        )

    return symbol


def process_stock_csv(
    source_file: Path
):

    validate_file(
        source_file
    )

    symbol = extract_symbol(
        source_file.name
    )

    logger.info(
        "Processing stock %s",
        symbol
    )

    total_rows = 0
    valid_rows = 0
    invalid_rows = 0
    duplicate_rows = 0

    previous_timestamp = None

    # Duplicate detection.
    seen_timestamps = set()

    errors = []

    with tempfile.TemporaryDirectory() as temp:

        temp_dir = Path(
            temp
        )

        with open(
            source_file,
            "r",
            encoding="utf-8-sig",
            newline=""
        ) as source:

            reader = csv.DictReader(
                source
            )

            schema_result = (
                validate_schema(
                    reader.fieldnames
                )
            )

            if schema_result[
                "unexpected"
            ]:

                logger.info(
                    "%s contains additional "
                    "columns: %s",
                    symbol,
                    schema_result[
                        "unexpected"
                    ]
                )

            # Original headers retained.
            original_headers = (
                reader.fieldnames
            )

            # Map normalized names to
            # exact source header names.
            header_map = {
                header.strip().lower():
                    header
                for header
                in original_headers
            }

            partition_writer = (
                MonthlyPartitionWriter(
                    temp_dir,
                    original_headers
                )
            )

            try:

                for line_number, original_row \
                        in enumerate(
                            reader,
                            start=2
                        ):

                    total_rows += 1

                    logical_row = {
                        name:
                            original_row.get(
                                actual
                            )
                        for name, actual
                        in header_map.items()
                    }

                    result = validate_row(
                        logical_row
                    )

                    if not result["valid"]:

                        invalid_rows += 1

                        errors.append({
                            "line": line_number,
                            "reason":
                                result["reason"],
                            "date":
                                logical_row.get(
                                    "date"
                                )
                        })

                        continue

                    timestamp = (
                        result["timestamp"]
                    )

                    timestamp_key = (
                        timestamp.isoformat()
                    )

                    if (
                        timestamp_key
                        in seen_timestamps
                    ):

                        duplicate_rows += 1

                        logger.warning(
                            "%s duplicate timestamp "
                            "line=%s value=%s",
                            symbol,
                            line_number,
                            logical_row.get(
                                "date"
                            )
                        )

                        # Requirement says:
                        # detect/report.
                        #
                        # DO NOT silently delete.
                        #
                        # Row still proceeds.

                    else:

                        seen_timestamps.add(
                            timestamp_key
                        )

                    if (
                        previous_timestamp
                        is not None
                        and timestamp
                        < previous_timestamp
                    ):

                        logger.warning(
                            "%s timestamp order "
                            "issue at line %s: %s",
                            symbol,
                            line_number,
                            logical_row.get(
                                "date"
                            )
                        )

                    previous_timestamp = (
                        timestamp
                    )

                    # Original row preserved.
                    partition_writer.write_row(
                        timestamp.year,
                        timestamp.month,
                        original_row
                    )

                    valid_rows += 1

            finally:

                partition_writer.close_all()

        validate_reconciliation(
            total_rows,
            valid_rows,
            invalid_rows,
            partition_writer.row_counts
        )

        uploaded = 0
        skipped = 0
        failed = 0

        for partition, row_count in sorted(
            partition_writer.row_counts.items()
        ):

            year_text, month_text = (
                partition.split("-")
            )

            year = int(
                year_text
            )

            month = int(
                month_text
            )

            local_file = (
                temp_dir /
                f"{partition}.csv"
            )

            try:

                result = (
                    upload_month_file(
                        local_file,
                        symbol,
                        year,
                        month
                    )
                )

                if (
                    result["status"]
                    == "UPLOADED"
                ):
                    uploaded += 1

                elif (
                    result["status"]
                    == "SKIPPED"
                ):
                    skipped += 1

            except Exception as exc:

                failed += 1

                logger.exception(
                    "Upload failed: "
                    "%s %s: %s",
                    symbol,
                    partition,
                    exc
                )

        report = {
            "symbol": symbol,
            "source_file":
                source_file.name,

            "total_rows":
                total_rows,

            "valid_rows":
                valid_rows,

            "invalid_rows":
                invalid_rows,

            "duplicate_rows":
                duplicate_rows,

            "monthly_rows":
                partition_writer.row_counts,

            "uploaded_objects":
                uploaded,

            "skipped_objects":
                skipped,

            "failed_objects":
                failed,

            "errors":
                errors[:100]
        }

        logger.info(
            (
                "%s COMPLETE | "
                "total=%s valid=%s "
                "invalid=%s duplicate=%s "
                "uploaded=%s skipped=%s "
                "failed=%s"
            ),
            symbol,
            total_rows,
            valid_rows,
            invalid_rows,
            duplicate_rows,
            uploaded,
            skipped,
            failed
        )

        return report