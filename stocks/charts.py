# charts.py
# WHY: Numbers are easier to understand as pictures.
# This file only draws charts. It does not download data or do the math.

import matplotlib.pyplot as plt


def _build_x_values(count):
    """Make a simple list 0, 1, 2, ... to use as the x-axis."""
    x_values = []
    for index in range(count):
        x_values.append(index)
    return x_values


def _values_without_none(values):
    """
    Moving averages and RSI start with None until enough days exist.
    Matplotlib should only plot the real numbers.
    """
    ready_x = []
    ready_y = []
    for index in range(len(values)):
        if values[index] is not None:
            ready_x.append(index)
            ready_y.append(values[index])
    return ready_x, ready_y


def _apply_date_ticks(axis, dates):
    """Show a few dates on the x-axis so the labels do not pile up."""
    if len(dates) == 0:
        return

    step = 20
    if len(dates) < step:
        step = 1

    tick_positions = []
    tick_labels = []
    for index in range(0, len(dates), step):
        tick_positions.append(index)
        tick_labels.append(dates[index])

    axis.set_xticks(tick_positions)
    axis.set_xticklabels(tick_labels, rotation=45, ha="right")


def show_technical_charts(
    ticker,
    dates,
    closing_prices,
    ma_short_list,
    ma_long_list,
    rsi_list,
    short_window,
    long_window,
):
    """
    Open one window with two charts:
    - top: price plus moving averages
    - bottom: RSI
    """
    x_values = _build_x_values(len(dates))
    ma_short_x, ma_short_y = _values_without_none(ma_short_list)
    ma_long_x, ma_long_y = _values_without_none(ma_long_list)
    rsi_x, rsi_y = _values_without_none(rsi_list)

    # 2 rows, 1 column: price on top, RSI underneath
    figure, (price_axis, rsi_axis) = plt.subplots(2, 1, figsize=(10, 7), sharex=True)
    figure.suptitle(f"{ticker} Technical Analysis")

    price_axis.plot(x_values, closing_prices, label="Closing price", color="black")
    if len(ma_short_y) > 0:
        price_axis.plot(
            ma_short_x,
            ma_short_y,
            label=f"{short_window}-day moving average",
            color="blue",
        )
    if len(ma_long_y) > 0:
        price_axis.plot(
            ma_long_x,
            ma_long_y,
            label=f"{long_window}-day moving average",
            color="orange",
        )
    price_axis.set_ylabel("Price (USD)")
    price_axis.legend()
    price_axis.grid(True, alpha=0.3)

    rsi_axis.plot(rsi_x, rsi_y, label="RSI", color="purple")
    rsi_axis.axhline(70, color="red", linestyle="--", label="70 (overbought)")
    rsi_axis.axhline(30, color="green", linestyle="--", label="30 (oversold)")
    rsi_axis.set_ylim(0, 100)
    rsi_axis.set_ylabel("RSI")
    rsi_axis.set_xlabel("Date")
    rsi_axis.legend()
    rsi_axis.grid(True, alpha=0.3)
    _apply_date_ticks(rsi_axis, dates)

    figure.tight_layout()
    plt.show()
