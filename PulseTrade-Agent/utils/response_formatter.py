import pandas as pd


def format_response(data, question):

    if not data:
        return {
            "text": """
No matching data was found.

Try changing the criteria or timeframe.
""",
            "table": None
        }


    df = pd.DataFrame(data)


    text = f"""
## PulseTrade AI Analysis

**Question analyzed**

{question}


**Observation**

The analysis returned {len(df)} matching records.

The results below are based on historical market data
available in the semantic layer.


**Interpretation**

The metrics indicate observed market behavior.
They should be considered historical observations
and not investment recommendations.
"""


    return {
        "text": text,
        "table": df
    }