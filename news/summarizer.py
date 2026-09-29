# summarizer.py
# WHY: Module 4 turns a headline + Yahoo preview into 2-3 easy sentences.
# Uses Groq AI if available, or clean fallback parsing when offline.

from news.ai_groq import generate_ai_news_summary, is_groq_available


def split_into_sentences(text):
    """Split text on '.', '!', or '?' without extra libraries."""
    if text is None:
        return []

    sentences = []
    current = ""
    for character in str(text).strip():
        current += character
        if character in ".!?":
            piece = current.strip()
            if len(piece) > 1:
                sentences.append(piece)
            current = ""

    leftover = current.strip()
    if leftover != "":
        sentences.append(leftover)

    return sentences


def summarize_article(article, company_name=""):
    """
    Build a 2-3 sentence summary a high-school student can read.

    1. If Groq API is available, use Groq AI for plain-English explanation.
    2. Fall back to local sentence extraction.
    """
    title = str(article.get("title", "")).strip()
    preview = str(article.get("summary", "")).strip()

    if is_groq_available():
        ai_summary = generate_ai_news_summary(title, preview, company_name or article.get("company_name", ""))
        if ai_summary:
            return ai_summary

    # Fallback local summary
    sentences = split_into_sentences(preview)

    chosen = []
    for sentence in sentences:
        chosen.append(sentence)
        if len(chosen) >= 3:
            break

    if len(chosen) == 0:
        if title == "":
            return "Yahoo did not include a preview for this article."
        return (
            title + ". "
            "Yahoo did not include a longer preview, so this is the headline only."
        )

    if len(chosen) == 1 and title != "" and title.lower() not in chosen[0].lower():
        return title + ". " + chosen[0]

    return " ".join(chosen)
