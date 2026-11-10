import { Link, NavLink, Outlet } from "react-router-dom";
import { useLanguage } from "../lib/i18n";

function NavItem({ to, label }: { to: string; label: string }) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        `rounded-full px-3 py-2 text-sm font-semibold transition-colors ${
          isActive
            ? "bg-white/20 text-white shadow-soft"
            : "text-white/80 hover:bg-white/10"
        }`
      }
    >
      {label}
    </NavLink>
  );
}

export function Layout() {
  const { t, dir } = useLanguage();

  return (
    <div className="app-shell" dir={dir}>
      <header className="app-header sticky top-0 z-30">
        <div className="container-app header-inner relative z-10 flex h-[100px] items-center justify-between">
          <Link to="/" className="flex items-center gap-0">
            <div className="logo-mark">
              <img
                src="/bayyen.png"
                alt="Bayyen logo"
                className="h-[108px] w-auto rounded-2xl object-contain"
              />
            </div>
            <div className="-ml-4 leading-tight">
              <div className="text-base font-semibold text-white">{t("brand")}</div>
            </div>
          </Link>

          <nav className="nav-glass hidden items-center gap-1 p-1 text-sm md:flex">
            <NavItem to="/" label={t("navHome")} />
            <NavItem to="/analyze" label={t("navAnalyze")} />
            <NavItem to="/dashboard" label={t("navDashboard")} />
            <NavItem to="/recent" label={t("navRecent")} />
            <NavItem to="/language" label={t("navLanguage")} />
          </nav>

          <a
            href="http://127.0.0.1:8000/docs"
            target="_blank"
            rel="noreferrer"
            className="cta-glow rounded-full px-4 py-2 text-sm font-semibold text-white transition hover:opacity-90"
          >
            {t("ctaDocs")}
          </a>
        </div>
          <div className="container-app header-inner pb-4 md:hidden">
            <nav className="nav-glass flex gap-2 overflow-x-auto p-1 text-xs font-semibold">
            <NavItem to="/" label={t("navHome")} />
            <NavItem to="/analyze" label={t("navAnalyze")} />
            <NavItem to="/dashboard" label={t("navDashboard")} />
            <NavItem to="/recent" label={t("navRecent")} />
            <NavItem to="/language" label={t("navLanguage")} />
          </nav>
        </div>
      </header>

      <main className="page-main">
        <Outlet />
      </main>

      <footer className="app-footer">
        <div className="container-app footer-inner grid gap-6 py-4 md:grid-cols-3">
          <div className="space-y-2">
            <div className="flex items-center gap-0">
              <div className="logo-mark">
                <img
                  src="/bayyen.png"
                  alt="Bayyen logo"
                  className="h-[108px] w-auto rounded-2xl object-contain"
                />
              </div>
              <div className="-ml-4">
                <div className="brand-strong text-base font-semibold">{t("brand")}</div>
              </div>
            </div>
            <p className="relative -top-7 text-sm text-white/70">{t("footerNote")}</p>
          </div>
          <div className="space-y-2 text-sm text-white/70 md:col-span-2 md:pt-10 md:text-center">
            <div className="font-semibold">{t("footerBuildNote")}</div>
            <div className="font-semibold">{t("footerTipBackend")}</div>
          </div>
        </div>
      </footer>
    </div>
  );
}
