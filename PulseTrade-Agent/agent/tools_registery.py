from tools.market_state import analyze_current_market
from tools.signals import analyze_signals
from tools.behavior import analyze_intraday_behavior
from tools.intraday import analyze_intraday_history
from tools.ranking import analyze_stock_ranking
from tools.daily import analyze_daily_history


TOOLS = [
    analyze_current_market,
    analyze_signals,
    analyze_intraday_behavior,
    analyze_intraday_history,
    analyze_stock_ranking,
    analyze_daily_history
]