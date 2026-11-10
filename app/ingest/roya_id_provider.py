from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from app.ingest.fetcher import http_get_text


_ID_RE = re.compile(r"/news/(\d+)")


@dataclass(frozen=True)
class RoyaIdBackfillConfig:
    section_url: str
    max_fail_streak: int = 50  # stop if too many consecutive misses


class RoyaIdBackfillProvider:
    """
    Fetch many Roya articles without pagination by:
    1) Discovering the latest /news/<id> from a section page
    2) Backfilling IDs downward until we collect the requested count
    """

    def __init__(self, cfg: RoyaIdBackfillConfig, timeout_sec: int) -> None:
        self.cfg = cfg
        self.timeout_sec = timeout_sec

    def discover_latest_id(self) -> int:
        html = http_get_text(self.cfg.section_url, timeout_sec=self.timeout_sec)
        soup = BeautifulSoup(html, "html.parser")

        max_id = 0
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            m = _ID_RE.search(href)
            if not m:
                continue
            max_id = max(max_id, int(m.group(1)))

        if max_id <= 0:
            raise RuntimeError(f"Could not discover latest Roya news id from {self.cfg.section_url}")

        return max_id

    def iter_urls(self, count: int) -> Iterable[str]:
        latest_id = self.discover_latest_id()
        collected = 0
        fail_streak = 0
        current = latest_id

        while collected < count and fail_streak < self.cfg.max_fail_streak:
            url = f"https://royanews.tv/news/{current}"
            current -= 1

            collected += 1
            yield url
