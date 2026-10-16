import { api } from "../api.js";
import { useApi } from "../lib/useApi.js";
import { themeColor, THEME_ORDER } from "../lib/palette.js";
import { Card, ViewHead, Loading, ErrorState, ThemeBadge } from "../components/ui.jsx";
import Network from "../components/charts/Network.jsx";
import Heatmap from "../components/charts/Heatmap.jsx";

const CODE = {
  "Weather & Environment": "WX",
  "Powerplant & Fuel": "PWR",
  "Human Factors & ATC": "HF",
  "Runway & Ground Ops": "RWY",
  "Mechanical & Systems": "MEC",
  "Loss of Control & Terrain": "LOC",
  Wildlife: "BIRD",
};
const codeOf = (id) => CODE[id] || id.slice(0, 3).toUpperCase();

export default function Relationships() {
  const { data, loading, error, reload } = useApi(() => api.relationships(), []);

  if (loading) return <Loading />;
  if (error) return <ErrorState error={error} onRetry={reload} />;

  const { nodes, edges } = data;
  const present = new Set(nodes.map((n) => n.id));
  const ordered = THEME_ORDER.filter((t) => present.has(t));

  // unordered-pair lookup
  const pair = {};
  for (const e of edges) {
    pair[[e.source, e.target].sort().join("|")] = e;
  }
  const lookup = (a, b) => pair[[a, b].sort().join("|")];
  const maxEdge = Math.max(1, ...edges.map((e) => e.count));

  const value = (i, j) => (i === j ? 0 : lookup(ordered[i], ordered[j])?.count || 0);
  const tipOf = (i, j) => {
    if (i === j)
      return (
        <>
          <div className="tt-title">{ordered[i]}</div>
          <div className="tt-row"><span className="k">Reports</span>
            <span className="v">{nodes.find((n) => n.id === ordered[i])?.count}</span></div>
        </>
      );
    const e = lookup(ordered[i], ordered[j]);
    return (
      <>
        <div className="tt-title">{ordered[i]} ↔ {ordered[j]}</div>
        <div className="tt-row"><span className="k">Co-occurrences</span><span className="v">{e?.count || 0}</span></div>
        {e && <div className="tt-row"><span className="k">Lift</span><span className="v">{e.lift.toFixed(2)}×</span></div>}
        {e && <div className="tt-row"><span className="k">Jaccard</span><span className="v">{e.jaccard.toFixed(3)}</span></div>}
      </>
    );
  };

  const topEdges = [...edges].sort((a, b) => b.lift - a.lift);

  return (
    <>
      <ViewHead stage="Stage 9 · Relationship Analysis" title="How contributing factors co-occur">
        When two safety themes appear in the same report they are linked. Edge width is the joint
        count; <b>lift</b> above 1 means the pair occurs together more often than chance, revealing
        compounding risk.
      </ViewHead>

      <div className="grid cols-2" style={{ marginBottom: 16 }}>
        <Card title="Co-occurrence network" hint="hover to isolate"
          sub="Node size = reports mentioning the theme · edge width = joint occurrences.">
          <Network nodes={nodes} edges={edges} colorOf={themeColor} codeOf={codeOf} />
          <div className="legend">
            {ordered.map((t) => (
              <span className="item" key={t}>
                <span className="swatch" style={{ background: themeColor(t) }} />
                <b style={{ fontWeight: 600 }}>{codeOf(t)}</b>&nbsp;{t}
              </span>
            ))}
          </div>
        </Card>

        <Card title="Co-occurrence matrix" hint="colour = joint count"
          sub="Every theme pair; darker cells co-occur more often. Codes match the network.">
          <Heatmap codes={ordered.map(codeOf)} fullLabels={ordered} value={value} max={maxEdge} tipOf={tipOf} />
        </Card>
      </div>

      <Card title="Strongest associations" hint="ranked by lift"
        sub="Pairs most over-represented relative to independent occurrence.">
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Theme pair</th>
                <th className="num">Co-occurrences</th>
                <th className="num">Lift</th>
                <th className="num">Jaccard</th>
              </tr>
            </thead>
            <tbody>
              {topEdges.map((e, i) => (
                <tr key={i}>
                  <td>
                    <div style={{ display: "flex", gap: 6, flexWrap: "wrap", alignItems: "center" }}>
                      <ThemeBadge theme={e.source} /><span className="muted">↔</span><ThemeBadge theme={e.target} />
                    </div>
                  </td>
                  <td className="num mono">{e.count}</td>
                  <td className="num mono" style={{ fontWeight: e.lift >= 1.15 ? 700 : 400,
                    color: e.lift >= 1.15 ? "var(--accent)" : undefined }}>{e.lift.toFixed(2)}×</td>
                  <td className="num mono">{e.jaccard.toFixed(3)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </>
  );
}
