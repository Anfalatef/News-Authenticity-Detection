from __future__ import annotations

import logging
import random
import time
from typing import Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

log = logging.getLogger("ingest")

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/121.0.0.0 Safari/537.36"
)

_DEFAULT_HEADERS = {
    "User-Agent": UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ar,en-US;q=0.9,en;q=0.8",
    "Connection": "keep-alive",
}


def _build_session() -> requests.Session:
    """
    Create a requests Session with safe retries for transient network/server errors.
    """
    s = requests.Session()

    retry = Retry(
        total=4,
        connect=4,
        read=4,
        status=4,
        backoff_factor=0.8,  # exponential backoff: 0.8, 1.6, 3.2, ...
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET",),
        raise_on_status=False,
        respect_retry_after_header=True,
    )

    adapter = HTTPAdapter(max_retries=retry, pool_connections=20, pool_maxsize=20)
    s.mount("http://", adapter)
    s.mount("https://", adapter)

    return s


_SESSION: Optional[requests.Session] = None


def http_get_text(url: str, timeout_sec: int = 25) -> str:
    """
    Fetch a URL and return response text.

    This function is resilient to transient failures (connection resets, 5xx, 429).
    It uses a single shared Session (connection pooling) + retries + backoff.
    """
    global _SESSION
    if _SESSION is None:
        _SESSION = _build_session()

    # Small jitter helps reduce burst patterns when scraping many URLs
    time.sleep(random.uniform(0.05, 0.25))

    try:
        r = _SESSION.get(url, headers=_DEFAULT_HEADERS, timeout=timeout_sec)
        # Handle "soft blocks" politely
        if r.status_code == 429:
            log.warning("HTTP 429 rate-limited url=%s", url)
        r.raise_for_status()
        return r.text

    except requests.exceptions.RequestException as e:
        # Let caller decide how to report/skip; we keep message concise here
        raise RuntimeError(f"fetch_failed: {type(e).__name__}: {e}") from e
