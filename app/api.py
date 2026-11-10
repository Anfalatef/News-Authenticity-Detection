from __future__ import annotations

import json
import logging
import re
import time
from typing import Any
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

from app.cache.keys import analyze_cache_key
from app.cache.redis_cache import RedisCache
from app.core.settings import SETTINGS
from app.eval.parse import parse_bias, parse_veracity
from app.eval.store import EvalStore
from app.llm.client import LLMClient
from app.llm.prompts import (
    PIPELINE_VERSION,
    PROMPT_VERSION,
    PROMPT_VERSION_AR,
    build_bias_prompt,
    build_veracity_prompt,
)
from app.rag.retriever import RagRetriever
from app.ingest.lang import detect_language
from app.search.cse_client import CSEItem, GoogleCSEClient


logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
log = logging.getLogger("api")

app = FastAPI(title="News AI Backend", version="0.1.0")

_retriever: RagRetriever | None = None
_llm: LLMClient | None = None
_cse: GoogleCSEClient | None = None
_cache: RedisCache | None = None
_store: EvalStore | None = None


class AnalyzeRequest(BaseModel):
    text: str
    language: str | None = None


@app.get("/")
def root() -> dict:
    return {"status": "ok", "service": "news-ai-backend"}


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


def get_retriever() -> RagRetriever:
    global _retriever
    if _retriever is None:
        _retriever = RagRetriever(
            faiss_index_path=SETTINGS.faiss_index_path,
            sqlite_path=SETTINGS.sqlite_path,
        )
        log.info(
            "RAG retriever initialized faiss=%s sqlite=%s",
            SETTINGS.faiss_index_path,
            SETTINGS.sqlite_path,
        )
    return _retriever


def get_llm() -> LLMClient:
    global _llm
    if _llm is None:
        if not SETTINGS.openai_api_key:
            raise HTTPException(status_code=500, detail="OPENAI_API_KEY is missing in .env")
        _llm = LLMClient(api_key=SETTINGS.openai_api_key, model=SETTINGS.openai_model)
        log.info("LLM client initialized model=%s", SETTINGS.openai_model)
    return _llm


def get_cse() -> GoogleCSEClient:
    global _cse
    if _cse is None:
        _cse = GoogleCSEClient(
            api_key=getattr(SETTINGS, "google_cse_api_key", ""),
            cx=getattr(SETTINGS, "google_cse_cx", ""),
            timeout_sec=20,
        )
        log.info("Google CSE client initialized configured=%s", _cse.is_configured())
    return _cse


def get_cache() -> RedisCache | None:
    """
    Redis cache is optional. If REDIS_URL is empty, caching is disabled.
    """
    global _cache
    if _cache is None:
        redis_url = getattr(SETTINGS, "redis_url", "").strip()
        ttl_sec = int(getattr(SETTINGS, "redis_ttl_sec", getattr(SETTINGS, "cache_ttl_sec", 172800)))

        log.info("CACHE init redis_url=%s ttl_sec=%s", redis_url or "(empty)", ttl_sec)

        if not redis_url:
            log.warning("CACHE disabled: REDIS_URL is empty")
            return None

        _cache = RedisCache(url=redis_url, ttl_sec=ttl_sec)
        log.info("Redis cache initialized configured=%s", _cache.is_configured())

    return _cache


def get_store() -> EvalStore:
    global _store
    if _store is None:
        _store = EvalStore(sqlite_path=SETTINGS.sqlite_path)
        log.info("Eval store initialized sqlite=%s", SETTINGS.sqlite_path)
    return _store


# -------------------------
# Eval endpoints
# -------------------------

@app.get("/eval/stats")
def eval_stats() -> dict:
    store = get_store()
    return store.stats()


@app.get("/eval/recent")
def eval_recent(limit: int = Query(50, ge=1, le=500)) -> dict:
    store = get_store()
    rows = store.recent(limit=limit)
    return {"items": rows, "limit": limit}


@app.get("/eval/diff")
def eval_diff(text_hash: str, limit: int = Query(200, ge=1, le=1000)) -> dict:
    store = get_store()
    rows = store.by_text_hash(text_hash=text_hash, limit=limit)
    return {"text_hash": text_hash, "items": rows, "limit": limit}


# -------------------------
# Fallback decision helpers
# -------------------------

