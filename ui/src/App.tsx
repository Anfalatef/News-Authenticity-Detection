import { Routes, Route } from "react-router-dom";
import { Layout } from "./components/Layout";
import { AnalyzePage } from "./pages/AnalyzePage";
import { DashboardPage } from "./pages/DashboardPage";
import { HomePage } from "./pages/HomePage";
import { LanguagePage } from "./pages/LanguagePage";
import { RecentRunsPage } from "./pages/RecentRunsPage";
import { RunDetailsPage } from "./pages/RunDetailsPage";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<HomePage />} />
        <Route path="/analyze" element={<AnalyzePage />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/recent" element={<RecentRunsPage />} />
        <Route path="/runs/:runId" element={<RunDetailsPage />} />
        <Route path="/language" element={<LanguagePage />} />
      </Route>
    </Routes>
  );
}
