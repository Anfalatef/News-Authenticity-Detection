from __future__ import annotations

from app.ingest.roya_id_provider import RoyaIdBackfillProvider, RoyaIdBackfillConfig
from app.ingest.fetcher import http_get_text


def main() -> None:
    cfg = RoyaIdBackfillConfig(section_url="https://royanews.tv/section/1")
    provider = RoyaIdBackfillProvider(cfg=cfg, timeout_sec=25)

    latest_id = provider.discover_latest_id()
    print(f"Latest ID: {latest_id}")

    urls = list(provider.iter_urls(count=30))
    print(f"Generated URLs: {len(urls)}")
    print("\n".join(urls[:10]))

    # Optional: quickly validate first URL returns HTML
    html = http_get_text(urls[0], timeout_sec=25)
    print(f"First URL HTML length: {len(html)}")


if __name__ == "__main__":
    main()
