from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini

from instructions.semantic_instructions import (
    PULSE_TRADE_SEMANTIC_INSTRUCTIONS
)

from tools.bigquery_tools import execute_bigquery



root_agent = Agent(

    name="pulse_trade_agent",

    model=Gemini(
        model_name="gemini-3.5-flash"
    ),

    description="""
    AI stock market analyst for PulseTrade.
    Answers market questions using approved semantic views.
    """,


    instruction=PULSE_TRADE_SEMANTIC_INSTRUCTIONS,


    tools=[
        execute_bigquery
    ]

)