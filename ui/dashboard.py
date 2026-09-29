# dashboard.py
# WHY: This file builds the Dash website and attaches the callbacks.

from pathlib import Path
from dash import Dash

from ui.callbacks import register_callbacks
from ui.layout import build_layout

UI_FOLDER = Path(__file__).resolve().parent

INDEX_STRING = """<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            /* Embedded high-priority dark theme styles for all React-Select Dropdowns */
            .Select, .Select-control, .dash-dropdown, .custom-dropdown,
            div[class*="Select"], div[class*="select__control"], div[class*="select__value-container"] {
                background-color: #1e293b !important;
                background: #1e293b !important;
                border: 1px solid #475569 !important;
                border-radius: 10px !important;
                color: #ffffff !important;
            }
            .Select-value, .Select-value-label, div[class*="select__single-value"] {
                color: #ffffff !important;
                font-weight: 600 !important;
            }
            .Select-placeholder, div[class*="select__placeholder"] {
                color: #94a3b8 !important;
            }
            .Select-menu-outer, .Select-menu, div[class*="select__menu"],
            div[class*="select__menu-list"], div[class*="VirtualizedSelect"],
            .Select-menu-outer div, .Select-menu div, div[class*="VirtualizedSelect"] div {
                background-color: #0f172a !important;
                background: #0f172a !important;
                color: #f8fafc !important;
            }
            .Select-menu-outer {
                border: 1px solid #334155 !important;
                border-radius: 10px !important;
                box-shadow: 0 12px 28px rgba(0, 0, 0, 0.7) !important;
            }
            .Select-menu-outer input, .Select-menu input, .Select-input > input,
            div[class*="select__input"] > input, div[class*="Select-input"] > input {
                background-color: #1e293b !important;
                background: #1e293b !important;
                color: #ffffff !important;
                border: 1px solid #475569 !important;
                border-radius: 8px !important;
            }
            .Select-option, .VirtualizedSelectOption, div[class*="select__option"] {
                background-color: #0f172a !important;
                background: #0f172a !important;
                color: #f8fafc !important;
                border-bottom: 1px solid #1e293b !important;
            }
            .Select-option.is-focused, .VirtualizedSelectFocusedOption,
            .Select-option:hover, .VirtualizedSelectOption:hover,
            div[class*="select__option--is-focused"] {
                background-color: #1e293b !important;
                background: #1e293b !important;
                color: #38bdf8 !important;
            }
            .Select-option.is-selected, .VirtualizedSelectSelectedOption,
            div[class*="select__option--is-selected"] {
                background-color: #0284c7 !important;
                background: #0284c7 !important;
                color: #ffffff !important;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>"""


def create_app():
    app = Dash(
        __name__,
        assets_folder=str(UI_FOLDER / "assets"),
        title="MarketScan",
        suppress_callback_exceptions=True,
    )
    app.index_string = INDEX_STRING
    app.layout = build_layout()
    register_callbacks(app)
    return app
