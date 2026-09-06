from google.cloud import bigquery
from datetime import date, datetime


def execute_query(sql, parameters=None):

    client = bigquery.Client()

    query_parameters = []


    if parameters:

        for key, value in parameters.items():


            # Handle array parameters
            if isinstance(value, list):

                query_parameters.append(
                    bigquery.ArrayQueryParameter(
                        key,
                        "STRING",
                        value
                    )
                )


            # Handle float
            elif isinstance(value, float):

                query_parameters.append(
                    bigquery.ScalarQueryParameter(
                        key,
                        "FLOAT64",
                        value
                    )
                )


            # Handle integer
            elif isinstance(value, int):

                query_parameters.append(
                    bigquery.ScalarQueryParameter(
                        key,
                        "INT64",
                        value
                    )
                )


            # Handle date
            elif isinstance(value, date):

                query_parameters.append(
                    bigquery.ScalarQueryParameter(
                        key,
                        "DATE",
                        value
                    )
                )


            # Handle string
            else:

                query_parameters.append(
                    bigquery.ScalarQueryParameter(
                        key,
                        "STRING",
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