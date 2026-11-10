from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.db.connection import SessionLocal
from app.db.models import Chunk, Article, Source, Embedding
from app.rag.settings import RAG_SETTINGS
from app.rag.embedding_model import EmbeddingModel
from app.rag.faiss_store import FaissStore

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | rag | %(message)s",
)
log = logging.getLogger("rag")


def fetch_chunk_details(session: Session, faiss_ids: list[int]) -> list[dict]:
    rows = (
        session.query(
            Embedding.faiss_id,
            Chunk.chunk_text,
            Article.url,
            Article.title,
            Article.published_at,
            Source.domain,
        )
        .join(Chunk, Chunk.chunk_id == Embedding.chunk_id)
        .join(Article, Article.article_id == Chunk.article_id)
        .join(Source, Source.source_id == Article.source_id)
        .filter(Embedding.faiss_id.in_(faiss_ids))
        .all()
    )

    out = []
    by_id = {int(r[0]): r for r in rows}
    for fid in faiss_ids:
        r = by_id.get(fid)
        if not r:
            continue
        out.append(
            {
                "faiss_id": int(r[0]),
                "source": str(r[5]),
                "url": str(r[2]),
                "title": (str(r[3]) if r[3] else ""),
                "published_at": (str(r[4]) if r[4] else ""),
                "chunk_preview": str(r[1])[:300],
            }
        )
    return out


def main() -> None:
    if not RAG_SETTINGS.faiss_index_path.exists():
        raise RuntimeError(
            f"FAISS index not found at {RAG_SETTINGS.faiss_index_path}. Run: python -m scripts.update_faiss_index"
        )

    store = FaissStore.load(RAG_SETTINGS.faiss_index_path)
    model = EmbeddingModel(RAG_SETTINGS.embedding_model_name)

    query = input("Enter a news text / claim: ").strip()
    if not query:
        return

    q = model.embed_query(query)
    if q.dim != store.dim:
        raise RuntimeError(f"Dim mismatch: query_dim={q.dim} index_dim={store.dim}")

    res = store.search(q.vectors, top_k=8)

    # FAISS returns -1 for empty slots; filter them out
    faiss_ids = [int(x) for x in res.faiss_ids.tolist() if int(x) != -1]
    scores = [float(x) for x in res.scores.tolist()[: len(faiss_ids)]]

    log.info("Top results (faiss_id, score): %s", list(zip(faiss_ids, scores)))

    session = SessionLocal()
    try:
        details = fetch_chunk_details(session, faiss_ids)
    finally:
        session.close()

    for d in details:
        print("-" * 100)
        print(f"FAISS_ID: {d['faiss_id']}")
        print(f"SOURCE: {d['source']}")
        print(f"TITLE: {d['title']}")
        print(f"URL: {d['url']}")
        print(f"PUBLISHED: {d['published_at']}")
        print(f"CHUNK: {d['chunk_preview']}")


if __name__ == "__main__":
    main()
