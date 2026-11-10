from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class UrlEvent:
    url: str
    title: str = ""
    reason: str = ""  # inserted / duplicate / short_text / cross_domain / error
    article_id: Optional[int] = None


@dataclass
class SourceReport:
    domain: str
    feed: str
    fetched_items: int = 0
    inserted: List[UrlEvent] = field(default_factory=list)
    skipped: List[UrlEvent] = field(default_factory=list)
    errors: List[UrlEvent] = field(default_factory=list)


@dataclass
class RunReport:
    started_at: str
    finished_at: str = ""
    settings: Dict[str, Any] = field(default_factory=dict)
    sources: Dict[str, SourceReport] = field(default_factory=dict)

    def _key(self, domain: str, feed: str) -> str:
        return f"{domain}::{feed}"

    def ensure_source(self, domain: str, feed: str) -> SourceReport:
        key = self._key(domain, feed)
        if key not in self.sources:
            self.sources[key] = SourceReport(domain=domain, feed=feed)
        return self.sources[key]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "settings": self.settings,
            "sources": {
                k: {
                    "domain": v.domain,
                    "feed": v.feed,
                    "fetched_items": v.fetched_items,
                    "inserted_count": len(v.inserted),
                    "skipped_count": len(v.skipped),
                    "errors_count": len(v.errors),
                    "inserted": [e.__dict__ for e in v.inserted],
                    "skipped": [e.__dict__ for e in v.skipped],
                    "errors": [e.__dict__ for e in v.errors],
                }
                for k, v in self.sources.items()
            },
        }


def save_run_report(report: RunReport, out_dir: str = "runs") -> str:
    """
    Writes a new JSON file per run (never overwrites an existing one).
    """
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = Path(out_dir) / f"ingest_report_{ts}.json"
    path.write_text(json.dumps(report.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    return str(path)
