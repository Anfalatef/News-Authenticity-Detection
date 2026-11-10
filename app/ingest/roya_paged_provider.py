from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable
from urllib.parse import urljoin, urlparse, urlunparse

from bs4 import BeautifulSoup

from app.ingest.fetcher import http_get_text
from app.ingest.providers import FeedItem


def _normalize(url: str) -> str:
    """
    Normalize Roya URLs:
    - strip fragment
    - drop query params (tracking)
    """
    p = urlparse(url.split("#", 1)[0])
    return urlunparse((p.scheme, p.netloc, p.path, "", "", ""))


def _is_roya_article(url: str) -> bool:
    p = urlparse(url)
    host = p.netloc.replace("www.", "")
    if host != "royanews.tv":
        return False
    return (p.path or "").lower().startswith("/news/")


@dataclass(frozen=True)
class RoyaPagedConfig:
    start_url: str
    max_pages: int = 60
    max_empty_pages: int = 3  # allow a few empty pages before stopping


class RoyaPagedProvider:
    """
    Paged provider for Roya listing pages.

    It collects /news/<id> URLs across multiple pages until 'limit' is reached,
    max_pages reached, or too many consecutive empty pages occur.

    We try multiple pagination patterns because Roya may differ by section.
    """

    def __init__(self, cfg: RoyaPagedConfig, timeout_sec: int) -> None:
        self.cfg = cfg
        self.timeout_sec = timeout_sec

    def _page_urls(self, page: int) -> list[str]:
        base = self.cfg.start_url.rstrip("/")
        return [
            f"{base}?page={page}",
            f"{base}/page/{page}",
            f"{base}?p={page}",
        ]

    def fetch(self, limit: int) -> list[FeedItem]:
        out: list[FeedItem] = []
        seen: set[str] = set()

        consecutive_empty = 0

        for page in range(1, self.cfg.max_pages + 1):
            page_candidates = self._page_urls(page)

            html = None
            used_url = None

            # Try multiple patterns; use the first one that returns a page with at least 1 article link
            for page_url in page_candidates:
                try:
                    candidate_html = http_get_text(page_url, timeout_sec=self.timeout_sec)
                except Exception:
                    continue

                soup = BeautifulSoup(candidate_html, "html.parser")
                found = self._count_roya_news_links(soup, page_url)
                if found > 0:
                    html = candidate_html
                    used_url = page_url
                    break

            if not html or not used_url:
                consecutive_empty += 1
                if consecutive_empty >= self.cfg.max_empty_pages:
                    break
                continue

            soup = BeautifulSoup(html, "html.parser")

            found_this_page = 0
            for a in soup.find_all("a", href=True):
                href = a["href"].strip()
                if not href:
                    continue

                abs_url = urljoin(used_url, href)
                if not _is_roya_article(abs_url):
                    continue

                norm = _normalize(abs_url)
                if norm in seen:
                    continue

                seen.add(norm)

                title = a.get_text(" ", strip=True)[:200]
                out.append(FeedItem(url=norm, title=title, published_at=""))
                found_this_page += 1

                if len(out) >= limit:
                    return out

            if found_this_page == 0:
                consecutive_empty += 1
                if consecutive_empty >= self.cfg.max_empty_pages:
                    break
            else:
                consecutive_empty = 0

        return out

    def _count_roya_news_links(self, soup: BeautifulSoup, base_url: str) -> int:
        count = 0
        for a in soup.find_all("a", href=True):
            abs_url = urljoin(base_url, a["href"].strip())
            if _is_roya_article(abs_url):
                count += 1
                if count >= 1:
                    return count
        return count
