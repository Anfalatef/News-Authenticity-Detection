export const API_BASE = import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8000";

export type AnalyzeResponse = {
  input: string;
  prompt_version: string;
  pipeline_version: string;
  retrieved: Array<{
    faiss_id?: number;
    score?: number;
    source?: string;
    title?: string;
    url?: string;
    published_at?: string | null;
    chunk_text?: string;
    type?: string;
  }>;
  veracity: unknown;
  bias: unknown;
  _fallback?: { used_cse?: boolean; cse_results_count?: number };
  _timing?: { rag_ms?: number; web_ms?: number; llm_ms?: number; total_ms?: number };
  _cache?: { key?: string; hit?: boolean };
};

export type EvalStats = {
  total_samples: number;
  cache_hits: number;
  cache_hit_rate: number;
  avg_total_ms: number | null;
  avg_llm_ms: number | null;
  avg_rag_ms: number | null;
};

export type EvalRecentItem = {
  id: number;
  created_at: string;
  text: string;
  text_hash: string;
  model: string;
  prompt_version: string;
  pipeline_version: string;
  rag_top_k: number;
  rag_count: number | null;
  rag_top_score: number | null;
  cache_key: string | null;
  cache_hit: number;
  used_cse: number;
  cse_count: number;
  total_ms: number | null;
  rag_ms: number | null;
  llm_ms: number | null;
  veracity_label: string | null;
  veracity_confidence: number | null;
  bias_has_bias: number | null;
  bias_severity: number | null;
  retrieved?: AnalyzeResponse["retrieved"];
  response?: unknown;
};

export type EvalRecentResponse = {
  items: EvalRecentItem[];
  limit: number;
};

export type EvalDiffResponse = {
  text_hash: string;
  items: EvalRecentItem[];
  limit: number;
};

async function http<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`HTTP ${res.status} ${res.statusText}: ${text}`.trim());
  }

  return (await res.json()) as T;
}

export const api = {
  analyze: (text: string, language?: "ar" | "en") =>
    http<AnalyzeResponse>("/analyze", {
      method: "POST",
      body: JSON.stringify({ text, language }),
    }),
  evalStats: () => http<EvalStats>("/eval/stats"),
  evalRecent: (limit = 50) => http<EvalRecentResponse>(`/eval/recent?limit=${limit}`),
  evalDiff: (textHash: string, limit = 200) =>
    http<EvalDiffResponse>(
      `/eval/diff?text_hash=${encodeURIComponent(textHash)}&limit=${limit}`
    ),
};
