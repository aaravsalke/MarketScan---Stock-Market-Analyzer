# config.py
# WHY: Keep settings in one place so we do not bury "magic numbers"
# and app-wide constants inside other files.

APP_NAME = "MarketScan"

# Yahoo Finance is free and does not need an API key.
# We use the yfinance library to talk to it.
STOCK_DATA_SOURCE = "Yahoo Finance (via yfinance)"

# Module 2: Technical Analysis
SHORT_MOVING_AVERAGE_DAYS = 20
LONG_MOVING_AVERAGE_DAYS = 50
RSI_PERIOD_DAYS = 14
PRICE_HISTORY_PERIOD = "6mo"
SEARCH_MAX_RESULTS = 8

# Module 3: News
NEWS_MAX_ARTICLES = 8
