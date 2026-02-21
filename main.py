"""
Niche AI Report Subscription — main pipeline.
Orchestrates: load config → scrape → generate report → format and save.
"""

import logging
import sys
from pathlib import Path

from config import NICHE_NAME, RSS_FEEDS
from formatter import format_and_save
from report_generator import generate_report
from scraper import scrape_articles

# Log to stdout so GitHub Actions and terminal show progress
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

# Rough cost estimate: gpt-4o-mini ~$0.15/1M input, ~$0.60/1M output; ~600 words ≈ 800 tokens out + prompt
COST_ESTIMATE_PER_RUN = "$0.01–0.03"


def main() -> None:
    """Run the full pipeline: config → scrape → generate → format and save."""
    print("Loading config...")
    print(f"  Niche: {NICHE_NAME}")
    print(f"  Feeds: {len(RSS_FEEDS)} configured")
    if len(RSS_FEEDS) == 0:
        raise ValueError(
            "No valid RSS feed URLs. Set RSS_FEEDS to comma-separated URLs, each starting with https:// or http:// "
            "(e.g. https://news.google.com/rss/search?q=example&hl=en)."
        )

    print("Scraping articles from RSS feeds...")
    articles = scrape_articles()
    print(f"  Found {len(articles)} articles (after deduplication)")

    if len(articles) < 3:
        raise ValueError(
            f"Not enough articles to generate a report (found {len(articles)}, need at least 3). "
            "Check RSS_FEEDS in .env and try again."
        )

    print("Generating report via OpenAI (gpt-4o-mini)...")
    raw_report = generate_report(articles)

    print("Formatting and saving HTML + TXT...")
    html_path, txt_path = format_and_save(raw_report)

    print("Done.")
    print(f"  HTML: {html_path}")
    print(f"  TXT:  {txt_path}")
    print(f"  Cost estimate: ~{COST_ESTIMATE_PER_RUN} per run (~$0.50–1/month if weekly)")


if __name__ == "__main__":
    try:
        main()
    except ValueError as e:
        logger.error("Configuration or data error: %s", e)
        sys.exit(1)
    except FileNotFoundError as e:
        logger.error("File error: %s", e)
        sys.exit(1)
    except Exception as e:
        logger.exception("Pipeline failed: %s", e)
        sys.exit(1)
