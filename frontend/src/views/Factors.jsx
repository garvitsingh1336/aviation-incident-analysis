import { api } from "../api.js";
import { useApi } from "../lib/useApi.js";
import { useApp } from "../appContext.js";
import { commas, pct } from "../lib/format.js";
import { themeColor, severityColor, SEVERITY_ORDER } from "../lib/palette.js";
import { Card, StatTile, ViewHead, Loading, ErrorState, ThemeBadge, Legend } from "../components/ui.jsx";
import HBar from "../components/charts/HBar.jsx";

function SevBar({ breakdown }) {
  const total = SEVERITY_ORDER.reduce((s, k) => s + (breakdown[k] || 0), 0) || 1;
  return (
    <div style={{ display: "flex", gap: 2, height: 9, width: 132, borderRadius: 4, overflow: "hidden" }}>
      {SEVERITY_ORDER.map((k) =>
        (breakdown[k] || 0) > 0 ? (
          <div key={k} title={`${k}: ${breakdown[k]}`}
            style={{ width: `${((breakdown[k] || 0) / total) * 100}%`, background: severityColor(k) }} />
        ) : null
      )}
    </div>
  );
}

export default function Factors() {
  const { data, loading, error, reload } = useApi(() => api.factors(), []);
  const { openReport } = useApp();

  if (loading) return <Loading />;
  if (error) return <ErrorState error={error} onRetry={reload} />;

  const { factors, themes, evaluation, total_reports } = data;
  const themeBars = [...themes]
    .sort((a, b) => b.count - a.count)
    .map((t) => ({ label: t.theme, value: t.count, color: themeColor(t.theme), sub: pct(t.share, 1) + " of corpus" }));

  const sevLegend = SEVERITY_ORDER.map((s) => ({ key: s, label: s, color: severityColor(s) }));

  return (
    <>
      <ViewHead stage="Stage 8 · Contributing-Factor Analysis" title="What is driving these incidents?">
        Each discovered topic is mapped onto a safety theme and quantified by how much of the corpus
        it explains, together with the severity mix of the reports it covers.
      </ViewHead>

      <div className="grid cols-2" style={{ marginBottom: 16 }}>
        <Card title="Safety themes by volume"
          sub="Reports grouped into higher-level themes (a topic may touch more than one theme).">
          <HBar data={themeBars} format={commas} labelWidth={185} />
        </Card>

        <Card title="Topic quality (validation)"
          sub="Diagnostic only — discovered topics compared against the corpus's latent factors.">
          <StatTile label="Mean topic purity" value={pct(evaluation.mean_purity * 100, 1)}
            meta="agreement of unsupervised topics with ground-truth factors" />
          <p className="secondary" style={{ fontSize: 12.5, marginTop: 12 }}>{evaluation.note}</p>
        </Card>
      </div>

      <Card title="Contributing factors" hint={`${factors.length} factors · ${commas(total_reports)} reports`}
        sub="Severity mix shown as a mini-bar (Incident · Serious Incident · Accident)."
        style={{ marginBottom: 16 }}>
        <Legend items={sevLegend} />
        <div className="table-wrap" style={{ marginTop: 12 }}>
          <table>
            <thead>
              <tr>
                <th>Contributing factor</th>
                <th>Theme</th>
                <th className="num">Reports</th>
                <th className="num">Share</th>
                <th>Severity mix</th>
                <th>Examples</th>
              </tr>
            </thead>
            <tbody>
              {factors.map((f) => (
                <tr key={f.factor_id}>
                  <td style={{ maxWidth: 260 }}>
                    <b style={{ fontWeight: 600 }}>{f.label}</b>
                    <div className="muted" style={{ fontSize: 11.5, marginTop: 2 }}>
                      {f.keywords.slice(0, 5).join(" · ")}
                    </div>
                  </td>
                  <td><ThemeBadge theme={f.theme} /></td>
                  <td className="num mono">{commas(f.count)}</td>
                  <td className="num mono">{pct(f.share, 1)}</td>
                  <td><SevBar breakdown={f.severity_breakdown} /></td>
                  <td>
                    <div style={{ display: "flex", gap: 5, flexWrap: "wrap" }}>
                      {(f.representative_idx || []).slice(0, 2).map((idx) => (
                        <button key={idx} className="btn ghost" style={{ fontSize: 11.5, padding: "3px 8px" }}
                          onClick={() => openReport(idx)}>
                          #{idx}
                        </button>
                      ))}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {evaluation.per_topic?.length > 0 && (
        <Card title="Per-topic alignment with latent factors"
          sub="For each discovered topic, the dominant ground-truth factor and the purity of that match.">
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Discovered topic</th>
                  <th>Dominant latent factor</th>
                  <th className="num">Purity</th>
                </tr>
              </thead>
              <tbody>
                {[...evaluation.per_topic].sort((a, b) => b.purity - a.purity).map((p, i) => (
                  <tr key={i}>
                    <td>{p.topic_label}</td>
                    <td className="secondary">{p.dominant_true_factor}</td>
                    <td className="num mono">{pct(p.purity * 100, 0)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </>
  );
}
