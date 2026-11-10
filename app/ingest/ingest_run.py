"""
End-to-end ingestion:
- Fetch feed items (RSS)
- Fetch article page HTML
- Extract title + text
- Clean text
- Detect language
- Save Article + Chunks into SQLite via SQLAlchemy
- Write a per-run JSON report (inserted / skipped / errors)

Run:
    python -m app.ingest.ingest_run
"""

from __future__ import annotations

import logging
import time
from datetime import datetime
from urllib.parse import urlparse

from sqlalchemy.exc import IntegrityError

from app.db.connection import SessionLocal
from app.db.models import Article, Chunk, Source
from app.ingest.config import SETTINGS, RSS_FEEDS, ROYA_PAGED, ROYA_SECTIONS
from app.ingest.fetcher import http_get_text
from app.ingest.extractor import extract_title_and_text
from app.ingest.cleaner import clean_text
from app.ingest.lang import detect_language
from app.ingest.chunker import chunk_by_paragraphs
from app.ingest.providers import RSSProvider
from app.ingest.roya_id_provider import RoyaIdBackfillProvider, RoyaIdBackfillConfig
from app.ingest.logging_config import configure_logging
from app.ingest.run_reporter import RunReport, SourceReport, UrlEvent, save_run_report

log = logging.getLogger("ingest")


def normalize_domain(url: str) -> str:
    return urlparse(url).netloc.replace("www.", "").strip().lower()


def normalize_known_urls(url: str) -> str:
    # Fix double slash issue for AlMamlaka links if present.
    return url.replace("://www.almamlakatv.com//", "://www.almamlakatv.com/")


def get_or_create_source(session, name: str, domain: str, country: str | None) -> Source:
    src = session.query(Source).filter(Source.domain == domain).first()
    if src:
        return src

    src = Source(name=name, domain=domain, country=country)
    session.add(src)
    session.commit()
    session.refresh(src)
    return src


def insert_article_with_chunks(
    session,
    source: Source,
    url: str,
    title: str,
    published_at: str,
    language: str | None,
    text: str,
) -> tuple[str, int | None]:
    """
    Insert an article and its chunks.

    Returns:
        ("inserted", article_id) on success
        ("duplicate", None) if URL already exists
    """
    article = Article(
        source_id=source.source_id,
        url=url,
        title=title or None,
        published_at=published_at or None,
        language=language,
        clean_text=text,
    )

    session.add(article)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        return "duplicate", None

    session.refresh(article)

    # For short articles (e.g., breaking), store a single chunk so retrieval still works.
    if len(text) < SETTINGS.min_chunk_chars:
        session.add(Chunk(article_id=article.article_id, chunk_index=0, chunk_text=text))
        session.commit()
        return "inserted", article.article_id

    # For longer articles, chunk by paragraphs.
    chunks = chunk_by_paragraphs(text)

    # Safety fallback: if chunker returns nothing, store one chunk.
    if not chunks:
        session.add(Chunk(article_id=article.article_id, chunk_index=0, chunk_text=text))
        session.commit()
        return "inserted", article.article_id

    for idx, chunk_text in enumerate(chunks):
        session.add(Chunk(article_id=article.article_id, chunk_index=idx, chunk_text=chunk_text))

    session.commit()
    return "inserted", article.article_id


def process_item(
    session,
    source: Source,
    url: str,
    fallback_title: str,
    published_at: str,
    sr: SourceReport,
) -> None:
    """
    Process a single URL and update the SourceReport with insert/skip/error events.
    """
    url = normalize_known_urls(url)

    domain = normalize_domain(url)
    if domain != source.domain:
        sr.skipped.append(UrlEvent(url=url, title=fallback_title, reason="cross_domain"))
        log.info("Skipping cross-domain URL: %s", url)
        return

    try:
        html = http_get_text(url, timeout_sec=SETTINGS.request_timeout_sec)
        page_title, raw_text = extract_title_and_text(html)
        text = clean_text(raw_text)

        # Skip only truly empty / useless pages.
        if len(text) < SETTINGS.min_article_chars:
            sr.skipped.append(UrlEvent(url=url, title=fallback_title, reason=f"too_short_{len(text)}"))
            log.warning("Skipping too-short extraction (%d chars): %s", len(text), url)
            return

        title = (fallback_title or page_title or "").strip()
        lang = detect_language(text)

        status, article_id = insert_article_with_chunks(
            session=session,
            source=source,
            url=url,
            title=title,
            published_at=published_at,
            language=lang,
            text=text,
        )

        if status == "duplicate":
            sr.skipped.append(UrlEvent(url=url, title=title, reason="duplicate"))
            log.info("Skipping duplicate URL: %s", url)
            return

        sr.inserted.append(UrlEvent(url=url, title=title, reason="inserted", article_id=article_id))
        log.info("Inserted article_id=%s source=%s lang=%s url=%s", article_id, source.domain, lang, url)

    except Exception as e:
        sr.errors.append(UrlEvent(url=url, title=fallback_title, reason=str(e)))
        log.exception("Failed processing URL: %s error=%s", url, str(e))

    time.sleep(SETTINGS.politeness_delay_sec)


