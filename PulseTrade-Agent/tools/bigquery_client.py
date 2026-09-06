from google.cloud import bigquery
from datetime import date, datetime


def execute_query(sql, parameters=None):

    client = bigquery.Client()

    query_parameters = []

    if parameters:
        for key, value in parameters.items():

            if isinstance(value, float):
                param_type = "FLOAT64"

            elif isinstance(value, int):
                param_type = "INT64"

            elif isinstance(value, date):
                param_type = "DATE"

            else:
                param_type = "STRING"


            query_parameters.append(
                bigquery.ScalarQueryParameter(
                    key,
                    param_type,
                    value
                )
            )


    job_config = bigquery.QueryJobConfig(
        query_parameters=query_parameters,
        use_query_cache=True
    )


    query_job = client.query(
        sql,
        job_config=job_config
    )


    results = []

    for row in query_job.result():

        record = dict(row)

        for key, value in record.items():

            if isinstance(value, (date, datetime)):
                record[key] = value.isoformat()


        results.append(record)


    return results