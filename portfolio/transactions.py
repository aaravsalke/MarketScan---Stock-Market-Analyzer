# transactions.py
# WHY: Every buy/sell trade gets recorded here.
# The transaction log lets the user look back at their history,
# and it also helps us verify portfolio math later.

from datetime import datetime

from utils.storage import load_json, save_json

TRANSACTIONS_FILE = "data/transactions.json"


def _load_transactions():
    """Load the list of past transactions from disk."""
    return load_json(TRANSACTIONS_FILE, [])


def _save_transactions(transactions):
    """Write the full transactions list back to disk."""
    save_json(TRANSACTIONS_FILE, transactions)


def record_transaction(action, ticker, shares, price_per_share, total_amount):
    """
    Add one trade to the transaction history.

    Parameters:
        action          : "BUY" or "SELL"
        ticker          : stock symbol like "AAPL"
        shares          : number of shares traded
        price_per_share : the price at the moment of the trade
        total_amount    : shares * price_per_share (cost for buy, proceeds for sell)
    """
    transactions = _load_transactions()

    new_record = {
        "action": action,
        "ticker": ticker.strip().upper(),
        "shares": shares,
        "price_per_share": price_per_share,
        "total_amount": total_amount,
        # strftime turns a datetime object into a readable string like "2026-09-27 14:30"
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }

    # We add the newest trade at the front so the table shows newest-first
    transactions.insert(0, new_record)

    # Keep a maximum of 200 records so the file stays small
    if len(transactions) > 200:
        transactions = transactions[:200]

    _save_transactions(transactions)


def get_transactions():
    """
    Return the full list of past trades, newest first.

    Each item in the list is a dictionary:
    {
        "action": "BUY",
        "ticker": "AAPL",
        "shares": 10,
        "price_per_share": 182.50,
        "total_amount": 1825.00,
        "timestamp": "2026-09-27 14:30"
    }
    """
    return _load_transactions()


def clear_transactions():
    """Wipe all transaction history. Used when resetting the portfolio."""
    _save_transactions([])
