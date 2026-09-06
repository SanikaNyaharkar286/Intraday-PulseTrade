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


    response = {
        "text": "",
        "table": None
    }


    # -----------------------------
    # Gemini text response
    # -----------------------------

    if isinstance(data, str):

        response["text"] = f"""
## 📈 PulseTrade AI Analysis

**Question**

{question}


**Response**

{data}


⚠️ This analysis is based on available market data 
and should not be considered investment advice.
"""

        return response



    # -----------------------------
    # Dictionary response
    # -----------------------------

    if isinstance(data, dict):

        response["text"] = data.get(
            "text",
            str(data)
        )


        if "data" in data:

            response["table"] = pd.DataFrame(
                data["data"]
            )


        return response



    # -----------------------------
    # BigQuery rows
    # -----------------------------

    if isinstance(data, list):

        df = pd.DataFrame(data)


        response["text"] = f"""
## 📈 PulseTrade AI Analysis

**Question**

{question}


**Observation**

The analysis returned 
**{len(df)} matching records**.


The results are based on market data 
available through the PulseTrade semantic layer.


⚠️ This is historical market analysis and 
not investment advice.
"""


        response["table"] = df

        return response



    # -----------------------------
    # Fallback
    # -----------------------------

    response["text"] = str(data)

    return response