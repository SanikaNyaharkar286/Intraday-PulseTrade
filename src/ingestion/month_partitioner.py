import csv

from collections import OrderedDict
from pathlib import Path

from src.utils.config import MAX_OPEN_FILES


class MonthlyPartitionWriter:

    def __init__(
        self,
        base_dir: Path,
        fieldnames: list
    ):

        self.base_dir = base_dir
        self.fieldnames = fieldnames

        self.open_files = OrderedDict()

        self.row_counts = {}

    def _partition_key(
        self,
        year: int,
        month: int
    ):

        return (
            f"{year:04d}-"
            f"{month:02d}"
        )

    def _get_writer(
        self,
        year: int,
        month: int
    ):

        partition = self._partition_key(
            year,
            month
        )

        if partition in self.open_files:

            handle, writer, path = (
                self.open_files.pop(
                    partition
                )
            )

            self.open_files[
                partition
            ] = (
                handle,
                writer,
                path
            )

            return writer, path

        if (
            len(self.open_files)
            >= MAX_OPEN_FILES
        ):

            _, (
                old_handle,
                _,
                _
            ) = self.open_files.popitem(
                last=False
            )

            old_handle.close()

        output_file = (
            self.base_dir /
            f"{partition}.csv"
        )

        exists = output_file.exists()

        handle = open(
            output_file,
            "a",
            encoding="utf-8",
            newline=""
        )

        writer = csv.DictWriter(
            handle,
            fieldnames=self.fieldnames
        )

        if not exists:
            writer.writeheader()

        self.open_files[
            partition
        ] = (
            handle,
            writer,
            output_file
        )

        return writer, output_file

    def write_row(
        self,
        year: int,
        month: int,
        original_row: dict
    ):

        writer, path = self._get_writer(
            year,
            month
        )

        # IMPORTANT:
        # original row written unchanged.
        writer.writerow(
            original_row
        )

        key = self._partition_key(
            year,
            month
        )

        self.row_counts[key] = (
            self.row_counts.get(
                key,
                0
            ) + 1
        )

        return path

    def close_all(self):

        for handle, _, _ in (
            self.open_files.values()
        ):
            handle.close()

        self.open_files.clear()