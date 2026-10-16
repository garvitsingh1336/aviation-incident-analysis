import { useState } from "react";
import { api } from "../api.js";
import { useApi } from "../lib/useApi.js";
import { useApp } from "../appContext.js";
import { commas, round } from "../lib/format.js";
import { Card, StatTile, ViewHead, Loading, ErrorState, BarMeter, Chips } from "../components/ui.jsx";

const kwList = (keywords) =>
  (keywords || []).map((k) => (Array.isArray(k) ? k[0] : k)).slice(0, 8);

export default function Topics() {
  const { data, loading, error, reload } = useApi(() => api.topics(), []);
  const { openReport } = useApp();
  const [engine, setEngine] = useState("primary");

  if (loading) return <Loading />;
  if (error) return <ErrorState error={error} onRetry={reload} />;

  const primary = data.primary;
  const lda = data.lda;
  const cmp = data.comparison;
  const active = engine === "primary" ? primary : lda;

  const topics = [...active.topics].sort((a, b) => {
    if (a.topic_id === -1) return 1;
    if (b.topic_id === -1) return -1;
    return b.size - a.size;
  });
  const maxSize = Math.max(...topics.filter((t) => t.topic_id !== -1).map((t) => t.size), 1);

  return (
    <>
      <ViewHead stage="Stage 6 · Topic Modelling" title="Discovered contributing-factor topics">
        Topics are induced from the incident narratives without labels. The primary engine
        ({primary.engine}) works on the transformer embeddings; a classical LDA model provides a
        comparison baseline.
      </ViewHead>

      <div className="grid cols-4" style={{ marginBottom: 16 }}>
        <StatTile label={`${cmp.primary_engine} topics`} value={cmp.primary_topics} />
        <StatTile label="LDA topics" value={cmp.lda_topics} />
        <StatTile label="LDA perplexity" value={round(cmp.lda_perplexity, 1)} meta="lower = tighter fit" />
        <StatTile label="Primary engine" value={primary.engine} />
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 14 }}>
        <div className="btn-group">
          <button className={engine === "primary" ? "active" : ""} onClick={() => setEngine("primary")}>
            {primary.engine}
          </button>
          <button className={engine === "lda" ? "active" : ""} onClick={() => setEngine("lda")}>
            LDA baseline
          </button>
        </div>
        <span className="muted" style={{ fontSize: 12.5 }}>
          {engine === "primary"
            ? "Embedding-based topics with representative reports."
            : "Bag-of-words topics for methodological comparison."}
        </span>
      </div>

      <div className="grid cols-3">
        {topics.map((t) => {
          const outlier = t.topic_id === -1;
          return (
            <Card key={t.topic_id} style={outlier ? { opacity: 0.72 } : undefined}>
              <div style={{ display: "flex", justifyContent: "space-between", gap: 10, marginBottom: 8 }}>
                <h3 style={{ fontSize: 14 }}>{t.label}</h3>
                <span className="chip mono">{commas(t.size)}</span>
              </div>
              {!outlier && (
                <div style={{ marginBottom: 12 }}>
                  <BarMeter value={t.size} max={maxSize} />
                </div>
              )}
              <Chips items={kwList(t.keywords)} />
              {t.representative_idx?.length > 0 && (
                <div style={{ marginTop: 12, display: "flex", gap: 6, flexWrap: "wrap" }}>
                  {t.representative_idx.slice(0, 3).map((idx) => (
                    <button key={idx} className="btn ghost" style={{ fontSize: 12, padding: "4px 9px" }}
                      onClick={() => openReport(idx)}>
                      Example #{idx}
                    </button>
                  ))}
                </div>
              )}
            </Card>
          );
        })}
      </div>
    </>
  );
}
