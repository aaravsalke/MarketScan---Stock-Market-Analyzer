# stock_search.py
# WHY: Users remember "Apple" more easily than "AAPL".
# This file turns a company name OR a ticker into a short list of matches.
# We search FIRST so we never ask Yahoo for a fake ticker (that caused the 404).

import logging

import yfinance as yf

from config import MAX_SEARCH_RESULTS

# yfinance prints extra HTTP errors. We hide those so the student
# only sees MarketScan's own messages.
logging.getLogger("yfinance").setLevel(logging.CRITICAL)


def search_stocks(user_query):
    """
    Search Yahoo Finance for companies that match a name or ticker.

    Returns:
        a list of dictionaries, each with:
            ticker, company_name, exchange

    Raises:
        ValueError: if the query is blank or nothing matches
        ConnectionError: if the internet request fails
    """
    cleaned_query = user_query.strip()

    if cleaned_query == "":
        raise ValueError("Please enter a company name or ticker.")

    try:
        search_results = yf.Search(
            cleaned_query,
            max_results=MAX_SEARCH_RESULTS,
            news_count=0,
        )
        raw_quotes = search_results.quotes
    except Exception as error:
        raise ConnectionError(
            "Could not search for that company. Check your internet connection."
        ) from error

    matches = []
    for quote in raw_quotes:
        # EQUITY means a regular stock, not a future or option
        if quote.get("quoteType") != "EQUITY":
            continue

        ticker = quote.get("symbol")
        company_name = quote.get("longname") or quote.get("shortname")
        exchange = quote.get("exchDisp") or quote.get("exchange")

        if ticker is None or company_name is None:
            continue

        matches.append(
            {
                "ticker": ticker,
                "company_name": company_name,
                "exchange": exchange,
            }
        )

    if len(matches) == 0:
        raise ValueError(
            f"No company found for '{cleaned_query}'. "
            "Try a ticker like AAPL, or a name like Apple."
        )

    return matches


def find_exact_ticker_match(matches, user_query):
    """
    If the user typed a ticker that is already in the list, return that match.
    Otherwise return None.
    """
    query_as_ticker = user_query.strip().upper()

    for match in matches:
        if match["ticker"].upper() == query_as_ticker:
            return match

    return None
