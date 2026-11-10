from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import requests

log = logging.getLogger("search")


@dataclass(frozen=True)
class CSEItem:
    title: str
    link: str
    snippet: str
    display_link: str


class GoogleCSEClient:
    """
    Google Custom Search JSON API client.
    """

    def __init__(self, api_key: str, cx: str, timeout_sec: int = 20) -> None:
        self.api_key = api_key.strip()
        self.cx = cx.strip()
        self.timeout_sec = timeout_sec

    def is_configured(self) -> bool:
        return bool(self.api_key) and bool(self.cx)

    def search(self, query: str, num: int = 5) -> list[CSEItem]:
        if not self.is_configured():
            return []

        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": self.api_key,
            "cx": self.cx,
            "q": query,
            "num": max(1, min(int(num), 10)),
        }

        r = requests.get(url, params=params, timeout=self.timeout_sec)
        r.raise_for_status()

        data: dict[str, Any] = r.json()
        items = data.get("items") or []

        out: list[CSEItem] = []
        for it in items:
            out.append(
                CSEItem(
                    title=(it.get("title") or "").strip(),
                    link=(it.get("link") or "").strip(),
                    snippet=(it.get("snippet") or "").strip(),
                    display_link=(it.get("displayLink") or "").strip(),
                )
            )
        return out
