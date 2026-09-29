# news_fetcher.py
# WHY: Module 3's job is to get the latest headlines for one company.
# We keep Yahoo's nested news JSON in this file and return a simple list
# of dictionaries the rest of the app can print.

import logging
from datetime import datetime

import yfinance as yf

logging.getLogger("yfinance").setLevel(logging.CRITICAL)


def _format_published_date(raw_date):
    """
    Yahoo may send a date as text ('2026-09-23T19:50:58Z')
    or as a Unix timestamp (seconds since 1970).

    We turn either one into: 2026-09-23 19:50
    """
    if raw_date is None or raw_date == "":
        return "Unknown date"

    if isinstance(raw_date, (int, float)):
        try:
            parsed = datetime.fromtimestamp(raw_date)
            return parsed.strftime("%Y-%m-%d %H:%M")
        except (OSError, OverflowError, ValueError):
            return "Unknown date"

    text_date = str(raw_date).replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text_date)
        return parsed.strftime("%Y-%m-%d %H:%M")
    except ValueError:
        return str(raw_date)


def _strip_simple_html(text):
    """
    Yahoo descriptions sometimes include tags like <p> or <a>.
    We walk the string once and keep only normal characters.
    """
    if text is None:
        return ""

    cleaned_characters = []
    inside_tag = False
    for character in str(text):
        if character == "<":
            inside_tag = True
        elif character == ">":
            inside_tag = False
        elif inside_tag is False:
            cleaned_characters.append(character)

    cleaned_text = "".join(cleaned_characters)
    return cleaned_text.strip()


def _read_nested_url(content):
    """Yahoo stores the article link inside a small dictionary."""
    for key in ["canonicalUrl", "clickThroughUrl"]:
        url_info = content.get(key)
        if isinstance(url_info, dict):
            url = url_info.get("url")
            if url:
                return url
        elif isinstance(url_info, str) and url_info != "":
            return url_info
    return None


def _parse_yahoo_article(item):
    """
    Turn one messy Yahoo news item into a clean dictionary:

        title, source, published_date, url, summary
    """
    content = item.get("content")

    # Newer yfinance: fields live under item["content"]
    if isinstance(content, dict):
        title = content.get("title")
        provider = content.get("provider")
        source = None
        if isinstance(provider, dict):
            source = provider.get("displayName")
        published_raw = content.get("pubDate")
        url = _read_nested_url(content)
        summary = content.get("summary")
        if summary is None:
            summary = content.get("description")
    else:
        # Older yfinance: fields were at the top level
        title = item.get("title")
        source = item.get("publisher")
        published_raw = item.get("providerPublishTime")
        url = item.get("link")
        summary = item.get("summary")

    if title is None or str(title).strip() == "":
        return None
    if url is None or str(url).strip() == "":
        return None

    if source is None or str(source).strip() == "":
        source = "Unknown source"

    article = {
        "title": str(title).strip(),
        "source": str(source).strip(),
        "published_date": _format_published_date(published_raw),
        "url": str(url).strip(),
        "summary": _strip_simple_html(summary),
    }
    return article


def fetch_company_news(ticker_symbol, max_articles=8):
    """
    Download the latest news for one ticker.

    Returns:
        a list of article dictionaries
    """
    cleaned_symbol = ticker_symbol.strip().upper()
    if cleaned_symbol == "":
        raise ValueError("Please enter a ticker symbol.")

    try:
        stock = yf.Ticker(cleaned_symbol)
        raw_news = stock.news
    except Exception as error:
        raise ConnectionError(
            "Could not download news. Check your internet connection."
        ) from error

    if not raw_news:
        return []

    articles = []
    for item in raw_news:
        article = _parse_yahoo_article(item)
        if article is None:
            continue
        articles.append(article)
        if len(articles) >= max_articles:
            break

    return articles
