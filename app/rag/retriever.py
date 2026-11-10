from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from sentence_transformers import SentenceTransformer
from sqlalchemy import create_engine, text as sql_text

from app.rag.faiss_store import FaissStore


@dataclass(frozen=True)
class RetrievedChunk:
    faiss_id: int
    score: float
    source: str
    title: str
    url: str
    published_at: str | None
    chunk_text: str


class RagRetriever:
    """
    Production-grade RAG retriever:
    - Embeds query using SentenceTransformer (E5 query prefix).
    - Searches FAISS for top_k nearest chunks.
    - Fetches chunk metadata in ONE SQL query (avoids N+1).
    """

    def __init__(
        self,
        faiss_index_path: str,
        sqlite_path: str,
        embedding_model: str = "intfloat/multilingual-e5-small",
    ) -> None:
        self.store = FaissStore(faiss_index_path)
        self.model = SentenceTransformer(embedding_model)

        # Pooling is fine even with SQLite; keep future=True for modern SQLAlchemy behavior.
        self.engine = create_engine(f"sqlite:///{sqlite_path}", future=True)

    def _embed_query(self, q: str) -> np.ndarray:
        # E5 recommends:
        # - "query: " prefix for queries
        # - "passage: " prefix for documents (done at ingestion time usually)
        emb = self.model.encode([f"query: {q}"], normalize_embeddings=True)
        return np.array(emb[0], dtype="float32")

    def _fetch_chunks_by_faiss_ids(self, faiss_ids: list[int]) -> dict[int, dict[str, Any]]:
        """
        Fetch all chunk rows by faiss_id in a single query.
        Returns a mapping: faiss_id -> row dict
        """
        if not faiss_ids:
            return {}

        # Use named parameters to avoid SQL injection and to work with SQLite.
        params = {f"id{i}": fid for i, fid in enumerate(faiss_ids)}
        placeholders = ", ".join(f":id{i}" for i in range(len(faiss_ids)))

        sql = sql_text(
            f"""
            SELECT
              e.faiss_id AS faiss_id,
              s.domain  AS source,
              a.title   AS title,
              a.url     AS url,
              a.published_at AS published_at,
              c.chunk_text AS chunk_text
            FROM embeddings e
            JOIN chunks c   ON c.chunk_id = e.chunk_id
            JOIN articles a ON a.article_id = c.article_id
            JOIN sources s  ON s.source_id = a.source_id
            WHERE e.faiss_id IN ({placeholders})
            """
        )

        out: dict[int, dict[str, Any]] = {}
        with self.engine.connect() as conn:
            rows = conn.execute(sql, params).mappings().all()
            for row in rows:
                fid = int(row["faiss_id"])
                out[fid] = dict(row)
        return out

    def search(self, query: str, top_k: int = 8) -> list[dict[str, Any]]:
        """
        Returns a list of dict contexts compatible with the rest of your pipeline.
        """
        query = (query or "").strip()
        if not query:
            return []

        qvec = self._embed_query(query)
        hits = self.store.search(qvec, top_k=top_k)
        if not hits:
            return []

        faiss_ids = [h.faiss_id for h in hits]
        rows_by_id = self._fetch_chunks_by_faiss_ids(faiss_ids)

        results: list[dict[str, Any]] = []
        for h in hits:
            row = rows_by_id.get(h.faiss_id)
            if not row:
                continue

            results.append(
                {
                    "faiss_id": int(h.faiss_id),
                    "score": float(h.score),
                    "source": str(row.get("source") or ""),
                    "title": str(row.get("title") or ""),
                    "url": str(row.get("url") or ""),
                    "published_at": row.get("published_at"),
                    "chunk_text": str(row.get("chunk_text") or ""),
                }
            )

        return results
