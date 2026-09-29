# pipeline.py
# WHY: Runs the news processing pipeline:
# fetch -> clean -> relevance filter -> summary (AI/local) -> sentiment (AI/local)

from config import NEWS_FETCH_LIMIT, NEWS_MAX_ARTICLES
from news.news_fetcher import fetch_company_news
from news.relevance import filter_relevant_articles
from news.sentiment import analyze_sentiment, summarize_sentiment_counts
from news.summarizer import summarize_article


def get_analyzed_news(ticker, company_name):
    """
    Download news for one ticker and return:
    - a list of relevant articles (with summary + sentiment)
    - a small overall sentiment dictionary
    - used_fallback: True if we had to show weaker matches
    """
    raw_articles = fetch_company_news(ticker, max_articles=NEWS_FETCH_LIMIT)
    relevant_articles = filter_relevant_articles(
        raw_articles,
        company_name,
        ticker,
        max_articles=NEWS_MAX_ARTICLES,
    )

    analyzed = []
    used_fallback = False
    for article in relevant_articles:
        if article.get("used_fallback") is True:
            used_fallback = True

        easy_summary = summarize_article(article, company_name=company_name)
        sentiment = analyze_sentiment(article, company_name=company_name, ticker=ticker)

        row = {}
        for key in article:
            row[key] = article[key]
        row["easy_summary"] = easy_summary
        row["sentiment"] = sentiment["sentiment"]
        row["confidence"] = sentiment["confidence"]
        row["explanation"] = sentiment["explanation"]
        row["source_type"] = sentiment.get("source", "Engine")
        analyzed.append(row)

    counts = summarize_sentiment_counts(analyzed)
    return {
        "articles": analyzed,
        "sentiment_counts": counts,
        "used_fallback": used_fallback,
        "raw_count": len(raw_articles),
        "kept_count": len(analyzed),
    }
