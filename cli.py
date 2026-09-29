# cli.py
# WHY: The old terminal menu still works for learning and for Colab.
# The website is started with python app.py instead.

import webbrowser

from config import (
    APP_NAME,
    LONG_MOVING_AVERAGE_DAYS,
    PRICE_HISTORY_PERIOD,
    RSI_PERIOD_DAYS,
    SEARCH_MAX_RESULTS,
    SHORT_MOVING_AVERAGE_DAYS,
)
from news.pipeline import get_analyzed_news
from stocks.charts import show_technical_charts
from stocks.indicators import build_technical_snapshot, rsi_plain_english
from stocks.stock_data import fetch_price_history, fetch_stock_quote, search_securities
from utils.formatters import format_market_cap, format_number, format_price


def print_welcome():
    print("=" * 50)
    print(f"{APP_NAME} terminal menu")
    print("The website is: python app.py")
    print("=" * 50)
    print("1. Stock search (quote)")
    print("2. Technical analysis (moving averages, RSI, chart)")
    print("3. Company news (filtered + summarized)")
    print("Q. Quit")
    print()


def print_quote(quote):
    print()
    print("-" * 50)
    print(f"Ticker:          {quote['ticker']}")
    print(f"Company:         {quote['company_name']}")
    print(f"Current price:   {format_price(quote['current_price'])}")
    print(f"Previous close:  {format_price(quote['previous_close'])}")
    print(f"52-week high:    {format_price(quote['week_52_high'])}")
    print(f"52-week low:     {format_price(quote['week_52_low'])}")
    print(f"Market cap:      {format_market_cap(quote['market_cap'])}")
    print(f"Volume:          {format_number(quote['volume'])}")
    print("-" * 50)
    print()


def print_search_matches(matches):
    print()
    print("I found more than one match:")
    index = 1
    for match in matches:
        company_name = match["company_name"]
        if company_name is None:
            company_name = "Unknown company"
        exchange = match["exchange"]
        if exchange is None:
            exchange = "Unknown exchange"
        print(f"  {index}. {match['ticker']} - {company_name} ({exchange})")
        index += 1
    print()


def pick_match_from_list(matches):
    print_search_matches(matches)
    while True:
        choice = input("Pick a number (or C to cancel): ")
        cleaned_choice = choice.strip().upper()
        if cleaned_choice == "C":
            return None
        if not cleaned_choice.isdigit():
            print("Please type a number from the list.")
            continue
        choice_number = int(cleaned_choice)
        if choice_number < 1 or choice_number > len(matches):
            print("That number is not in the list.")
            continue
        return matches[choice_number - 1]


def choose_security(query):
    matches = search_securities(query, max_results=SEARCH_MAX_RESULTS)
    if len(matches) == 0:
        raise ValueError(
            f"No stocks found for '{query.strip()}'. "
            "Try a ticker like AAPL or a company name like Apple."
        )

    typed_text = query.strip().upper()
    for match in matches:
        if match["ticker"].upper() == typed_text:
            return match

    if len(matches) == 1:
        return matches[0]

    chosen_match = pick_match_from_list(matches)
    if chosen_match is None:
        raise ValueError("Search cancelled.")
    return chosen_match


def ask_for_chosen_security():
    user_input = input("Enter a company name or ticker: ")
    if user_input.strip() == "":
        raise ValueError("Please enter a company name or ticker.")
    return choose_security(user_input)


def format_optional_price(value):
    if value is None:
        return "Not enough history yet"
    return format_price(value)


def format_optional_rsi(value):
    if value is None:
        return "Not enough history yet"
    return f"{value:.1f}"


