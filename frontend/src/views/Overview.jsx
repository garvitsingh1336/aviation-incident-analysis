import { api } from "../api.js";
import { useApi } from "../lib/useApi.js";
import { useApp } from "../appContext.js";
import { commas, pct, prettyDate, round } from "../lib/format.js";
import { severityColor, themeColor, STATUS } from "../lib/palette.js";
import { SEVERITY_ORDER } from "../lib/palette.js";
import { Card, StatTile, ViewHead, Loading, ErrorState, Legend } from "../components/ui.jsx";
import HBar from "../components/charts/HBar.jsx";
import SegmentBar from "../components/charts/SegmentBar.jsx";
import LineChart from "../components/charts/LineChart.jsx";

export default function Overview() {
  const { data, loading, error, reload } = useApi(() => api.overview(), []);
  const { navigate } = useApp();

  if (loading) return <Loading />;
  if (error) return <ErrorState error={error} onRetry={reload} />;

  const { stats, top_factors, trends, topics_comparison, meta } = data;

  const sevData = SEVERITY_ORDER.filter((s) => stats.severity_counts[s]).map((s) => ({
    label: s,
    value: stats.severity_counts[s] || 0,
    color: severityColor(s),
  }));

  const factorBars = top_factors.map((f) => ({
    label: f.label,
    value: f.count,
    color: themeColor(f.theme),
    sub: f.theme,
  }));

  const engines = meta.engines || {};
  const engineRows = [
    ["Embeddings", engines.embeddings],
    ["Topic modelling", engines.topic_modeling],
    ["Named-entity recognition", engines.ner],
    ["Clustering", engines.clustering],
    ["Comparison model", engines.lda],
  ];

  return (
    <>
      <ViewHead
        stage="Stages 1–14 · Summary"
        title="Corpus at a glance"
      >
        Unsupervised analysis of {commas(stats.total_reports)} aviation incident narratives —
        contributing factors, clusters, relationships and trends discovered without labels.
      </ViewHead>

      <div className="grid cols-4" style={{ marginBottom: 16 }}>
        <StatTile label="Incident reports analysed" value={commas(stats.total_reports)} hero
          meta={`${prettyDate(stats.date_range[0])} – ${prettyDate(stats.date_range[1])}`} />
        <StatTile label="Contributing-factor topics" value={stats.n_topics}
          meta={`${topics_comparison.primary_engine} + LDA comparison`} />
        <StatTile label="Incident clusters" value={stats.n_clusters}
          meta={`silhouette ${round(stats.silhouette, 3)}`} />
        <StatTile label="Safety themes" value={stats.n_themes}
          meta="grouped from topics" />
      </div>

      <div className="grid cols-2" style={{ marginBottom: 16 }}>
        <Card title="Top contributing factors" hint="click to explore"
          sub="Each discovered topic mapped onto a safety theme (colour). Share of the corpus by report count.">
          <div onClick={() => navigate("factors")} style={{ cursor: "pointer" }}>
            <HBar data={factorBars} format={commas}
              onSelect={() => navigate("factors")} labelWidth={190} />
          </div>
        </Card>

        <Card title="Severity distribution"
          sub="How the corpus splits across occurrence severity.">
          <SegmentBar data={sevData} />
          <Legend items={sevData.map((s) => ({ key: s.label, label: `${s.label} · ${commas(s.value)}`, color: s.color }))} />
          <div style={{ height: 12 }} />
          <div className="grid cols-3" style={{ gap: 10 }}>
            {sevData.map((s) => (
              <div key={s.label} className="tile" style={{ padding: "10px 12px" }}>
                <div className="label">{s.label}</div>
                <div className="value" style={{ fontSize: 20 }}>{pct((s.value / stats.total_reports) * 100, 0)}</div>
              </div>
            ))}
          </div>
        </Card>
      </div>

      <div className="grid cols-2">
        <Card title="Incidents by year"
          sub="Volume of analysed reports per year across the corpus window.">
          <LineChart years={trends.years} values={trends.total_by_year} label="Reports" />
          <div style={{ marginTop: 10, display: "flex", flexDirection: "column", gap: 6 }}>
            {trends.signals.slice(0, 4).map((sig) => {
              const st = STATUS[sig.direction] || STATUS.stable;
              return (
                <div key={sig.theme} style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 12.5 }}>
                  <span style={{ color: st.varName, fontWeight: 700 }}>{st.icon}</span>
                  <span style={{ flex: 1 }}>{sig.theme}</span>
                  <span className="muted mono">{sig.first_half} → {sig.second_half}</span>
                </div>
              );
            })}
          </div>
        </Card>

        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          <Card title="Topic model comparison"
            sub="The primary engine is validated against a classical LDA baseline (Stage 6).">
            <div className="grid cols-2" style={{ gap: 10 }}>
              <StatTile label={topics_comparison.primary_engine + " topics"} value={topics_comparison.primary_topics} />
              <StatTile label="LDA topics" value={topics_comparison.lda_topics}
                meta={`perplexity ${round(topics_comparison.lda_perplexity, 1)}`} />
            </div>
          </Card>
          <Card title="Analysis engines"
            sub="Every stage runs on the full NLP stack, with a scikit-learn fallback.">
            <dl className="kv" style={{ gridTemplateColumns: "180px 1fr" }}>
              {engineRows.map(([k, v]) => (
                <div key={k} style={{ display: "contents" }}>
                  <dt>{k}</dt>
                  <dd style={{ fontSize: 12.5 }}>{v || "—"}</dd>
                </div>
              ))}
            </dl>
          </Card>
        </div>
      </div>
    </>
  );
}
