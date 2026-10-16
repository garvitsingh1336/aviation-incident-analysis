import { useState } from "react";
import { api } from "../api.js";
import { useApi } from "../lib/useApi.js";
import { useApp } from "../appContext.js";
import { commas, prettyDate } from "../lib/format.js";
import { THEME_ORDER, SEVERITY_ORDER } from "../lib/palette.js";
import { ViewHead, Loading, ErrorState, SeverityBadge } from "../components/ui.jsx";
import Icon from "../components/Icon.jsx";

const LIMIT = 20;

export default function Reports() {
  const { openReport } = useApp();

  // Filter option sources (topics + clusters + corpus window) — loaded once.
  const meta = useApi(
    () => Promise.all([api.topics(), api.clusters(), api.overview()]).then(([t, c, o]) => ({ t, c, o })),
    []
  );

  const [f, setF] = useState({
    topic_id: "", cluster_id: "", theme: "", severity: "", year: "", q: "",
  });
  const [qInput, setQInput] = useState("");
  const [offset, setOffset] = useState(0);

  const setFilter = (key, value) => {
    setF((prev) => ({ ...prev, [key]: value }));
    setOffset(0);
  };
  const applyQuery = (value) => {
    setF((prev) => ({ ...prev, q: value }));
    setOffset(0);
  };
  const clearAll = () => {
    setF({ topic_id: "", cluster_id: "", theme: "", severity: "", year: "", q: "" });
    setQInput("");
    setOffset(0);
  };

  const list = useApi(
    () => api.reports({ ...f, limit: LIMIT, offset }),
    [f.topic_id, f.cluster_id, f.theme, f.severity, f.year, f.q, offset]
  );

  if (meta.loading) return <Loading />;
  if (meta.error) return <ErrorState error={meta.error} onRetry={meta.reload} />;

  const topics = [...meta.data.t.primary.topics].sort((a, b) => b.size - a.size);
  const clusters = [...meta.data.c.clusters].sort((a, b) => b.size - a.size);
  const years = yearRange(meta.data.o.stats?.date_range);
  const activeCount = Object.values(f).filter(Boolean).length;

  const total = list.data?.total ?? 0;
  const items = list.data?.items ?? [];
  const from = total === 0 ? 0 : offset + 1;
  const to = Math.min(offset + LIMIT, total);

  return (
    <>
      <ViewHead stage="Explore · Incident Corpus" title="Browse the analysed reports">
        Every report the pipeline ingested, with its discovered topic, cluster and safety themes.
        Filter by any facet or free-text search, then open a report for its full narrative, extracted
        entities and nearest neighbours.
      </ViewHead>

      <div className="filters">
        <form
          className="filter-search"
          onSubmit={(e) => { e.preventDefault(); applyQuery(qInput.trim()); }}
        >
          <span className="search-ico"><Icon name="search" size={15} /></span>
          <input
            type="text" value={qInput} onChange={(e) => setQInput(e.target.value)}
            placeholder="Search narratives…" aria-label="Search report text"
          />
        </form>

        <Select label="Topic" value={f.topic_id} onChange={(v) => setFilter("topic_id", v)}
          options={topics.map((t) => [t.topic_id, t.label])} allLabel="All topics" />
        <Select label="Cluster" value={f.cluster_id} onChange={(v) => setFilter("cluster_id", v)}
          options={clusters.map((c) => [c.cluster_id, `#${c.cluster_id} ${c.label}`])} allLabel="All clusters" />
        <Select label="Theme" value={f.theme} onChange={(v) => setFilter("theme", v)}
          options={THEME_ORDER.map((t) => [t, t])} allLabel="All themes" />
        <Select label="Severity" value={f.severity} onChange={(v) => setFilter("severity", v)}
          options={SEVERITY_ORDER.map((s) => [s, s])} allLabel="All severities" />
        <Select label="Year" value={f.year} onChange={(v) => setFilter("year", v)}
          options={years.map((y) => [y, y])} allLabel="All years" />

        {activeCount > 0 && (
          <button className="btn ghost" onClick={clearAll} style={{ alignSelf: "flex-end" }}>
            Clear ({activeCount})
          </button>
        )}
      </div>

      <div className="list-meta">
        {list.loading ? "Loading…" : `Showing ${commas(from)}–${commas(to)} of ${commas(total)} reports`}
      </div>

      {list.error ? (
        <ErrorState error={list.error} onRetry={list.reload} />
      ) : (
        <>
          <div className="table-wrap" style={{ opacity: list.loading ? 0.55 : 1, transition: "opacity .15s" }}>
            <table className="rows-clickable">
              <thead>
                <tr>
                  <th>Report</th>
                  <th>Date</th>
                  <th>Severity</th>
                  <th>Topic</th>
                  <th>Aircraft</th>
                  <th>Location</th>
                  <th>Phase</th>
                </tr>
              </thead>
              <tbody>
                {items.map((r) => (
                  <tr key={r.idx} onClick={() => openReport(r.idx)} tabIndex={0}
                    onKeyDown={(e) => (e.key === "Enter" ? openReport(r.idx) : null)}>
                    <td>
                      <b style={{ fontWeight: 600 }}>{r.report_id}</b>
                      {r.snippet && <div className="muted cell-snippet">{r.snippet}</div>}
                    </td>
                    <td className="mono nowrap">{prettyDate(r.date)}</td>
                    <td><SeverityBadge severity={r.severity} /></td>
                    <td className="secondary">{r.topic_label}</td>
                    <td className="secondary nowrap">{r.aircraft_type || "—"}</td>
                    <td className="secondary">{r.location || r.airport || "—"}</td>
                    <td className="secondary nowrap">{r.phase_of_flight || "—"}</td>
                  </tr>
                ))}
                {!list.loading && items.length === 0 && (
                  <tr><td colSpan={7} className="empty-row">No reports match these filters.</td></tr>
                )}
              </tbody>
            </table>
          </div>

          <div className="pager">
            <button className="btn ghost" disabled={offset === 0}
              onClick={() => setOffset(Math.max(0, offset - LIMIT))}>
              <Icon name="chevron" size={14} /> Previous
            </button>
            <span className="muted" style={{ fontSize: 12.5 }}>
              Page {Math.floor(offset / LIMIT) + 1} of {Math.max(1, Math.ceil(total / LIMIT))}
            </span>
            <button className="btn ghost" disabled={to >= total}
              onClick={() => setOffset(offset + LIMIT)}>
              Next <span style={{ display: "inline-flex", transform: "rotate(180deg)" }}><Icon name="chevron" size={14} /></span>
            </button>
          </div>
        </>
      )}
    </>
  );
}

function Select({ label, value, onChange, options, allLabel }) {
  return (
    <label className="field">
      <span>{label}</span>
      <select value={value} onChange={(e) => onChange(e.target.value)}>
        <option value="">{allLabel}</option>
        {options.map(([val, lbl]) => (
          <option key={val} value={val}>{lbl}</option>
        ))}
      </select>
    </label>
  );
}

function yearRange(range) {
  if (!range || range.length < 2) return [];
  const a = Number(String(range[0]).slice(0, 4));
  const b = Number(String(range[1]).slice(0, 4));
  if (Number.isNaN(a) || Number.isNaN(b)) return [];
  const out = [];
  for (let y = b; y >= a; y--) out.push(y);
  return out;
}
