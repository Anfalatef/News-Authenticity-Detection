from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

import numpy as np
from sentence_transformers import SentenceTransformer


def _normalize_l2(vectors: np.ndarray) -> np.ndarray:
    """
    Normalize vectors to unit length for cosine similarity.
    """
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1.0, norms)
    return vectors / norms


@dataclass(frozen=True)
class EmbeddingResult:
    vectors: np.ndarray  # float32, shape: (n, dim)
    dim: int
    model_name: str


class EmbeddingModel:
    """
    Production-friendly wrapper around SentenceTransformers.

    Uses E5-style models. For E5 retrieval quality, we add prefixes:
    - documents: "passage: ..."
    - queries: "query: ..."
    """

    def __init__(self, model_name: str) -> None:
        self.model_name = model_name
        self._model = SentenceTransformer(model_name)

    def embed_passages(self, passages: List[str]) -> EmbeddingResult:
        """
        Create embeddings for documents (chunks).
        """
        texts = [f"passage: {p}" for p in passages]
        vecs = self._model.encode(
            texts,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=False,
        )

        vecs = np.asarray(vecs, dtype=np.float32)
        vecs = _normalize_l2(vecs)

        return EmbeddingResult(vectors=vecs, dim=vecs.shape[1], model_name=self.model_name)

    def embed_query(self, query: str) -> EmbeddingResult:
        """
        Create embedding for a user query (news text / claim).
        """
        texts = [f"query: {query}"]
        vecs = self._model.encode(
            texts,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=False,
        )

        vecs = np.asarray(vecs, dtype=np.float32)
        vecs = _normalize_l2(vecs)

        return EmbeddingResult(vectors=vecs, dim=vecs.shape[1], model_name=self.model_name)
