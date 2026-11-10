"""
Seed known sources into the database.

Run:
    python -m scripts.seed_sources
"""

from __future__ import annotations

import logging

from sqlalchemy.exc import IntegrityError

from app.db.connection import SessionLocal
from app.db.models import Source
from app.ingest.logging_config import configure_logging

log = logging.getLogger("seed_sources")


SOURCES = [
    {"name": "AlMamlakaTV", "domain": "almamlakatv.com", "country": "Jordan", "trust_level": 0},
    {"name": "RoyaNews", "domain": "royanews.tv", "country": "Jordan", "trust_level": 0},
    {"name": "BBC", "domain": "bbc.com", "country": "Global", "trust_level": 0},
    {"name": "RT", "domain": "rt.com", "country": "Global", "trust_level": 0},
]


def run() -> None:
    configure_logging()
    session = SessionLocal()
    try:
        for s in SOURCES:
            src = Source(
                name=s["name"],
                domain=s["domain"],
                country=s.get("country"),
                trust_level=s.get("trust_level", 0),
            )
            session.add(src)
            try:
                session.commit()
                log.info("Inserted source: %s", s["domain"])
            except IntegrityError:
                session.rollback()
                log.info("Source already exists: %s", s["domain"])
    finally:
        session.close()


if __name__ == "__main__":
    run()
