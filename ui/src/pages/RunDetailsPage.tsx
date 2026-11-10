import { useEffect, useMemo, useState } from "react";
import { useLocation, useParams } from "react-router-dom";
import { api, type EvalRecentItem } from "../api";
import { Badge } from "../components/Badge";
import { Card, CardBody, CardHeader } from "../components/StatCard";
import { JsonBlock } from "../components/JsonBlock";
import { formatVeracityLabel, formatYesNo } from "../lib/formatters";
import { useLanguage } from "../lib/i18n";

type LocationState = {
  run?: EvalRecentItem;
};

function safeParseJson(value: unknown) {
  if (!value) return null;
  if (typeof value === "object") {
    const maybeText = (value as { text?: unknown }).text;
    if (typeof maybeText === "string") {
      return safeParseJson(maybeText);
    }
    return value;
  }
  if (typeof value !== "string") return null;
  const match = value.match(/```(?:json)?\s*([\s\S]*?)\s*```/i);
  const raw = (match?.[1] ?? value).trim();
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

export function RunDetailsPage() {
  const { t } = useLanguage();
  const { runId } = useParams();
  const location = useLocation();
  const state = location.state as LocationState | null;
  const [run, setRun] = useState<EvalRecentItem | null>(state?.run ?? null);
  const [loading, setLoading] = useState(!state?.run);
  const [error, setError] = useState<string | null>(null);
  const [showRaw, setShowRaw] = useState(false);

  const runIdNumber = useMemo(() => Number(runId), [runId]);

  useEffect(() => {
    if (state?.run) return;
    if (!runIdNumber) return;
    let mounted = true;
    (async () => {
      setLoading(true);
      try {
        const res = await api.evalRecent(200);
        const match = res.items.find((item) => item.id === runIdNumber) ?? null;
        if (mounted) setRun(match);
        if (mounted && !match) setError(t("runDetailsNotFoundRecent"));
      } catch (err: any) {
        if (mounted) setError(err?.message ?? t("error"));
      } finally {
        if (mounted) setLoading(false);
      }
    })();
    return () => {
      mounted = false;
    };
  }, [runIdNumber, state?.run, t]);

  const evidence = run?.retrieved ?? [];
  const response = run?.response as { bias?: unknown } | undefined;
  const parsedBias = useMemo(() => safeParseJson(response?.bias), [response]);
  const biasTypes = Array.isArray((parsedBias as any)?.types) ? (parsedBias as any).types : [];
  const biasQuotes = Array.isArray((parsedBias as any)?.quotes) ? (parsedBias as any).quotes : [];

  return (
    <div className="space-y-16">
      <section className="page-hero">
        <div className="container-app hero-inner">
          <div className="max-w-2xl space-y-3">
            <div className="hero-tag">{t("brand")}</div>
            <h1 className="hero-title font-semibold text-white">{t("runDetailsTitle")}</h1>
            <p className="hero-subtitle text-white/80">{t("runDetailsSubtitle")}</p>
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

          {loading ? (
            <div className="surface p-6 text-sm text-muted">{t("loading")}</div>
          ) : run ? (
            <div className="grid gap-6 lg:grid-cols-12">
              <div className="space-y-6 lg:col-span-8">
                <Card>
                  <CardHeader
                    title={t("runDetailsRunSummaryTitle")}
                    subtitle={`${t("runDetailsRunSummarySubtitle")} ${run.id}`}
                  />
                  <CardBody>
                    <div className="space-y-3 text-sm text-ink/90">
                      <div>
                        <div className="text-xs font-semibold uppercase text-muted">
                          {t("runDetailsTextLabel")}
                        </div>
                        <div className="mt-1 rounded-2xl border border-line bg-canvas/60 p-3">
                          {run.text}
                        </div>
                      </div>
                      <div className="grid gap-3 md:grid-cols-2">
                        <div className="rounded-2xl border border-line bg-white p-3">
                          <div className="text-xs font-semibold text-muted">
                            {t("runDetailsCreatedAt")}
                          </div>
                          <div className="mt-1 text-sm text-ink/90">{run.created_at}</div>
                        </div>
                        <div className="rounded-2xl border border-line bg-white p-3">
                          <div className="text-xs font-semibold text-muted">
                            {t("runDetailsModel")}
                          </div>
                          <div className="mt-1 text-sm text-ink/90">{run.model}</div>
                        </div>
                        <div className="rounded-2xl border border-line bg-white p-3">
                          <div className="text-xs font-semibold text-muted">
                            {t("runDetailsPromptVersion")}
                          </div>
                          <div className="mt-1 text-sm text-ink/90">{run.prompt_version}</div>
                        </div>
                        <div className="rounded-2xl border border-line bg-white p-3">
                          <div className="text-xs font-semibold text-muted">
                            {t("runDetailsPipelineVersion")}
                          </div>
                          <div className="mt-1 text-sm text-ink/90">{run.pipeline_version}</div>
                        </div>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        <Badge
                          label={`${t("labelVeracity")}: ${formatVeracityLabel(
                            run.veracity_label,
                            t
                          )}`}
                          tone={String(run.veracity_label ?? "").toLowerCase() === "fake" ? "bad" : "good"}
                        />
                        <Badge
                          label={`${t("labelConfidence")}: ${run.veracity_confidence ?? t("labelNA")}`}
                          tone="neutral"
                        />
                        <Badge
                          label={`${t("labelBias")}: ${formatYesNo(run.bias_has_bias, t)}`}
                          tone={run.bias_has_bias ? "warn" : "good"}
                        />
                        <Badge
                          label={`${t("labelSeverity")}: ${run.bias_severity ?? t("labelNA")}`}
                          tone="neutral"
                        />
                      </div>

                      {parsedBias ? (
                        <div className="mt-4 rounded-2xl border border-line bg-canvas/60 p-4">
                          <div className="text-xs font-semibold text-muted">
                            {t("analyzeBiasReasons")}
                          </div>
                          <div className="mt-3 grid gap-3 md:grid-cols-2">
                            <div>
                              <div className="text-xs font-semibold text-muted">
                                {t("analyzeBiasTypes")}
                              </div>
                              {biasTypes.length ? (
                                <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-ink/90">
                                  {biasTypes.map((item: string, index: number) => (
                                    <li key={index}>{item}</li>
                                  ))}
                                </ul>
                              ) : (
                                <div className="mt-2 text-sm text-muted">
                                  {t("analyzeBiasTypesEmpty")}
                                </div>
                              )}
                            </div>
                            <div>
                              <div className="text-xs font-semibold text-muted">
                                {t("analyzeBiasQuotes")}
                              </div>
                              {biasQuotes.length ? (
                                <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-ink/90">
                                  {biasQuotes.map((item: string, index: number) => (
                                    <li key={index}>{item}</li>
                                  ))}
                                </ul>
                              ) : (
                                <div className="mt-2 text-sm text-muted">
                                  {t("analyzeBiasQuotesEmpty")}
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      ) : null}
                    </div>
                  </CardBody>
                </Card>

                <Card>
                  <CardHeader
                    title={t("runDetailsEvidenceTitle")}
                    subtitle={t("runDetailsEvidenceSubtitle")}
                  />
                  <CardBody>
                    {evidence.length ? (
                      <div className="space-y-3">
                        {evidence.map((item, index) => (
                          <div key={index} className="rounded-2xl border border-line bg-canvas/60 p-4">
                            <div className="flex flex-wrap items-center justify-between gap-2">
                              <div className="text-sm font-semibold text-ink">
                                {item.title || `${t("analyzeEvidenceItemFallback")} ${index + 1}`}
                              </div>
                              <div className="text-xs text-muted">
                                {t("labelScore")}:{" "}
                                {typeof item.score === "number" ? item.score.toFixed(3) : t("labelNA")}
                              </div>
                            </div>
                            {item.url ? (
                              <a
                                className="mt-1 block truncate text-xs font-medium text-brand-700 hover:underline"
                                href={item.url}
                                target="_blank"
                                rel="noreferrer"
                              >
                                {item.url}
                              </a>
                            ) : null}
                            <p className="mt-2 text-sm text-ink/80">{item.chunk_text ?? ""}</p>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="text-sm text-muted">{t("runDetailsNoEvidence")}</div>
                    )}
                  </CardBody>
                </Card>
              </div>

              <div className="space-y-6 lg:col-span-4">
                <Card>
                  <CardHeader
                    title={t("runDetailsTimingTitle")}
                    subtitle={t("runDetailsTimingSubtitle")}
                  />
                  <CardBody>
                    <div className="grid gap-3 text-sm">
                      <div className="rounded-2xl border border-line bg-white p-3">
                        <div className="text-xs font-semibold text-muted">{t("runDetailsTotalMs")}</div>
                        <div className="mt-1 text-sm text-ink/90">{run.total_ms ?? t("labelNA")}</div>
                      </div>
                      <div className="rounded-2xl border border-line bg-white p-3">
                        <div className="text-xs font-semibold text-muted">{t("runDetailsRagMs")}</div>
                        <div className="mt-1 text-sm text-ink/90">{run.rag_ms ?? t("labelNA")}</div>
                      </div>
                      <div className="rounded-2xl border border-line bg-white p-3">
                        <div className="text-xs font-semibold text-muted">{t("runDetailsLlmMs")}</div>
                        <div className="mt-1 text-sm text-ink/90">{run.llm_ms ?? t("labelNA")}</div>
                      </div>
                    </div>
                  </CardBody>
                </Card>

                <Card>
                  <CardHeader
                    title={t("runDetailsRawJsonTitle")}
                    subtitle={t("runDetailsRawJsonSubtitle")}
                  />
                  <CardBody>
                    <button
                      onClick={() => setShowRaw((prev) => !prev)}
                      className="rounded-full border border-line bg-white px-4 py-2 text-sm font-semibold text-ink/80 hover:bg-canvas"
                    >
                      {showRaw ? t("runDetailsHideRaw") : t("runDetailsShowRaw")}
                    </button>
                    {showRaw ? (
                      <div className="mt-4">
                        <JsonBlock title={t("runDetailsRawJsonTitle")} value={run} />
                      </div>
                    ) : null}
                  </CardBody>
                </Card>
              </div>
            </div>
          ) : (
            <div className="surface p-6 text-sm text-muted">{t("runDetailsNotFound")}</div>
          )}
        </div>
      </section>
    </div>
  );
}
