import { api } from "../api.js";
import { useApi } from "../lib/useApi.js";
import { useApp } from "../appContext.js";
import { prettyDate, scorePct } from "../lib/format.js";
import { SeverityBadge, ThemeBadge, Loading } from "../components/ui.jsx";
import Icon from "../components/Icon.jsx";

const ENTITY_GROUPS = [
  ["aircraft", "Aircraft"],
  ["organisation", "Organisations"],
  ["airport", "Airports"],
  ["location", "Locations"],
  ["equipment", "Equipment"],
  ["facility", "Facilities"],
];

export default function ReportDetail({ idx, onClose }) {
  const { data, loading } = useApi(() => api.report(idx), [idx]);
  const { openReport } = useApp();

  const r = data?.report;
  const grouped = {};
  if (r?.entities) {
    for (const e of r.entities) {
      (grouped[e.type] ||= new Set()).add(e.text);
    }
  }

  return (
    <div className="modal-scrim" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-head">
          <div>
            <div className="muted" style={{ fontSize: 12 }}>Incident report</div>
            <h3 style={{ fontSize: 16 }}>{r?.report_id || "…"}</h3>
          </div>
          <button className="icon-btn" onClick={onClose} aria-label="Close">
            <Icon name="close" size={16} />
          </button>
        </div>

        {loading || !r ? (
          <Loading label="Loading report…" />
        ) : (
          <div className="modal-body">
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
              <SeverityBadge severity={r.severity} />
              {r.themes?.map((t) => <ThemeBadge key={t} theme={t} />)}
            </div>

            <p className="narrative">{r.narrative}</p>

            <dl className="kv">
              <dt>Date</dt><dd>{prettyDate(r.date)}</dd>
              <dt>Aircraft</dt><dd>{r.aircraft_type || "—"}</dd>
              <dt>Operator</dt><dd>{r.operator || "—"}</dd>
              <dt>Location</dt><dd>{r.location || "—"}</dd>
              <dt>Airport</dt><dd>{r.airport || "—"}</dd>
              <dt>Phase of flight</dt><dd>{r.phase_of_flight || "—"}</dd>
              <dt>Injury level</dt><dd>{r.injury_level || "—"}</dd>
              <dt>Topic</dt><dd>{r.topic_label}</dd>
              <dt>Cluster</dt><dd>#{r.cluster_id} · {r.cluster_label}</dd>
            </dl>

            {Object.keys(grouped).length > 0 && (
              <div>
                <h4 style={{ fontSize: 13, marginBottom: 8 }}>Extracted entities (NER)</h4>
                <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                  {ENTITY_GROUPS.filter(([k]) => grouped[k]).map(([k, label]) => (
                    <div key={k} style={{ display: "flex", gap: 8, alignItems: "baseline" }}>
                      <span className="muted" style={{ fontSize: 11, minWidth: 92 }}>{label}</span>
                      <div className="chips">
                        {[...grouped[k]].map((t) => <span className="chip" key={t}>{t}</span>)}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {data.similar?.length > 0 && (
              <div>
                <h4 style={{ fontSize: 13, marginBottom: 8 }}>
                  Semantically similar reports
                </h4>
                <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                  {data.similar.map((s) => (
                    <button
                      key={s.idx}
                      className="btn ghost"
                      style={{ justifyContent: "space-between", width: "100%", textAlign: "left" }}
                      onClick={() => openReport(s.idx)}
                    >
                      <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                        <b style={{ fontWeight: 600 }}>{s.report?.report_id}</b>
                        <span className="muted"> · {s.report?.topic_label}</span>
                      </span>
                      <span className="chip mono">{scorePct(s.score)}</span>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
