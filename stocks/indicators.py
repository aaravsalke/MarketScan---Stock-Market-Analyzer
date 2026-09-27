# indicators.py
# WHY: Technical analysis means "look at recent prices and summarize them."
# We keep the math here so stock_data.py only downloads numbers,
# and charts.py only draws pictures.


def calculate_moving_average(prices, window_size):
    """
    For each day, average the last `window_size` closing prices.

    Example for a 3-day average of [10, 12, 11, 15]:
        day 1: not enough data -> None
        day 2: not enough data -> None
        day 3: (10+12+11) / 3 = 11.0
        day 4: (12+11+15) / 3 = 12.67

    We use None until we have enough days. That is easier to read than
    pretending the average exists on day 1.
    """
    moving_averages = []

    for index in range(len(prices)):
        days_so_far = index + 1
        if days_so_far < window_size:
            moving_averages.append(None)
            continue

        window_start = index - window_size + 1
        window = prices[window_start : index + 1]
        average = sum(window) / window_size
        moving_averages.append(average)

    return moving_averages


def calculate_rsi(prices, period=14):
    """
    RSI (Relative Strength Index) is a 0 to 100 score.

    A common classroom reading:
    - RSI above 70: the stock has risen quickly (often called overbought)
    - RSI below 30: the stock has fallen quickly (often called oversold)
    - RSI near 50: more balanced recent up and down moves

    How we calculate it (simple version, no extra smoothing):
    1. Look at the last `period` day-to-day changes.
    2. Average the gains and average the losses.
    3. RSI = 100 - (100 / (1 + average_gain / average_loss))
    """
    rsi_values = []

    for index in range(len(prices)):
        if index < period:
            rsi_values.append(None)
            continue

        gains = 0.0
        losses = 0.0

        # Walk through the last `period` price changes
        for lookback in range(index - period + 1, index + 1):
            change = prices[lookback] - prices[lookback - 1]
            if change > 0:
                gains += change
            else:
                losses += abs(change)

        average_gain = gains / period
        average_loss = losses / period

        if average_loss == 0:
            rsi = 100.0
        else:
            relative_strength = average_gain / average_loss
            rsi = 100 - (100 / (1 + relative_strength))

        rsi_values.append(rsi)

    return rsi_values


def last_ready_value(values):
    """Return the newest number in the list that is not None."""
    index = len(values) - 1
    while index >= 0:
        if values[index] is not None:
            return values[index]
        index -= 1
    return None


def build_technical_snapshot(closing_prices, short_window, long_window, rsi_period):
    """
    Run every indicator once and return both:
    - the full lists (for charts)
    - the latest numbers (for printing)
    """
    ma_short = calculate_moving_average(closing_prices, short_window)
    ma_long = calculate_moving_average(closing_prices, long_window)
    rsi_values = calculate_rsi(closing_prices, rsi_period)

    snapshot = {
        "ma_short_list": ma_short,
        "ma_long_list": ma_long,
        "rsi_list": rsi_values,
        "latest_close": last_ready_value(closing_prices),
        "latest_ma_short": last_ready_value(ma_short),
        "latest_ma_long": last_ready_value(ma_long),
        "latest_rsi": last_ready_value(rsi_values),
    }
    return snapshot
