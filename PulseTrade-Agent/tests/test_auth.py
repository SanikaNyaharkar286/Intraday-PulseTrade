from google.cloud import bigquery


client = bigquery.Client()

query = """
SELECT SESSION_USER()
"""

result = client.query(query).result()

for row in result:
    print(row[0])