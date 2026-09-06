import csv

from collections import OrderedDict
#Imports an ordered dictionary. It remembers the order in which items were added.
from pathlib import Path


from src.utils.config import MAX_OPEN_FILES
"""
Valid CSV row
→ read its timestamp
→ get year and month
→ build key like 2026-08
→ write row into 2026-08.csv
→ increase that month’s row count
→ repeat for all rows
→ close all temporary monthly files

"""

class MonthlyPartitionWriter:

    def __init__(
        self,
        base_dir: Path,
        fieldnames: list
    ):

        self.base_dir = base_dir
        #Stores the output folder.
        self.fieldnames = fieldnames
        #Stores the CSV column names.
        self.open_files = OrderedDict()
        #Creates a collection of currently open files.
        self.row_counts = {}

    def _partition_key(# helper function
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
            #Removes the existing entry temporarily so it can be 
            #moved to the end of the ordered dictionary.

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
            #Removes the least recently used file.

#last=False removes the first item.
#old_handle is the file handle.
#_ means the other values are not needed.

            old_handle.close()

        output_file = (
            self.base_dir /
            f"{partition}.csv"
        )#Builds the output path

        exists = output_file.exists()
        #Checks whether the monthly file already exists.

        """Opens the file in append mode.

"a" preserves existing data and adds new rows at the end.
encoding="utf-8" supports standard text characters.
newline="" prevents unwanted blank lines in CSV files."""
        handle = open(
            output_file,
            "a",
            encoding="utf-8",
            newline=""
        )
        """Creates a CSV writer that writes dictionaries using the configured column names."""
        writer = csv.DictWriter(
            handle,
            fieldnames=self.fieldnames
        )
        #Checks whether this is a new file.
        if not exists:
            writer.writeheader()

        self.open_files[
            partition
        ] = (
            handle,
            writer,
            output_file
        )
        """self.open_files = OrderedDict({
    "2024-01": (
        january_file_handle,
        january_csv_writer,
        Path("data/2024-01.csv")
    ),
    "2024-02": (
        february_file_handle,
        february_csv_writer,
        Path("data/2024-02.csv")
    )
})"""

        return writer, output_file
    """self.row_counts = {
    "2024-01": 1500,
    "2024-02": 1420,
    "2024-03": 1605
}"""



    def write_row(#Writes one data row to the correct monthly file
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