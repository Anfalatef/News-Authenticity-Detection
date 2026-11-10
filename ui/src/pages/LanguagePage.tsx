import { useLanguage } from "../lib/i18n";
import { Card, CardBody } from "../components/StatCard";

export function LanguagePage() {
  const { language, setLanguage, t } = useLanguage();

  return (
    <div className="space-y-16">
      <section className="page-hero">
        <div className="container-app hero-inner">
          <div className="max-w-2xl space-y-3">
            <div className="hero-tag">{t("brand")}</div>
            <h1 className="hero-title font-semibold text-white">{t("languageTitle")}</h1>
            <p className="hero-subtitle text-white/80">{t("languageSubtitle")}</p>
          </div>
        </div>
      </section>

      <section className="page-section">
        <div className="container-app">
          <Card>
            <CardBody>
              <div className="grid gap-4 md:grid-cols-2">
                <button
                  onClick={() => setLanguage("en")}
                  className={`rounded-2xl border px-5 py-4 text-left transition ${
                    language === "en"
                      ? "border-brand-500 bg-brand-100 text-ink shadow-soft"
                      : "border-line bg-white text-ink/80 hover:bg-canvas"
                  } focus:outline-none focus:ring-0 focus:ring-transparent`}
                >
                  <div className="text-sm font-semibold">{t("languageEnglish")}</div>
                  <p className="mt-1 text-xs text-muted">{t("languageEnglishHint")}</p>
                </button>

                <button
                  onClick={() => setLanguage("ar")}
                  className={`rounded-2xl border px-5 py-4 text-left transition ${
                    language === "ar"
                      ? "border-brand-500 bg-brand-100 text-ink shadow-soft"
                      : "border-line bg-white text-ink/80 hover:bg-canvas"
                  } focus:outline-none focus:ring-0 focus:ring-transparent`}
                >
                  <div className="text-sm font-semibold">{t("languageArabic")}</div>
                  <p className="mt-1 text-xs text-muted">{t("languageArabicHint")}</p>
                </button>
              </div>
            </CardBody>
          </Card>
        </div>
      </section>
    </div>
  );
}
