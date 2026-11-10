from __future__ import annotations

import hashlib


def normalize_text(s: str) -> str:
    s = (s or "").strip()
    s = " ".join(s.split())
    return s


def analyze_cache_key(*, text: str, model: str, top_k: int, prompt_version: str, pipeline_version: str) -> str:
    """
    Versioned cache key.
    Changing prompt_version or pipeline_version automatically isolates cached results.
    """
    norm = normalize_text(text)
    h = hashlib.sha256(norm.encode("utf-8")).hexdigest()
    return f"analyze:{pipeline_version}:{prompt_version}:{h}:{model}:k{int(top_k)}"
