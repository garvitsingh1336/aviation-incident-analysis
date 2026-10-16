import { useState, useEffect, useCallback } from "react";
import { api } from "./api.js";
import { useApi } from "./lib/useApi.js";
import { AppContext } from "./appContext.js";
import Icon from "./components/Icon.jsx";
import ReportDetail from "./views/ReportDetail.jsx";

import Overview from "./views/Overview.jsx";
import Topics from "./views/Topics.jsx";
import Clusters from "./views/Clusters.jsx";
import Factors from "./views/Factors.jsx";
import Relationships from "./views/Relationships.jsx";
import Trends from "./views/Trends.jsx";
import Entities from "./views/Entities.jsx";
import Search from "./views/Search.jsx";
import Reports from "./views/Reports.jsx";

const NAV = [
  { id: "overview", label: "Overview", icon: "overview", C: Overview, title: "Overview" },
  { id: "topics", label: "Topics", icon: "topics", C: Topics, title: "Topic Modelling" },
  { id: "clusters", label: "Clusters", icon: "clusters", C: Clusters, title: "Incident Clustering" },
  { id: "factors", label: "Factors", icon: "factors", C: Factors, title: "Contributing Factors" },
  { id: "relationships", label: "Relationships", icon: "relationships", C: Relationships, title: "Factor Relationships" },
  { id: "trends", label: "Trends", icon: "trends", C: Trends, title: "Trend Analysis" },
  { id: "entities", label: "Entities", icon: "entities", C: Entities, title: "Named Entities" },
  { id: "search", label: "Search", icon: "search", C: Search, title: "Semantic Search" },
  { id: "reports", label: "Reports", icon: "reports", C: Reports, title: "Incident Reports" },
];

function useHashRoute() {
  const parse = () => (window.location.hash.replace(/^#\/?/, "") || "overview").split("?")[0];
  const [route, setRoute] = useState(parse);
  useEffect(() => {
    const onHash = () => setRoute(parse());
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);
  const navigate = useCallback((id) => {
    window.location.hash = `/${id}`;
  }, []);
  return [route, navigate];
}

function useTheme() {
  const [theme, setTheme] = useState(
    () => localStorage.getItem("av-theme") ||
      (window.matchMedia?.("(prefers-color-scheme: dark)").matches ? "dark" : "light")
  );
  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("av-theme", theme);
  }, [theme]);
  return [theme, () => setTheme((t) => (t === "dark" ? "light" : "dark"))];
}

export default function App() {
  const [route, navigate] = useHashRoute();
  const [theme, toggleTheme] = useTheme();
  const [reportIdx, setReportIdx] = useState(null);
  const health = useApi(() => api.health(), []);

  const current = NAV.find((n) => n.id === route) || NAV[0];
  const View = current.C;

  const openReport = useCallback((idx) => setReportIdx(idx), []);

  return (
    <AppContext.Provider value={{ openReport, navigate }}>
      <div className="app">
        <aside className="sidebar">
          <div className="brand">
            <div className="logo">✈</div>
            <div className="brand-text">
              <b>Aviation Incident AI</b>
              <span>Contributing-Factor Discovery</span>
            </div>
          </div>
          <div className="nav-section">Analysis pipeline</div>
          {NAV.map((n) => (
            <button
              key={n.id}
              className={`nav-item ${route === n.id ? "active" : ""}`}
              onClick={() => navigate(n.id)}
            >
              <span className="ico"><Icon name={n.icon} size={17} /></span>
              {n.label}
            </button>
          ))}
          <div className="sidebar-foot">
            Minor Project · CSE · Session 2026–27
            <br />
            ABES Engineering College
          </div>
        </aside>

        <div className="main">
          <header className="topbar">
            <div>
              <h1>{current.title}</h1>
              <div className="sub">AI-Powered Aviation Incident Analysis</div>
            </div>
            <div className="spacer" />
            {health.data && (
              <span className="engine-badge" title={engineTitle(health.data)}>
                <span className="dot" />
                {health.data.capabilities?.forced_lightweight ? "Lightweight engine" : "Full NLP stack"}
              </span>
            )}
            <button className="icon-btn" onClick={toggleTheme} title="Toggle theme"
              aria-label="Toggle colour theme">
              <Icon name={theme === "dark" ? "sun" : "moon"} size={17} />
            </button>
          </header>

          <main className="content">
            <View />
          </main>
        </div>
      </div>

      {reportIdx !== null && (
        <ReportDetail idx={reportIdx} onClose={() => setReportIdx(null)} />
      )}
    </AppContext.Provider>
  );
}

function engineTitle(h) {
  const e = h.engines || {};
  return [
    `Embeddings: ${e.embeddings}`,
    `Topics: ${e.topic_modeling}`,
    `NER: ${e.ner}`,
    `Clustering: ${e.clustering}`,
  ].join("\n");
}
