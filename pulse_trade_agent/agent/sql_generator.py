import yaml


PROJECT_ID = "project-001658fa-3ce5-4746-980"
DATASET = "pulse_trade_semantic"


class SQLGenerator:


    def __init__(self):
        pass



    def generate(self, intent_result):

        view = intent_result.get("view")

        filters = intent_result.get("filters", [])


        if not view:

            raise Exception(
                "No semantic view found"
            )


        table_reference = (
            f"`{PROJECT_ID}.{DATASET}.{view}`"
        )


        query = f"""
SELECT *
FROM {table_reference}
"""


        if filters:

            where_conditions = []


            for condition in filters:

                column = condition["column"]
                operator = condition["operator"]
                value = condition["value"]


                if isinstance(value, bool):

                    value = str(value).upper()


                elif isinstance(value, str):

                    value = f"'{value}'"


                where_conditions.append(
                    f"{column} {operator} {value}"
                )


            query += "\nWHERE\n"

            query += (
                " AND\n".join(where_conditions)
            )


        query += """

LIMIT 50
"""


        return query.strip()