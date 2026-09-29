# formatters.py
# WHY: Stock numbers are huge and currencies vary around the world (USD, EUR, GBP, JPY, INR, CAD).
# Formats numbers cleanly into human-readable strings with their native currency symbols.

CURRENCY_SYMBOLS = {
    "USD": "$",
    "EUR": "€",
    "GBP": "£",
    "GBp": "p",       # British pence (used by London Stock Exchange)
    "JPY": "¥",
    "INR": "₹",
    "CAD": "CA$",
    "AUD": "AU$",
    "CHF": "CHF ",
    "CNY": "¥",
    "HKD": "HK$",
    "SGD": "SG$",
    "KRW": "₩",
    "SEK": "kr ",
    "NOK": "kr ",
    "DKK": "kr ",
    "NZD": "NZ$",
    "BRL": "R$",
    "MXN": "Mex$",
    "ZAR": "R ",
    "ILS": "₪",
    "TWD": "NT$",
}


def get_currency_symbol(currency="USD"):
    """Return the symbol for a currency code (e.g. 'EUR' -> '€', 'INR' -> '₹')."""
    if not currency:
        return "$"
    curr_upper = str(currency).strip()
    return CURRENCY_SYMBOLS.get(curr_upper, f"{curr_upper} ")


def format_price(price, currency="USD"):
    """
    Format a price into a localized money string using its native currency.
    Examples:
        format_price(180.50, 'USD') -> '$180.50'
        format_price(55.72, 'EUR')  -> '€55.72'
        format_price(1226.0, 'INR') -> '₹1,226.00'
        format_price(2989.5, 'JPY') -> '¥2,989.50'
    """
    if price is None:
        return "N/A"
    symbol = get_currency_symbol(currency)
    return f"{symbol}{price:,.2f}"


def format_number(number):
    """Turn a large count (volume) into a comma-separated string."""
    if number is None:
        return "N/A"
    return f"{number:,}"


def format_market_cap(market_cap, currency="USD"):
    """
    Turn a market cap into a short, readable label with the native currency symbol.
    Example:
        format_market_cap(2500000000000, 'USD') -> '$2.50 Trillion'
        format_market_cap(38500000000, 'EUR')   -> '€38.50 Billion'
    """
    if market_cap is None:
        return "N/A"

    symbol = get_currency_symbol(currency)
    trillion = 1_000_000_000_000
    billion = 1_000_000_000
    million = 1_000_000

    if market_cap >= trillion:
        value = market_cap / trillion
        return f"{symbol}{value:.2f} Trillion"
    elif market_cap >= billion:
        value = market_cap / billion
        return f"{symbol}{value:.2f} Billion"
    elif market_cap >= million:
        value = market_cap / million
        return f"{symbol}{value:.2f} Million"
    else:
        return f"{symbol}{market_cap:,.0f}"
