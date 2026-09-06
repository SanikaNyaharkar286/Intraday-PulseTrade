CURRENT_MARKET_STATE_SCHEMA = """

============================================================
TABLE: spot_ai_current_market_state
============================================================


Purpose:

Contains the latest market snapshot for each stock symbol.

This table represents the current/latest technical state
of stocks.

Data Grain:

One latest record per symbol.



------------------------------------------------------------
COLUMN DEFINITIONS
------------------------------------------------------------


symbol

Data Type:
STRING

Description:

Unique stock ticker identifier.



------------------------------------------------------------


company_name

Data Type:
STRING

Description:

Name of the company associated with the stock symbol.



------------------------------------------------------------


sector

Data Type:
STRING

Description:

Industry sector classification of the company.



------------------------------------------------------------


trade_date

Data Type:
DATE

Description:

Trading date for the market snapshot.






timestamp

Data Type:
DATETIME

Description:

Timestamp when the market snapshot was recorded.






close

Data Type:
FLOAT64

Description:

Latest closing price of the stock.






day_return_pct

Data Type:
FLOAT64

Description:

Percentage price return for the trading day.






volume

Data Type:
FLOAT64

Description:

Total traded volume for the stock.





relative_volume

Data Type:
FLOAT64

Description:

Current trading volume compared with average volume.

Higher values indicate unusual trading activity.






rsi_14

Data Type:
FLOAT64

Description:

14-period Relative Strength Index indicator.

Used as a momentum measurement.






macd

Data Type:
FLOAT64

Description:

Moving Average Convergence Divergence value.

Used for momentum and trend analysis.






macd_signal

Data Type:
FLOAT64

Description:

MACD signal line value.

Used for MACD comparison analysis.






ema_9

Data Type:
FLOAT64

Description:

9-period Exponential Moving Average.

Represents short-term price trend.






ema_20

Data Type:
FLOAT64

Description:

20-period Exponential Moving Average.

Represents medium-term price trend.






vwap

Data Type:
FLOAT64

Description:

Volume Weighted Average Price.

Represents the average price weighted by trading volume.





price_vs_vwap

Data Type:
STRING

Description:

Relationship between current price and VWAP.






price_vs_ema20

Data Type:
STRING

Description:

Relationship between current price and EMA20.






price_vs_sma20

Data Type:
STRING

Description:

Relationship between current price and SMA20.






volume_status

Data Type:
STRING

Description:

Categorical classification of current volume condition.






trend

Data Type:
STRING

Description:

Current stock trend classification.






momentum_score

Data Type:
INT64

Description:

Calculated momentum ranking score.

Higher values represent stronger momentum.






processed_at

Data Type:
TIMESTAMP

Description:

Timestamp when the semantic record was processed.

Used for data freshness tracking.



"""
SIGNAL_HISTORY_SCHEMA = """


TABLE: spot_ai_signal_history_90d



Purpose:

Contains historical technical trading signals generated from
intraday market analysis.


Data Grain:

One record per:

symbol + trade_date + timestamp + timeframe + signal_type

COLUMN DEFINITIONS
symbol

Data Type:
STRING
Description:
Stock ticker identifier associated with the signal.
trade_date
Data Type:
DATE
Description:
Trading date when the signal occurred.
timestamp
Data Type:
DATETIME
Description:
Exact timestamp when the technical signal was generated.
timeframe
Data Type:
STRING
Description:
Intraday candle timeframe used for generating the signal.
Available values:

1M:
One minute candle timeframe.


5M:
Five minute candle timeframe.






signal_type

Data Type:
STRING

Description:

Category of technical trading signal generated.


Examples of signal categories:

- MACD_BULLISH_CROSSOVER
- MACD_BEARISH_CROSSOVER
- EMA_BULLISH_CROSSOVER
- EMA_BEARISH_CROSSOVER
- DAY_HIGH_BREAKOUT
- DAY_LOW_BREAKDOWN
- VOLUME_BREAKOUT
- VWAP_CROSS_UP
- VWAP_CROSS_DOWN






signal_value

Data Type:
FLOAT64

Description:

Numeric value associated with the generated signal.

Represents the signal measurement or strength
calculated by the pipeline.






reference_value

Data Type:
FLOAT64

Description:

Reference or comparison value used for evaluating
the signal condition.






processed_at

Data Type:
TIMESTAMP

Description:

Timestamp when the semantic record was processed.

Used for data freshness tracking.



"""
INTRADAY_HISTORY_SCHEMA = """
TABLE: spot_ai_intraday_history_90d

Purpose:
Contains historical intraday price movements and technical
indicator values for stocks.
This table is used for analyzing intraday behavior,
price movement, volatility, and technical indicator trends.
Data Grain:
One record per:
symbol + trade_date + timestamp + timeframe

COLUMN DEFINITIONS

symbol
Data Type:
STRING
Description:
Stock ticker identifier.
trade_date
Data Type:
DATE
Description:
Trading date for the intraday record.
timestamp
Data Type:
DATETIME
Description:
Timestamp of the intraday candle.
timeframe
Data Type:
STRING
Description:
Intraday candle interval used for the record.
Available values:
1M:
One minute candle timeframe.
5M:
Five minute candle timeframe.
open
Data Type:
FLOAT64
Description:
Opening price of the candle.
high
Data Type:
FLOAT64
Description:
Highest price reached during the candle period.
low
Data Type:
FLOAT64
Description:
Lowest price reached during the candle period.
close
Data Type:
FLOAT64
Description:
Closing price of the candle.
volume
Data Type:
FLOAT64
Description:
Trading volume during the candle period.
rsi_14
Data Type:
FLOAT64
Description:
14-period Relative Strength Index indicator.
Used to measure momentum conditions.
macd
Data Type:
FLOAT64
Description:
Moving Average Convergence Divergence value.
Used for momentum and trend analysis.
macd_signal
Data Type:
FLOAT64
Description:
MACD signal line value.
Used for MACD comparison analysis.
ema_9
Data Type:
FLOAT64
Description:
9-period Exponential Moving Average.
Represents short-term price trend.
ema_20
Data Type:
FLOAT64
Description:
20-period Exponential Moving Average.
Represents medium-term price trend.
vwap
Data Type:
FLOAT64
Description:
Volume Weighted Average Price.
Represents average traded price weighted by volume.
relative_volume
Data Type:
FLOAT64
Description:
Current candle volume compared with average volume.
Used to identify unusual volume activity.
processed_at
Data Type:
TIMESTAMP
Description:
Timestamp when the semantic record was processed.
Used for data freshness tracking.
"""
DAILY_HISTORY_SCHEMA = """

TABLE: spot_ai_daily_history

Purpose:
Contains historical daily price movements and volume metrics
for stocks.
This table is used for longer-term performance analysis,
historical comparison, returns analysis, and daily behavior.
Data Grain:
One record per:
symbol + trade_date
COLUMN DEFINITIONS
symbol
Data Type:
STRING
Description:
Stock ticker identifier.
trade_date
Data Type:
DATE
Description:
Trading date for the daily market record.
open
Data Type:
FLOAT64
Description:
Opening price of the stock for the trading day.
high
Data Type:
FLOAT64
Description:
Highest traded price during the trading day.
low
Data Type:
FLOAT64
Description:
Lowest traded price during the trading day.
close
Data Type:
FLOAT64
Description:
Closing price of the stock for the trading day.
volume
Data Type:
FLOAT64
Description:
Total trading volume for the trading day.
previous_close
Data Type:
FLOAT64
Description:
Previous trading day's closing price.
Used for calculating daily price movement.
return_pct
Data Type:
FLOAT64
Description:
Percentage return generated during the trading day.
gap_pct
Data Type:
FLOAT64
Description:
Percentage difference between current opening price
and previous closing price.
Used for identifying gap-up or gap-down movements.
daily_range_pct
Data Type:
FLOAT64
Description:
Percentage price range during the trading day.
Represents daily volatility.
avg_volume_20
Data Type:
FLOAT64
Description:
20-day average trading volume.
Used as a benchmark for comparing current volume activity.
relative_volume
Data Type:
FLOAT64
Description:
Current trading volume compared with average volume.
Higher values indicate unusual trading activity.
processed_at
Data Type:
TIMESTAMP
Description:
Timestamp when the semantic record was processed.
Used for data freshness tracking.
"""
INTRADAY_BEHAVIOR_SCHEMA = """

TABLE: spot_ai_intraday_behavior
Purpose:
Contains derived intraday trading behavior metrics.
This table captures daily intraday patterns such as:
- gap movements
- VWAP holding behavior
- breakout conditions
- breakdown conditions
- intraday trend behavior
Data Grain:
One record per:
symbol + trade_date

COLUMN DEFINITIONS

symbol
Data Type:
STRING
Description:
Stock ticker identifier.
trade_date
Data Type:
DATE
Description:
Trading date for the intraday behavior record.
open_price
Data Type:
FLOAT64
Description:
Opening price of the stock for the trading session.
previous_close
Data Type:
FLOAT64
Description:
Previous trading day's closing price.
Used for calculating gap movement.
day_high
Data Type:
FLOAT64
Description:
Highest price reached during the trading session.
day_low
Data Type:
FLOAT64
Description:
Lowest price reached during the trading session.
close_price
Data Type:
FLOAT64
Description:
Closing price of the stock for the trading session.
gap_pct
Data Type:
FLOAT64
Description:
Percentage difference between opening price and
previous closing price.
Used to identify gap-up and gap-down movements.
intraday_range_pct
Data Type:
FLOAT64
Description:
Percentage movement between day high and day low.
Represents intraday volatility range.
total_volume
Data Type:
FLOAT64
Description:
Total trading volume during the trading session.
avg_volume
Data Type:
FLOAT64
Description:
Average trading volume used as a comparison benchmark.
avg_vwap
Data Type:
FLOAT64
Description:
Average Volume Weighted Average Price during the session.
vwap_hold_percentage
Data Type:
FLOAT64
Description:
Percentage of the trading session where price remained
above VWAP.
Used to evaluate intraday strength.
high_breakout_flag
Data Type:
BOOL
Description:
Indicates whether the stock achieved a high breakout
condition during the session.
low_breakdown_flag
Data Type:
BOOL
Description:
Indicates whether the stock achieved a low breakdown
condition during the session.
day_trend
Data Type:
STRING
Description:
Overall intraday trend classification.
processed_at
Data Type:
TIMESTAMP
Description:
Timestamp when the semantic record was processed.
Used for data freshness tracking.
"""
STOCK_SUMMARY_SCHEMA = """

TABLE: spot_ai_stock_summary

Purpose:
Contains summarized stock-level metrics for quick analysis,
screening, ranking, and comparison.
This table provides pre-calculated performance,
risk, momentum, and trend information.
Data Grain:
One record per:
symbol
COLUMN DEFINITIONS
symbol
Data Type:
STRING
Description:
Stock ticker identifier.
return_90d_pct
Data Type:
FLOAT64
Description:
Total percentage return generated by the stock
over the last 90 trading days.
avg_daily_range_pct
Data Type:
FLOAT64
Description:
Average daily price movement percentage.
Represents average daily volatility.
avg_volume_90d
Data Type:
FLOAT64
Description:
Average trading volume over the last 90 days.
latest_close
Data Type:
FLOAT64
Description:
Most recent closing price available for the stock.
latest_rsi
Data Type:
FLOAT64
Description:
Latest 14-period Relative Strength Index value.
Used for current momentum condition analysis.
latest_momentum_score
Data Type:
INT64
Description:
Latest calculated momentum score.
Higher values indicate stronger momentum.
current_trend
Data Type:
STRING
Description:
Current trend classification of the stock.
volume_status
Data Type:
STRING
Description:
Current volume activity classification.
Indicates whether volume is normal or unusual.
processed_at
Data Type:
TIMESTAMP
Description:
Timestamp when the semantic record was processed.
Used for data freshness tracking.
"""
AI_SCHEMA = f"""
{CURRENT_MARKET_STATE_SCHEMA}
{SIGNAL_HISTORY_SCHEMA}
{INTRADAY_HISTORY_SCHEMA}
{DAILY_HISTORY_SCHEMA}
{INTRADAY_BEHAVIOR_SCHEMA}
{STOCK_SUMMARY_SCHEMA}
"""