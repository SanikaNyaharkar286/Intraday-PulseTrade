from transform.bronze.bronze import (
    process_new_file,
)


def run_incremental(file_path):

    if not file_path:
        raise ValueError(
            "file_path is required"
        )

    if not file_path.lower().endswith(".csv"):

        print(
            f"Skipping non-CSV file: "
            f"{file_path}"
        )

        return

    print(
        f"Incremental file received: "
        f"{file_path}"
    )

    process_new_file(
        file_path
    )