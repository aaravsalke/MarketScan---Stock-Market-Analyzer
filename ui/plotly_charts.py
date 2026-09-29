# plotly_charts.py
# WHY: The Dash site uses Plotly graphs (interactive in the browser).
# Configured for high contrast and native currency representation.

import plotly.graph_objects as go
from utils.formatters import get_currency_symbol


def build_price_figure(dates, closing_prices, moving_average, ma_days, extra_ma, extra_label, currency="USD"):
    """One chart: close price + slider moving average (+ optional extra line) in native currency."""
    figure = go.Figure()
    sym = get_currency_symbol(currency)
    
    # Stock Close Price line
    figure.add_trace(
        go.Scatter(
            x=dates,
            y=closing_prices,
            name="Close Price",
            line={"color": "#38bdf8", "width": 2.5},
            hovertemplate=f"Date: %{{x}}<br>Price: {sym}%{{y:.2f}}<extra></extra>",
        )
    )
    
    # User Slider Moving Average line
    figure.add_trace(
        go.Scatter(
            x=dates,
            y=moving_average,
            name=f"{ma_days}-Day MA",
            line={"color": "#f59e0b", "width": 2, "dash": "solid"},
            hovertemplate=f"Date: %{{x}}<br>{ma_days}-Day MA: {sym}%{{y:.2f}}<extra></extra>",
        )
    )
    
    # Optional 50-day Moving Average line
    if extra_ma is not None:
        figure.add_trace(
            go.Scatter(
                x=dates,
                y=extra_ma,
                name=extra_label,
                line={"color": "#a855f7", "width": 2, "dash": "dot"},
                hovertemplate=f"Date: %{{x}}<br>{extra_label}: {sym}%{{y:.2f}}<extra></extra>",
            )
        )

    figure.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#0f172a",
        margin={"l": 55, "r": 20, "t": 30, "b": 40},
        font={"color": "#f8fafc", "family": "Segoe UI, sans-serif"},
        legend={
            "orientation": "h",
            "y": 1.12,
            "x": 0.0,
            "font": {"color": "#f8fafc", "size": 12},
        },
        xaxis={
            "title": {"text": "Date", "font": {"color": "#f8fafc", "size": 12}},
            "gridcolor": "#1e293b",
            "tickfont": {"color": "#cbd5e1", "size": 11},
        },
        yaxis={
            "title": {"text": f"Price ({currency})", "font": {"color": "#f8fafc", "size": 12}},
            "gridcolor": "#1e293b",
            "tickfont": {"color": "#cbd5e1", "size": 11},
            "tickprefix": sym,
        },
        height=380,
        hoverlabel={"bgcolor": "#1e293b", "font_color": "#ffffff", "font_size": 13},
    )
    return figure


def build_rsi_figure(dates, rsi_values):
    """RSI line with 70 and 30 guide lines."""
    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=dates,
            y=rsi_values,
            name="RSI (14)",
            line={"color": "#c084fc", "width": 2},
            hovertemplate="Date: %{x}<br>RSI: %{y:.1f}<extra></extra>",
        )
    )
    figure.add_hline(
        y=70,
        line_dash="dash",
        line_color="#f87171",
        annotation_text="Overbought (70)",
        annotation_font_color="#f87171",
        annotation_position="top left",
    )
    figure.add_hline(
        y=30,
        line_dash="dash",
        line_color="#34d399",
        annotation_text="Oversold (30)",
        annotation_font_color="#34d399",
        annotation_position="bottom left",
    )
    figure.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#0f172a",
        margin={"l": 55, "r": 20, "t": 30, "b": 40},
        font={"color": "#f8fafc", "family": "Segoe UI, sans-serif"},
        yaxis={
            "range": [0, 100],
            "title": {"text": "RSI", "font": {"color": "#f8fafc", "size": 12}},
            "gridcolor": "#1e293b",
            "tickfont": {"color": "#cbd5e1", "size": 11},
        },
        xaxis={
            "title": {"text": "Date", "font": {"color": "#f8fafc", "size": 12}},
            "gridcolor": "#1e293b",
            "tickfont": {"color": "#cbd5e1", "size": 11},
        },
        height=260,
        hoverlabel={"bgcolor": "#1e293b", "font_color": "#ffffff", "font_size": 13},
    )
    return figure


def empty_figure(message):
    figure = go.Figure()
    figure.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#0f172a",
        height=280,
        annotations=[
            {
                "text": message,
                "xref": "paper",
                "yref": "paper",
                "x": 0.5,
                "y": 0.5,
                "showarrow": False,
                "font": {"size": 15, "color": "#94a3b8"},
            }
        ],
        xaxis={"showgrid": False, "zeroline": False, "showticklabels": False},
        yaxis={"showgrid": False, "zeroline": False, "showticklabels": False},
    )
    return figure
