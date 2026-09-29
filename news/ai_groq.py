# ai_groq.py
# WHY: Uses Groq's fast LLM API to power financial sentiment, news explanations,
# and executive market summaries. Auto-detects supported models dynamically.

import json
import logging
import requests

from config import GROQ_API_KEY
from utils.formatters import get_currency_symbol

logger = logging.getLogger(__name__)

GROQ_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODELS_ENDPOINT = "https://api.groq.com/openai/v1/models"

_CACHED_MODEL = None


def is_groq_available():
    """Return True if a non-empty Groq API key is present."""
    return bool(GROQ_API_KEY and len(GROQ_API_KEY) > 5)


def _get_working_model():
    """Find the best available text generation model on Groq."""
    global _CACHED_MODEL
    if _CACHED_MODEL:
        return _CACHED_MODEL

    if not is_groq_available():
        return None

    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    preferred = [
        "openai/gpt-oss-20b",
        "openai/gpt-oss-120b",
        "qwen/qwen3.8-27b",
        "allam-2-7b",
        "llama-3.3-70b-versatile",
    ]

    try:
        resp = requests.get(GROQ_MODELS_ENDPOINT, headers=headers, timeout=4)
        if resp.status_code == 200:
            available_models = [m["id"] for m in resp.json().get("data", [])]
            for pref in preferred:
                if pref in available_models:
                    _CACHED_MODEL = pref
                    return _CACHED_MODEL
            for model_id in available_models:
                if "whisper" not in model_id and "guard" not in model_id and "orpheus" not in model_id:
                    _CACHED_MODEL = model_id
                    return _CACHED_MODEL
    except Exception as e:
        logger.warning(f"Failed to query Groq model list: {e}")

    _CACHED_MODEL = "openai/gpt-oss-20b"
    return _CACHED_MODEL


def _call_groq_api(system_prompt, user_prompt, temperature=0.2, json_mode=False):
    """
    Make a request to the Groq API.
    """
    if not is_groq_available():
        return None

    model = _get_working_model()
    if not model:
        return None

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperature,
        "max_tokens": 800,
    }

    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    try:
        response = requests.post(GROQ_ENDPOINT, headers=headers, json=payload, timeout=6)
        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"].strip()
            return content
        else:
            logger.warning(f"Groq API returned status code {response.status_code}: {response.text}")
            return None
    except Exception as err:
        logger.warning(f"Groq API call failed: {err}")
        return None


def analyze_sentiment_groq(title, summary, company_name, ticker):
    """
    Use Groq AI to classify financial sentiment accurately with context & reasoning.
    """
    if not is_groq_available():
        return None

    system_prompt = (
        "You are an expert financial sentiment analyst for stock market news. "
        "Analyze the tone specifically regarding the target stock/company. "
        "Return strictly a JSON object with keys: "
        '"sentiment" (must be "Positive", "Neutral", or "Negative"), '
        '"confidence" (integer 50-98), and '
        '"explanation" (1 crisp sentence explaining why).'
    )

    user_prompt = (
        f"Target Stock: {ticker} ({company_name})\n"
        f"Headline: {title}\n"
        f"Article Preview: {summary}\n\n"
        "Provide JSON output:"
    )

    raw_response = _call_groq_api(system_prompt, user_prompt, temperature=0.1, json_mode=True)
    if not raw_response:
        return None

    try:
        data = json.loads(raw_response)
        sentiment = data.get("sentiment", "").capitalize()
        if sentiment not in ["Positive", "Neutral", "Negative"]:
            sentiment = "Neutral"

        confidence = int(data.get("confidence", 75))
        confidence = max(50, min(98, confidence))

        explanation = str(data.get("explanation", "")).strip()
        if not explanation:
            explanation = f"AI classified sentiment as {sentiment} based on the news tone."

        return {
            "sentiment": sentiment,
            "confidence": confidence,
            "explanation": explanation,
            "source": "AI (Groq)",
        }
    except Exception as e:
        logger.warning(f"Failed to parse Groq sentiment JSON: {e}")
        return None


def generate_ai_news_summary(title, summary, company_name):
    """
    Generate an easy-to-understand 2-3 sentence breakdown for retail investors.
    """
    if not is_groq_available():
        return None

    system_prompt = (
        "You are a friendly financial educator. Explain this news article in 2-3 clear, simple sentences "
        "for a student or beginner investor. Avoid jargon, or explain jargon briefly. "
        "Do NOT give buy/sell recommendations."
    )

    user_prompt = f"Company: {company_name}\nHeadline: {title}\nSummary: {summary}\n\nClear Explanation:"

    return _call_groq_api(system_prompt, user_prompt, temperature=0.3)


def generate_market_summary_groq(quote, technical_info, news_articles, portfolio_tickers):
    """
    Institutional-grade executive AI analysis that works for ANY stock worldwide:
    Synthesizes company fundamentals, business model, valuation, technical signals, and recent headlines.
    """
    if not is_groq_available():
        return None

    system_prompt = (
        "You are MarketScan's Senior Equity Research AI. "
        "Provide a sharp, educational 3-bullet executive overview of the selected stock. "
        "Cover: \n"
        "1. Core Business & Competitive Position (What they do and their competitive moat)\n"
        "2. Valuation & Financial Fundamentals (Market cap, valuation/PE, growth drivers)\n"
        "3. Technical Trends & Key Risks to Watch (RSI momentum, headwinds or catalysts)\n"
        "Start each bullet point strictly with '• '. Format with bold titles like '• **Business & Moat:** ...'. "
        "Keep it educational, objective, and concise. Never give explicit buy or sell advice."
    )

    ticker = quote.get("ticker", "")
    company = quote.get("company_name", ticker)
    currency = quote.get("currency", "USD")
    sym = get_currency_symbol(currency)
    price = quote.get("current_price", "N/A")
    sector = quote.get("sector", "N/A")
    industry = quote.get("industry", "N/A")
    pe = quote.get("pe_ratio")
    pe_str = f"{pe:.1f}" if pe is not None else "N/A"
    summary_snippet = quote.get("business_summary", "")[:350]
    
    rsi_val = technical_info.get("rsi")
    rsi_str = f"{rsi_val:.1f}" if rsi_val is not None else "N/A"
    ma_status = technical_info.get("ma_status", "")

    if news_articles:
        headlines = "\n".join([f"- {a.get('title', '')}" for a in news_articles[:4]])
    else:
        headlines = "No major company-specific headlines reported today."

    user_prompt = (
        f"Company: {ticker} ({company})\n"
        f"Exchange Currency: {currency} ({sym})\n"
        f"Current Price: {sym}{price}\n"
        f"Sector: {sector} | Industry: {industry}\n"
        f"Valuation: P/E Ratio = {pe_str}\n"
        f"Business Overview: {summary_snippet}\n"
        f"Technicals: 14-day RSI = {rsi_str} | {ma_status}\n"
        f"Recent Headlines:\n{headlines}\n\n"
        "Executive Analysis (strictly 3 bullet points starting with '• '):"
    )

    return _call_groq_api(system_prompt, user_prompt, temperature=0.25)
