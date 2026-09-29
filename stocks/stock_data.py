# stock_data.py
# WHY: All internet lookups for stocks live here.
# Handles quotes, currency detection, search, and historical prices for domestic & international stocks.

import logging
import yfinance as yf

logging.getLogger("yfinance").setLevel(logging.CRITICAL)


def _pick_first_available(info, keys):
    """Try each key in order and return the first one with a value."""
    for key in keys:
        value = info.get(key)
        if value is not None:
            return value
    return None


def is_valid_quote(info):
    """A real ticker should at least have a name or a price."""
    if not info:
        return False
    name = _pick_first_available(info, ["longName", "shortName", "displayName"])
    price = _pick_first_available(info, ["currentPrice", "regularMarketPrice"])
    return name is not None or price is not None


def search_securities(query, max_results=8):
    """
    Search Yahoo by ticker OR company name.
    Supports domestic and international stocks.
    """
    cleaned_query = query.strip()
    if cleaned_query == "":
        raise ValueError("Please enter a company name or ticker symbol.")

    matches = []
    allowed_types = ["EQUITY", "ETF"]

    try:
        search_result = yf.Search(cleaned_query, max_results=max_results)
        raw_matches = search_result.quotes or []
    except Exception:
        raw_matches = []

    for item in raw_matches:
        quote_type = item.get("quoteType", "").upper()
        if quote_type and quote_type not in allowed_types:
            continue

        ticker = item.get("symbol")
        if not ticker:
            continue

        company_name = _pick_first_available(
            item, ["longname", "shortname", "longName", "shortName"]
        )
        exchange = _pick_first_available(item, ["exchDisp", "exchange"])

        matches.append(
            {
                "ticker": ticker,
                "company_name": company_name or ticker,
                "exchange": exchange,
            }
        )
        if len(matches) >= max_results:
            break

    # Direct ticker fallback: If search returned nothing, check if query itself is a valid ticker
    if not matches:
        try:
            ticker_upper = cleaned_query.upper()
            direct_stock = yf.Ticker(ticker_upper)
            info = direct_stock.info
            if is_valid_quote(info):
                name = _pick_first_available(info, ["longName", "shortName", "displayName"]) or ticker_upper
                exch = info.get("exchange", "")
                matches.append(
                    {
                        "ticker": ticker_upper,
                        "company_name": name,
                        "exchange": exch,
                    }
                )
        except Exception:
            pass

    return matches


def fetch_stock_quote(ticker_symbol):
    """
    Download quote data for one ticker.
    Captures native currency, company fundamentals, and valuation metrics.
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
    
    # Native Currency Detection
    currency = info.get("currency") or info.get("financialCurrency") or "USD"

    # Fundamentals for AI Analysis
    sector = info.get("sector", "N/A")
    industry = info.get("industry", "N/A")
    pe_ratio = info.get("trailingPE") or info.get("forwardPE")
    business_summary = info.get("longBusinessSummary", "")

    quote = {
        "ticker": cleaned_symbol,
        "company_name": company_name,
        "current_price": current_price,
        "previous_close": previous_close,
        "week_52_high": week_52_high,
        "week_52_low": week_52_low,
        "market_cap": market_cap,
        "volume": volume,
        "currency": currency,
        "sector": sector,
        "industry": industry,
        "pe_ratio": pe_ratio,
        "business_summary": business_summary,
    }
    return quote


def fetch_price_history(ticker_symbol, period="6mo"):
    """
    Download daily closing prices for charts and indicators.
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
