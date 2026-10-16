import { useState } from "react";
import { api } from "../api.js";
import { useApi } from "../lib/useApi.js";
import { useApp } from "../appContext.js";
import { commas, round } from "../lib/format.js";
import { severityColor, SEVERITY_ORDER } from "../lib/palette.js";
import { Card, StatTile, ViewHead, Loading, ErrorState, BarMeter, Chips, Legend } from "../components/ui.jsx";
import Scatter from "../components/charts/Scatter.jsx";

export default function Clusters() {
  const { data, loading, error, reload } = useApi(
    () => Promise.all([api.clusters(), api.scatter()]).then(([c, s]) => ({ c, s })),
    []
  );
  const { openReport } = useApp();
  const [selected, setSelected] = useState(null);

  if (loading) return <Loading />;
  if (error) return <ErrorState error={error} onRetry={reload} />;

  const { c, s } = data;
  const points = s.points;
  const clusters = [...c.clusters].sort((a, b) => b.size - a.size);
  const maxSize = Math.max(...clusters.map((cl) => cl.size), 1);

  const colorOf = (p) =>
    selected !== null && p.cluster_id !== selected ? "var(--grid)" : severityColor(p.severity);

  const sevLegend = SEVERITY_ORDER.map((sv) => ({ key: sv, label: sv, color: severityColor(sv) }));

  return (
    <>
      <ViewHead stage="Stage 7 · Clustering" title="Semantic incident map">
        Reports are embedded with a transformer model, grouped with K-Means in cosine space, and
        projected to 2-D. Nearby points describe similar occurrences; colour encodes severity.
        Select a cluster below to highlight it on the map, or click any point to open the report.
      </ViewHead>

      <div className="grid cols-4" style={{ marginBottom: 16 }}>
        <StatTile label="Incident clusters" value={c.n_clusters} />
        <StatTile label="Silhouette score" value={round(c.silhouette, 3)} meta="cluster separation (−1…1)" />
        <StatTile label="Reports mapped" value={commas(points.length)} />
        <StatTile label="Highlighted" value={selected === null ? "All" : `#${selected}`}
          meta={selected !== null ? "click again to clear" : "select a cluster"} />
      </div>

      <Card title="2-D projection of the embedding space" hint="hover a point for details"
        sub="Projection via UMAP (falls back to truncated SVD). Colour = severity; a legend maps each hue."
        style={{ marginBottom: 16 }}>
        <Scatter points={points} colorOf={colorOf} onSelect={openReport} />
        <Legend items={sevLegend} />
      </Card>

      <div className="grid cols-3">
        {clusters.map((cl) => {
          const on = selected === cl.cluster_id;
          return (
            <Card key={cl.cluster_id}
              style={{ cursor: "pointer", borderColor: on ? "var(--accent)" : undefined,
                boxShadow: on ? "0 0 0 2px var(--accent-wash)" : undefined }}>
              <div onClick={() => setSelected(on ? null : cl.cluster_id)}>
                <div style={{ display: "flex", justifyContent: "space-between", gap: 10, marginBottom: 8 }}>
                  <h3 style={{ fontSize: 13.5 }}>
                    <span className="muted mono">#{cl.cluster_id}</span> {cl.label}
                  </h3>
                  <span className="chip mono">{commas(cl.size)}</span>
                </div>
                <div style={{ marginBottom: 12 }}>
                  <BarMeter value={cl.size} max={maxSize} />
                </div>
                <Chips items={cl.keywords.slice(0, 6)} />
              </div>
              {cl.representative_idx?.length > 0 && (
                <div style={{ marginTop: 12, display: "flex", gap: 6, flexWrap: "wrap" }}>
                  {cl.representative_idx.slice(0, 3).map((idx) => (
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
