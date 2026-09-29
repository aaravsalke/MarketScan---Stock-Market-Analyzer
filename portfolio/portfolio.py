# portfolio.py
# WHY: All the logic for the virtual paper-trading portfolio lives here.
# The dashboard just calls these functions — it does not handle money math itself.
#
# Paper trading means we use fake/pretend money.
# Real money is never involved. This is an educational tool only.

from utils.storage import load_json, save_json

# Where the portfolio data lives on disk
PORTFOLIO_FILE = "data/portfolio.json"

# How much fake cash a brand-new user starts with
STARTING_CASH = 50_000.00


def _load_portfolio():
    """
    Load the portfolio from data/portfolio.json.

    The portfolio is stored as a dictionary:
    {
        "cash": 100000.0,
        "holdings": {
            "AAPL": {"shares": 10, "avg_cost": 175.50},
            "MSFT": {"shares": 5,  "avg_cost": 310.00}
        }
    }
    """
    default = {"cash": STARTING_CASH, "holdings": {}}
    return load_json(PORTFOLIO_FILE, default)


def _save_portfolio(portfolio):
    """Write the portfolio dictionary back to disk."""
    save_json(PORTFOLIO_FILE, portfolio)


def get_portfolio():
    """
    Return the full portfolio dictionary.
    Other modules call this to read the current state.
    """
    return _load_portfolio()


def get_cash():
    """Return how much fake cash is left."""
    portfolio = _load_portfolio()
    return portfolio.get("cash", STARTING_CASH)


def get_holdings():
    """
    Return the holdings dictionary.
    Example: {"AAPL": {"shares": 10, "avg_cost": 175.50}}
    """
    portfolio = _load_portfolio()
    return portfolio.get("holdings", {})


def buy_stock(ticker, shares, price_per_share):
    """
    Buy `shares` shares of `ticker` at `price_per_share`.

    Rules:
    - Ticker must be a non-empty string.
    - Shares must be a positive whole number.
    - Price must be a positive number.
    - The user must have enough fake cash.

    Returns:
        A dictionary with:
            "success"  : True or False
            "message"  : What happened (shown in the dashboard)
            "cost"     : Total cost of the trade (0 if failed)
    """
    # --- Input checks ---
    ticker = ticker.strip().upper()
    if ticker == "":
        return {"success": False, "message": "Ticker cannot be blank.", "cost": 0}

    try:
        shares = int(shares)
        price_per_share = float(price_per_share)
    except (ValueError, TypeError):
        return {
            "success": False,
            "message": "Shares and price must be valid numbers.",
            "cost": 0,
        }

    if shares <= 0:
        return {"success": False, "message": "Shares must be greater than zero.", "cost": 0}

    if price_per_share <= 0:
        return {"success": False, "message": "Price per share must be greater than zero.", "cost": 0}

    # --- Load and check cash ---
    portfolio = _load_portfolio()
    total_cost = shares * price_per_share
    current_cash = portfolio.get("cash", STARTING_CASH)

    if total_cost > current_cash:
        return {
            "success": False,
            "message": (
                f"Not enough cash. Trade costs ${total_cost:,.2f} "
                f"but you only have ${current_cash:,.2f}."
            ),
            "cost": 0,
        }

    # --- Update cash ---
    portfolio["cash"] = current_cash - total_cost

    # --- Update holdings using average cost method ---
    # If you already own AAPL at $150 (avg) and buy more at $160,
    # the new average sits somewhere in between.
    holdings = portfolio.get("holdings", {})

    if ticker in holdings:
        old_shares = holdings[ticker]["shares"]
        old_avg_cost = holdings[ticker]["avg_cost"]
        new_total_shares = old_shares + shares
        # Weighted average: blend the old cost with the new purchase cost
        new_avg_cost = (
            (old_shares * old_avg_cost) + (shares * price_per_share)
        ) / new_total_shares
        holdings[ticker]["shares"] = new_total_shares
        holdings[ticker]["avg_cost"] = new_avg_cost
    else:
        holdings[ticker] = {"shares": shares, "avg_cost": price_per_share}

    portfolio["holdings"] = holdings
    _save_portfolio(portfolio)

    return {
        "success": True,
        "message": (
            f"Bought {shares} share(s) of {ticker} at ${price_per_share:,.2f} each. "
            f"Total cost: ${total_cost:,.2f}."
        ),
        "cost": total_cost,
    }


