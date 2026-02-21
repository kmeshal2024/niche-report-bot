"""
Report generator for the Niche AI Report Subscription system.
Builds a prompt from scraped articles and calls OpenAI (gpt-4o-mini) to produce a weekly digest.
"""

import logging
from typing import Any

from openai import OpenAI

from config import NICHE_DESCRIPTION, NICHE_NAME, OPENAI_API_KEY, REPORT_LANGUAGE

logger = logging.getLogger(__name__)


def _build_articles_context(articles: list[dict[str, Any]]) -> str:
    """Format article list into a string block for the prompt."""
    lines = []
    for i, a in enumerate(articles, 1):
        lines.append(
            f"[{i}] Title: {a.get('title', '')}\n"
            f"    Summary: {a.get('summary', '')}\n"
            f"    Link: {a.get('link', '')}\n"
            f"    Published: {a.get('published', '')}"
        )
    return "\n\n".join(lines)


def generate_report(articles: list[dict[str, Any]]) -> str:
    """
    Generate a 600-word professional weekly digest from the given articles.

    Uses NICHE_NAME and NICHE_DESCRIPTION in the prompt. Instructs GPT to produce:
    - Header (issue number + date)
    - Executive Summary (2-3 sentences)
    - Top 3 Key Developments (title, explanation, why it matters)
    - Opportunities & Risks
    - Action Items (3 bullet points)
    - Sources list with links

    Calls OpenAI API with model gpt-4o-mini, temperature 0.7. Logs token usage.

    Returns:
        Raw report text from the model.
    """
    if not OPENAI_API_KEY or not OPENAI_API_KEY.strip():
        raise ValueError("OPENAI_API_KEY is not set. Add it to your .env file.")

    articles_context = _build_articles_context(articles)

    system = (
        f"You are a professional analyst writing a weekly digest for: {NICHE_NAME}. "
        f"Context: {NICHE_DESCRIPTION}. "
        f"Write in {REPORT_LANGUAGE}. Be concise, factual, and actionable. "
        "Output only the report body (no meta-commentary). Use clear section headings."
    )
    user = (
        f"Using the following articles, write a professional weekly digest of approximately 600 words.\n\n"
        "Structure the report exactly as follows:\n\n"
        "1. **Header**: Issue number and date (e.g. 'Issue #1 — [date]').\n"
        "2. **Executive Summary**: 2–3 sentences summarizing the week's main takeaways.\n"
        "3. **Top 3 Key Developments**: For each development include a title, a short explanation, and 'Why it matters' in one line.\n"
        "4. **Opportunities & Risks**: One short paragraph on opportunities and one on risks.\n"
        "5. **Action Items**: Exactly 3 bullet points for the reader.\n"
        "6. **Sources**: A list of source titles with their URLs (use the links from the articles).\n\n"
        "Articles to use:\n\n"
        f"{articles_context}"
    )

    client = OpenAI(api_key=OPENAI_API_KEY)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.7,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )

    usage = getattr(response, "usage", None)
    if usage:
        logger.info(
            "Token usage: prompt=%s, completion=%s, total=%s",
            getattr(usage, "prompt_tokens", "?"),
            getattr(usage, "completion_tokens", "?"),
            getattr(usage, "total_tokens", "?"),
        )

    content = response.choices[0].message.content
    return content or ""
