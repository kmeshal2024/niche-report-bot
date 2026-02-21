"""
RSS feed scraper for the Niche AI Report Subscription system.
Parses feeds with stdlib XML, extracts articles, cleans HTML with BeautifulSoup, and deduplicates by title.
"""

import logging
import xml.etree.ElementTree as ET
from typing import Any
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup

from config import MAX_ARTICLES_PER_FEED, RSS_FEEDS

logger = logging.getLogger(__name__)

# RSS 2.0 and Atom namespaces
RSS_NS = {}
ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}


def _clean_html(text: str) -> str:
    """Remove HTML tags from summary and return plain text."""
    if not text or not text.strip():
        return ""
    soup = BeautifulSoup(text, "lxml")
    return soup.get_text(separator=" ", strip=True)


def _normalize_title(title: str) -> str:
    """Normalize title for deduplication (strip and lower)."""
    return (title or "").strip().lower()


def _fetch_feed(feed_url: str) -> ET.Element | None:
    """Fetch and parse RSS/Atom feed; return root element or None on failure."""
    feed_url = (feed_url or "").strip()
    if not feed_url or not (feed_url.startswith("http://") or feed_url.startswith("https://")):
        logger.warning("Skipping invalid feed URL (must start with http:// or https://)")
        return None
    try:
        req = Request(feed_url, headers={"User-Agent": "NicheReportBot/1.0"})
        with urlopen(req, timeout=15) as resp:
            tree = ET.parse(resp)
            return tree.getroot()
    except Exception as e:
        logger.warning("Error fetching feed %s: %s", feed_url, e)
        return None


def _text(el: ET.Element | None, default: str = "") -> str:
    """Get element text or default."""
    if el is None:
        return default
    return (el.text or "").strip() or default


def _parse_rss_items(root: ET.Element) -> list[dict[str, Any]]:
    """Parse RSS 2.0 <channel><item>...</item></channel>."""
    items = []
    channel = root.find("channel", RSS_NS)
    if channel is None:
        return items
    for item in list(channel.findall("item", RSS_NS))[:MAX_ARTICLES_PER_FEED]:
        title = _text(item.find("title", RSS_NS))
        if not title:
            continue
        link = _text(item.find("link", RSS_NS))
        desc = _text(item.find("description", RSS_NS))
        pub = _text(item.find("pubDate", RSS_NS))
        items.append({"title": title, "summary": desc, "link": link, "published": pub})
    return items


def _parse_atom_entries(root: ET.Element) -> list[dict[str, Any]]:
    """Parse Atom <feed><entry>...</entry></feed>."""
    entries = []
    for entry in list(root.findall("atom:entry", ATOM_NS))[:MAX_ARTICLES_PER_FEED]:
        title_el = entry.find("atom:title", ATOM_NS)
        title = _text(title_el)
        if not title:
            continue
        link_el = entry.find("atom:link", ATOM_NS)
        link = ""
        if link_el is not None and link_el.get("href"):
            link = (link_el.get("href") or "").strip()
        summary_el = entry.find("atom:summary", ATOM_NS) or entry.find("atom:content", ATOM_NS)
        summary = _text(summary_el)
        updated = _text(entry.find("atom:updated", ATOM_NS)) or _text(entry.find("atom:published", ATOM_NS))
        entries.append({"title": title, "summary": summary, "link": link, "published": updated})
    return entries


def _parse_feed(root: ET.Element) -> list[dict[str, Any]]:
    """Dispatch to RSS or Atom parser."""
    if root.tag == "rss" or root.find("channel", RSS_NS) is not None:
        return _parse_rss_items(root)
    if "http://www.w3.org/2005/Atom" in (root.tag or "") or root.find("atom:entry", ATOM_NS) is not None:
        return _parse_atom_entries(root)
    return []


def scrape_articles() -> list[dict[str, Any]]:
    """
    Scrape all configured RSS feeds and return a deduplicated list of articles.

    For each feed, fetches up to MAX_ARTICLES_PER_FEED entries. Extracts title,
    summary (HTML cleaned), link, and published date. Deduplicates by title.
    If a feed fails, logs a warning and continues with the rest.

    Returns:
        List of dicts with keys: title, summary, link, published
    """
    seen_titles: set[str] = set()
    articles: list[dict[str, Any]] = []

    for feed_url in RSS_FEEDS:
        root = _fetch_feed(feed_url)
        if root is None:
            continue
        try:
            raw_items = _parse_feed(root)
        except Exception as e:
            logger.warning("Error parsing feed %s: %s", feed_url, e)
            continue
        for item in raw_items:
            title = (item.get("title") or "").strip()
            if not title:
                continue
            key = _normalize_title(title)
            if key in seen_titles:
                continue
            seen_titles.add(key)
            summary = _clean_html(item.get("summary") or "")
            link = (item.get("link") or "").strip()
            published = str(item.get("published", ""))
            articles.append({
                "title": title,
                "summary": summary,
                "link": link,
                "published": published,
            })

    return articles
