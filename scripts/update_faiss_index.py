from __future__ import annotations

import logging
from pathlib import Path

import numpy as np

from app.db.connection import SessionLocal
from app.rag.settings import RAG_SETTINGS
from app.rag.embedding_model import EmbeddingModel
from app.rag.faiss_store import FaissStore
from app.rag.db_ops import fetch_unembedded_chunks, get_next_faiss_id, insert_embeddings_rows

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | rag | %(message)s",
)
log = logging.getLogger("rag")


def main() -> None:
    RAG_SETTINGS.faiss_dir.mkdir(parents=True, exist_ok=True)

    model = EmbeddingModel(RAG_SETTINGS.embedding_model_name)

    # Load existing index if exists, otherwise create when we know dim.
    store: FaissStore | None = None

    total_added = 0

    session = SessionLocal()
    try:
        while True:
            batch = fetch_unembedded_chunks(session, limit=RAG_SETTINGS.batch_size)
            if not batch:
                break

            texts = [b.chunk_text for b in batch]
            ids_start = get_next_faiss_id(session)

            emb = model.embed_passages(texts)  # vectors float32 (n, dim) normalized

            if store is None:
                if RAG_SETTINGS.faiss_index_path.exists():
                    store = FaissStore.load(RAG_SETTINGS.faiss_index_path)
                    if store.dim != emb.dim:
                        raise RuntimeError(
                            f"FAISS index dim mismatch. index_dim={store.dim} model_dim={emb.dim}"
                        )
                else:
                    store = FaissStore(dim=emb.dim)

            faiss_ids = np.arange(ids_start, ids_start + len(batch), dtype=np.int64)

            store.add(ids=faiss_ids, vectors=emb.vectors)

            insert_rows = [
                (batch[i].chunk_id, int(faiss_ids[i]), emb.model_name, emb.dim)
                for i in range(len(batch))
            ]
            insert_embeddings_rows(session, insert_rows)

            total_added += len(batch)
            log.info("Indexed batch: added=%d total_added=%d", len(batch), total_added)

        if store is None:
            log.info("No new chunks to embed. Nothing to do.")
            return

        store.save(RAG_SETTINGS.faiss_index_path)
        log.info("FAISS index saved: %s", RAG_SETTINGS.faiss_index_path)

    finally:
        session.close()

    log.info("Done. Total embedded and indexed: %d", total_added)


if __name__ == "__main__":
    main()
