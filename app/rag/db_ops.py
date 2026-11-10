from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.models import Chunk, Embedding


@dataclass(frozen=True)
class ChunkRow:
    chunk_id: int
    chunk_text: str


def get_next_faiss_id(session: Session) -> int:
    """
    Next FAISS ID = max(existing) + 1, or 1 if empty.
    """
    max_id = session.query(func.max(Embedding.faiss_id)).scalar()
    return int(max_id or 0) + 1


def fetch_unembedded_chunks(session: Session, limit: int) -> List[ChunkRow]:
    """
    Return chunks that do not have embeddings yet.
    """
    rows = (
        session.query(Chunk.chunk_id, Chunk.chunk_text)
        .outerjoin(Embedding, Embedding.chunk_id == Chunk.chunk_id)
        .filter(Embedding.chunk_id.is_(None))
        .order_by(Chunk.chunk_id.asc())
        .limit(limit)
        .all()
    )
    return [ChunkRow(chunk_id=int(r[0]), chunk_text=str(r[1])) for r in rows]


def insert_embeddings_rows(
    session: Session,
    rows: List[Tuple[int, int, str, int]],
) -> None:
    """
    rows: list of (chunk_id, faiss_id, model_name, dim)
    """
    for chunk_id, faiss_id, model_name, dim in rows:
        session.add(
            Embedding(
                chunk_id=chunk_id,
                faiss_id=faiss_id,
                model_name=model_name,
                dim=dim,
            )
        )
    session.commit()
