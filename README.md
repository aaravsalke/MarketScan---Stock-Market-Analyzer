# MarketScan

A student project for learning Python by building a stock research tool.

This app is built **one module at a time**. **Modules 1, 2, and 3** currently work.

Read `progress.txt` to see what is done, what is next, and how to continue.

## How to run (VS Code)

1. Open this folder in VS Code.
2. Create a virtual environment (recommended):

```bash
python -m venv .venv
```

3. Activate it:

- Windows PowerShell: `.venv\Scripts\Activate.ps1`
- macOS / Linux: `source .venv/bin/activate`

4. Install libraries:

```bash
pip install -r requirements.txt
```

5. Start the app:

```bash
python app.py
```

6. Menu:

- `1` quote
- `2` technical analysis
- `3` company news (then type an article number to open it)
- `Q` quit

You can search with a ticker (`AAPL`) or a company name (`Apple`).

## How to run (Google Colab)

1. Upload the project files to Colab (or copy them into cells).
2. Install libraries:

```python
!pip install yfinance matplotlib
```

3. Make sure Colab's working folder contains `app.py`, `config.py`, `stocks/`, `news/`, and `utils/`.
4. Run:

```python
!python app.py
```

In Colab, charts may appear as image output instead of a desktop window. News links are printed so you can click them even if a browser window does not open.

## Current folder structure

```
MarketScan/
├── app.py                 # Main application (text menu)
├── config.py              # App settings
├── progress.txt           # Handoff log for the next coding session
├── data/                  # Saved files (later modules)
├── stocks/
│   ├── stock_data.py      # Search companies and download quotes / history
│   ├── indicators.py      # Moving averages and RSI math
│   └── charts.py          # Price, moving average, and RSI charts
├── news/
│   └── news_fetcher.py    # Latest headlines for a ticker
├── utils/
│   └── formatters.py      # Turn big numbers into readable text
├── requirements.txt
└── README.md
```

Later modules will add summaries, sentiment, and `portfolio/`.

## Data source

Quotes, charts, and news come from **Yahoo Finance** through the free `yfinance` library. No API key is required.
