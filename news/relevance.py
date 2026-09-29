# relevance.py
# WHY: Yahoo's news feed mixes in loosely related market stories.
# We do not change Yahoo. We score each article AFTER we download it
# and keep the ones that actually mention this company.

from config import NEWS_RELEVANCE_THRESHOLD


def _clean_text(text):
    if text is None:
        return ""
    return str(text).lower()


def build_company_keywords(company_name, ticker):
    """
    Build a short list of phrases we will look for.

    Example:
        ticker = AAPL
        company_name = Apple Inc.
        keywords -> ["aapl", "apple inc.", "apple"]
    """
    keywords = []
    if ticker:
        keywords.append(ticker.lower().strip())

    if company_name:
        full_name = company_name.lower().strip()
        keywords.append(full_name)

        short_name = full_name
        extra_words = [
            " incorporated",
            " corporation",
            " company",
            " holdings",
            " limited",
            " inc.",
            " inc",
            " corp.",
            " corp",
            " ltd.",
            " ltd",
            " plc",
            " co.",
            " co",
        ]
        for extra in extra_words:
            short_name = short_name.replace(extra, "")
        short_name = short_name.strip(" .,")
        if short_name != "" and short_name not in keywords:
            keywords.append(short_name)

    return keywords


def score_article(article, company_name, ticker):
    """
    Give the article points based on WHERE the company is mentioned.

    Title matches score higher than summary matches.
    Returns a dictionary with score, label, and a short reason.
    """
    title = _clean_text(article.get("title", ""))
    summary = _clean_text(article.get("summary", ""))
    ticker_text = _clean_text(ticker)
    keywords = build_company_keywords(company_name, ticker)

    score = 0
    reasons = []

    if ticker_text != "" and ticker_text in title:
        score += 40
        reasons.append("ticker in title")

    for keyword in keywords:
        if keyword == ticker_text:
            continue
        if keyword != "" and keyword in title:
            score += 35
            reasons.append("company name in title")
            break

    if ticker_text != "" and ticker_text in summary:
        score += 20
        reasons.append("ticker in summary")

    for keyword in keywords:
        if keyword == ticker_text:
            continue
        if keyword != "" and keyword in summary:
            score += 15
            reasons.append("company name in summary")
            break

    if score >= 35:
        label = "High"
    elif score >= NEWS_RELEVANCE_THRESHOLD:
        label = "Medium"
    else:
        label = "Low"

    if len(reasons) == 0:
        reason_text = "No clear mention of this company"
    else:
        reason_text = "; ".join(reasons)

    return {
        "relevance_score": score,
        "relevance_label": label,
        "relevance_reason": reason_text,
    }


def is_relevant(article, company_name, ticker):
    """True when the article scores at or above the threshold."""
    details = score_article(article, company_name, ticker)
    return details["relevance_score"] >= NEWS_RELEVANCE_THRESHOLD


def _article_copy_with_score(article, details):
    """Make a new dictionary so we do not change Yahoo's original item in place."""
    copied = {}
    for key in article:
        copied[key] = article[key]
    copied["relevance_score"] = details["relevance_score"]
    copied["relevance_label"] = details["relevance_label"]
    copied["relevance_reason"] = details["relevance_reason"]
    return copied


def remove_duplicate_articles(articles):
    """Drop repeats that share the same link or the same title."""
    unique_articles = []
    seen_urls = []
    seen_titles = []

    for article in articles:
        url = _clean_text(article.get("url", ""))
        title = _clean_text(article.get("title", ""))

        if url != "" and url in seen_urls:
            continue
        if title != "" and title in seen_titles:
            continue

        unique_articles.append(article)
        if url != "":
            seen_urls.append(url)
        if title != "":
            seen_titles.append(title)

    return unique_articles


def filter_relevant_articles(articles, company_name, ticker, max_articles=8):
    """
    Score, drop duplicates, keep relevant stories, sort best-first.

    If NOTHING passes the threshold, we still return the closest few
    so the news card is not empty. Those are marked as a fallback.
    """
    unique_articles = remove_duplicate_articles(articles)
    scored_articles = []

    for article in unique_articles:
        details = score_article(article, company_name, ticker)
        scored_articles.append(_article_copy_with_score(article, details))

    def sort_key(item):
        # Higher score first. Title matches already have bigger scores.
        return item["relevance_score"]

    scored_articles.sort(key=sort_key, reverse=True)

    relevant = []
    for article in scored_articles:
        if article["relevance_score"] >= NEWS_RELEVANCE_THRESHOLD:
            article["used_fallback"] = False
            relevant.append(article)

    if len(relevant) > 0:
        return relevant[:max_articles]

    fallback = []
    for article in scored_articles[:3]:
        article["used_fallback"] = True
        fallback.append(article)
    return fallback
