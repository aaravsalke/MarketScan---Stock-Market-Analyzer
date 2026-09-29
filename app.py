# app.py
# WHY: Front door of MarketScan.
# Running this file starts the Dash website on localhost.

import os
import sys

# Ensure the root project directory is on sys.path so modules can always be imported
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from config import APP_NAME, DASH_HOST, DASH_PORT
from ui.dashboard import create_app


def main():
    app = create_app()
    print(f"\n==================================================")
    print(f"  {APP_NAME} Dashboard is starting...")
    print(f"  Open this link in your browser: http://{DASH_HOST}:{DASH_PORT}/")
    print(f"  Press CTRL+C in the terminal to stop the server.")
    print(f"==================================================\n")
    
    app.run(host=DASH_HOST, port=DASH_PORT, debug=False)


if __name__ == "__main__":
    main()
