"""
Lightweight language detection.

Stores:
- 'ar' for Arabic
- 'en' for English
- fallback to detected code, or None if uncertain
"""

from __future__ import annotations

from langdetect import detect, LangDetectException


def detect_language(text: str) -> str | None:
    try:
        if len(text) < 80:
            return None
        code = detect(text)
        if code.startswith("ar"):
            return "ar"
        if code.startswith("en"):
            return "en"
        return code
    except LangDetectException:
        return None
