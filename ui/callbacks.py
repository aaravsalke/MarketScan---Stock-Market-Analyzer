# callbacks.py
# WHY: Dash callbacks manage user interaction, dynamic charts, and portfolio trades.

import json
import pandas as pd
import dash
from dash import ALL, Input, Output, State, html, callback_context

from config import (
    LONG_MOVING_AVERAGE_DAYS,
    PRICE_HISTORY_PERIOD,
    RSI_PERIOD_DAYS,
    SEARCH_MAX_RESULTS,
)
from news.pipeline import get_analyzed_news
from news.ai_groq import generate_market_summary_groq, is_groq_available
from portfolio.portfolio import (
    buy_stock,
    sell_stock,
    get_holdings,
    calculate_portfolio_value,
)
from portfolio.transactions import record_transaction, get_transactions
from portfolio.watchlist import add_to_watchlist, get_watchlist, remove_from_watchlist
from stocks.indicators import (
    add_moving_average_column,
    calculate_moving_average,
    calculate_rsi,
    last_ready_value,
    rsi_plain_english,
)
from stocks.stock_data import fetch_price_history, fetch_stock_quote, search_securities
from ui.plotly_charts import build_price_figure, build_rsi_figure, empty_figure
from utils.formatters import format_market_cap, format_number, format_price, get_currency_symbol


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------

def _blank(value):
    if value is None or value == "":
        return "--"
    return value


def _format_optional_price(value, currency="USD"):
    if value is None:
        return "Not enough history yet"
    return format_price(value, currency=currency)


def _history_to_store(history):
    return {
        "ticker": history["ticker"],
        "dates": history["dates"],
        "closing_prices": history["closing_prices"],
    }


def _make_price_frame(history_store):
    return pd.DataFrame(
        {
            "Date": history_store["dates"],
            "Close": history_store["closing_prices"],
        }
    )


def _sentiment_color(label):
    if label == "Positive":
        return "#34d399"
    if label == "Negative":
        return "#f87171"
    return "#fbbf24"


def _pl_color(value):
    if value is None:
        return "#e2e8f0"
    if value >= 0:
        return "#34d399"
    return "#f87171"


def _make_news_card(article):
    color = _sentiment_color(article["sentiment"])
    return html.Div(
        className="news-card",
        children=[
            html.Div(article["title"], className="news-title"),
            html.Div(
                f"{article['source']}  ·  {article['published_date']}",
                className="news-meta",
            ),
            html.Div(
                style={"marginBottom": "8px"},
                children=[
                    html.Span(
                        f"{article['sentiment']} ({article['confidence']}% confidence)",
                        style={"color": color, "fontWeight": "700", "fontSize": "12px", "marginRight": "10px"},
                    ),
                    html.Span(
                        article.get("relevance_label", ""),
                        className="relevance-badge",
                    ),
                ],
            ),
            html.P(article.get("easy_summary", ""), className="news-summary"),
            html.A(
                "Read original article →",
                href=article["url"],
                target="_blank",
                className="news-link",
            ),
        ],
    )