def sell_stock(ticker, shares, price_per_share):
    """
    Sell `shares` shares of `ticker` at `price_per_share`.

    Rules:
    - The user must own that stock.
    - The user cannot sell more shares than they own.

    Returns:
        A dictionary with:
            "success"  : True or False
            "message"  : What happened
            "proceeds" : Cash received from the sale (0 if failed)
    """
    ticker = ticker.strip().upper()
    if ticker == "":
        return {"success": False, "message": "Ticker cannot be blank.", "proceeds": 0}

    try:
        shares = int(shares)
        price_per_share = float(price_per_share)
    except (ValueError, TypeError):
        return {
            "success": False,
            "message": "Shares and price must be valid numbers.",
            "proceeds": 0,
        }

    if shares <= 0:
        return {"success": False, "message": "Shares must be greater than zero.", "proceeds": 0}

    portfolio = _load_portfolio()
    holdings = portfolio.get("holdings", {})

    if ticker not in holdings:
        return {
            "success": False,
            "message": f"You do not own any shares of {ticker}.",
            "proceeds": 0,
        }

    owned_shares = holdings[ticker]["shares"]
    if shares > owned_shares:
        return {
            "success": False,
            "message": (
                f"Cannot sell {shares} share(s). You only own {owned_shares} share(s) of {ticker}."
            ),
            "proceeds": 0,
        }

    proceeds = shares * price_per_share
    portfolio["cash"] = portfolio.get("cash", STARTING_CASH) + proceeds

    remaining = owned_shares - shares
    if remaining == 0:
        del holdings[ticker]
    else:
        holdings[ticker]["shares"] = remaining

    portfolio["holdings"] = holdings
    _save_portfolio(portfolio)

    return {
        "success": True,
        "message": (
            f"Sold {shares} share(s) of {ticker} at ${price_per_share:,.2f} each. "
            f"Proceeds: ${proceeds:,.2f}."
        ),
        "proceeds": proceeds,
    }


def calculate_portfolio_value(current_prices):
    """
    Calculate the total market value of all holdings right now.

    Parameters:
        current_prices : a dictionary like {"AAPL": 182.50, "MSFT": 315.00}
                         These are the live prices from yfinance.

    Returns a dictionary with useful summary numbers.
    """
    portfolio = _load_portfolio()
    cash = portfolio.get("cash", STARTING_CASH)
    holdings = portfolio.get("holdings", {})

    holdings_value = 0.0
    total_cost_basis = 0.0
    rows = []

    for ticker, info in holdings.items():
        shares = info["shares"]
        avg_cost = info["avg_cost"]
        current_price = current_prices.get(ticker)

        cost_basis = shares * avg_cost
        total_cost_basis += cost_basis

        if current_price is not None:
            market_value = shares * current_price
            holdings_value += market_value
            profit_loss = market_value - cost_basis
            profit_loss_pct = (profit_loss / cost_basis) * 100 if cost_basis > 0 else 0
        else:
            market_value = None
            profit_loss = None
            profit_loss_pct = None

        rows.append(
            {
                "ticker": ticker,
                "shares": shares,
                "avg_cost": avg_cost,
                "current_price": current_price,
                "market_value": market_value,
                "profit_loss": profit_loss,
                "profit_loss_pct": profit_loss_pct,
            }
        )

    total_value = cash + holdings_value
    total_pl = holdings_value - total_cost_basis

    return {
        "cash": cash,
        "holdings_value": holdings_value,
        "total_value": total_value,
        "total_pl": total_pl,
        "cost_basis": total_cost_basis,
        "rows": rows,
    }


def reset_portfolio():
    """
    Wipe all holdings and restore the starting cash.
    Useful for testing or starting over.
    """
    fresh = {"cash": STARTING_CASH, "holdings": {}}
    _save_portfolio(fresh)
