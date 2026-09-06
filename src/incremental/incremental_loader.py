from transform.bronze.bronze import (
    process_new_file,
)


def run_incremental(file_path):

    if not file_path:
        raise ValueError(
            "file_path is required"
        )
#only csv file will be processed other file get igonre 

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
#it says like bronze module will process the new files 
    process_new_file(
        file_path
    )