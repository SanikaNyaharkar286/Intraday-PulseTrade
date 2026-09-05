import pandas as pd


def format_agent_response(result, question):

    if not result:
        return """
No matching data was found.

Try changing your criteria or timeframe.
"""


    df = pd.DataFrame(result)


    response = f"""
## PulseTrade AI Analysis

Question:
{question}


### Observation

The analysis returned {len(df)} matching records.


### Results

"""


    response += df.to_markdown(
        index=False
    )


    response += """

### Interpretation

The results show observed market behavior
based on available technical indicators.

This is historical analysis and not investment advice.
"""


    return response