import shutil
import tempfile
import zipfile

from pathlib import Path


def get_csv_members(
    zip_path: Path
):

    with zipfile.ZipFile(
        zip_path,
        "r"
    ) as zip_file:

        return [
            item.filename
            for item in zip_file.infolist()
            if (
                not item.is_dir()
                and item.filename
                .lower()
                .endswith(".csv")
            )
        ]
#takes only .csv files

def extract_member(
    zip_path: Path,
    member_name: str,
    destination: Path
):

    with zipfile.ZipFile(
        zip_path,
        "r"
    ) as zip_file:

        target = (
            destination /
            Path(member_name).name
        )
#keeps only the filename, removing any folders inside the ZIP.
        with zip_file.open(
            member_name
        ) as source:

            with open(
                target,
                "wb"
            ) as output:
#A new file is created in the destination folder.
                shutil.copyfileobj(
                    source,
                    output,
                    length=8 * 1024 * 1024
                )

        return target