def print_technical_snapshot(ticker, company_name, snapshot):
    print()
    print("-" * 50)
    print(f"Ticker:                 {ticker}")
    print(f"Company:                {company_name}")
    print(f"Latest close:           {format_optional_price(snapshot['latest_close'])}")
    print(
        f"{SHORT_MOVING_AVERAGE_DAYS}-day moving average:  "
        f"{format_optional_price(snapshot['latest_ma_short'])}"
    )
    print(
        f"{LONG_MOVING_AVERAGE_DAYS}-day moving average:  "
        f"{format_optional_price(snapshot['latest_ma_long'])}"
    )
    print(f"RSI ({RSI_PERIOD_DAYS} days):            {format_optional_rsi(snapshot['latest_rsi'])}")
    print(rsi_plain_english(snapshot["latest_rsi"]))
    print("-" * 50)
    print()


def handle_stock_search():
    chosen = ask_for_chosen_security()
    quote = fetch_stock_quote(chosen["ticker"])
    print_quote(quote)


def handle_technical_analysis():
    chosen = ask_for_chosen_security()
    history = fetch_price_history(chosen["ticker"], period=PRICE_HISTORY_PERIOD)
    snapshot = build_technical_snapshot(
        history["closing_prices"],
        SHORT_MOVING_AVERAGE_DAYS,
        LONG_MOVING_AVERAGE_DAYS,
        RSI_PERIOD_DAYS,
    )
    print_technical_snapshot(chosen["ticker"], chosen["company_name"], snapshot)
    print("Opening the chart window. Close it to continue.")
    show_technical_charts(
        chosen["ticker"],
        history["dates"],
        history["closing_prices"],
        snapshot["ma_short_list"],
        snapshot["ma_long_list"],
        snapshot["rsi_list"],
        SHORT_MOVING_AVERAGE_DAYS,
        LONG_MOVING_AVERAGE_DAYS,
    )


def print_articles(ticker, company_name, news_pack):
    print()
    print("-" * 50)
    print(f"News for {company_name} ({ticker})")
    print(f"Raw Yahoo items: {news_pack['raw_count']} | Kept: {news_pack['kept_count']}")
    if news_pack["used_fallback"]:
        print("No strong matches, so the closest headlines are shown.")
    print("-" * 50)

    index = 1
    for article in news_pack["articles"]:
        print(f"{index}. {article['title']}")
        print(f"   Source:     {article['source']}")
        print(f"   Date:       {article['published_date']}")
        print(f"   Relevance:  {article.get('relevance_label')} ({article.get('relevance_score')})")
        print(f"   Sentiment:  {article['sentiment']} ({article['confidence']}%)")
        print(f"   Why:        {article['explanation']}")
        print(f"   Summary:    {article['easy_summary']}")
        print(f"   Link:       {article['url']}")
        print()
        index += 1


def handle_company_news():
    chosen = ask_for_chosen_security()
    news_pack = get_analyzed_news(chosen["ticker"], chosen["company_name"])
    if news_pack["kept_count"] == 0:
        print(f"No news found for {chosen['ticker']}.")
        print()
        return

    print_articles(chosen["ticker"], chosen["company_name"], news_pack)
    choice = input("Type a number to open an article (or Enter to go back): ")
    cleaned_choice = choice.strip()
    if cleaned_choice == "":
        return
    if not cleaned_choice.isdigit():
        print("Please type a number from the list.")
        print()
        return
    choice_number = int(cleaned_choice)
    articles = news_pack["articles"]
    if choice_number < 1 or choice_number > len(articles):
        print("That number is not in the list.")
        print()
        return
    article = articles[choice_number - 1]
    print()
    print("Opening this article:")
    print(article["url"])
    print()
    webbrowser.open(article["url"])


def run_menu():
    while True:
        print_welcome()
        choice = input("Choose an option: ")
        cleaned_choice = choice.strip().upper()
        if cleaned_choice == "Q":
            print("Goodbye!")
            break
        try:
            if cleaned_choice == "1":
                handle_stock_search()
            elif cleaned_choice == "2":
                handle_technical_analysis()
            elif cleaned_choice == "3":
                handle_company_news()
            else:
                print("Please choose 1, 2, 3, or Q.")
                print()
        except ValueError as error:
            print(f"Oops: {error}")
            print()
        except ConnectionError as error:
            print(f"Oops: {error}")
            print()


def main():
    run_menu()


if __name__ == "__main__":
    main()
