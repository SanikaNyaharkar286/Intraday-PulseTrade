
from pathlib import Path
from datetime import datetime, timezone
import time

#basically this lets python work with files path
from google.cloud import bigquery

#get configuration form config.py
from transform.config import (
    AUDIT_DATASET,
    AUDIT_TABLE,
    BQ_LOCATION,
    BRONZE_DATASET,
    BRONZE_TABLE,
    PROJECT_ID,
    RUN_GOLD_AFTER_SILVER,
    SILVER_DATASET,
)


#create empty bigquery client var
#at initial stage is no connection
_bq_client = None
_bq_location = None


def _format_int(value):
    if value is None:
        return "0"

    return f"{int(value):,}"


def _format_ts(value):
    if value is None:
        return "N/A"

    return str(value)


#finds where bronze dataset is located
#THIS function finds where the dataset location
def get_bq_location():
    global _bq_location

    #if not then create the connection get project id
    if _bq_location is None:
        #create bigquery connection
        metadata_client = bigquery.Client(
            project=PROJECT_ID
        )

        #try to get the bronze dataset info
        try:
            dataset = metadata_client.get_dataset(
                f"{PROJECT_ID}.{BRONZE_DATASET}"
            )

            #save loction to the var
            _bq_location = dataset.location

        #if dataset not found throw exception
        except Exception:
            _bq_location = BQ_LOCATION

    return _bq_location


#this function provide the bigquery cliennt
def get_bq_client():
    global _bq_client

    if _bq_client is None:
        _bq_client = bigquery.Client(
            project=PROJECT_ID,
            location=get_bq_location()
        )

    return _bq_client


def _sql_string(value):
    return "'" + str(value).replace("'", "''") + "'"
#Converts a value to text and escapes single quotes.

#FUNCTION prepare your sql before sending them to bigquery
#It replaces placeholders with real project and filtering values.
def _render_sql(
    sql,
    scope_symbol=None,
    scope_start=None,
    scope_end=None
):
    if scope_symbol and scope_start and scope_end:

        source_filter = f"""
        WHERE symbol = {_sql_string(scope_symbol)}
            AND timestamp BETWEEN
                TIMESTAMP_SUB(
                    TIMESTAMP({_sql_string(scope_start)}),
                    INTERVAL 100 DAY
                )
                AND TIMESTAMP({_sql_string(scope_end)})
        """
        #the above query is writte n to get rolling indicators values for calculation

        candidate_filter = f"""
        b.symbol = {_sql_string(scope_symbol)}
            AND b.bronze_timestamp BETWEEN
                TIMESTAMP({_sql_string(scope_start)})
                AND TIMESTAMP({_sql_string(scope_end)})
        """
        #records that actually need recalculation
        #     Limits the final output to the requested new/affected range.

    else:
        source_filter = ""
        candidate_filter = "TRUE"

    #replace the value with real values
    values = {
        "PROJECT_ID": PROJECT_ID,
        "BQ_LOCATION": get_bq_location(),
        "BRONZE_DATASET": BRONZE_DATASET,
        "BRONZE_TABLE": BRONZE_TABLE,
        "SILVER_DATASET": SILVER_DATASET,
        "BRONZE_SOURCE_FILTER": source_filter,
        "BRONZE_CANDIDATE_FILTER": candidate_filter,
    }

    #goes through each configuration values
    for key, value in values.items():
        sql = sql.replace(
            "{{" + key + "}}",
            #Finds placeholders in the SQL and replaces them.
            value
        )

    return sql


#run and find the sql file
#create silver table
#store procdure sql present in sql folder
def _run_sql_file(
    file_name,
    scope_symbol=None,
    scope_start=None,
    scope_end=None
):
    sql_path = ( # sql file path builder
        Path(__file__).parent
        / "sql"
        / file_name
    )

    #so here it read sql files
    #replace the value with real value
    #became the final sql
    sql = _render_sql(
        sql_path.read_text(),
        scope_symbol=scope_symbol,
        scope_start=scope_start,
        scope_end=scope_end
    )

    #excute the sql
    get_bq_client().query(
        sql
    ).result()     #wait until the bigwuery finish exectuing it
"""
Find SQL file
   ↓
Read it
   ↓
Fill in real values
   ↓
Run it in BigQuery
"""

def _query_one(query):
    rows = (
        get_bq_client()
        .query(query)
        .result()
    )# will return first row only

    return next(iter(rows), None)

#THIS FUNCTION IS FOR MONITORING BIGQUERY JOBS AND WAIT UNTIL IT FINSIH 
#this function is used to run the sql file and wait until bigquery finish executing it
def _wait_for_job_with_progress(job, label):
    started_at = datetime.now(timezone.utc)

    print(f"{label} BigQuery job id: {job.job_id}")
    print(f"{label} start time: {started_at.isoformat()}")

    #job not done means still running so we wait until it finish
    while not job.done():
        elapsed_minutes = (
            datetime.now(timezone.utc) - started_at
        ).total_seconds() / 60

        """print(
            f"{label} still running: "
            f"{elapsed_minutes:.1f} minutes elapsed"
        )"""

        time.sleep(60)

        #check again/refreshes the job status gtom bigquery
        job.reload()

    #if job is done retunr the result
    result = job.result()

    ended_at = datetime.now(timezone.utc)
    #Records when the job ended.

    elapsed_minutes = (
        ended_at - started_at
    ).total_seconds() / 60

    print(f"{label} end time: {ended_at.isoformat()}")
    print(f"{label} total time: {elapsed_minutes:.1f} minutes")

    return result


#this function makes sure silver table and stored procedure are available
def ensure_silver_objects(
    scope_symbol=None,
    scope_start=None,
    scope_end=None
):

    _run_sql_file(
        "01_create_silver_tables.sql"
    )

    _run_sql_file(
        "02_sp_bronze_to_silver.sql",
        scope_symbol=scope_symbol,
        scope_start=scope_start,
        scope_end=scope_end
    )


def run_silver_pipeline(
    scope_symbol=None,
    scope_start=None,
    scope_end=None
):
    ensure_silver_objects(
        scope_symbol=scope_symbol,
        scope_start=scope_start,
        scope_end=scope_end
    )

    """print("=" * 60)
    print("Silver pipeline starting")
    print("=" * 60)"""
    #checker for incremental 
    if scope_symbol and scope_start and scope_end:
        print("Silver incremental scope")
        print(f"  symbol: {scope_symbol}")
        print(f"  start: {scope_start}")
        print(f"  end: {scope_end}")

    procedure_id = (
        f"`{PROJECT_ID}."
        f"{SILVER_DATASET}."
        "sp_bronze_to_silver`"
    )
    #Calls the stored procedure in BigQuery.
    job = get_bq_client().query(
        f"CALL {procedure_id}()"
    )

    _wait_for_job_with_progress(
        job,
        "Silver pipeline"
    )

    print(
        "Silver pipeline completed"
    )

    if RUN_GOLD_AFTER_SILVER:
        from transform.gold.gold import run_gold_pipeline

        run_gold_pipeline(
            scope_symbol=scope_symbol,
            scope_start=scope_start,
            scope_end=scope_end
        )

