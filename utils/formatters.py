# formatters.py
# WHY: Stock numbers are huge (like 3,500,000,000,000).
# Humans read them more easily as "$3.50 Trillion".
# We keep formatting here so stock_data.py stays focused on fetching data.


def format_price(price):
    """Turn a number into a money string, or 'N/A' if the value is missing."""
    if price is None:
        return "N/A"
    return f"${price:,.2f}"


def format_number(number):
    """Turn a large count (volume) into a comma-separated string."""
    if number is None:
        return "N/A"
    return f"{number:,}"


def format_market_cap(market_cap):
    """
    Turn a market cap into a short label.

    Example:
        2500000000000 -> "$2.50 Trillion"
    """
    if market_cap is None:
        return "N/A"

    trillion = 1_000_000_000_000
    billion = 1_000_000_000
    million = 1_000_000

    if market_cap >= trillion:
        value = market_cap / trillion
        return f"${value:.2f} Trillion"
    elif market_cap >= billion:
        value = market_cap / billion
        return f"${value:.2f} Billion"
    elif market_cap >= million:
        value = market_cap / million
        return f"${value:.2f} Million"
    else:
        return f"${market_cap:,.0f}"
