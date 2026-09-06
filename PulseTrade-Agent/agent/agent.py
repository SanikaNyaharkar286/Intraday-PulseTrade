from google.adk.agents import Agent

from agent.instructions import INSTRUCTIONS
from tools.comparison import analyze_stock_comparison
from tools.market_state import analyze_current_market
from tools.signals import analyze_signals
from tools.behavior import analyze_intraday_behavior
from tools.intraday import analyze_intraday_history
from tools.ranking import analyze_stock_ranking
from tools.daily import analyze_daily_history
from tools.symbol_lookup import resolve_symbol


root_agent = Agent(
    name="pulsetrade_ai",
    model="gemini-2.5-flash",
    description="""
    AI powered stock market analysis assistant.
    """,
    instruction=INSTRUCTIONS,
    tools=[

        analyze_current_market,
        analyze_signals,
        analyze_intraday_behavior,
        analyze_intraday_history,
        analyze_stock_ranking,
        analyze_daily_history,
        analyze_stock_comparison,
        resolve_symbol

    ]
)