# stock_data.py
# WHY: All internet lookups for stocks live here.
# Other files ask for a quote, a search list, or price history.
# They should not talk to Yahoo Finance themselves.

import logging

import yfinance as yf

# yfinance sometimes prints ugly HTTP errors. We keep our own messages instead.
logging.getLogger("yfinance").setLevel(logging.CRITICAL)


def _pick_first_available(info, keys):
    """
    Yahoo sometimes uses different field names for the same idea.
    We try each key in order and return the first one that has a value.
    """
    for key in keys:
        value = info.get(key)
        if value is not None:
            return value
    return None


def is_valid_quote(info):
    """
    A real ticker should at least have a name or a price.
    Empty dictionaries usually mean the ticker does not exist.
    """
    if not info:
        return False

    name = _pick_first_available(info, ["longName", "shortName", "displayName"])
    price = _pick_first_available(info, ["currentPrice", "regularMarketPrice"])
    return name is not None or price is not None


def search_securities(query, max_results=8):
    """
    Search Yahoo by ticker OR company name.

    Example queries: "AAPL", "Apple", "microsoft"

    Returns:
        a list of dictionaries, each with ticker, company_name, and exchange
    """
    cleaned_query = query.strip()
    if cleaned_query == "":
        raise ValueError("Please enter a company name or ticker symbol.")

    try:
        search_result = yf.Search(cleaned_query, max_results=max_results)
        raw_matches = search_result.quotes
    except Exception as error:
        raise ConnectionError(
            "Could not search for that company. Check your internet connection."
        ) from error

    if not raw_matches:
        return []

    matches = []
    allowed_types = ["EQUITY", "ETF"]

    for item in raw_matches:
        quote_type = item.get("quoteType")
        if quote_type not in allowed_types:
            # Skip futures and other non-stock results
            continue

        ticker = item.get("symbol")
        if ticker is None:
            continue

        company_name = _pick_first_available(
            item, ["longname", "shortname", "longName", "shortName"]
        )
        exchange = _pick_first_available(item, ["exchDisp", "exchange"])

        matches.append(
            {
                "ticker": ticker,
                "company_name": company_name,
                "exchange": exchange,
            }
        )

        if len(matches) >= max_results:
            break

    return matches


def fetch_stock_quote(ticker_symbol):
    """
    Download quote data for one ticker.

    Call this only after search_securities() found a real match.
    That way we do not request data for fake tickers.

    Returns:
        a dictionary of stock facts

    Raises:
        ValueError: if the ticker is blank or not found
        ConnectionError: if the internet request fails
    """
    cleaned_symbol = ticker_symbol.strip().upper()

    if cleaned_symbol == "":
        raise ValueError("Please enter a ticker symbol.")

    try:
        stock = yf.Ticker(cleaned_symbol)
        info = stock.info
    except Exception as error:
        raise ConnectionError(
            "Could not download stock data. Check your internet connection."
        ) from error

    if not is_valid_quote(info):
        raise ValueError(
            f"No stock data found for '{cleaned_symbol}'. Check the name and try again."
        )

    company_name = _pick_first_available(
        info, ["longName", "shortName", "displayName"]
    )
    current_price = _pick_first_available(
        info, ["currentPrice", "regularMarketPrice"]
    )
    previous_close = _pick_first_available(
        info, ["previousClose", "regularMarketPreviousClose"]
    )
    week_52_high = info.get("fiftyTwoWeekHigh")
    week_52_low = info.get("fiftyTwoWeekLow")
    market_cap = info.get("marketCap")
    volume = _pick_first_available(info, ["volume", "regularMarketVolume"])

    quote = {
        "ticker": cleaned_symbol,
        "company_name": company_name,
        "current_price": current_price,
        "previous_close": previous_close,
        "week_52_high": week_52_high,
        "week_52_low": week_52_low,
        "market_cap": market_cap,
        "volume": volume,
    }
    return quote


def fetch_price_history(ticker_symbol, period="6mo"):
    """
    Download daily closing prices for charts and indicators.

    period examples: "3mo", "6mo", "1y"

    Returns:
        a dictionary with two lists: dates and closing_prices
    """
    cleaned_symbol = ticker_symbol.strip().upper()

    try:
        stock = yf.Ticker(cleaned_symbol)
        history = stock.history(period=period)
    except Exception as error:
        raise ConnectionError(
            "Could not download price history. Check your internet connection."
        ) from error

    if history is None or len(history) == 0:
        raise ValueError(f"No price history found for '{cleaned_symbol}'.")

    dates = []
    closing_prices = []

    for date_value in history.index:
        dates.append(date_value.strftime("%Y-%m-%d"))

    for price in history["Close"].tolist():
        closing_prices.append(float(price))

    return {
        "ticker": cleaned_symbol,
        "dates": dates,
        "closing_prices": closing_prices,
    }
