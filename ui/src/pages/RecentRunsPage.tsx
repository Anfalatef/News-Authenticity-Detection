import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, type EvalRecentItem } from "../api";
import { Badge } from "../components/Badge";
import { Card, CardBody, CardHeader } from "../components/StatCard";
import { formatVeracityLabel } from "../lib/formatters";
import { useLanguage } from "../lib/i18n";

export function RecentRunsPage() {
  const { t } = useLanguage();
  const [runs, setRuns] = useState<EvalRecentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    (async () => {
      setLoading(true);
      try {
        const res = await api.evalRecent(50);
        if (mounted) setRuns(res.items ?? []);
      } catch (err: any) {
        if (mounted) setError(err?.message ?? t("error"));
      } finally {
        if (mounted) setLoading(false);
      }
    })();
    return () => {
      mounted = false;
    };
  }, [t]);

  return (
    <div className="space-y-16">
      <section className="page-hero">
        <div className="container-app hero-inner">
          <div className="max-w-2xl space-y-3">
            <div className="hero-tag">{t("brand")}</div>
            <h1 className="hero-title font-semibold text-white">{t("recentTitle")}</h1>
            <p className="hero-subtitle text-white/80">{t("recentSubtitle")}</p>
          </div>
        </div>
      </section>

      <section className="page-section -mt-32 p-0">
        <div className="container-app space-y-6">
          {error ? (
            <div className="rounded-2xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-800">
              {error}
            </div>
          ) : null}

          <Card>
            <CardHeader title={t("recentLatestRunsTitle")} subtitle={t("recentLatestRunsSubtitle")} />
            <CardBody>
              {loading ? (
                <div className="text-sm text-muted">{t("loading")}</div>
              ) : runs.length ? (
                <div className="overflow-hidden rounded-2xl border border-line bg-white/90">
                  <table className="w-full text-left text-sm">
                    <thead className="bg-canvas/80 text-xs uppercase text-muted">
                      <tr>
                        <th className="px-4 py-3">{t("recentTableCreated")}</th>
                        <th className="px-4 py-3">{t("recentTableText")}</th>
                        <th className="px-4 py-3">{t("recentTableModel")}</th>
                        <th className="px-4 py-3">{t("recentTableVeracity")}</th>
                        <th className="px-4 py-3">{t("recentTableCache")}</th>
                        <th className="px-4 py-3">{t("recentTableTotalMs")}</th>
                        <th className="px-4 py-3">{t("recentTableActions")}</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-line bg-white">
                      {runs.map((run) => (
                        <tr key={run.id} className="hover:bg-canvas/50">
                          <td className="px-4 py-3 text-xs text-muted">{run.created_at}</td>
                          <td className="px-4 py-3">
                            <div className="max-w-xs truncate text-sm text-ink" title={run.text}>
                              {run.text}
                            </div>
                            <div className="text-xs text-muted">{run.text_hash}</div>
                          </td>
                          <td className="px-4 py-3 text-xs text-muted">{run.model}</td>
                          <td className="px-4 py-3">
                            <Badge
                              label={`${formatVeracityLabel(run.veracity_label, t)} ${
                                run.veracity_confidence ? `(${run.veracity_confidence})` : ""
                              }`}
                              tone={
                                String(run.veracity_label ?? "").toLowerCase() === "fake"
                                  ? "bad"
                                  : "good"
                              }
                            />
                          </td>
                          <td className="px-4 py-3">
                            <Badge
                              label={run.cache_hit ? t("labelCacheHit") : t("labelCacheMiss")}
                              tone={run.cache_hit ? "neutral" : "warn"}
                            />
                          </td>
                          <td className="px-4 py-3 text-xs text-muted">
                            {run.total_ms ?? t("labelNA")}
                          </td>
                          <td className="px-4 py-3">
                            <div className="flex flex-wrap gap-2 text-xs font-semibold">
                              <Link
                                to={`/runs/${run.id}`}
                                state={{ run }}
                                className="text-brand-700 hover:underline"
                              >
                                {t("recentActionsDetails")}
                              </Link>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="text-sm text-muted">{t("recentNoRuns")}</div>
              )}
            </CardBody>
          </Card>
        </div>
      </section>
    </div>
  );
}
