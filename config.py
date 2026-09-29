# config.py
# WHY: Keep settings in one place so we do not bury "magic numbers",
# API keys, and app-wide constants inside other files.

import os

APP_NAME = "MarketScan"

# Load simple .env file if present
def _load_env_file():
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip().strip("'\"")
                    if key and not os.environ.get(key):
                        os.environ[key] = val

_load_env_file()

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "").strip()
GROQ_MODEL = "llama-3.3-70b-versatile"  # High performance free tier model on Groq

# Yahoo Finance is free and does not need an API key.
STOCK_DATA_SOURCE = "Yahoo Finance (via yfinance)"

# Module 2: Technical Analysis
SHORT_MOVING_AVERAGE_DAYS = 20
LONG_MOVING_AVERAGE_DAYS = 50
RSI_PERIOD_DAYS = 14
PRICE_HISTORY_PERIOD = "2y"
SEARCH_MAX_RESULTS = 8

# Module 3: News
NEWS_MAX_ARTICLES = 8
NEWS_FETCH_LIMIT = 30
NEWS_RELEVANCE_THRESHOLD = 20

# Dash website
DASH_HOST = "127.0.0.1"
DASH_PORT = 8050

# Moving-average slider
MA_SLIDER_MIN = 1
MA_SLIDER_MAX = 300
MA_SLIDER_STEP = 1
MA_SLIDER_DEFAULT = 20
