from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass
from typing import Any, Optional


def stable_text_hash(text: str) -> str:
    t = (text or "").strip().encode("utf-8")
    return hashlib.sha256(t).hexdigest()


@dataclass
class EvalStore:
    sqlite_path: str

    def _connect(self) -> sqlite3.Connection:
        con = sqlite3.connect(self.sqlite_path)
        con.row_factory = sqlite3.Row
        return con

    def _row_to_dict(self, row: sqlite3.Row) -> dict[str, Any]:
        out = dict(row)
        raw = out.get("response_json")
        if isinstance(raw, str):
            try:
                payload = json.loads(raw)
            except Exception:
                payload = None
            if isinstance(payload, dict):
                out["response"] = payload
                out["retrieved"] = payload.get("retrieved")
        return out

    def insert_sample(
        self,
        *,
        text: str,
        model: str,
        prompt_version: str,
        pipeline_version: str,
        rag_top_k: int,
        cache_key: Optional[str],
        cache_hit: bool,
        rag_count: Optional[int],
        rag_top_score: Optional[float],
        used_cse: bool,
        cse_count: int,
        total_ms: Optional[int],
        rag_ms: Optional[int],
        llm_ms: Optional[int],
        veracity_label: Optional[str],
        veracity_confidence: Optional[int],
        bias_has_bias: Optional[bool],
        bias_severity: Optional[int],
        response_json: dict[str, Any],
    ) -> None:
        """
        Insert one evaluation/telemetry sample into SQLite.
        response_json is the full API response payload (stored as a JSON string).
        """
        h = stable_text_hash(text)
        payload = json.dumps(response_json, ensure_ascii=False)

        con = self._connect()
        try:
            cur = con.cursor()
            cur.execute(
                """
                INSERT INTO eval_samples (
                  text, text_hash,
                  model, prompt_version, pipeline_version, rag_top_k,
                  cache_key, cache_hit,
                  rag_count, rag_top_score,
                  used_cse, cse_count,
                  total_ms, rag_ms, llm_ms,
                  veracity_label, veracity_confidence,
                  bias_has_bias, bias_severity,
                  response_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    text, h,
                    model, prompt_version, pipeline_version, int(rag_top_k),
                    cache_key, 1 if cache_hit else 0,
                    rag_count, rag_top_score,
                    1 if used_cse else 0, int(cse_count),
                    total_ms, rag_ms, llm_ms,
                    veracity_label, veracity_confidence,
                    None if bias_has_bias is None else (1 if bias_has_bias else 0),
                    bias_severity,
                    payload,
                ),
            )
            con.commit()
        finally:
            con.close()

    def stats(self) -> dict[str, Any]:
        con = self._connect()
        try:
            cur = con.execute(
                """
                SELECT
                  COUNT(*) AS total_samples,
                  COALESCE(SUM(cache_hit), 0) AS cache_hits,
                  AVG(total_ms) AS avg_total_ms,
                  AVG(llm_ms) AS avg_llm_ms,
                  AVG(rag_ms) AS avg_rag_ms
                FROM eval_samples
                """
            )
            row = cur.fetchone()
            total_samples = int(row["total_samples"] or 0)
            cache_hits = int(row["cache_hits"] or 0)
            cache_hit_rate = (cache_hits / total_samples) if total_samples else 0.0
            return {
                "total_samples": total_samples,
                "cache_hits": cache_hits,
                "cache_hit_rate": cache_hit_rate,
                "avg_total_ms": row["avg_total_ms"],
                "avg_llm_ms": row["avg_llm_ms"],
                "avg_rag_ms": row["avg_rag_ms"],
            }
        finally:
            con.close()

    def recent(self, limit: int = 50) -> list[dict[str, Any]]:
        con = self._connect()
        try:
            cur = con.execute(
                """
                SELECT *
                FROM eval_samples
                ORDER BY id DESC
                LIMIT ?
                """,
                (int(limit),),
            )
            rows = cur.fetchall()
            return [self._row_to_dict(r) for r in rows]
        finally:
            con.close()

    def by_text_hash(self, text_hash: str, limit: int = 200) -> list[dict[str, Any]]:
        con = self._connect()
        try:
            cur = con.execute(
                """
                SELECT *
                FROM eval_samples
                WHERE text_hash = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (text_hash, int(limit)),
            )
            rows = cur.fetchall()
            return [self._row_to_dict(r) for r in rows]
        finally:
            con.close()
