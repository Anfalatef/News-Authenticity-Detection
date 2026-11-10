"""
Ingestion configuration.

This configuration keeps the scraping scope controlled and predictable.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class IngestSettings:
    per_source_limit: int = 100
    request_timeout_sec: int = 25
    politeness_delay_sec: float = 0.6

    # Accept short news items (breaking)
    min_article_chars: int = 120

    # Only chunk if the text is reasonably long
    min_chunk_chars: int = 250



SETTINGS = IngestSettings()


# RSS feeds (stable, scalable)
RSS_FEEDS = [
    # AlMamlaka TV
    {
        "name": "AlMamlakaTV",
        "domain": "almamlakatv.com",
        "country": "Jordan",
        "rss": "https://www.almamlakatv.com/rss.xml",
    },

    # BBC (expanded)
    {"name": "BBC", "domain": "bbc.com", "country": "Global", "rss": "https://feeds.bbci.co.uk/news/world/rss.xml"},
    {"name": "BBC", "domain": "bbc.com", "country": "Global", "rss": "https://feeds.bbci.co.uk/news/world/middle_east/rss.xml"},
    {"name": "BBC", "domain": "bbc.com", "country": "Global", "rss": "https://feeds.bbci.co.uk/news/business/rss.xml"},
    {"name": "BBC", "domain": "bbc.com", "country": "Global", "rss": "https://feeds.bbci.co.uk/news/technology/rss.xml"},

    # BBC extra sections
    {"name": "BBC", "domain": "bbc.com", "country": "Global", "rss": "https://feeds.bbci.co.uk/news/science_and_environment/rss.xml"},
    {"name": "BBC", "domain": "bbc.com", "country": "Global", "rss": "https://feeds.bbci.co.uk/news/health/rss.xml"},
    {"name": "BBC", "domain": "bbc.com", "country": "Global", "rss": "https://feeds.bbci.co.uk/news/uk/rss.xml"},
    {"name": "BBC", "domain": "bbc.com", "country": "Global", "rss": "https://feeds.bbci.co.uk/news/world/asia/rss.xml"},
    {"name": "BBC", "domain": "bbc.com", "country": "Global", "rss": "https://feeds.bbci.co.uk/news/world/africa/rss.xml"},
    {"name": "BBC", "domain": "bbc.com", "country": "Global", "rss": "https://feeds.bbci.co.uk/news/world/europe/rss.xml"},

    # RT
    {"name": "RT", "domain": "rt.com", "country": "Global", "rss": "https://www.rt.com/rss/"},

    # Jordanian sources (RSS pages)
    {"name": "AlGhad", "domain": "alghad.com", "country": "Jordan", "rss": "https://alghad.com/rss"},  # :contentReference[oaicite:1]{index=1}
    {"name": "Ammon", "domain": "ammonnews.net", "country": "Jordan", "rss": "https://www.ammonnews.net/rss.php"},  # :contentReference[oaicite:2]{index=2}
    {"name": "SarayaNews", "domain": "sarayanews.com", "country": "Jordan", "rss": "https://www.sarayanews.com/rss.php"},  # :contentReference[oaicite:3]{index=3}

    # Global sources (RSS)
    {"name": "AlJazeera", "domain": "aljazeera.com", "country": "Global", "rss": "https://www.aljazeera.com/xml/rss/all.xml"},  # :contentReference[oaicite:4]{index=4}
    {"name": "DW", "domain": "dw.com", "country": "Global", "rss": "https://rss.dw.com/rdf/rss-en-all"},  # :contentReference[oaicite:5]{index=5}
]


# Roya ingestion via pagination across multiple sections
ROYA_SECTIONS = [
    {"id": 1, "name": "local"},
    {"id": 4, "name": "palestine"},
    {"id": 8, "name": "economy"},
    {"id": 9, "name": "sports"},
    {"id": 12, "name": "tech"},
    {"id": 14, "name": "lifestyle"},
    {"id": 15, "name": "health"},
    {"id": 17, "name": "education"},
    {"id": 19, "name": "cars"},
]

ROYA_PAGED = {
    "name": "RoyaNews",
    "domain": "royanews.tv",
    "country": "Jordan",
    "target_items_per_section": 200,  # start here
    "max_fail_streak": 80,            # stop after too many bad IDs
}

