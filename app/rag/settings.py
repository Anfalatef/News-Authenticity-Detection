from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RagSettings:
    # Open-source multilingual embedding model (free).
    # - "intfloat/multilingual-e5-small" (fast, good baseline)
    embedding_model_name: str = "intfloat/multilingual-e5-small"

    # Where to store FAISS index on disk
    faiss_dir: Path = Path("data") / "faiss"
    faiss_index_path: Path = faiss_dir / "chunks.index"

    # Embedding behavior
    batch_size: int = 64
    normalize_embeddings: bool = True

    # Retrieval
    top_k_default: int = 8


RAG_SETTINGS = RagSettings()
