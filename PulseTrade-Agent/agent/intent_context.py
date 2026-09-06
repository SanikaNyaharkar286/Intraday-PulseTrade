from typing import Literal
BehaviorIntent = Literal[
    "gap_screening",
    "vwap_hold_analysis",
    "breakout_screening",
    "breakdown_screening",
    "trend_behavior"
]
DailyIntent = Literal[
    "stock_performance",
    "stock_comparison",
    "return_ranking",
    "volatility_ranking",
    "price_history"
]
MarketIntent = Literal[
    "symbol_overview",
    "rsi_screening",
    "momentum_ranking",
    "trend_screening",
    "volume_screening",
    "vwap_screening"
]
SignalIntent = Literal[
    "latest_signal",
    "signal_screening",
    "stock_signal_history",
    "timeframe_signal_analysis"
]
SIGNAL_KEYWORDS = {
    "MACD bullish": 
        "MACD_BULLISH_CROSSOVER",
    "MACD bearish":
        "MACD_BEARISH_CROSSOVER",
    "EMA bullish":
        "EMA_BULLISH_CROSSOVER",
    "EMA bearish":
        "EMA_BEARISH_CROSSOVER",
    "above VWAP":
        "VWAP_CROSS_UP",
    "below VWAP":
        "VWAP_CROSS_DOWN",
    "breaking highs":
        "DAY_HIGH_BREAKOUT",
    "breakout":
        "DAY_HIGH_BREAKOUT",
    "breaking lows":
        "DAY_LOW_BREAKDOWN",
    "high volume breakout":
        "VOLUME_BREAKOUT"
}
INTENT_CONTEXT = """


PULSETRADE AI INTENT ROUTING
Your responsibility:
Understand the user's question,
identify the financial analysis intent,
and select the correct semantic data source.
Never directly query raw datasets.
Always use the semantic tables defined below.
"""
INTENT_CONTEXT += """
Intraday behavior screening:
Use analyze_intraday_behavior for:
- Which stocks showed VWAP holding?
- Which stocks had breakout behavior?
- Which stocks had gap movements?
For individual stock movement:
Use analyze_intraday_history.

1. CURRENT MARKET ANALYSIS
Purpose:
Answer questions about the latest market condition
of stocks.
Use table:
spot_ai_current_market_state
Use when user asks about:
Current price
Keywords:
- current price
- latest price
- today's price
- now
Required fields:
symbol
close
trade_date
Momentum analysis
Keywords:
- momentum
- strong momentum
- weak momentum
- trending stocks
Use fields:
symbol
momentum_score
trend
rsi_14
RSI analysis
Keywords:
- RSI
- oversold
- overbought
Use fields:
symbol
rsi_14
trend
Interpretation:
RSI < 30:
Potential oversold condition
RSI > 70:
Potential overbought condition
Volume analysis
Keywords:
- unusual volume
- high volume
- volume spike
Use fields:

symbol
volume
relative_volume
volume_status





VWAP analysis


Keywords:

- above VWAP
- below VWAP
- VWAP


Use fields:

symbol
vwap
price_vs_vwap

INTENT: stock_comparison

Purpose:
Compare two stocks using historical market metrics.

Examples:

"Compare RELIANCE and HDFCBANK"

"Compare HDFCBANK and ICICIBANK"

"Which performed better between TCS and INFY?"

"Compare VWAP deviation between two stocks"

Tool:
analyze_stock_comparison


Use:
spot_ai_daily_history
spot_ai_intraday_behavior



"""
INTENT_CONTEXT += """


6. STOCK SCREENING AND RANKING



Purpose:

Answer ranking, comparison,
and screening questions.


Use table:

spot_ai_stock_summary



Use when user asks:





Top performers


Keywords:

- top stocks
- best performers
- highest return
- strongest stocks


Use fields:

symbol
return_90d_pct






Momentum ranking


Keywords:

- strongest momentum
- momentum stocks


Use fields:

symbol
latest_momentum_score
latest_rsi
current_trend






Volatility ranking


Keywords:

- most volatile
- high volatility


Use fields:

symbol
avg_daily_range_pct






Volume ranking


Keywords:

- high volume stocks
- active stocks


Use fields:

symbol
avg_volume_90d
volume_status






Trend screening


Keywords:

- bullish stocks
- bearish stocks
- trending stocks


Use fields:

symbol
current_trend





Example questions:


"Top performing stocks in last 90 days"


"Which stocks have strongest momentum?"


"Show most volatile stocks"



"""
INTENT_CONTEXT += """


2. TECHNICAL SIGNAL ANALYSIS



Purpose:

Answer questions about generated technical signals.


Use table:

spot_ai_signal_history_90d



MACD signals


Keywords:

- MACD crossover
- MACD bullish
- MACD bearish


Signal mapping:


Bullish:

MACD_BULLISH_CROSSOVER


Bearish:

MACD_BEARISH_CROSSOVER






EMA signals


Keywords:

- EMA crossover
- moving average crossover


Signal mapping:


Bullish:

EMA_BULLISH_CROSSOVER


Bearish:

EMA_BEARISH_CROSSOVER






Breakout signals


Keywords:

- breakout
- high breakout


Signal mapping:

DAY_HIGH_BREAKOUT






Breakdown signals


Keywords:

- breakdown
- low breakdown


Signal mapping:

DAY_LOW_BREAKDOWN
VWAP signals
Keywords:
- crossed VWAP
- VWAP breakout
Signal mapping:
Above VWAP:
VWAP_CROSS_UP
Below VWAP:
VWAP_CROSS_DOWN
Volume breakout
Keywords:
- volume breakout
- unusual volume signal
Signal mapping:
VOLUME_BREAKOUT
"""
INTENT_CONTEXT += """
3. INTRADAY PRICE ANALYSIS
Purpose:
Analyze intraday price movement and indicators.
Use table:
spot_ai_intraday_history_90d
Use when user asks:
- intraday movement
- 5 minute analysis
- 1 minute analysis
- candle movement
- session analysis
- VWAP movement
Important:
Available timeframes:
1M
5M
Fields:
symbol
timestamp
open
high
low
close
volume
rsi_14
macd
ema_9
ema_20
vwap
"""
INTENT_CONTEXT += """
4. DAILY HISTORICAL ANALYSIS
Purpose:
Answer questions related to historical daily stock
performance, returns, and long-term comparisons.
Use table:
spot_ai_daily_history
Use when user asks about:
Historical performance
Keywords:
- historical performance
- past performance
- previous years
- last year
- yearly performance
- long term
Use fields:
symbol
trade_date
open
high
low
close
return_pct

Return analysis
Keywords:
- returns
- percentage gain
- percentage loss
- performance
Use fields:
symbol
trade_date
return_pct

Gap analysis
Keywords:
- gap up
- gap down
- opening gap
Use fields:
symbol
trade_date
gap_pct

Volatility analysis
Keywords:
- daily volatility
- daily range
- price movement
Use fields:
symbol
daily_range_pct

Volume trend analysis
Keywords:
- volume trend
- average volume
- unusual daily volume
Use fields:
symbol
volume
avg_volume_20
relative_volume
Example questions:
"How did RELIANCE perform in 2025?"
"Which stocks had the highest returns this year?"
"Show stocks with large gap up openings"
"Compare historical returns of INFY and TCS"
"""
INTENT_CONTEXT += """
5. INTRADAY BEHAVIOR ANALYSIS

Purpose:
Analyze trading behavior patterns,
not just price movement.
Use table:
spot_ai_intraday_behavior
Use when user asks about:

Gap movements
Keywords:
- gap up
- gap down
- opened higher
- opened lower
Use fields:
symbol
trade_date
gap_pct

VWAP holding behavior
Keywords:
- held VWAP
- stayed above VWAP
- VWAP support
Use fields:
symbol
avg_vwap
vwap_hold_percentage

Breakout behavior
Keywords:
- breakout stocks
- high breakout
- broke resistance
Use fields:
symbol
high_breakout_flag
day_high
close_price

Breakdown behavior
Keywords:
- breakdown stocks
- broke support
- low breakdown
Use fields:
symbol
low_breakdown_flag
day_low
close_price
Intraday trend
Keywords:
- intraday trend
- session trend
- trading direction
Use fields:
symbol
day_trend
intraday_range_pct
Example questions:
"Which stocks gapped up today and held VWAP?"
"Which stocks showed high breakout behavior?"
"Find stocks with strong intraday trend"
"""