SOCIAL_BLOCKLIST = {
    "instagram.com",
    "www.instagram.com",
    "facebook.com",
    "www.facebook.com",
    "x.com",
    "www.x.com",
    "twitter.com",
    "www.twitter.com",
    "tiktok.com",
    "www.tiktok.com",
}


def _domain(url: str) -> str:
    try:
        return urlparse(url).netloc.lower()
    except Exception:
        return ""


def _looks_temporal(text: str) -> bool:
    t = text.lower()

    if re.search(r"\b(today|yesterday|this week|last week|this month|last month)\b", t):
        return True
    if re.search(r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{4}\b", t):
        return True

    if re.search(r"(اليوم|أمس|هذا الأسبوع|الأسبوع الماضي|هذا الشهر|الشهر الماضي)", text):
        return True
    if re.search(r"\b(20\d{2}|19\d{2})\b", text):
        return True

    return False


def _keyword_overlap_score(claim: str, contexts: list[dict[str, Any]]) -> float:
    """
    Compute a lightweight overlap between claim tokens and retrieved evidence text.
    This is used to decide whether web fallback is needed.
    """
    claim_l = claim.lower()

    tokens = re.findall(r"[a-z0-9]{4,}|[\u0600-\u06FF]{3,}", claim_l)
    stop = {"this", "that", "with", "from", "بعد", "على", "الى", "هذا", "هذه"}
    tokens = [t for t in tokens if t not in stop]
    tokens = list(dict.fromkeys(tokens))[:12]

    if not tokens:
        return 1.0

    blob = " ".join((c.get("chunk_text") or c.get("text") or "").lower() for c in contexts[:6])
    hit = sum(1 for tok in tokens if tok in blob)
    return hit / max(1, len(tokens))


def _retrieval_needs_web(claim: str, contexts: list[dict[str, Any]]) -> bool:
    """
    Decide whether local retrieval is insufficient and web fallback should be used.
    """
    if not contexts or len(contexts) < 3:
        return True

    top_score = float(contexts[0].get("score") or 0.0)
    if top_score < 0.80:
        return True

    coverage = _keyword_overlap_score(claim, contexts)

    if _looks_temporal(claim):
        if not (top_score >= 0.92 and coverage >= 0.60):
            return True

    if coverage < 0.35:
        return True

    return False

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def _filter_cse_items(items: list[CSEItem]) -> list[CSEItem]:
    out: list[CSEItem] = []
    for it in items:
        if not it.link:
            continue
        if _domain(it.link) in SOCIAL_BLOCKLIST:
            continue
        out.append(it)
    return out


def _cse_to_contexts(items: list[CSEItem]) -> list[dict[str, Any]]:
    """
    Normalize CSE results into the same schema as RAG contexts.
    """
    out: list[dict[str, Any]] = []
    for it in items:
        out.append(
            {
                "type": "web_snippet",
                "source": it.display_link or _domain(it.link) or "web",
                "title": it.title,
                "url": it.link,
                "chunk_text": it.snippet,
                "score": 0.0,
            }
        )
    return out


# -------------------------
# Parsing helpers
# -------------------------

def _unwrap_parse_result(result: Any) -> dict[str, Any]:
    """
    Some parse functions may return a tuple (parsed, raw/error).
    This helper guarantees a dict output.
    """
    if isinstance(result, tuple) and result:
        candidate = result[0]
        return candidate if isinstance(candidate, dict) else {}
    return result if isinstance(result, dict) else {}


def _extract_llm_text(x: Any) -> str:
    """
    Normalize LLM output into a single text string for parsing.
    Supports dict outputs like {"text": "..."} or raw strings.
    """
    if isinstance(x, dict):
        return str(x.get("text") or "")
    return str(x or "")


def _should_fallback_after_llm(veracity_obj: Any) -> bool:
    """
    Trigger web fallback if the LLM can't decide confidently.
    """
    try:
        parsed = _unwrap_parse_result(
            parse_veracity(_extract_llm_text(veracity_obj))
        )
        label = str(parsed.get("label") or "").lower().strip()
        confidence = int(parsed.get("confidence") or 0)

        # Fallback if unclear or low confidence
        return label == "unclear" or confidence < 70
    except Exception:
        # Fail-safe: allow web fallback
        return True

def _count_local_contexts(contexts: list[dict[str, Any]]) -> int:
    """
    Count local RAG contexts (exclude web snippets).
    """
    return sum(1 for c in contexts if (c.get("type") or "") != "web_snippet")


def _dedupe_contexts(contexts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Remove repeated evidence items (often multiple chunks from the same article).
    Prefer the first occurrence which is typically the highest-scoring hit.
    """
    seen: set[object] = set()
    out: list[dict[str, Any]] = []

    for c in contexts:
        url = str(c.get("url") or "").strip()
        if url:
            key: object = url
        else:
            key = (
                str(c.get("source") or ""),
                str(c.get("title") or ""),
                str(c.get("chunk_text") or ""),
            )

        if key in seen:
            continue

        seen.add(key)
        out.append(c)

    return out

def is_probably_news(text: str) -> bool:
    """
    Conservative gate:
    - Reject only clearly non-news inputs (questions, instructions, random chat).
    - Allow most headlines and news bodies through.
    This prevents false negatives (rejecting real news).
    """
    t = (text or "").strip()
    if not t:
        return False

    # 1) Hard reject: obvious questions / conversations / instructions
    lower = t.lower()

    # If it contains many question marks, it's almost certainly not a news item.
    if "?" in t or "؟" in t:
        return False

    # Strong non-news intent markers (Arabic + English)
    non_news_markers = [
        "ساعدني", "اشرح", "ترجم", "اكتب", "اعمل", "سوّي", "كيف", "ليش", "شو", "ممكن",
        "help me", "explain", "translate", "write", "make", "how to", "why", "what is",
        "code", "python", "javascript", "sql", "api", "fastapi", "react",
    ]
    if any(m in lower for m in non_news_markers):
        # Still allow if it looks like a news-style headline with a speaker prefix.
        # Example: "وزير البيئة: ..." or "الشرطة: ..."
        if ":" not in t and "：" not in t:
            return False

    # 2) If it's long enough, treat it as news body by default
    # This fixes your second example (multi-paragraph).
    if len(t) >= 120:
        return True

    # 3) For short texts (headlines), accept common headline patterns
    # Speaker prefix is a strong news signal: "X: ..."
    if ":" in t or "：" in t:
        return True

    # Contains typical news verbs or institutional terms (expanded set)
    headline_markers = [
        "وزير", "وزارة", "أمانة", "الحكومة", "الملك", "الديوان", "القوات المسلحة",
        "الشرطة", "الأمن", "الدفاع المدني", "النيابة", "محكمة", "قاض", "قاضي",
        "أعلن", "تعلن", "أكد", "أكدت", "أوضحت", "صرّح", "قال", "ذكرت", "أفاد",
        "بدء", "إعداد", "برنامج", "خطة", "تنفيذ", "إجراءات", "قرار", "بيان",
        "حادث", "تدهور", "إغلاق", "تحويل", "أحوال جوية", "تباطؤ", "ازدحام",
        "عقوبات", "مذكرة", "توقيف", "هجوم", "انفجار", "زلزال", "وفيات", "إصابات",
        "اجتماع", "مؤتمر", "جلسة", "محادثات",
    ]
    if any(m in t for m in headline_markers):
        return True

    # Contains numbers/dates (often appear in headlines)
    if re.search(r"\b\d+\b", t) or re.search(r"\b(20\d{2}|19\d{2})\b", t):
        return True

    # 4) If it's a very short generic phrase without any signals, reject
    # Keep the minimum low to avoid rejecting real headlines.
    if len(t) < 20:
        return False

    # Default: accept (avoid false negatives)
    return True
# -------------------------



NEWS_GATE_VERSION = "v1"

def build_news_gate_prompt(text: str) -> list[dict[str, str]]:
    """
    Lightweight classifier prompt to decide if the input is a news text/claim suitable for analysis.
    Must return strict JSON only.
    """
    return [
        {
            "role": "system",
            "content": (
                "You are a strict classifier. Decide if the input is a NEWS text/claim suitable for fact-checking. "
                "If it's a generic question, chit-chat, instructions, programming, or unrelated request, return is_news=false. "
                "Return ONLY valid JSON with keys: is_news (boolean), category (string), reason (string). "
                "Categories: news, rumor, question, instruction, other."
            ),
        },
        {"role": "user", "content": text},
    ]


def parse_news_gate(raw: Any) -> dict[str, Any]:
    """
    Parse the gate output defensively. Supports dict outputs like {"text": "..."} or raw string.
    Always returns a dict with is_news/category/reason.
    """
    if isinstance(raw, dict):
        s = str(raw.get("text") or "")
    else:
        s = str(raw or "")

    # Try to extract JSON from fenced blocks or plain text
    s = s.strip()
    if "```" in s:
        # Extract the first fenced block content
        parts = s.split("```")
        if len(parts) >= 2:
            s = parts[1].strip()
            # Strip optional language tag like "json"
            if s.lower().startswith("json"):
                s = s[4:].strip()

    try:
        obj = json.loads(s)
    except Exception:
        return {"is_news": False, "category": "other", "reason": "Gate returned non-JSON output."}

    is_news = bool(obj.get("is_news", False))
    category = str(obj.get("category") or "other")
    reason = str(obj.get("reason") or "")

    return {"is_news": is_news, "category": category, "reason": reason}

# -------------------------
# Main endpoint
# -------------------------

@app.post("/analyze")
def analyze(req: AnalyzeRequest) -> dict:
    t0 = time.time()

    text = (req.text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="text is required")

    
    if not is_probably_news(text):
        raise HTTPException(status_code=400, detail="Only news text/claims are supported.")

    # --- LLM guardrail: reject non-news inputs before doing any expensive work ---
    try:
        llm = get_llm()  
        gate_prompt = build_news_gate_prompt(text)
        gate_raw = llm.chat(gate_prompt)
        gate = parse_news_gate(gate_raw)

        if not gate.get("is_news", False):
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Only news text/claims are supported.",
                    "category": gate.get("category", "other"),
                    "reason": gate.get("reason", ""),
                    "gate_version": NEWS_GATE_VERSION,
                },
            )
    except HTTPException:
        raise
    except Exception as e:
        # Fail closed to keep the system strict (and safe)
        log.warning("News gate failed err=%s", str(e))
        raise HTTPException(status_code=400, detail="Only news text/claims are supported.")

    store = get_store()

    cache = get_cache()
    if req.language in {"ar", "en"}:
        lang = req.language
    else:
        lang = detect_language(text)
        if lang is None:
            lang = "ar" if re.search(r"[\u0600-\u06FF]", text) else "en"
        elif lang not in {"ar", "en"}:
            lang = "en"
    prompt_version = PROMPT_VERSION_AR if lang == "ar" else PROMPT_VERSION

    cache_key = analyze_cache_key(
        text=text,
        model=SETTINGS.openai_model,
        top_k=SETTINGS.rag_top_k,
        prompt_version=prompt_version,
        pipeline_version=PIPELINE_VERSION,
    )

    # Cache HIT path
    if cache is not None:
        cached = cache.get_json(cache_key)
        if cached is not None:
            total_ms = int((time.time() - t0) * 1000)
            log.info("CACHE HIT key=%s text_len=%d ms=%d", cache_key, len(text), total_ms)

            try:
                v_parsed = _unwrap_parse_result(parse_veracity(_extract_llm_text(cached.get("veracity"))))
                b_parsed = _unwrap_parse_result(parse_bias(_extract_llm_text(cached.get("bias"))))

                retrieved = cached.get("retrieved") or []
                rag_top_score = 0.0
                if isinstance(retrieved, list) and retrieved:
                    first = retrieved[0] if isinstance(retrieved[0], dict) else {}
                    rag_top_score = float(first.get("score") or 0.0)

                store.insert_sample(
                    text=text,
                    model=SETTINGS.openai_model,
                    prompt_version=prompt_version,
                    pipeline_version=PIPELINE_VERSION,
                    rag_top_k=int(SETTINGS.rag_top_k),
                    cache_key=cache_key,
                    cache_hit=True,
                    rag_count=len(retrieved) if isinstance(retrieved, list) else None,
                    rag_top_score=rag_top_score,
                    used_cse=bool((cached.get("_fallback") or {}).get("used_cse") or False),
                    cse_count=int((cached.get("_fallback") or {}).get("cse_results_count") or 0),
                    total_ms=total_ms,
                    rag_ms=int((cached.get("_timing") or {}).get("rag_ms") or 0),
                    llm_ms=int((cached.get("_timing") or {}).get("llm_ms") or 0),
                    veracity_label=v_parsed.get("label"),
                    veracity_confidence=v_parsed.get("confidence"),
                    bias_has_bias=b_parsed.get("has_bias"),
                    bias_severity=b_parsed.get("severity"),
                    response_json=cached,
                )
            except Exception as e:
                log.warning("EvalStore insert failed (cache hit) err=%s", str(e))

            return cached

        log.info("CACHE MISS key=%s text_len=%d", cache_key, len(text))
    else:
        log.info("CACHE OFF key=%s text_len=%d", cache_key, len(text))

    # Cache MISS path
    retriever = get_retriever()
    llm = get_llm()
    cse = get_cse()

    # 1) Local retrieval
    t_rag = time.time()
    contexts: list[dict[str, Any]] = retriever.search(text, top_k=SETTINGS.rag_top_k)
    rag_ms = int((time.time() - t_rag) * 1000)

    top_score = float(contexts[0].get("score") or 0.0) if contexts else 0.0
    log.info("RAG retrieved=%d top_score=%.3f rag_ms=%d", len(contexts), top_score, rag_ms)

    local_count = _count_local_contexts(contexts)

    # 2) Web fallback
    used_cse = False
    cse_results_count = 0
    web_ms = 0

    if cse.is_configured() and _retrieval_needs_web(text, contexts):
        t_web = time.time()
        used_cse = True
        num = int(getattr(SETTINGS, "google_cse_num", 5))

        items = _filter_cse_items(cse.search(query=text, num=num))
        web_contexts = _cse_to_contexts(items)
        cse_results_count = len(web_contexts)

        contexts = contexts + web_contexts
        web_ms = int((time.time() - t_web) * 1000)

        log.info("CSE used=true results=%d web_ms=%d", cse_results_count, web_ms)
    else:
        log.info("CSE used=false configured=%s", cse.is_configured())

    # Deduplicate evidence (multiple chunks from the same article).
    contexts = _dedupe_contexts(contexts)
    local_count = _count_local_contexts(contexts)

    # 3) LLM inference
    t_llm = time.time()
    veracity = llm.chat(build_veracity_prompt(user_text=text, contexts=contexts, language=lang))
    bias = llm.chat(build_bias_prompt(user_text=text, contexts=contexts))
    llm_ms = int((time.time() - t_llm) * 1000)

    total_ms = int((time.time() - t0) * 1000)
    log.info("ANALYZE done total_ms=%d llm_ms=%d", total_ms, llm_ms)

    out = {
        "input": text,
        "prompt_version": prompt_version,
        "pipeline_version": PIPELINE_VERSION,
        "retrieved": contexts,
        "veracity": veracity,
        "bias": bias,
        "_fallback": {"used_cse": used_cse, "cse_results_count": cse_results_count},
        "_timing": {"rag_ms": rag_ms, "web_ms": web_ms, "llm_ms": llm_ms, "total_ms": total_ms},
        "_cache": {"key": cache_key, "hit": False},
    }

    # Save to cache
    if cache is not None:
        try:
            cache.set_json(cache_key, out)
        except Exception as e:
            log.warning("Cache set failed key=%s err=%s", cache_key, str(e))

    # Save eval sample
    try:
        v_parsed = _unwrap_parse_result(parse_veracity(_extract_llm_text(veracity)))
        b_parsed = _unwrap_parse_result(parse_bias(_extract_llm_text(bias)))

        store.insert_sample(
            text=text,
            model=SETTINGS.openai_model,
            prompt_version=prompt_version,
            pipeline_version=PIPELINE_VERSION,
            rag_top_k=int(SETTINGS.rag_top_k),
            cache_key=cache_key,
            cache_hit=False,
            rag_count=local_count,
            rag_top_score=top_score,
            used_cse=used_cse,
            cse_count=cse_results_count,
            total_ms=total_ms,
            rag_ms=rag_ms,
            llm_ms=llm_ms,
            veracity_label=v_parsed.get("label"),
            veracity_confidence=v_parsed.get("confidence"),
            bias_has_bias=b_parsed.get("has_bias"),
            bias_severity=b_parsed.get("severity"),
            response_json=out,
        )
    except Exception as e:
        log.warning("EvalStore insert failed (cache miss) err=%s", str(e))

    return out
