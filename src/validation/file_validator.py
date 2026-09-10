from pathlib import Path


def validate_file(file_path: Path):

    if not file_path.exists():
        raise FileNotFoundError(
            f"File not found: {file_path}"
        )

    if not file_path.is_file():
        raise ValueError(
            f"Not a file: {file_path}"
        )

    if file_path.stat().st_size == 0:
        raise ValueError(
            f"File is empty: {file_path.name}"
        )

    if file_path.suffix.lower() != ".csv":
        raise ValueError(
            f"Expected CSV file: {file_path.name}"
        )