def _make_holdings_table(holdings, current_quotes):
    if not holdings:
        return html.P("No holdings yet. Use the Buy form above to start paper trading.", className="status-text")

    header = html.Tr([
        html.Th("Ticker"),
        html.Th("Shares"),
        html.Th("Avg Cost"),
        html.Th("Current Price"),
        html.Th("Market Value"),
        html.Th("Profit / Loss"),
        html.Th("P/L %"),
    ])

    rows = []
    for ticker, info in holdings.items():
        shares = info["shares"]
        avg_cost = info["avg_cost"]
        quote = current_quotes.get(ticker)
        current_price = quote.get("current_price") if quote else None
        curr = quote.get("currency", "USD") if quote else "USD"

        cost_basis = shares * avg_cost

        if current_price is not None:
            market_value = shares * current_price
            pl = market_value - cost_basis
            pl_pct = (pl / cost_basis * 100) if cost_basis > 0 else 0
            price_str = format_price(current_price, currency=curr)
            value_str = format_price(market_value, currency=curr)
            pl_str = f"{'+' if pl >= 0 else ''}{format_price(pl, currency=curr)}"
            pct_str = f"{'+' if pl_pct >= 0 else ''}{pl_pct:.1f}%"
            pl_col = _pl_color(pl)
        else:
            price_str = "N/A"
            value_str = "N/A"
            pl_str = "N/A"
            pct_str = "N/A"
            pl_col = "#e2e8f0"

        rows.append(
            html.Tr([
                html.Td(ticker, style={"fontWeight": "700"}),
                html.Td(str(shares)),
                html.Td(format_price(avg_cost, currency=curr)),
                html.Td(price_str),
                html.Td(value_str),
                html.Td(pl_str, style={"color": pl_col, "fontWeight": "700"}),
                html.Td(pct_str, style={"color": pl_col}),
            ])
        )

    return html.Table(
        className="data-table",
        children=[html.Thead(header), html.Tbody(rows)],
    )


def _make_transactions_table(transactions):
    if not transactions:
        return html.P("No transactions recorded yet.", className="status-text")

    header = html.Tr([
        html.Th("Date & Time"),
        html.Th("Action"),
        html.Th("Ticker"),
        html.Th("Shares"),
        html.Th("Price / Share"),
        html.Th("Total Value"),
    ])

    rows = []
    for tx in transactions[:20]:
        action = tx.get("action", "")
        color = "#34d399" if action == "BUY" else "#f87171"
        curr = tx.get("currency", "USD")
        rows.append(
            html.Tr([
                html.Td(tx.get("timestamp", "")),
                html.Td(action, style={"color": color, "fontWeight": "700"}),
                html.Td(tx.get("ticker", ""), style={"fontWeight": "700"}),
                html.Td(str(tx.get("shares", ""))),
                html.Td(format_price(tx.get("price_per_share"), currency=curr)),
                html.Td(format_price(tx.get("total_amount"), currency=curr)),
            ])
        )

    return html.Table(
        className="data-table",
        children=[html.Thead(header), html.Tbody(rows)],
    )


def _fetch_quotes_for_tickers(tickers):
    quotes = {}
    for ticker in set(tickers):
        try:
            quotes[ticker] = fetch_stock_quote(ticker)
        except (ValueError, ConnectionError):
            quotes[ticker] = None
    return quotes


def _build_portfolio_summary(current_quotes=None):
    holdings = get_holdings()
    if current_quotes is None:
        current_quotes = _fetch_quotes_for_tickers(list(holdings.keys()))

    price_map = {}
    for t, q in current_quotes.items():
        price_map[t] = q.get("current_price") if q else None

    summary = calculate_portfolio_value(price_map)
    cash_str = f"${summary['cash']:,.2f}"
    holdings_val_str = f"${summary['holdings_value']:,.2f}"
    total_val_str = f"${summary['total_value']:,.2f}"

    pl = summary["total_pl"]
    pl_str = f"{'+' if pl >= 0 else ''}${pl:,.2f}"

    holdings_table = _make_holdings_table(holdings, current_quotes)
    tx_table = _make_transactions_table(get_transactions())

    return cash_str, holdings_val_str, total_val_str, pl_str, holdings_table, tx_table


