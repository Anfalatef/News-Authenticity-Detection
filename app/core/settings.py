"""
Application settings.

Loads environment variables from .env and exposes runtime configuration.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from dotenv import load_dotenv

# Load .env once at application startup
load_dotenv()


@dataclass(frozen=True)
class Settings:
    # App
    app_env: str = os.getenv("APP_ENV", "dev").strip()

    # OpenAI / LLM
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "").strip()
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()

    # Storage paths
    sqlite_path: str = os.getenv("SQLITE_PATH", "data/news.db").strip()
    faiss_index_path: str = os.getenv("FAISS_INDEX_PATH", "data/faiss/chunks.index").strip()

    # Retrieval
    rag_top_k: int = int(os.getenv("RAG_TOP_K", "8"))

    # Google CSE (fallback web search)
    google_cse_api_key: str = os.getenv("GOOGLE_CSE_API_KEY", "").strip()
    google_cse_cx: str = os.getenv("GOOGLE_CSE_CX", "").strip()
    google_cse_num: int = int(os.getenv("GOOGLE_CSE_NUM", "5"))
    

    # Cache (Redis) - optional
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0").strip()
    cache_ttl_sec: int = 172800


SETTINGS = Settings()
