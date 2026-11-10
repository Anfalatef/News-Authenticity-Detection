import { Link } from "react-router-dom";
import { Card, CardBody } from "../components/StatCard";
import { useLanguage } from "../lib/i18n";

export function HomePage() {
  const { t } = useLanguage();

  return (
    <div className="space-y-16">
      <section className="page-hero">
        <div className="container-app grid gap-8 lg:grid-cols-[1.1fr_0.9fr]">
          <div className="mx-auto max-w-2xl space-y-4 lg:mx-0 lg:pl-16">
            <div className="hero-tag">{t("tagline")}</div>
            <h1 className="text-3xl font-semibold text-white md:text-4xl">{t("homeTitle")}</h1>
            <p className="max-w-lg text-sm text-white/80">{t("homeSubtitle")}</p>

            <div className="flex flex-wrap gap-3">
              <Link
                to="/analyze"
                className="cta-glow rounded-full px-5 py-2 text-sm font-semibold text-white transition hover:opacity-90"
              >
                {t("navAnalyze")}
              </Link>
              <Link
                to="/dashboard"
                className="rounded-full border border-white/30 bg-white/10 px-5 py-2 text-sm font-semibold text-white/80 hover:bg-white/20"
              >
                {t("navDashboard")}
              </Link>
            </div>
          </div>

          <div className="hero-panel mx-auto max-w-sm space-y-3 lg:mx-0 lg:-ml-5">
            <div className="rounded-3xl border border-white/20 bg-white/10 p-4">
              <div className="text-[11px] font-semibold uppercase tracking-wide text-white/70">
                {t("homeFeatureEvidenceTitle")}
              </div>
              <p className="mt-1 text-sm text-white/80">{t("homeFeatureEvidenceBody")}</p>
            </div>
            <div className="rounded-3xl border border-white/20 bg-white/10 p-4">
              <div className="text-[11px] font-semibold uppercase tracking-wide text-white/70">
                {t("homeFeatureEvalTitle")}
              </div>
              <p className="mt-1 text-sm text-white/80">{t("homeFeatureEvalBody")}</p>
              </div>
          </div>
        </div>
      </section>

      <section className="page-section -mt-64 pt-0 pb-16">
        <div className="container-app flex justify-center">
          <div className="grid w-full max-w-5xl gap-5 md:grid-cols-3 lg:pl-12">
          <Card className="surface-muted">
            <CardBody className="p-0">
              <div className="text-xs font-semibold uppercase tracking-wide text-muted">
                {t("homeCardAnalyzeLabel")}
              </div>
              <div className="mt-1 text-base font-semibold text-ink">{t("homeCardAnalyzeTitle")}</div>
              <p className="mt-1 text-sm text-muted">{t("homeCardAnalyzeBody")}</p>
            </CardBody>
          </Card>
          <Card className="surface-muted">
            <CardBody className="p-0">
              <div className="text-xs font-semibold uppercase tracking-wide text-muted">
                {t("homeCardDashboardLabel")}
              </div>
              <div className="mt-1 text-base font-semibold text-ink">
                {t("homeCardDashboardTitle")}
              </div>
              <p className="mt-1 text-sm text-muted">{t("homeCardDashboardBody")}</p>
            </CardBody>
          </Card>
          <Card className="surface-muted">
            <CardBody className="p-0">
              <div className="text-xs font-semibold uppercase tracking-wide text-muted">
                {t("homeCardRecentLabel")}
              </div>
              <div className="mt-1 text-base font-semibold text-ink">{t("homeCardRecentTitle")}</div>
              <p className="mt-1 text-sm text-muted">{t("homeCardRecentBody")}</p>
            </CardBody>
          </Card>
          </div>
        </div>
      </section>
    </div>
  );
}