def _build_watchlist_ui(current_ticker=None):
    watchlist = get_watchlist()

    if not watchlist:
        return html.P(
            "Your watchlist is empty. Search for a stock above and click '+ Add to Watchlist' to track it here.",
            className="status-text",
        )

    cards = []
    for ticker in watchlist:
        is_active = (ticker == current_ticker)
        try:
            quote = fetch_stock_quote(ticker)
            price = quote.get("current_price")
            prev_close = quote.get("previous_close")
            company_name = quote.get("company_name", ticker)
            curr = quote.get("currency", "USD")

            if price is not None and prev_close is not None:
                change = price - prev_close
                pct_change = (change / prev_close) * 100
                sym = get_currency_symbol(curr)
                change_str = f"{'+' if change >= 0 else ''}{sym}{change:.2f} ({'+' if pct_change >= 0 else ''}{pct_change:.2f}%)"
                color = "#34d399" if change >= 0 else "#f87171"
                price_str = format_price(price, currency=curr)
            else:
                price_str = "N/A"
                change_str = "--"
                color = "#94a3b8"
        except Exception:
            price_str = "N/A"
            change_str = "Offline"
            color = "#94a3b8"
            company_name = ticker

        cards.append(
            html.Div(
                className="watchlist-card" + (" watchlist-card-active" if is_active else ""),
                children=[
                    html.Div(
                        className="watchlist-info",
                        children=[
                            html.Span(ticker, className="watchlist-ticker"),
                            html.Span(company_name, className="watchlist-company"),
                        ],
                    ),
                    html.Div(
                        className="watchlist-price-box",
                        children=[
                            html.Span(price_str, className="watchlist-price"),
                            html.Span(change_str, className="watchlist-change", style={"color": color}),
                        ],
                    ),
                    html.Div(
                        className="watchlist-actions",
                        children=[
                            html.Button(
                                "🔍 View Stock",
                                id={"type": "watchlist-select-btn", "index": ticker},
                                n_clicks=0,
                                className="view-button",
                            ),
                            html.Button(
                                "❌ Remove",
                                id={"type": "watchlist-remove-btn", "index": ticker},
                                n_clicks=0,
                                className="remove-button",
                            ),
                        ],
                    ),
                ],
            )
        )

    return html.Div(cards)


# ---------------------------------------------------------------------------
# Callback Registration
# ---------------------------------------------------------------------------

