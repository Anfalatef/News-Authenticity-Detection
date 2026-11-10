"""
Incremental FAISS index builder.

This module keeps FAISS index and SQLite embeddings table in sync.

Design:
- chunks are the source of truth (SQLite table `chunks`)
- embeddings table maps chunk_id <-> faiss_id
- faiss_id must match the vector position in FAISS

Modes:
- rebuild=True  : wipe embeddings table and rebuild FAISS from all chunks
- rebuild=False : embed only new chunks not present in embeddings table and append to FAISS
"""

from __future__ import annotations

import logging
import os
import sqlite3
from pathlib import Path
from typing import Iterable, List, Tuple

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


log = logging.getLogger("rag.indexer")


def _ensure_parent_dir(path: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def _connect(sqlite_path: str) -> sqlite3.Connection:
    con = sqlite3.connect(sqlite_path)
    con.execute("PRAGMA journal_mode=WAL;")
    con.execute("PRAGMA foreign_keys=ON;")
    return con


def _ensure_embeddings_table(con: sqlite3.Connection) -> None:
    """
    Create embeddings table if it doesn't exist.

    This table is required by RagRetriever:
      embeddings.faiss_id -> embeddings.chunk_id -> chunks
    """
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS embeddings (
          chunk_id INTEGER NOT NULL UNIQUE,
          faiss_id INTEGER NOT NULL UNIQUE,
          created_at TEXT NOT NULL DEFAULT (datetime('now')),
          FOREIGN KEY (chunk_id) REFERENCES chunks(chunk_id) ON DELETE CASCADE
        )
        """
    )
    con.execute("CREATE INDEX IF NOT EXISTS idx_embeddings_faiss_id ON embeddings(faiss_id)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_embeddings_chunk_id ON embeddings(chunk_id)")
    con.commit()


def _fetch_all_chunks(con: sqlite3.Connection) -> List[Tuple[int, str]]:
    cur = con.execute(
        """
        SELECT chunk_id, chunk_text
        FROM chunks
        ORDER BY chunk_id ASC
        """
    )
    rows = cur.fetchall()
    out: List[Tuple[int, str]] = []
    for cid, txt in rows:
        t = (txt or "").strip()
        if not t:
            continue
        out.append((int(cid), t))
    return out


def _fetch_new_chunks(con: sqlite3.Connection) -> List[Tuple[int, str]]:
    """
    Fetch chunks that do not have embeddings yet.
    """
    cur = con.execute(
        """
        SELECT c.chunk_id, c.chunk_text
        FROM chunks c
        LEFT JOIN embeddings e ON e.chunk_id = c.chunk_id
        WHERE e.chunk_id IS NULL
        ORDER BY c.chunk_id ASC
        """
    )
    rows = cur.fetchall()
    out: List[Tuple[int, str]] = []
    for cid, txt in rows:
        t = (txt or "").strip()
        if not t:
            continue
        out.append((int(cid), t))
    return out


def _load_or_create_index(index_path: str, dim: int) -> faiss.Index:
    if os.path.exists(index_path):
        idx = faiss.read_index(index_path)
        return idx
    return faiss.IndexFlatIP(dim)


def _embed_passages(model: SentenceTransformer, texts: List[str], batch_size: int = 64) -> np.ndarray:
    """
    E5 recommends prefixing documents with "passage: ".
    """
    prefixed = [f"passage: {t}" for t in texts]
    emb = model.encode(
        prefixed,
        batch_size=batch_size,
        show_progress_bar=True,
        normalize_embeddings=True,
    )
    return np.asarray(emb, dtype="float32")


def build_faiss_index(
    *,
    sqlite_path: str,
    faiss_index_path: str,
    embedding_model: str = "intfloat/multilingual-e5-small",
    rebuild: bool = False,
    batch_size: int = 64,
) -> dict:
    """
    Build or incrementally update FAISS index and embeddings table.

    Returns a small report dict for logging/monitoring.
    """
    _ensure_parent_dir(faiss_index_path)

    con = _connect(sqlite_path)
    try:
        _ensure_embeddings_table(con)

        model = SentenceTransformer(embedding_model)

        if rebuild:
            log.warning("Rebuild requested: wiping embeddings table and rebuilding FAISS from all chunks.")
            con.execute("DELETE FROM embeddings")
            con.commit()

            chunks = _fetch_all_chunks(con)
            if not chunks:
                log.warning("No chunks found; skipping FAISS build.")
                return {"mode": "rebuild", "added": 0, "total_vectors": 0}

            chunk_ids = [c[0] for c in chunks]
            texts = [c[1] for c in chunks]

            vectors = _embed_passages(model, texts, batch_size=batch_size)
            dim = int(vectors.shape[1])

            index = faiss.IndexFlatIP(dim)
            index.add(vectors)

            # faiss_id is the vector position [0..ntotal-1]
            rows = [(int(chunk_ids[i]), int(i)) for i in range(len(chunk_ids))]
            con.executemany("INSERT INTO embeddings(chunk_id, faiss_id) VALUES (?, ?)", rows)
            con.commit()

            faiss.write_index(index, faiss_index_path)

            return {"mode": "rebuild", "added": len(rows), "total_vectors": int(index.ntotal)}

        # Incremental mode
        new_chunks = _fetch_new_chunks(con)
        if not new_chunks:
            # Ensure index exists even if no new data (optional)
            if not os.path.exists(faiss_index_path):
                # Create empty index with correct dim by embedding a dummy passage once.
                dummy_vec = _embed_passages(model, ["dummy"], batch_size=1)
                dim = int(dummy_vec.shape[1])
                index = faiss.IndexFlatIP(dim)
                faiss.write_index(index, faiss_index_path)
                log.info("Created empty FAISS index path=%s dim=%d", faiss_index_path, dim)
            return {"mode": "incremental", "added": 0, "total_vectors": _safe_ntotal(faiss_index_path)}

        texts = [c[1] for c in new_chunks]
        vectors = _embed_passages(model, texts, batch_size=batch_size)
        dim = int(vectors.shape[1])

        index = _load_or_create_index(faiss_index_path, dim)
        start = int(index.ntotal)

        index.add(vectors)
        end = int(index.ntotal)

        # Assign faiss_ids sequentially based on vector positions
        rows = []
        for i, (chunk_id, _) in enumerate(new_chunks):
            faiss_id = start + i
            rows.append((int(chunk_id), int(faiss_id)))

        con.executemany("INSERT INTO embeddings(chunk_id, faiss_id) VALUES (?, ?)", rows)
        con.commit()

        faiss.write_index(index, faiss_index_path)

        log.info("FAISS updated added=%d ntotal=%d path=%s", len(rows), int(index.ntotal), faiss_index_path)
        return {"mode": "incremental", "added": len(rows), "total_vectors": int(index.ntotal)}

    finally:
        con.close()


def _safe_ntotal(index_path: str) -> int:
    try:
        idx = faiss.read_index(index_path)
        return int(idx.ntotal)
    except Exception:
        return 0
