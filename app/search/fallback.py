from __future__ import annotations

import logging
from dataclasses import dataclass

from app.search.cse_client import GoogleCSEClient, SearchResult

log = logging.getLogger("search")


@dataclass(frozen=True)
class EvidenceItem:
    source: str
    title: str
    url: str
    text: str


class SearchFallback:
    """
    Turns web search results into evidence items.
    We do NOT scrape full pages here to keep MVP stable and fast.
    We use snippet as evidence and provide URL citation.
    """

    def __init__(self, client: GoogleCSEClient) -> None:
        self.client = client

    def build_evidence(self, query: str, num: int = 5) -> list[EvidenceItem]:
        results: list[SearchResult] = self.client.search(query=query, num=num)
        evidence: list[EvidenceItem] = []

        for r in results:
            if not r.url:
                continue
            evidence.append(
                EvidenceItem(
                    source=r.display_link or "web",
                    title=r.title,
                    url=r.url,
                    text=r.snippet,
                )
            )

        return evidence
