import json
#used to read checkopoint from json file and write checkpoint to json file 
from pathlib import Path

from transform.config import (
    HISTORICAL_CHECKPOINT_FILE,
    HISTORICAL_START_YEAR,
    HISTORICAL_START_MONTH,
    HISTORICAL_END_YEAR,
    HISTORICAL_END_MONTH,
    HISTORICAL_RUN_SILVER_EACH_MONTH,
)

from transform.bronze.bronze import process_historical_month
from transform.silver.silver import run_silver_pipeline

#here month+year into single number so we can compare months easily 
def _month_value(year, month):
    return (year * 12) + month

#this function use to move on to the next month 
def _next_month(year, month):
    month += 1

    if month > 12:
        month = 1
        year += 1

    return year, month

#checkpoint is used to keep track of last completed month and year so if we
#  terminate the code and rerun it will start tfrom the last completed month annd year 
#
def _read_checkpoint():
    checkpoint_path = Path(HISTORICAL_CHECKPOINT_FILE)

    if not checkpoint_path.exists():
        return None

    with checkpoint_path.open("r", encoding="utf-8") as checkpoint_file:
        return json.load(checkpoint_file)

# this bascially weite the checkpoint to the json to keep the teack 
def _write_checkpoint(year, month, silver_completed=False):
    checkpoint_path = Path(HISTORICAL_CHECKPOINT_FILE)
    checkpoint_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    checkpoint = {
        "last_completed_year": year,
        "last_completed_month": month,
        "silver_completed": silver_completed,
    }

    with checkpoint_path.open("w", encoding="utf-8") as checkpoint_file:
        json.dump(
            checkpoint,
            checkpoint_file,
            indent=2
        )


def _get_start_month():
    start_year = HISTORICAL_START_YEAR
    start_month = HISTORICAL_START_MONTH
    end_value = _month_value(
        HISTORICAL_END_YEAR,
        HISTORICAL_END_MONTH
    )

    checkpoint = _read_checkpoint()

    if not checkpoint:
        return start_year, start_month

    completed_year = checkpoint.get(
        "last_completed_year"
    )

    completed_month = checkpoint.get(
        "last_completed_month"
    )

    if not completed_year or not completed_month:
        return start_year, start_month

    completed_value = _month_value(
        completed_year,
        completed_month
    )

    configured_start_value = _month_value(
        start_year,
        start_month
    )

    if completed_value < configured_start_value:
        return start_year, start_month

    if completed_value >= end_value:
        return None, None

    return _next_month(
        completed_year,
        completed_month
    )

# main historical controller fucntion which run pipeline for year and month 
def run_historical():

    year, month = _get_start_month()
    completed_months = 0
#if year and month is none means we have completed the historical pipeline for 
#the this range so we can check if silver pipeline is completed or not if not then we run the silver pipleine 
    if year is None or month is None:
        checkpoint = _read_checkpoint()
        #this line get the silver status 
        silver_completed = (
            checkpoint
            and checkpoint.get("silver_completed")
        )

        if (
            #if not historicl is false it became true and not silver is flase it became true then run the silver pipline
            #if historical run silver each month 
            not HISTORICAL_RUN_SILVER_EACH_MONTH
            and not silver_completed
        ):
            print(
                "Historical Bronze load is complete. "
                "Running pending Silver pipeline."
            )

            run_silver_pipeline()

            _write_checkpoint(
                HISTORICAL_END_YEAR,
                HISTORICAL_END_MONTH,
                silver_completed=True
            )

            return

        print(
            "Historical pipeline already completed for configured range"
        )

        return

    while True:

        print("=" * 60)
        print(f"Processing historical month: {year}-{month:02d}")
        print("=" * 60)

        try:
            process_historical_month(
                year,
                month,
                run_silver=HISTORICAL_RUN_SILVER_EACH_MONTH
            )

            print(
                f"Completed historical month: "
                f"{year}-{month:02d}"
            )

            _write_checkpoint(
                year,
                month,
                silver_completed=HISTORICAL_RUN_SILVER_EACH_MONTH
            )

            completed_months += 1

        except Exception as e:

            print(
                f"FAILED historical month: "
                f"{year}-{month:02d}"
            )

            print(f"Error: {e}")

            # Stop immediately if a month fails
            raise

        # Stop when end month is reached
        if (
            year == HISTORICAL_END_YEAR
            and month == HISTORICAL_END_MONTH
        ):
            break

        year, month = _next_month(
            year,
            month
        )
#done with all the month and if silver was not in run then silver pipeline after all month 
    if completed_months and not HISTORICAL_RUN_SILVER_EACH_MONTH:
        print("=" * 60)
        print("Running Silver pipeline after historical Bronze load")
        print("=" * 60)

        run_silver_pipeline()

        _write_checkpoint(
            HISTORICAL_END_YEAR,
            HISTORICAL_END_MONTH,
            silver_completed=True
        )


if __name__ == "__main__":

    print("=" * 60)
    print("Starting historical pipeline")
    print("=" * 60)

    run_historical()

    print("=" * 60)
    print("Historical pipeline completed successfully")
    print("=" * 60)
