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

# RSS feeds: comma-separated string → list
RSS_FEEDS_RAW: str = _get_env("RSS_FEEDS", "")
RSS_FEEDS: list[str] = [u.strip() for u in RSS_FEEDS_RAW.split(",") if u.strip()]

# Optional with defaults
MAX_ARTICLES_PER_FEED: int = int(os.getenv("MAX_ARTICLES_PER_FEED", "5"))
