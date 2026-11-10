from __future__ import annotations

import json
import re
from typing import Any, Dict, Optional


_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)


def _extract_json_object(text: str) -> Optional[Dict[str, Any]]:
    """
    Extract a JSON object from a model response.
    Handles cases where JSON is wrapped in ```json fences or returned as raw JSON.
    Returns None if no valid JSON object can be parsed.
    """
    if not text:
        return None

    s = text.strip()

    # 1) Try fenced JSON block
    m = _JSON_FENCE_RE.search(s)
    if m:
        candidate = m.group(1).strip()
        try:
            return json.loads(candidate)
        except Exception:
            pass

    # 2) Try raw JSON (sometimes model returns pure JSON)
    try:
        return json.loads(s)
    except Exception:
        return None


def parse_veracity(text: Any) -> Dict[str, Any]:
    """
    Parse veracity response into a normalized dict.
    This function ALWAYS returns a dict (never a tuple).
    """
    raw = ""
    if isinstance(text, dict):
        raw = str(text.get("text") or "")
    else:
        raw = str(text or "")

    obj = _extract_json_object(raw) or {}

    label = obj.get("label")
    confidence = obj.get("confidence")
    reasons = obj.get("reasons")
    evidence_urls = obj.get("evidence_urls")

    # Normalize
    if label is not None:
        label = str(label).strip()

    if confidence is not None:
        try:
            confidence = int(confidence)
        except Exception:
            confidence = None

    if not isinstance(reasons, list):
        reasons = []

    if not isinstance(evidence_urls, list):
        evidence_urls = []

    return {
        "label": label,
        "confidence": confidence,
        "reasons": reasons,
        "evidence_urls": evidence_urls,
        "_raw": raw,
        "_parsed_ok": bool(obj),
    }


def parse_bias(text: Any) -> Dict[str, Any]:
    """
    Parse bias response into a normalized dict.
    This function ALWAYS returns a dict (never a tuple).
    """
    raw = ""
    if isinstance(text, dict):
        raw = str(text.get("text") or "")
    else:
        raw = str(text or "")

    obj = _extract_json_object(raw) or {}

    has_bias = obj.get("has_bias")
    types_ = obj.get("types")
    severity = obj.get("severity")
    quotes = obj.get("quotes")
    neutral_rewrite = obj.get("neutral_rewrite")

    # Normalize
    if has_bias is not None:
        if isinstance(has_bias, bool):
            pass
        elif isinstance(has_bias, str):
            has_bias = has_bias.strip().lower() in {"true", "1", "yes"}
        else:
            has_bias = bool(has_bias)

    if not isinstance(types_, list):
        types_ = []

    if severity is not None:
        try:
            severity = int(severity)
        except Exception:
            severity = None

    if not isinstance(quotes, list):
        quotes = []

    if neutral_rewrite is not None:
        neutral_rewrite = str(neutral_rewrite)

    return {
        "has_bias": has_bias,
        "types": types_,
        "severity": severity,
        "quotes": quotes,
        "neutral_rewrite": neutral_rewrite,
        "_raw": raw,
        "_parsed_ok": bool(obj),
    }
