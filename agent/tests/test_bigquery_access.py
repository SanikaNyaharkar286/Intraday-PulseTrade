from google.cloud import bigquery


client = bigquery.Client()


def test_query(sql):

    print("\nRunning:")
    print(sql)

    try:

        result = client.query(sql).result()

        for row in result:
            print(dict(row))

        print("SUCCESS")

    except Exception as e:
        print("FAILED")
        print(e)



# Should PASS
test_query("""
SELECT *
FROM `project-001658fa-3ce5-4746-980.pulse_trade_semantic.ai_vw_scanner`
LIMIT 5
""")


# Should PASS
test_query("""
SELECT *
FROM `project-001658fa-3ce5-4746-980.pulse_trade_ai.ai_current_intraday_snapshot`
LIMIT 5
""")


# Should FAIL
test_query("""
SELECT *
FROM `project-001658fa-3ce5-4746-980.pulse_trade_gold.fact_intraday_metrics`
LIMIT 5
""")