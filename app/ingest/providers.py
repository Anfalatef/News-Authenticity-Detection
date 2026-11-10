"""
Feed providers:
- RSSProvider: reads RSS and yields article URLs
- HTMLListProvider: extracts article URLs from listing pages (fallback)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional
from urllib.parse import urlparse, urljoin

import feedparser
from bs4 import BeautifulSoup

from app.ingest.fetcher import http_get_text


@dataclass(frozen=True)
class FeedItem:
    url: str
    title: str = ""
    published_at: str = ""


class RSSProvider:
    def __init__(self, rss_url: str) -> None:
        self.rss_url = rss_url

    def fetch(self, limit: int) -> list[FeedItem]:
        feed = feedparser.parse(self.rss_url)
        items: list[FeedItem] = []

        for entry in getattr(feed, "entries", [])[:limit]:
            url = getattr(entry, "link", None)
            if not url:
                continue
            title = (getattr(entry, "title", "") or "").strip()
            published = (getattr(entry, "published", "") or getattr(entry, "updated", "") or "").strip()
            items.append(FeedItem(url=url.strip(), title=title, published_at=published))
        return items


class HTMLListProvider:
    """
    Extracts article URLs from an HTML listing page.

    Strategy:
    - Parse all <a href="..."> links
    - Keep links that appear to be article pages (same domain, not assets)
    - De-duplicate
    """

    def __init__(self, page_url: str, domain: str) -> None:
        self.page_url = page_url
        self.domain = domain

    def fetch(self, limit: int) -> list[FeedItem]:
        html = http_get_text(self.page_url)
        soup = BeautifulSoup(html, "html.parser")

        out: list[FeedItem] = []
        seen: set[str] = set()

        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if not href:
                continue

            abs_url = urljoin(self.page_url, href)
            if not self._is_candidate(abs_url):
                continue

            norm = self._normalize(abs_url)
            if norm in seen:
                continue
            seen.add(norm)

            title = a.get_text(" ", strip=True)[:200]
            out.append(FeedItem(url=norm, title=title, published_at=""))
            if len(out) >= limit:
                break

        return out

    def _is_candidate(self, url: str) -> bool:
        p = urlparse(url)
        if not p.netloc:
            return False
        host = p.netloc.replace("www.", "")
        if host != self.domain:
            return False

        # Filter obvious non-article links
        bad_ext = (".jpg", ".jpeg", ".png", ".gif", ".svg", ".css", ".js", ".pdf", ".mp4")
        if p.path.lower().endswith(bad_ext):
            return False

        # Avoid some common non-content paths
        bad_parts = ("/tag/", "/tags/", "/search", "/login", "/privacy", "/terms")
        if any(bp in p.path.lower() for bp in bad_parts):
            return False

        # Heuristic: article pages usually have some path depth
        return len(p.path.strip("/").split("/")) >= 1

    def _normalize(self, url: str) -> str:
        # Keep it simple for now (strip fragment)
        return url.split("#", 1)[0]
