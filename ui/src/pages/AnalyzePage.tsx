import { useMemo, useState } from "react";
import { api, type AnalyzeResponse } from "../api";
import { Badge } from "../components/Badge";
import { Card, CardBody, CardHeader } from "../components/StatCard";
import { formatVeracityLabel, formatYesNo } from "../lib/formatters";
import { useLanguage } from "../lib/i18n";

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

function dedupeEvidence(items: AnalyzeResponse["retrieved"]) {
  const seen = new Set<string>();
  const out: AnalyzeResponse["retrieved"] = [];

  for (const item of items) {
    const url = (item.url ?? "").trim();
    const key = url || `${item.source ?? ""}|${item.title ?? ""}|${item.chunk_text ?? ""}`;
    if (seen.has(key)) continue;
    seen.add(key);
    out.push(item);
  }

  return out;
}

export function AnalyzePage() {
  const { t, language } = useLanguage();
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<AnalyzeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showAllEvidence, setShowAllEvidence] = useState(false);

  const parsed = useMemo(() => {
    if (!data) return { veracity: null as any, bias: null as any };
    return {
      veracity: safeParseJson(
        typeof data.veracity === "object" ? data.veracity : String(data.veracity ?? "")
      ),
      bias: safeParseJson(typeof data.bias === "object" ? data.bias : String(data.bias ?? "")),
    };
  }, [data]);

  async function onAnalyze() {
    const trimmed = text.trim();
    setError(null);
    setData(null);
    setShowAllEvidence(false);

    if (!trimmed) {
      setError(t("analyzeErrorEmpty"));
      return;
    }

    setLoading(true);
    try {
      const res = await api.analyze(trimmed, language);
      setData(res);
    } catch (err: any) {
      setError(err?.message ?? t("error"));
    } finally {
      setLoading(false);
    }
  }

  const labelTone =
    String(parsed.veracity?.label ?? "").toLowerCase() === "real"
      ? "good"
      : String(parsed.veracity?.label ?? "").toLowerCase() === "fake"
        ? "bad"
        : parsed.veracity?.label
          ? "warn"
          : "neutral";

  const biasTypes = Array.isArray(parsed.bias?.types) ? parsed.bias.types : [];
  const biasQuotes = Array.isArray(parsed.bias?.quotes) ? parsed.bias.quotes : [];

  const evidenceList = useMemo(() => dedupeEvidence(data?.retrieved ?? []), [data]);
  const topEvidence = evidenceList[0];

  return (
    <div className="space-y-8">
      <section className="page-hero">
        <div className="container-app hero-inner grid gap-12 lg:grid-cols-[1fr_1fr]">
          <div className="space-y-6">
            <div className="hero-tag">{t("brand")}</div>
            <h1 className="hero-title font-semibold text-white">{t("analyzeTitle")}</h1>
            <p className="hero-subtitle max-w-xl text-white/80">{t("analyzeSubtitle")}</p>

            <div className="mt-6 grid gap-3 sm:grid-cols-3">
              <div className="rounded-2xl border border-white/20 bg-white/10 p-3 text-xs text-white/80">
                {t("analyzeHintVeracity")}
              </div>
              <div className="rounded-2xl border border-white/20 bg-white/10 p-3 text-xs text-white/80">
                {t("analyzeHintBias")}
              </div>
              <div className="rounded-2xl border border-white/20 bg-white/10 p-3 text-xs text-white/80">
                {t("analyzeHintEvidence")}
              </div>
            </div>
          </div>

          <div className="hero-panel max-w-md bg-white/95 text-ink shadow-soft lg:-ml-4">
            <div className="surface-muted p-5">
              <label className="text-xs font-semibold uppercase tracking-wide text-muted">
                {t("analyzeInputLabel")}
              </label>
              <textarea
                value={text}
                onChange={(event) => setText(event.target.value)}
                rows={9}
                className="mt-2 w-full resize-none rounded-2xl border border-line bg-white p-4 text-sm text-ink outline-none focus:border-brand-200 focus:ring-0 focus:ring-transparent"
                placeholder={t("analyzePlaceholder")}
              />

              <div className="mt-4 flex flex-wrap items-center gap-3">
                <button
                  onClick={onAnalyze}
                  disabled={loading}
                  className="cta-glow inline-flex items-center justify-center rounded-full px-5 py-2 text-sm font-semibold text-white transition hover:opacity-90 disabled:opacity-60"
                >
                  {loading ? t("loading") : t("analyzeButton")}
                </button>
                <button
                  onClick={() => {
                    setText("");
                    setData(null);
                    setError(null);
                  }}
                  className="rounded-full border border-line bg-white px-4 py-2 text-sm font-semibold text-ink/80 hover:bg-canvas"
                >
                  {t("clearButton")}
                </button>
                {data?._cache?.hit ? <Badge label={t("analyzeCacheHit")} tone="neutral" /> : null}
                {data?._fallback?.used_cse ? (
                  <Badge label={t("analyzeWebFallback")} tone="warn" />
                ) : null}
              </div>

              {error ? (
                <div className="mt-4 rounded-2xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-800">
                  {error}
                </div>
              ) : null}
            </div>
          </div>
        </div>
      </section>

      <section className="page-section pt-0">
        <div className="container-app grid gap-5 lg:grid-cols-12 lg:pl-6">
          <div className="order-2 space-y-5 lg:order-1 lg:col-span-8">
            {loading ? (
              <div className="surface p-6 text-sm text-muted">{t("analyzeLoadingMessage")}</div>
            ) : null}

            {data ? (
              <>
                <Card className="overflow-hidden text-[13px]">
                  <CardHeader
                    title={t("analyzeResultsTitle")}
                    subtitle={t("analyzeResultsSubtitle")}
                  />
                  <CardBody>
                    <div className="flex flex-wrap items-center gap-2">
                      <Badge
                        label={`${t("labelVeracity")}: ${formatVeracityLabel(
                          parsed.veracity?.label,
                          t
                        )}`}
                        tone={labelTone as any}
                      />
                      <Badge
                        label={`${t("labelConfidence")}: ${
                          parsed.veracity?.confidence ?? t("labelNA")
                        }`}
                      />
                      <Badge
                        label={`${t("labelBias")}: ${formatYesNo(parsed.bias?.has_bias, t)}`}
                        tone={parsed.bias?.has_bias ? "warn" : "good"}
                      />
                      <Badge
                        label={`${t("labelSeverity")}: ${parsed.bias?.severity ?? t("labelNA")}`}
                      />
                    </div>

                    <div className="mt-3 grid gap-3 md:grid-cols-2">
                      <div className="rounded-2xl border border-line bg-canvas/60 p-4">
                        <div className="text-xs font-semibold text-muted">
                          {t("analyzeVeracityReasons")}
                        </div>
                        <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-ink/90">
                          {(parsed.veracity?.reasons ?? []).map(
                            (reason: string, index: number) => (
                              <li key={index}>{reason}</li>
                            )
                          )}
                        </ul>
                      </div>

                      <div className="rounded-2xl border border-line bg-canvas/60 p-4">
                        <div className="text-xs font-semibold text-muted">
                          {t("analyzeNeutralRewrite")}
                        </div>
                        <p className="mt-2 text-sm text-ink/90">
                          {parsed.bias?.neutral_rewrite ?? t("labelNA")}
                        </p>
                      </div>
                    </div>

                    <div className="mt-3 rounded-2xl border border-line bg-canvas/60 p-4">
                      <div className="text-xs font-semibold text-muted">
                        {t("analyzeBiasReasons")}
                      </div>
                      <div className="mt-2 grid gap-3 md:grid-cols-2">
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
                  </CardBody>
                </Card>

                <Card className="overflow-hidden text-[13px]">
                  <CardHeader
                    title={t("analyzeEvidenceTitle")}
                    subtitle={t("analyzeEvidenceSubtitle")}
                  />
                  <CardBody>
                    {topEvidence ? (
                    <div className="rounded-2xl border border-line bg-canvas/60 p-4">
                        <div className="flex flex-wrap items-center justify-between gap-2">
                          <div className="text-sm font-semibold text-ink">
                            {topEvidence.title || t("analyzeTopEvidenceFallback")}
                          </div>
                          <div className="text-xs text-muted">
                            {t("labelScore")}:{" "}
                            {typeof topEvidence.score === "number"
                              ? topEvidence.score.toFixed(3)
                              : t("labelNA")}
                          </div>
                        </div>
                        {topEvidence.url ? (
                          <a
                            className="mt-1 block truncate text-xs font-medium text-brand-700 hover:underline"
                            href={topEvidence.url}
                            target="_blank"
                            rel="noreferrer"
                          >
                            {topEvidence.url}
                          </a>
                        ) : null}
                        <p className="mt-2 text-sm text-ink/80">{topEvidence.chunk_text ?? ""}</p>
                      </div>
                    ) : (
                      <div className="text-sm text-muted">{t("analyzeNoEvidence")}</div>
                    )}

                    {evidenceList.length > 1 ? (
                    <div className="mt-3">
                        <button
                          onClick={() => setShowAllEvidence((prev) => !prev)}
                          className="rounded-full border border-line bg-white px-4 py-2 text-sm font-semibold text-ink/80 hover:bg-canvas"
                        >
                          {showAllEvidence
                            ? t("analyzeHideAllEvidence")
                            : t("analyzeShowAllEvidence")}
                        </button>
                      </div>
                    ) : null}

                    {showAllEvidence ? (
                    <div className="mt-3 space-y-3">
                        {evidenceList.map((item, index) => (
                        <div key={index} className="rounded-2xl border border-line bg-white p-4">
                            <div className="flex flex-wrap items-center justify-between gap-2">
                              <div className="text-sm font-semibold text-ink">
                                {item.title || `${t("analyzeEvidenceItemFallback")} ${index + 1}`}
                              </div>
                              <div className="text-xs text-muted">
                                {t("labelScore")}:{" "}
                                {typeof item.score === "number"
                                  ? item.score.toFixed(3)
                                  : t("labelNA")}
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
                    ) : null}
                  </CardBody>
                </Card>
              </>
            ) : (
              <div className="surface p-6 text-sm text-muted">{t("analyzeSubtitle")}</div>
            )}
          </div>

          <div className="order-1 lg:order-2 lg:col-span-4">
            <Card>
              <CardHeader
                title={t("analyzeTelemetryTitle")}
                subtitle={t("analyzeTelemetrySubtitle")}
              />
              <CardBody>
                <div className="grid gap-3">
                  <div className="rounded-2xl border border-line bg-canvas/60 p-3">
                    <div className="text-xs font-semibold text-muted">{t("analyzeTimingTitle")}</div>
                    <div className="mt-1 text-sm text-ink/90">
                      {t("analyzeTimingRag")}: {data?._timing?.rag_ms ?? t("labelNA")}{" "}
                      {t("unitMs")} | {t("analyzeTimingWeb")}:{" "}
                      {data?._timing?.web_ms ?? t("labelNA")} {t("unitMs")} |{" "}
                      {t("analyzeTimingLlm")}: {data?._timing?.llm_ms ?? t("labelNA")} {t("unitMs")}
                    </div>
                  </div>

                  <div className="rounded-2xl border border-line bg-canvas/60 p-3">
                    <div className="text-xs font-semibold text-muted">
                      {t("analyzeVersionsTitle")}
                    </div>
                    <div className="mt-1 text-sm text-ink/90">
                      {t("analyzePromptVersion")}: {data?.prompt_version ?? t("labelNA")} |{" "}
                      {t("analyzePipelineVersion")}: {data?.pipeline_version ?? t("labelNA")}
                    </div>
                  </div>

                  <div className="rounded-2xl border border-line bg-canvas/60 p-3">
                    <div className="text-xs font-semibold text-muted">
                      {t("analyzeCacheKeyTitle")}
                    </div>
                    <div className="mt-1 break-all text-xs text-ink/80">
                      {data?._cache?.key ?? t("labelNA")}
                    </div>
                  </div>

                  <div className="rounded-2xl border border-telemetry-border bg-telemetry-bg p-3 text-xs text-telemetry-text">
                    {t("analyzeTelemetryNote")}
                  </div>
                </div>
              </CardBody>
            </Card>
          </div>
        </div>
      </section>
    </div>
  );
}