def run() -> None:
    configure_logging()
    log.info("Starting ingestion. per_source_limit=%d", SETTINGS.per_source_limit)

    report = RunReport(started_at=datetime.now().isoformat(timespec="seconds"))
    report.settings = {
        "per_source_limit": SETTINGS.per_source_limit,
        "request_timeout_sec": SETTINGS.request_timeout_sec,
        "politeness_delay_sec": SETTINGS.politeness_delay_sec,
        "min_article_chars": SETTINGS.min_article_chars,
        "min_chunk_chars": SETTINGS.min_chunk_chars,
        "roya_target_items_per_section": int(ROYA_PAGED["target_items_per_section"]),
        "roya_max_fail_streak": int(ROYA_PAGED.get("max_fail_streak", 80)),
    }

    session = SessionLocal()
    try:
        # RSS sources
        for cfg in RSS_FEEDS:
            name = cfg["name"]
            domain = cfg["domain"]
            country = cfg.get("country")
            rss_url = cfg["rss"]

            source = get_or_create_source(session, name=name, domain=domain, country=country)

            log.info("Fetching RSS: source=%s rss=%s", domain, rss_url)
            provider = RSSProvider(rss_url=rss_url)
            items = provider.fetch(limit=SETTINGS.per_source_limit)
            log.info("RSS items fetched: source=%s count=%d", domain, len(items))

            sr = report.ensure_source(domain=domain, feed=rss_url)
            sr.fetched_items = len(items)

            for item in items:
                process_item(
                    session=session,
                    source=source,
                    url=item.url,
                    fallback_title=item.title,
                    published_at=item.published_at,
                    sr=sr,
                )

        # Roya backfill across sections (ID-based, no pagination)
        roya_source = get_or_create_source(
            session,
            name=ROYA_PAGED["name"],
            domain=ROYA_PAGED["domain"],
            country=ROYA_PAGED.get("country"),
        )

        target_per_section = int(ROYA_PAGED["target_items_per_section"])
        max_fail_streak = int(ROYA_PAGED.get("max_fail_streak", 80))

        for sec in ROYA_SECTIONS:
            section_id = sec["id"]
            section_name = sec["name"]

            section_url = f"https://royanews.tv/section/{section_id}"
            feed_label = f"{section_url} (id_backfill:{section_name})"

            log.info(
                "Fetching Roya by ID backfill: section=%s section_url=%s target=%d",
                section_name,
                section_url,
                target_per_section,
            )

            sr_roya = report.ensure_source(domain=ROYA_PAGED["domain"], feed=feed_label)

            provider = RoyaIdBackfillProvider(
                cfg=RoyaIdBackfillConfig(section_url=section_url, max_fail_streak=max_fail_streak),
                timeout_sec=SETTINGS.request_timeout_sec,
            )

            urls = list(provider.iter_urls(count=target_per_section))
            sr_roya.fetched_items = len(urls)

            for url in urls:
                process_item(
                    session=session,
                    source=roya_source,
                    url=url,
                    fallback_title="",
                    published_at="",
                    sr=sr_roya,
                )

            log.info("Roya done: section=%s generated=%d", section_name, len(urls))

        log.info("Ingestion finished.")

    finally:
        session.close()

    report.finished_at = datetime.now().isoformat(timespec="seconds")
    report_path = save_run_report(report, out_dir="runs")
    log.info("Run report saved: %s", report_path)


if __name__ == "__main__":
    run()
