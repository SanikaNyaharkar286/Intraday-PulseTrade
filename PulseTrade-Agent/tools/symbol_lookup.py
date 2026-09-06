from config import PROJECT_ID, AI_DATASET
from tools.bigquery_client import execute_query


def resolve_symbol(
    company_name: str,
    limit: int = 10
):

    table = (
        f"`{PROJECT_ID}.{AI_DATASET}."
        "spot_ai_stock_summary`"
    )


    sql = f"""
    SELECT
        symbol,
        company_name
    FROM {table}

    WHERE LOWER(company_name)
    LIKE CONCAT('%', LOWER(@company_name), '%')

    OR LOWER(symbol)
    LIKE CONCAT('%', LOWER(@company_name), '%')

    LIMIT {limit}
    """


    result = execute_query(
        sql,
        parameters={
            "company_name": company_name
        }
    )


    return {
        "matches": result,
        "count": len(result)
    }