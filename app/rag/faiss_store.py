from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import faiss
import numpy as np


@dataclass(frozen=True)
class SearchResult:
    faiss_id: int
    score: float


class FaissStore:
    def __init__(self, index_path: str) -> None:
        self.index_path = Path(index_path)
        if not self.index_path.exists():
            raise FileNotFoundError(f"FAISS index not found: {self.index_path}")

        self.index = faiss.read_index(str(self.index_path))

    def search(self, query_vec: np.ndarray, top_k: int) -> list[SearchResult]:
        """
        query_vec: shape (dim,) or (1, dim) float32
        """
        if query_vec.ndim == 1:
            query_vec = query_vec.reshape(1, -1)
        query_vec = query_vec.astype("float32", copy=False)

        scores, ids = self.index.search(query_vec, top_k)
        out: list[SearchResult] = []
        for i in range(min(top_k, ids.shape[1])):
            faiss_id = int(ids[0, i])
            score = float(scores[0, i])
            if faiss_id < 0:
                continue
            out.append(SearchResult(faiss_id=faiss_id, score=score))
        return out
