# layout.py
# WHY: Describes the HTML structure of the MarketScan Dash website.

from dash import dcc, html

from config import (
    APP_NAME,
    LONG_MOVING_AVERAGE_DAYS,
    MA_SLIDER_DEFAULT,
    MA_SLIDER_MAX,
    MA_SLIDER_MIN,
    MA_SLIDER_STEP,
)


def _stat_box(label, element_id):
    """Small labelled stat tile."""
    return html.Div(
        className="stat-box",
        children=[
            html.Div(label, className="stat-label"),
            html.Div("--", id=element_id, className="stat-value"),
        ],
    )


def build_layout():
    return html.Div(
        className="page",
        children=[
            # ----- Hidden stores -----
            dcc.Store(id="price-history-store"),
            dcc.Store(id="company-store"),
            dcc.Store(id="active-ticker-store"),

            # ----- Header -----
            html.Div(
                className="hero",
                children=[
                    html.H1(APP_NAME, className="hero-title"),
                    html.P(
                        "Stock analysis & virtual paper-trading dashboard — powered by Yahoo Finance & Groq AI.",
                        className="hero-subtitle",
                    ),
                ],
            ),

            # ================================================================
            # SECTION 1 — SEARCH
            # ================================================================
            html.Div(
                className="card",
                children=[
                    html.H2("Stock Search", className="card-title"),
                    html.Div(
                        className="search-row",
                        children=[
                            dcc.Input(
                                id="search-input",
                                type="text",
                                placeholder="Enter ticker or company name (e.g. AAPL, NVDA, Tesla)",
                                className="search-input",
                                debounce=False,
                                n_submit=0,
                                style={"height": "42px"},
                            ),
                            html.Button(
                                "Search Stock",
                                id="search-button",
                                n_clicks=0,
                                className="primary-button",
                            ),
                        ],
                    ),
                    html.Div(
                        style={"marginTop": "14px"},
                        children=[
                            html.Label(
                                "Matching companies found:",
                                style={"color": "#cbd5e1", "fontSize": "13px", "fontWeight": "600", "marginBottom": "6px", "display": "block"}
                            ),
                            dcc.Dropdown(
                                id="match-dropdown",
                                placeholder="Search results will appear here...",
                                options=[],
                                className="custom-dropdown",
                                style={"backgroundColor": "#1e293b", "color": "#ffffff"}
                            )
                        ],
                    ),
                    html.P("", id="search-status", className="status-text"),
                ],
            ),

            # ================================================================
            # SECTION 2 — AI MARKET & STOCK SUMMARY CARD
            # ================================================================
            html.Div(
                className="card ai-card",
                children=[
                    html.Div(
                        style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "marginBottom": "10px"},
                        children=[
                            html.H2("🤖 AI Stock & Market Analysis", className="card-title", style={"margin": "0"}),
                            html.Span(id="ai-badge", className="ai-badge"),
                        ],
                    ),
                    html.Div(
                        id="ai-summary-content",
                        className="ai-summary-text",
                        children=[
                            html.P("Search for a stock to generate instant AI market summaries.", className="status-text")
                        ],
                    ),
                ],
            ),

            # ================================================================
            # SECTION 3 — STOCK INFORMATION
            # ================================================================
            html.Div(
                className="card",
                children=[
                    html.H2("Stock Information", className="card-title"),
                    html.Div(
                        className="stats-grid",
                        children=[
                            _stat_box("Ticker", "stat-ticker"),
                            _stat_box("Company", "stat-company"),
                            _stat_box("Current Price", "stat-price"),
                            _stat_box("Previous Close", "stat-previous"),
                            _stat_box("52-Week High", "stat-high"),
                            _stat_box("52-Week Low", "stat-low"),
                            _stat_box("Market Cap", "stat-market-cap"),
                            _stat_box("Volume", "stat-volume"),
                        ],
                    ),
                    html.Div(
                        style={"marginTop": "16px", "display": "flex", "gap": "12px", "alignItems": "center"},
                        children=[
                            html.Button(
                                "＋ Add to Watchlist",
                                id="watchlist-add-button",
                                n_clicks=0,
                                className="secondary-button",
                            ),
                            html.P("", id="watchlist-add-status", className="status-text", style={"margin": "0"}),
                        ],
                    ),
                ],
            ),

            # ================================================================
            # SECTION 4 — PRICE CHART & MA SLIDER
            # ================================================================
            html.Div(
                className="card",
                children=[
                    html.H2("Price Chart & Interactive Moving Average", className="card-title"),
                    html.Div(
                        style={"display": "flex", "alignItems": "center", "gap": "16px", "marginBottom": "12px", "flexWrap": "wrap"},
                        children=[
                            html.H3(
                                f"Moving Average: {MA_SLIDER_DEFAULT} Days",
                                id="ma-label",
                                className="ma-label",
                                style={"margin": "0"}
                            ),
                            html.Div(
                                style={"display": "flex", "alignItems": "center", "gap": "6px"},
                                children=[
                                    html.Span("Direct Days Input (1-300):", style={"color": "#94a3b8", "fontSize": "13px", "fontWeight": "600"}),
                                    dcc.Input(
                                        id="ma-number-input",
                                        type="number",
                                        min=MA_SLIDER_MIN,
                                        max=MA_SLIDER_MAX,
                                        step=1,
                                        value=MA_SLIDER_DEFAULT,
                                        className="trade-input",
                                        style={"width": "80px", "textAlign": "center", "height": "36px", "padding": "4px"}
                                    )
                                ]
                            )
                        ],
                    ),
                    dcc.Slider(
                        id="ma-slider",
                        min=MA_SLIDER_MIN,
                        max=MA_SLIDER_MAX,
                        step=MA_SLIDER_STEP,
                        value=MA_SLIDER_DEFAULT,
                        marks={
                            1: "1",
                            20: "20",
                            50: "50",
                            100: "100",
                            200: "200",
                            300: "300",
                        },
                        tooltip={"placement": "bottom", "always_visible": False},
                    ),
                    html.Div(
                        style={"marginTop": "18px", "maxWidth": "340px"},
                        children=[
                            html.Label("Compare with additional indicator:", style={"color": "#cbd5e1", "fontSize": "13px", "fontWeight": "600", "marginBottom": "6px", "display": "block"}),
                            dcc.Dropdown(
                                id="extra-line-dropdown",
                                value="none",
                                clearable=False,
                                className="custom-dropdown",
                                style={"backgroundColor": "#1e293b", "color": "#ffffff"},
                                options=[
                                    {"label": "Only slider moving average", "value": "none"},
                                    {
                                        "label": f"{LONG_MOVING_AVERAGE_DAYS}-day moving average",
                                        "value": "ma50",
                                    },
                                ],
                            ),
                        ],
                    ),
                    html.P("", id="ma-note", className="note"),
                    dcc.Graph(id="price-chart", style={"marginTop": "10px"}),
                ],
            ),

            # ================================================================
            # SECTION 5 — TECHNICAL INDICATORS
            # ================================================================
            html.Div(
                className="card",
                children=[
                    html.H2("Technical Indicators (RSI & Moving Averages)", className="card-title"),
                    html.Div(
                        className="stats-grid",
                        children=[
                            _stat_box("Latest Close", "ind-close"),
                            _stat_box("Slider MA", "ind-ma"),
                            _stat_box("50-Day MA", "ind-ma50"),
                            _stat_box("RSI (14)", "ind-rsi"),
                        ],
                    ),
                    html.P("", id="rsi-comment", className="status-text", style={"marginTop": "12px", "fontSize": "14px"}),
                    dcc.Graph(id="rsi-chart", style={"marginTop": "10px"}),
                ],
            ),

            # ================================================================
            # SECTION 6 — NEWS & SENTIMENT ANALYSIS
            # ================================================================
            html.Div(
                className="two-col",
                children=[
                    html.Div(
                        className="card",
                        children=[
                            html.H2("Recent Financial News", className="card-title"),
                            html.P("", id="news-status", className="status-text"),
                            html.Div(id="news-cards-container", style={"marginTop": "12px"}),
                        ],
                    ),
                    html.Div(
                        className="card",
                        children=[
                            html.H2("News Sentiment Overview", className="card-title"),
                            html.Div(
                                className="stats-grid",
                                children=[
                                    _stat_box("Overall", "sent-overall"),
                                    _stat_box("Positive", "sent-pos"),
                                    _stat_box("Neutral", "sent-neu"),
                                    _stat_box("Negative", "sent-neg"),
                                ],
                            ),
                            html.Div(id="sentiment-details", style={"marginTop": "14px"}),
                        ],
                    ),
                ],
            ),

            # ================================================================
            # SECTION 7 — NEWS SUMMARIES ("Explain the News")
            # ================================================================
            html.Div(
                className="card",
                children=[
                    html.H2("Explain the News (AI / Plain-English Summaries)", className="card-title"),
                    html.P(
                        "Simplified 2-3 sentence breakdowns explaining what happened and why it matters.",
                        className="status-text",
                        style={"marginBottom": "14px"},
                    ),
                    html.Div(id="summary-cards"),
                ],
            ),

            # ================================================================
            # SECTION 8 — WATCHLIST (ENHANCED)
            # ================================================================
            html.Div(
                className="card",
                children=[
                    html.Div(
                        style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "marginBottom": "12px"},
                        children=[
                            html.H2("Stock Watchlist", className="card-title", style={"margin": "0"}),
                            html.Span("Track live prices & load stocks into dashboard", className="status-text"),
                        ],
                    ),
                    html.Div(id="watchlist-container"),
                ],
            ),

            # ================================================================
            # SECTION 9 — VIRTUAL PORTFOLIO
            # ================================================================
            html.Div(
                className="card",
                id="portfolio-section",
                children=[
                    html.H2("Virtual Paper-Trading Portfolio ($50,000 Starting Cash)", className="card-title"),
                    html.P(
                        "Simulate buying and selling stocks with virtual money to test your strategies.",
                        className="status-text",
                        style={"marginBottom": "16px"},
                    ),
                    html.Div(
                        className="stats-grid",
                        children=[
                            _stat_box("Available Cash", "port-cash"),
                            _stat_box("Holdings Value", "port-holdings-value"),
                            _stat_box("Total Portfolio Value", "port-total-value"),
                            _stat_box("Total Profit / Loss", "port-pl"),
                        ],
                    ),
                    # Buy / Sell form with Interactive Stepper Buttons (- / +)
                    html.Div(
                        className="trade-row",
                        style={"marginTop": "20px"},
                        children=[
                            html.Div(
                                className="trade-box",
                                children=[
                                    html.H3("Buy Shares", className="trade-title", style={"color": "#4ade80"}),
                                    html.Div(
                                        className="trade-inputs",
                                        children=[
                                            dcc.Input(
                                                id="buy-ticker-input",
                                                type="text",
                                                placeholder="Ticker (e.g. AAPL)",
                                                className="trade-input",
                                            ),
                                            html.Label("Share Quantity:", style={"color": "#cbd5e1", "fontSize": "12px", "fontWeight": "600", "marginTop": "4px"}),
                                            html.Div(
                                                className="stepper-row",
                                                children=[
                                                    html.Button("-", id="buy-minus-btn", n_clicks=0, className="stepper-btn"),
                                                    dcc.Input(
                                                        id="buy-shares-input",
                                                        type="number",
                                                        min=1,
                                                        value=1,
                                                        className="trade-input stepper-input",
                                                    ),
                                                    html.Button("+", id="buy-plus-btn", n_clicks=0, className="stepper-btn"),
                                                ],
                                            ),
                                        ],
                                    ),
                                    html.Button(
                                        "BUY SHARES",
                                        id="buy-button",
                                        n_clicks=0,
                                        className="buy-button",
                                    ),
                                    html.P("", id="buy-status", className="status-text"),
                                ],
                            ),
                            html.Div(
                                className="trade-box",
                                children=[
                                    html.H3("Sell Shares", className="trade-title", style={"color": "#f87171"}),
                                    html.Div(
                                        className="trade-inputs",
                                        children=[
                                            dcc.Input(
                                                id="sell-ticker-input",
                                                type="text",
                                                placeholder="Ticker (e.g. AAPL)",
                                                className="trade-input",
                                            ),
                                            html.Label("Share Quantity:", style={"color": "#cbd5e1", "fontSize": "12px", "fontWeight": "600", "marginTop": "4px"}),
                                            html.Div(
                                                className="stepper-row",
                                                children=[
                                                    html.Button("-", id="sell-minus-btn", n_clicks=0, className="stepper-btn"),
                                                    dcc.Input(
                                                        id="sell-shares-input",
                                                        type="number",
                                                        min=1,
                                                        value=1,
                                                        className="trade-input stepper-input",
                                                    ),
                                                    html.Button("+", id="sell-plus-btn", n_clicks=0, className="stepper-btn"),
                                                ],
                                            ),
                                        ],
                                    ),
                                    html.Button(
                                        "SELL SHARES",
                                        id="sell-button",
                                        n_clicks=0,
                                        className="sell-button",
                                    ),
                                    html.P("", id="sell-status", className="status-text"),
                                ],
                            ),
                        ],
                    ),
                    # Holdings & Transactions
                    html.Div(
                        style={"marginTop": "22px"},
                        children=[
                            html.H3("Current Portfolio Holdings", className="card-title", style={"fontSize": "15px"}),
                            html.Div(id="holdings-table-container"),
                        ],
                    ),
                    html.Div(
                        style={"marginTop": "22px"},
                        children=[
                            html.H3("Transaction History", className="card-title", style={"fontSize": "15px"}),
                            html.Div(id="transactions-table-container"),
                        ],
                    ),
                ],
            ),

        ],
    )
