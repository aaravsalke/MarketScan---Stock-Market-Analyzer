# watchlist.py
# WHY: A watchlist is a simple list of tickers the user wants to follow
# without actually buying them yet.
# We store it in data/watchlist.json — just a list of ticker strings.

from utils.storage import load_json, save_json

WATCHLIST_FILE = "data/watchlist.json"


def _load_watchlist():
    """Load the list of tickers from disk."""
    return load_json(WATCHLIST_FILE, [])


def _save_watchlist(watchlist):
    """Write the watchlist back to disk."""
    save_json(WATCHLIST_FILE, watchlist)


def get_watchlist():
    """
    Return the current watchlist as a list of ticker strings.
    Example: ["AAPL", "MSFT", "NVDA"]
    """
    return _load_watchlist()


def add_to_watchlist(ticker):
    """
    Add a ticker to the watchlist.

    Returns:
        A dictionary with "success" (True/False) and "message".
    """
    ticker = ticker.strip().upper()
    if ticker == "":
        return {"success": False, "message": "Ticker cannot be blank."}

    watchlist = _load_watchlist()

    if ticker in watchlist:
        return {"success": False, "message": f"{ticker} is already in your watchlist."}

    if len(watchlist) >= 20:
        return {
            "success": False,
            "message": "Watchlist is full (20 stocks maximum). Remove one first.",
        }

    watchlist.append(ticker)
    _save_watchlist(watchlist)
    return {"success": True, "message": f"{ticker} added to your watchlist."}


def remove_from_watchlist(ticker):
    """
    Remove a ticker from the watchlist.

    Returns:
        A dictionary with "success" (True/False) and "message".
    """
    ticker = ticker.strip().upper()
    watchlist = _load_watchlist()

    if ticker not in watchlist:
        return {"success": False, "message": f"{ticker} is not in your watchlist."}

    watchlist.remove(ticker)
    _save_watchlist(watchlist)
    return {"success": True, "message": f"{ticker} removed from your watchlist."}
