"""
Configuration loader for the Niche AI Report Subscription system.
Loads all environment variables using python-dotenv.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root
_env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=_env_path)


def _get_env(key: str, default: str | None = None) -> str:
    """Get required or optional env variable."""
    value = os.getenv(key, default)
    if value is None and default is None:
        raise ValueError(f"Missing required environment variable: {key}")
    return value or ""


# Required
OPENAI_API_KEY: str = _get_env("OPENAI_API_KEY", "")
NICHE_NAME: str = _get_env("NICHE_NAME", "Niche Report")
NICHE_DESCRIPTION: str = _get_env("NICHE_DESCRIPTION", "Weekly intelligence digest")
REPORT_LANGUAGE: str = _get_env("REPORT_LANGUAGE", "English")

# RSS feeds: comma-separated string → list of valid URLs only (must start with https:// or http://)
RSS_FEEDS_RAW: str = _get_env("RSS_FEEDS", "")
_all: list[str] = [
    u.strip().strip("\r\n") for s in RSS_FEEDS_RAW.replace("\n", ",").split(",") for u in [s.strip()] if u
]
RSS_FEEDS: list[str] = [
    u for u in _all
    if u and (u.startswith("http://") or u.startswith("https://"))
]
if len(_all) > len(RSS_FEEDS):
    import logging
    logging.getLogger(__name__).warning(
        "Skipped %s invalid feed(s): each URL must start with https:// or http:// (no spaces or line breaks).",
        len(_all) - len(RSS_FEEDS),
    )
if not RSS_FEEDS:
    raise ValueError(
        "RSS_FEEDS has no valid URLs. Set comma-separated URLs in .env or GitHub secret, e.g. "
        "RSS_FEEDS=https://example.com/feed1.xml,https://example.com/feed2.xml"
    )

# Optional with defaults
MAX_ARTICLES_PER_FEED: int = int(os.getenv("MAX_ARTICLES_PER_FEED", "5"))

# Unsubscribe link in report footer (e.g. your Beehiiv manage/unsubscribe URL)
UNSUBSCRIBE_URL: str = os.getenv("UNSUBSCRIBE_URL", "").strip() or "#"
