import { useEffect, useMemo, useState } from "react";
import { api, type EvalRecentItem, type EvalStats } from "../api";
import { Card, CardBody, CardHeader } from "../components/StatCard";
import { useLanguage } from "../lib/i18n";

const SPARK_WIDTH = 160;
const SPARK_HEIGHT = 40;
const BAR_WIDTH = 160;
const BAR_HEIGHT = 40;

function toSparkPath(values: Array<number | null | undefined>) {
  const points = values.filter((v): v is number => typeof v === "number" && !Number.isNaN(v));
  if (points.length < 2) return "";

  const min = Math.min(...points);
  const max = Math.max(...points);
  const range = max - min || 1;

  return points
    .map((v, idx) => {
      const x = (idx / (points.length - 1)) * SPARK_WIDTH;
      const y = SPARK_HEIGHT - ((v - min) / range) * (SPARK_HEIGHT - 6) - 3;
      return `${idx === 0 ? "M" : "L"}${x.toFixed(2)},${y.toFixed(2)}`;
    })
    .join(" ");
}

function Sparkline({ values }: { values: Array<number | null | undefined> }) {
  const path = useMemo(() => toSparkPath(values), [values]);
  return (
    <svg
      viewBox={`0 0 ${SPARK_WIDTH} ${SPARK_HEIGHT}`}
      className="mt-3 h-9 w-full"
      aria-hidden
    >
      <path
        d={path || `M0,${SPARK_HEIGHT - 3} L${SPARK_WIDTH},${SPARK_HEIGHT - 3}`}
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        className="text-brand-300"
        strokeLinecap="round"
      />
    </svg>
  );
}

function MiniBars({ values }: { values: number[] }) {
  const max = Math.max(1, ...values);
  const step = BAR_WIDTH / Math.max(values.length, 1);
  return (
    <svg viewBox={`0 0 ${BAR_WIDTH} ${BAR_HEIGHT}`} className="mt-3 h-10 w-full" aria-hidden>
      {values.map((v, i) => {
        const height = (v / max) * (BAR_HEIGHT - 6);
        const x = i * step + 1;
        const y = BAR_HEIGHT - height - 3;
        const w = Math.max(3, step - 2);
        return (
          <rect
            key={i}
            x={x}
            y={y}
            width={w}
            height={height}
            rx={2}
            className="fill-brand-100"
          />
        );
      })}
    </svg>
  );
}

function Donut({ value, total }: { value: number; total: number }) {
  const radius = 18;
  const circumference = 2 * Math.PI * radius;
  const ratio = total ? Math.max(0, Math.min(1, value / total)) : 0;
  const filled = circumference * ratio;
  return (
    <svg viewBox="0 0 48 48" className="h-12 w-12" aria-hidden>
      <circle
        cx="24"
        cy="24"
        r={radius}
        fill="none"
        stroke="currentColor"
        strokeWidth="6"
        className="text-line"
      />
      <circle
        cx="24"
        cy="24"
        r={radius}
        fill="none"
        stroke="currentColor"
        strokeWidth="6"
        strokeDasharray={`${filled} ${circumference - filled}`}
        strokeLinecap="round"
        className="text-brand-300"
        transform="rotate(-90 24 24)"
      />
    </svg>
  );
}

function summarize(values: Array<number | null | undefined>) {
  const nums = values.filter((v): v is number => typeof v === "number" && !Number.isNaN(v));
  if (!nums.length) return null;
  const total = nums.reduce((a, b) => a + b, 0);
  return {
    avg: total / nums.length,
    min: Math.min(...nums),
    max: Math.max(...nums),
    last: nums[nums.length - 1],
  };
}

function formatNumber(value: number | null | undefined) {
  if (typeof value !== "number" || Number.isNaN(value)) return null;
  return Math.round(value).toString();
}