def register_callbacks(app):

    # ========================================================================
    # CALLBACK 1 — SEARCH STOCKS (Click or Enter Key)
    # ========================================================================
    @app.callback(
        Output("match-dropdown", "options"),
        Output("match-dropdown", "value"),
        Output("search-status", "children"),
        Input("search-button", "n_clicks"),
        Input("search-input", "n_submit"),
        State("search-input", "value"),
        prevent_initial_call=True,
    )
    def search_companies(n_clicks, n_submit, query):
        if query is None or str(query).strip() == "":
            return [], None, "Please enter a ticker symbol or company name."

        cleaned_query = query.strip()
        try:
            matches = search_securities(cleaned_query, max_results=SEARCH_MAX_RESULTS)
        except ConnectionError as error:
            return [], None, str(error)

        if len(matches) == 0:
            return [], None, f"No stocks found for '{cleaned_query}'. Try a direct ticker like AAPL, BMW.DE, or RELIANCE.NS."

        options = []
        for match in matches:
            company_name = match.get("company_name") or "Unknown Company"
            label = f"{match['ticker']} — {company_name}"
            options.append({"label": label, "value": match["ticker"]})

        typed_upper = cleaned_query.upper()
        selected = options[0]["value"]
        for option in options:
            if option["value"].upper() == typed_upper:
                selected = option["value"]
                break

        return options, selected, f"Found {len(options)} matching stock(s). Displaying {selected}."

    # ========================================================================
    # CALLBACK 2 — LOAD COMPANY & GENERATE AI SUMMARY
    # ========================================================================
    @app.callback(
        Output("stat-ticker", "children"),
        Output("stat-company", "children"),
        Output("stat-price", "children"),
        Output("stat-previous", "children"),
        Output("stat-high", "children"),
        Output("stat-low", "children"),
        Output("stat-market-cap", "children"),
        Output("stat-volume", "children"),
        Output("price-history-store", "data"),
        Output("company-store", "data"),
        Output("active-ticker-store", "data"),
        Output("rsi-chart", "figure"),
        Output("ind-close", "children"),
        Output("ind-ma50", "children"),
        Output("ind-rsi", "children"),
        Output("rsi-comment", "children"),
        Output("news-cards-container", "children"),
        Output("news-status", "children"),
        Output("sent-overall", "children"),
        Output("sent-pos", "children"),
        Output("sent-neu", "children"),
        Output("sent-neg", "children"),
        Output("sentiment-details", "children"),
        Output("summary-cards", "children"),
        Output("ai-badge", "children"),
        Output("ai-badge", "className"),
        Output("ai-summary-content", "children"),
        Output("port-cash", "children"),
        Output("port-holdings-value", "children"),
        Output("port-total-value", "children"),
        Output("port-pl", "children"),
        Output("holdings-table-container", "children"),
        Output("transactions-table-container", "children"),
        Output("watchlist-container", "children"),
        Output("buy-ticker-input", "value"),
        Output("sell-ticker-input", "value"),
        Input("match-dropdown", "value"),
        prevent_initial_call=True,
    )
    def load_company(ticker):
        empty_outputs = (
            "--", "--", "--", "--", "--", "--", "--", "--",
            None, None, None,
            empty_figure("Search for a stock to display chart data."),
            "--", "--", "--", "",
            html.P("Search for a stock to view news.", className="status-text"),
            "",
            "--", "0", "0", "0",
            html.P("No sentiment data available.", className="status-text"),
            html.P("No summaries available.", className="status-text"),
            "💡 Local Mode", "ai-badge ai-badge-local",
            html.P("Add GROQ_API_KEY to your .env file to enable real-time Groq AI market analysis.", className="status-text"),
            *_build_portfolio_summary(),
            _build_watchlist_ui(),
            "", "",
        )

        if ticker is None or str(ticker).strip() == "":
            return empty_outputs

        try:
            quote = fetch_stock_quote(ticker)
            history = fetch_price_history(ticker, period=PRICE_HISTORY_PERIOD)
            news_pack = get_analyzed_news(ticker, quote["company_name"])
        except Exception as error:
            failed = list(empty_outputs)
            failed[17] = f"Unable to load stock '{ticker}': {error}"
            return tuple(failed)

        curr = quote.get("currency", "USD")

        # Indicators
        rsi_list = calculate_rsi(history["closing_prices"], RSI_PERIOD_DAYS)
        ma50_list = calculate_moving_average(history["closing_prices"], LONG_MOVING_AVERAGE_DAYS)
        latest_rsi = last_ready_value(rsi_list)
        latest_ma50 = last_ready_value(ma50_list)
        latest_close = last_ready_value(history["closing_prices"])

        # News & Summaries
        news_cards = []
        detail_blocks = []
        summary_blocks = []
        for article in news_pack["articles"]:
            news_cards.append(_make_news_card(article))
            color = _sentiment_color(article["sentiment"])
            src_text = article.get("source_type", "Engine")
            detail_blocks.append(
                html.Div(
                    style={"marginTop": "12px", "paddingBottom": "10px", "borderBottom": "1px solid #1e293b"},
                    children=[
                        html.Div(article["title"], style={"fontWeight": "700", "color": "#f8fafc"}),
                        html.Div(
                            f"Sentiment: {article['sentiment']} ({article['confidence']}% confidence via {src_text})",
                            style={"color": color, "fontSize": "13px", "fontWeight": "600", "marginTop": "2px"},
                        ),
                        html.Div(article["explanation"], className="status-text"),
                    ],
                )
            )
            summary_blocks.append(
                html.Div(
                    className="summary-card",
                    children=[
                        html.Div(article["title"], style={"fontWeight": "700", "marginBottom": "6px", "color": "#f8fafc"}),
                        html.P(article["easy_summary"], className="news-summary"),
                        html.A("Read full story →", href=article["url"], target="_blank", className="news-link"),
                    ],
                )
            )

        if news_pack["used_fallback"]:
            news_status = f"Yahoo returned {news_pack['raw_count']} item(s). Showing closest headlines."
        elif news_pack["kept_count"] > 0:
            news_status = f"Displaying {news_pack['kept_count']} relevant story(ies)."
        else:
            news_status = "No news articles found for this ticker today."

        if not summary_blocks:
            summary_blocks = [html.P("No news articles available to summarize.", className="status-text")]
        if not detail_blocks:
            detail_blocks = [html.P("No sentiment analysis available.", className="status-text")]
        if not news_cards:
            news_cards = [html.P("No recent news found for this company.", className="status-text")]

        rsi_figure = build_rsi_figure(history["dates"], rsi_list)
        rsi_text = f"{latest_rsi:.1f}" if latest_rsi is not None else "Insufficient history"

        counts = news_pack["sentiment_counts"]

        # Technical signals for AI summary
        ma_comparison = ""
        if latest_close and latest_ma50:
            if latest_close > latest_ma50:
                ma_comparison = f"Trading above 50-day MA ({format_price(latest_ma50, currency=curr)})"
            else:
                ma_comparison = f"Trading below 50-day MA ({format_price(latest_ma50, currency=curr)})"

        technical_info = {
            "rsi": latest_rsi,
            "ma_status": ma_comparison,
        }

        watchlist_tickers = get_watchlist()
        if is_groq_available():
            ai_badge_text = "⚡ Powered by Groq AI"
            ai_badge_class = "ai-badge ai-badge-active"
            ai_exec_text = generate_market_summary_groq(
                quote, technical_info, news_pack["articles"], watchlist_tickers
            )
            if ai_exec_text:
                bullets = [b.strip() for b in ai_exec_text.split("\n") if b.strip()]
                ai_content = html.Div([
                    html.P(b, style={"marginBottom": "8px", "color": "#e2e8f0"}) for b in bullets
                ])
            else:
                ai_content = html.P(
                    f"AI Summary for {quote['ticker']}: Sector {quote['sector']}, trading at {format_price(quote['current_price'], currency=curr)}.",
                    className="status-text"
                )
        else:
            ai_badge_text = "💡 Local Mode"
            ai_badge_class = "ai-badge ai-badge-local"
            pe_val = f"P/E: {quote['pe_ratio']:.1f}" if quote.get("pe_ratio") else "P/E: N/A"
            ai_content = html.Div([
                html.P(f"• {quote['company_name']} operates in {quote['sector']} ({quote['industry']}). {pe_val}.", style={"color": "#e2e8f0"}),
                html.P(f"• Technicals: 14-day RSI is currently at {rsi_text} ({rsi_plain_english(latest_rsi)}). {ma_comparison}.", style={"color": "#e2e8f0"}),
                html.P(f"• Market Sentiment: Tone across recent coverage is {counts['overall']}.", style={"color": "#e2e8f0"}),
                html.P("💡 Pro-Tip: Add your free GROQ_API_KEY to a .env file to enable real-time Groq AI executive summaries!", style={"color": "#fbbf24", "fontSize": "13px"}),
            ])

        # Refresh Portfolio & Watchlist UI
        holdings = get_holdings()
        held_tickers = list(holdings.keys())
        if ticker not in held_tickers:
            held_tickers = [ticker] + held_tickers
        current_quotes = _fetch_quotes_for_tickers(held_tickers)
        cash_str, hv_str, tv_str, pl_str, h_table, tx_table = _build_portfolio_summary(current_quotes)

        watchlist_ui = _build_watchlist_ui(current_ticker=ticker)

        company_store_data = {
            "ticker": quote["ticker"],
            "company_name": quote["company_name"],
            "currency": curr,
        }

        return (
            quote["ticker"],
            _blank(quote["company_name"]),
            format_price(quote["current_price"], currency=curr),
            format_price(quote["previous_close"], currency=curr),
            format_price(quote["week_52_high"], currency=curr),
            format_price(quote["week_52_low"], currency=curr),
            format_market_cap(quote["market_cap"], currency=curr),
            format_number(quote["volume"]),
            _history_to_store(history),
            company_store_data,
            quote["ticker"],
            rsi_figure,
            _format_optional_price(latest_close, currency=curr),
            _format_optional_price(latest_ma50, currency=curr),
            rsi_text,
            rsi_plain_english(latest_rsi),
            news_cards,
            news_status,
            counts["overall"],
            str(counts["positive"]),
            str(counts["neutral"]),
            str(counts["negative"]),
            detail_blocks,
            summary_blocks,
            ai_badge_text,
            ai_badge_class,
            ai_content,
            cash_str, hv_str, tv_str, pl_str,
            h_table, tx_table,
            watchlist_ui,
            quote["ticker"],
            quote["ticker"],
        )

    # ========================================================================
    # CALLBACK 3 — MOVING AVERAGE SLIDER & NUMBER BOX BI-DIRECTIONAL SYNC
    # ========================================================================
    @app.callback(
        Output("ma-slider", "value"),
        Output("ma-number-input", "value"),
        Input("ma-slider", "value"),
        Input("ma-number-input", "value"),
        prevent_initial_call=True,
    )
    def sync_ma_inputs(slider_val, input_val):
        triggered_id = callback_context.triggered[0]["prop_id"].split(".")[0]
        if triggered_id == "ma-number-input" and input_val is not None:
            val = max(1, min(300, int(input_val)))
            return val, val
        elif slider_val is not None:
            val = max(1, min(300, int(slider_val)))
            return val, val
        return 20, 20

    @app.callback(
        Output("price-chart", "figure"),
        Output("ma-label", "children"),
        Output("ma-note", "children"),
        Output("ind-ma", "children"),
        Input("ma-slider", "value"),
        Input("extra-line-dropdown", "value"),
        Input("price-history-store", "data"),
        State("company-store", "data"),
    )
    def update_moving_average_chart(ma_days, extra_line, history_store, company_data):
        if ma_days is None:
            ma_days = 20
        ma_days = int(ma_days)
        label = f"Moving Average: {ma_days} Days"

        curr = company_data.get("currency", "USD") if company_data else "USD"

        if history_store is None:
            return (
                empty_figure("Search for a stock to view interactive price chart."),
                label, "", "--",
            )

        price_frame = _make_price_frame(history_store)
        day_count = len(price_frame)

        note = ""
        if ma_days > day_count:
            note = (
                f"This stock has {day_count} days of available trading history. "
                f"A {ma_days}-day moving average cannot be computed."
            )

        price_frame = add_moving_average_column(price_frame, ma_days)
        ma_values = price_frame["Moving_Average"].tolist()

        latest_ma = None
        if day_count >= ma_days:
            latest_ma = ma_values[-1]
            if pd.isna(latest_ma):
                latest_ma = None

        extra_ma = None
        extra_label = f"{LONG_MOVING_AVERAGE_DAYS}-Day MA"
        if extra_line == "ma50":
            close_only = price_frame[["Date", "Close"]].copy()
            extra_frame = add_moving_average_column(close_only, LONG_MOVING_AVERAGE_DAYS)
            extra_ma = extra_frame["Moving_Average"].tolist()

        figure = build_price_figure(
            price_frame["Date"].tolist(),
            price_frame["Close"].tolist(),
            ma_values,
            ma_days,
            extra_ma,
            extra_label,
            currency=curr,
        )
        return figure, label, note, _format_optional_price(latest_ma, currency=curr)

    # ========================================================================
    # CALLBACK 4 — SHARE STEPPER BUTTONS (- / + FOR BUY AND SELL)
    # ========================================================================
    @app.callback(
        Output("buy-shares-input", "value"),
        Input("buy-minus-btn", "n_clicks"),
        Input("buy-plus-btn", "n_clicks"),
        State("buy-shares-input", "value"),
        prevent_initial_call=True,
    )
    def update_buy_shares(minus_clicks, plus_clicks, current_val):
        triggered_id = callback_context.triggered[0]["prop_id"].split(".")[0]
        current = int(current_val or 1)
        if triggered_id == "buy-minus-btn":
            return max(1, current - 1)
        elif triggered_id == "buy-plus-btn":
            return current + 1
        return current

    @app.callback(
        Output("sell-shares-input", "value"),
        Input("sell-minus-btn", "n_clicks"),
        Input("sell-plus-btn", "n_clicks"),
        State("sell-shares-input", "value"),
        prevent_initial_call=True,
    )
    def update_sell_shares(minus_clicks, plus_clicks, current_val):
        triggered_id = callback_context.triggered[0]["prop_id"].split(".")[0]
        current = int(current_val or 1)
        if triggered_id == "sell-minus-btn":
            return max(1, current - 1)
        elif triggered_id == "sell-plus-btn":
            return current + 1
        return current

    # ========================================================================
    # CALLBACK 5 — BUY BUTTON
    # ========================================================================
    @app.callback(
        Output("buy-status", "children"),
        Output("port-cash", "children", allow_duplicate=True),
        Output("port-holdings-value", "children", allow_duplicate=True),
        Output("port-total-value", "children", allow_duplicate=True),
        Output("port-pl", "children", allow_duplicate=True),
        Output("holdings-table-container", "children", allow_duplicate=True),
        Output("transactions-table-container", "children", allow_duplicate=True),
        Input("buy-button", "n_clicks"),
        State("buy-ticker-input", "value"),
        State("buy-shares-input", "value"),
        prevent_initial_call=True,
    )
    def handle_buy(n_clicks, ticker, shares):
        if not ticker or not shares:
            return "Please enter a valid stock ticker and share quantity.", *_build_portfolio_summary()

        ticker = ticker.strip().upper()

        try:
            quote = fetch_stock_quote(ticker)
            price = quote.get("current_price")
            curr = quote.get("currency", "USD")
        except Exception as error:
            return f"Unable to fetch price for {ticker}: {error}", *_build_portfolio_summary()

        if price is None:
            return f"No price quote available for {ticker}.", *_build_portfolio_summary()

        result = buy_stock(ticker, shares, price)

        if result["success"]:
            record_transaction("BUY", ticker, int(shares), price, result["cost"])

        holdings = get_holdings()
        quotes = _fetch_quotes_for_tickers(list(holdings.keys()))
        cash_str, hv_str, tv_str, pl_str, h_table, tx_table = _build_portfolio_summary(quotes)

        cost_formatted = format_price(result["cost"], currency=curr)
        msg = f"Bought {shares} share(s) of {ticker} at {format_price(price, currency=curr)} each. Total: {cost_formatted}." if result["success"] else result["message"]

        return msg, cash_str, hv_str, tv_str, pl_str, h_table, tx_table

    # ========================================================================
    # CALLBACK 6 — SELL BUTTON
    # ========================================================================
    @app.callback(
        Output("sell-status", "children"),
        Output("port-cash", "children", allow_duplicate=True),
        Output("port-holdings-value", "children", allow_duplicate=True),
        Output("port-total-value", "children", allow_duplicate=True),
        Output("port-pl", "children", allow_duplicate=True),
        Output("holdings-table-container", "children", allow_duplicate=True),
        Output("transactions-table-container", "children", allow_duplicate=True),
        Input("sell-button", "n_clicks"),
        State("sell-ticker-input", "value"),
        State("sell-shares-input", "value"),
        prevent_initial_call=True,
    )
    def handle_sell(n_clicks, ticker, shares):
        if not ticker or not shares:
            return "Please enter a valid stock ticker and share quantity.", *_build_portfolio_summary()

        ticker = ticker.strip().upper()

        try:
            quote = fetch_stock_quote(ticker)
            price = quote.get("current_price")
            curr = quote.get("currency", "USD")
        except Exception as error:
            return f"Unable to fetch price for {ticker}: {error}", *_build_portfolio_summary()

        if price is None:
            return f"No price quote available for {ticker}.", *_build_portfolio_summary()

        result = sell_stock(ticker, shares, price)

        if result["success"]:
            record_transaction("SELL", ticker, int(shares), price, result["proceeds"])

        holdings = get_holdings()
        quotes = _fetch_quotes_for_tickers(list(holdings.keys()))
        cash_str, hv_str, tv_str, pl_str, h_table, tx_table = _build_portfolio_summary(quotes)

        proceeds_formatted = format_price(result["proceeds"], currency=curr)
        msg = f"Sold {shares} share(s) of {ticker} at {format_price(price, currency=curr)} each. Proceeds: {proceeds_formatted}." if result["success"] else result["message"]

        return msg, cash_str, hv_str, tv_str, pl_str, h_table, tx_table

    # ========================================================================
    # CALLBACK 7 — ADD TO WATCHLIST
    # ========================================================================
    @app.callback(
        Output("watchlist-add-status", "children"),
        Output("watchlist-container", "children", allow_duplicate=True),
        Input("watchlist-add-button", "n_clicks"),
        State("active-ticker-store", "data"),
        prevent_initial_call=True,
    )
    def handle_watchlist_add(n_clicks, ticker):
        if not ticker:
            return "Search for a stock first, then click Add to Watchlist.", _build_watchlist_ui()

        result = add_to_watchlist(ticker)
        return result["message"], _build_watchlist_ui(current_ticker=ticker)

    # ========================================================================
    # CALLBACK 8 — WATCHLIST ACTIONS (SELECT STOCK OR REMOVE)
    # Uses dash.no_update so removing or idling NEVER resets dropdown to Apple!
    # ========================================================================
    @app.callback(
        Output("match-dropdown", "options", allow_duplicate=True),
        Output("match-dropdown", "value", allow_duplicate=True),
        Output("watchlist-container", "children", allow_duplicate=True),
        Input({"type": "watchlist-select-btn", "index": dash.ALL}, "n_clicks"),
        Input({"type": "watchlist-remove-btn", "index": dash.ALL}, "n_clicks"),
        State("match-dropdown", "options"),
        State("active-ticker-store", "data"),
        prevent_initial_call=True,
    )
    def handle_watchlist_actions(select_clicks, remove_clicks, current_options, active_ticker):
        triggered = callback_context.triggered
        if not triggered:
            return dash.no_update, dash.no_update, _build_watchlist_ui(current_ticker=active_ticker)

        triggered_prop = triggered[0]["prop_id"]
        triggered_id_str = triggered_prop.split(".")[0]

        try:
            id_dict = json.loads(triggered_id_str)
            action_type = id_dict.get("type")
            ticker = id_dict.get("index")
        except Exception:
            return dash.no_update, dash.no_update, _build_watchlist_ui(current_ticker=active_ticker)

        if action_type == "watchlist-remove-btn" and ticker:
            remove_from_watchlist(ticker)
            # DO NOT touch match-dropdown value or options on remove!
            return dash.no_update, dash.no_update, _build_watchlist_ui(current_ticker=active_ticker)

        elif action_type == "watchlist-select-btn" and ticker:
            options = current_options or []
            found = any(opt["value"] == ticker for opt in options)
            if not found:
                try:
                    quote = fetch_stock_quote(ticker)
                    comp_name = quote.get("company_name", ticker)
                except Exception:
                    comp_name = ticker
                options.append({"label": f"{ticker} — {comp_name}", "value": ticker})

            return options, ticker, _build_watchlist_ui(current_ticker=ticker)

        return dash.no_update, dash.no_update, _build_watchlist_ui(current_ticker=active_ticker)
