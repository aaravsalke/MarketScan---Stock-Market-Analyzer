# sentiment.py
# WHY: Analyzes stock news headlines and previews to produce Positive / Neutral / Negative tone.
#
# If a Groq API key is present in .env, it calls Groq's fast LLM model for AI sentiment.
# Otherwise, it uses our local, enhanced financial rule engine with negation handling
# and financial phrase weighting.

import re
from news.ai_groq import analyze_sentiment_groq, is_groq_available

# High-impact multi-word financial phrases and their scores
FINANCIAL_PHRASES = {
    # Strong Positive (+3 points)
    "beat estimates": 3,
    "beats estimates": 3,
    "beat expectations": 3,
    "beats expectations": 3,
    "record revenue": 3,
    "record profit": 3,
    "record high": 3,
    "strong earnings": 3,
    "loss narrowed": 3,
    "losses narrowed": 3,
    "upgraded to buy": 3,
    "raised guidance": 3,
    "raises guidance": 3,
    "all-time high": 3,
    
    # Moderate Positive (+2 points)
    "profit surge": 2,
    "revenue growth": 2,
    "dividend increase": 2,
    "stock jumps": 2,
    "shares rally": 2,
    "shares surge": 2,
    "outperform": 2,
    "bullish outlook": 2,
    "market gain": 2,
    "partnership announced": 2,

    # Strong Negative (-3 points)
    "missed estimates": -3,
    "misses estimates": -3,
    "missed expectations": -3,
    "misses expectations": -3,
    "lowered guidance": -3,
    "lowers guidance": -3,
    "bankruptcy filing": -3,
    "sec investigation": -3,
    "downgraded to sell": -3,
    "record loss": -3,
    "all-time low": -3,

    # Moderate Negative (-2 points)
    "profit decline": -2,
    "profit drops": -2,
    "shares plunge": -2,
    "stock tumbles": -2,
    "shares slump": -2,
    "lawsuit filed": -2,
    "recalls products": -2,
    "regulatory fine": -2,
    "layoffs announced": -2,
    "cuts jobs": -2,
}

POSITIVE_WORDS = {
    "gain", "gains", "gained", "surge", "surges", "surged", "rally", "rallies", "rallied",
    "record", "beat", "beats", "growth", "profit", "profits", "profitable", "upgrade",
    "upgrades", "upgraded", "strong", "bullish", "outperform", "high", "higher", "rise",
    "rises", "risen", "rose", "jump", "jumps", "jumped", "positive", "success", "successful",
    "win", "wins", "won", "boost", "boosts", "boosted", "soar", "soars", "soared"
}

NEGATIVE_WORDS = {
    "loss", "losses", "fall", "falls", "fallen", "fell", "drop", "drops", "dropped",
    "decline", "declines", "declined", "miss", "misses", "missed", "lawsuit", "fine",
    "recall", "recalls", "weak", "weakness", "bearish", "downgrade", "downgrades",
    "downgraded", "cut", "cuts", "risk", "risks", "warning", "warnings", "crash",
    "crashes", "crashed", "plunge", "plunges", "plunged", "slump", "slumps", "slumped",
    "negative", "fear", "panic", "tumble", "tumbles", "tumbled"
}

NEGATION_WORDS = {"not", "no", "neither", "nor", "never", "without", "hardly", "barely", "doesn't", "don't", "didn't", "won't"}


def _clean_text(text):
    if text is None:
        return ""
    return str(text).lower().strip()


def analyze_sentiment_local(article):
    """
    Local Enhanced Financial Rule Engine:
    - Checks multi-word financial phrases first
    - Scans words while handling negations ("not bad", "no decline")
    - Gives 1.5x weight to title over preview summary
    """
    title = _clean_text(article.get("title", ""))
    summary = _clean_text(article.get("summary", ""))
    company_name = _clean_text(article.get("company_name", ""))
    ticker = _clean_text(article.get("ticker", ""))

    full_text = f"{title} {summary}"

    score = 0.0
    matched_reasons = []

    # 1. Check Multi-Word Financial Phrases
    for phrase, phrase_score in FINANCIAL_PHRASES.items():
        if phrase in full_text:
            multiplier = 1.5 if phrase in title else 1.0
            added = phrase_score * multiplier
            score += added
            matched_reasons.append(f"'{phrase}' ({'+' if added > 0 else ''}{added:.1f})")

    # 2. Tokenized Word Analysis with Negation Window
    words = re.findall(r'\b[a-z\']+\b', full_text)
    
    for i, word in enumerate(words):
        # Look back up to 2 words for negation
        is_negated = False
        if i > 0 and words[i-1] in NEGATION_WORDS:
            is_negated = True
        elif i > 1 and words[i-2] in NEGATION_WORDS:
            is_negated = True

        weight = 1.5 if word in title else 1.0

        if word in POSITIVE_WORDS:
            if is_negated:
                score -= 1.0 * weight
                matched_reasons.append(f"negated '{word}' (-{weight})")
            else:
                score += 1.0 * weight
                matched_reasons.append(f"'{word}' (+{weight})")
        elif word in NEGATIVE_WORDS:
            if is_negated:
                score += 1.0 * weight
                matched_reasons.append(f"negated '{word}' (+{weight})")
            else:
                score -= 1.0 * weight
                matched_reasons.append(f"'{word}' (-{weight})")

    # Determine Final Sentiment Label & Confidence
    if score >= 1.5:
        sentiment = "Positive"
        confidence = min(95, 60 + int(abs(score) * 8))
        explanation = f"Positive financial tone detected ({', '.join(matched_reasons[:3])})."
    elif score <= -1.5:
        sentiment = "Negative"
        confidence = min(95, 60 + int(abs(score) * 8))
        explanation = f"Negative financial tone detected ({', '.join(matched_reasons[:3])})."
    else:
        sentiment = "Neutral"
        confidence = 60
        if matched_reasons:
            explanation = f"Balanced tone with mixed financial cues ({', '.join(matched_reasons[:3])})."
        else:
            explanation = "Neutral tone with no strong positive or negative financial keywords."

    return {
        "sentiment": sentiment,
        "confidence": confidence,
        "explanation": explanation,
        "source": "Rule Engine",
    }


def analyze_sentiment(article, company_name="", ticker=""):
    """
    Main Sentiment Entrypoint:
    Uses Groq AI if key is set, otherwise falls back to local rule engine.
    """
    title = article.get("title", "")
    summary = article.get("summary", "")

    # Try Groq AI first if available
    if is_groq_available():
        ai_res = analyze_sentiment_groq(title, summary, company_name or article.get("company_name", ""), ticker or article.get("ticker", ""))
        if ai_res:
            return ai_res

    # Fallback to smart local rule engine
    return analyze_sentiment_local(article)


def summarize_sentiment_counts(articles):
    """Summarize counts of positive, neutral, and negative articles."""
    counts = {"Positive": 0, "Neutral": 0, "Negative": 0}
    for article in articles:
        label = article.get("sentiment", "Neutral")
        if label in counts:
            counts[label] += 1
        else:
            counts["Neutral"] += 1

    if counts["Positive"] > counts["Negative"] and counts["Positive"] >= counts["Neutral"]:
        overall = "Positive"
    elif counts["Negative"] > counts["Positive"] and counts["Negative"] >= counts["Neutral"]:
        overall = "Negative"
    else:
        overall = "Neutral"

    return {
        "positive": counts["Positive"],
        "neutral": counts["Neutral"],
        "negative": counts["Negative"],
        "overall": overall,
    }