export function DashboardPage() {
  const { t } = useLanguage();
  const [stats, setStats] = useState<EvalStats | null>(null);
  const [recent, setRecent] = useState<EvalRecentItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    const load = async (silent: boolean) => {
      if (!silent) setLoading(true);
      try {
        const [statsRes, recentRes] = await Promise.all([
          api.evalStats(),
          api.evalRecent(80),
        ]);
        if (mounted) {
          setStats(statsRes);
          setRecent(recentRes.items ?? []);
        }
      } catch (err: any) {
        if (mounted) setError(err?.message ?? t("error"));
      } finally {
        if (mounted && !silent) setLoading(false);
      }
    };

    load(false);
    const id = setInterval(() => load(true), 20000);
    return () => {
      mounted = false;
      clearInterval(id);
    };
  }, [t]);

  const recentOrdered = useMemo(() => [...recent].reverse(), [recent]);
  const lastUpdated = useMemo(() => recent[0]?.created_at ?? null, [recent]);
  const recentTotal = useMemo(
    () => recentOrdered.map((r) => r.total_ms ?? null),
    [recentOrdered]
  );
  const recentRag = useMemo(
    () => recentOrdered.map((r) => r.rag_ms ?? null),
    [recentOrdered]
  );
  const recentLlm = useMemo(
    () => recentOrdered.map((r) => r.llm_ms ?? null),
    [recentOrdered]
  );

  const totalSummary = useMemo(() => summarize(recentTotal), [recentTotal]);
  const ragSummary = useMemo(() => summarize(recentRag), [recentRag]);
  const llmSummary = useMemo(() => summarize(recentLlm), [recentLlm]);

  const recentBuckets = useMemo(() => {
    if (!recent.length) return [];
    const parsed = recent
      .map((r) => new Date(r.created_at))
      .filter((d) => !Number.isNaN(d.getTime()));
    if (!parsed.length) return [];
    const maxTs = Math.max(...parsed.map((d) => d.getTime()));
    const buckets = Array.from({ length: 8 }, () => 0);
    for (const d of parsed) {
      const diffHours = Math.floor((maxTs - d.getTime()) / (60 * 60 * 1000));
      if (diffHours >= 0 && diffHours < buckets.length) {
        buckets[buckets.length - 1 - diffHours] += 1;
      }
    }
    return buckets;
  }, [recent]);

  return (
    <div className="space-y-16">
      <section className="page-hero">
        <div className="container-app hero-inner">
          <div className="max-w-2xl space-y-3">
            <div className="hero-tag">{t("brand")}</div>
            <h1 className="hero-title font-semibold text-white">{t("dashboardTitle")}</h1>
            <p className="hero-subtitle text-white/80">{t("dashboardSubtitle")}</p>
            <div className="text-xs text-white/60">
              {t("dashboardUpdated")}: {lastUpdated ?? t("labelNA")}
            </div>
          </div>
        </div>
      </section>

      <section className="page-section">
        <div className="container-app space-y-6">
          {error ? (
            <div className="rounded-2xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-800">
              {error}
            </div>
          ) : null}

          <Card>
            <CardHeader title={t("dashboardStatsTitle")} subtitle={t("dashboardStatsSubtitle")} />
            <CardBody>
              {loading ? (
                <div className="text-sm text-muted">{t("loading")}</div>
              ) : stats ? (
                <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                  <div className="rounded-2xl border border-line bg-canvas/60 p-4">
                    <div className="text-xs font-semibold text-muted">{t("statsTotalSamples")}</div>
                    <div className="mt-2 text-2xl font-semibold text-ink">{stats.total_samples}</div>
                    <div className="mt-1 text-xs text-muted">
                      {t("dashboardRecentSamples")}: {recent.length}
                    </div>
                    {recentBuckets.length ? <MiniBars values={recentBuckets} /> : null}
                  </div>
                  <div className="rounded-2xl border border-line bg-canvas/60 p-4">
                    <div className="text-xs font-semibold text-muted">{t("statsCacheHitRate")}</div>
                    <div className="mt-2 flex items-center justify-between gap-3">
                      <div className="text-2xl font-semibold text-ink">
                        {(stats.cache_hit_rate * 100).toFixed(1)}%
                      </div>
                      <Donut value={stats.cache_hits} total={stats.total_samples} />
                    </div>
                    <div className="mt-2 flex items-center justify-between text-xs text-muted">
                      <span>
                        {t("dashboardCacheHits")}: {stats.cache_hits}
                      </span>
                      <span>
                        {t("dashboardCacheMisses")}: {stats.total_samples - stats.cache_hits}
                      </span>
                    </div>
                  </div>
                  <div className="rounded-2xl border border-line bg-canvas/60 p-4">
                    <div className="text-xs font-semibold text-muted">{t("statsAvgTotal")}</div>
                    <div className="mt-2 text-2xl font-semibold text-ink">
                      {stats.avg_total_ms ? Math.round(stats.avg_total_ms) : t("labelNA")}
                    </div>
                    <div className="mt-2 flex flex-wrap gap-3 text-xs text-muted">
                      <span>
                        {t("dashboardLast")}: {formatNumber(totalSummary?.last) ?? t("labelNA")}
                      </span>
                      <span>
                        {t("dashboardMin")}: {formatNumber(totalSummary?.min) ?? t("labelNA")}
                      </span>
                      <span>
                        {t("dashboardMax")}: {formatNumber(totalSummary?.max) ?? t("labelNA")}
                      </span>
                    </div>
                    <Sparkline values={recentTotal} />
                  </div>
                  <div className="rounded-2xl border border-line bg-canvas/60 p-4">
                    <div className="text-xs font-semibold text-muted">{t("statsAvgRag")}</div>
                    <div className="mt-2 text-2xl font-semibold text-ink">
                      {stats.avg_rag_ms ? Math.round(stats.avg_rag_ms) : t("labelNA")}
                    </div>
                    <div className="mt-2 flex flex-wrap gap-3 text-xs text-muted">
                      <span>
                        {t("dashboardLast")}: {formatNumber(ragSummary?.last) ?? t("labelNA")}
                      </span>
                      <span>
                        {t("dashboardMin")}: {formatNumber(ragSummary?.min) ?? t("labelNA")}
                      </span>
                      <span>
                        {t("dashboardMax")}: {formatNumber(ragSummary?.max) ?? t("labelNA")}
                      </span>
                    </div>
                    <Sparkline values={recentRag} />
                  </div>
                  <div className="rounded-2xl border border-line bg-canvas/60 p-4">
                    <div className="text-xs font-semibold text-muted">{t("statsAvgLlm")}</div>
                    <div className="mt-2 text-2xl font-semibold text-ink">
                      {stats.avg_llm_ms ? Math.round(stats.avg_llm_ms) : t("labelNA")}
                    </div>
                    <div className="mt-2 flex flex-wrap gap-3 text-xs text-muted">
                      <span>
                        {t("dashboardLast")}: {formatNumber(llmSummary?.last) ?? t("labelNA")}
                      </span>
                      <span>
                        {t("dashboardMin")}: {formatNumber(llmSummary?.min) ?? t("labelNA")}
                      </span>
                      <span>
                        {t("dashboardMax")}: {formatNumber(llmSummary?.max) ?? t("labelNA")}
                      </span>
                    </div>
                    <Sparkline values={recentLlm} />
                  </div>
                  <div className="rounded-2xl border border-line bg-canvas/60 p-4">
                    <div className="text-xs font-semibold text-muted">
                      {t("dashboardLatencySummary")}
                    </div>
                    <div className="mt-2 text-2xl font-semibold text-ink">
                      {formatNumber(totalSummary?.avg) ?? t("labelNA")}
                    </div>
                    <div className="mt-1 text-xs text-muted">
                      {t("dashboardAvgLabel")} {t("unitMs")}
                    </div>
                    <div className="mt-3 grid gap-2 text-xs text-muted">
                      <div>
                        {t("statsAvgRag")}: {formatNumber(ragSummary?.avg) ?? t("labelNA")}
                      </div>
                      <div>
                        {t("statsAvgLlm")}: {formatNumber(llmSummary?.avg) ?? t("labelNA")}
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-sm text-muted">{t("dashboardNoStats")}</div>
              )}
            </CardBody>
          </Card>
        </div>
      </section>
    </div>
  );
}
