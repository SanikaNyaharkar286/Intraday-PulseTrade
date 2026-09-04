import functions_framework


from historical.historical_loader import (
    run_historical,
)

from incremental.incremental_loader import (
    run_incremental,
)


@functions_framework.cloud_event
def process_new_csv(cloud_event):

    print(
        "Received Cloud Storage event"
    )

    data = cloud_event.data

    bucket = data.get("bucket")
    file_path = data.get("name")

    print(
        f"Bucket: {bucket}"
    )

    print(
        f"File: {file_path}"
    )

    if not file_path:

        print(
            "No file name found in event"
        )

        return

    if not file_path.lower().endswith(".csv"):

        print(
            f"Ignoring non-CSV file: "
            f"{file_path}"
        )

        return

    run_incremental(
        file_path
    )

    print(
        f"Incremental processing finished: "
        f"{file_path}"
    )


def main():
    run_historical()


if __name__ == "__main__":
    main()
