import { useState } from "react";
import { api } from "../api.js";
import { useApp } from "../appContext.js";
import { scorePct, prettyDate } from "../lib/format.js";
import { ViewHead, SeverityBadge, ThemeBadge } from "../components/ui.jsx";
import Icon from "../components/Icon.jsx";

const EXAMPLES = [
  "bird strike on takeoff",
  "engine failure and emergency landing",
  "runway incursion due to ATC miscommunication",
  "loss of control in icing conditions",
  "fuel exhaustion",
];

const K = 12;

export default function Search() {
  const { openReport } = useApp();
  const [q, setQ] = useState("");
  const [state, setState] = useState({ status: "idle", query: "", results: [] });

  async function run(query) {
    const term = (query ?? q).trim();
    if (!term) return;
    setQ(term);
    setState({ status: "loading", query: term, results: [] });
    try {
      const data = await api.search(term, K);
      setState({ status: "done", query: term, results: data.results || [] });
    } catch (e) {
      setState({ status: "error", query: term, results: [], error: e });
    }
  }

  return (
    <>
      <ViewHead stage="Stage 12 · Semantic Search" title="Find reports by meaning, not keywords">
        The query is embedded with the same transformer model as the corpus, then ranked by cosine
        similarity. A search for “engine fire” surfaces powerplant blazes even when those exact words
        never appear — matching concepts, not strings.
      </ViewHead>

      <form
        className="search-bar"
        onSubmit={(e) => {
          e.preventDefault();
          run();
        }}
      >
        <span className="search-ico"><Icon name="search" size={17} /></span>
        <input
          type="text"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Describe an incident — e.g. “tail strike during landing”"
          aria-label="Search incident reports"
          autoFocus
        />
        <button className="btn primary" type="submit" disabled={!q.trim() || state.status === "loading"}>
          {state.status === "loading" ? "Searching…" : "Search"}
        </button>
      </form>

      <div className="example-row">
        <span className="muted" style={{ fontSize: 12.5 }}>Try:</span>
        {EXAMPLES.map((ex) => (
          <button key={ex} className="chip clickable" onClick={() => run(ex)}>
            {ex}
          </button>
        ))}
      </div>

      {state.status === "error" && (
        <div className="error-box" style={{ marginTop: 16 }}>
          <b>Search failed.</b>
          <div className="secondary" style={{ marginTop: 6 }}>{String(state.error?.message || state.error)}</div>
        </div>
      )}

      {state.status === "done" && (
        <div style={{ marginTop: 18 }}>
          <div className="muted" style={{ fontSize: 12.5, marginBottom: 10 }}>
            {state.results.length > 0
              ? `${state.results.length} closest reports for “${state.query}”`
              : `No reports matched “${state.query}”.`}
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {state.results.map((res) => {
              const r = res.report || {};
              return (
                <button key={res.idx} className="result-card" onClick={() => openReport(res.idx)}>
                  <div className="result-score">
                    <div className="score-num">{scorePct(res.score)}</div>
                    <div className="score-lbl">match</div>
                  </div>
                  <div className="result-body">
                    <div className="result-head">
                      <b style={{ fontWeight: 600 }}>{r.report_id || `Report #${res.idx}`}</b>
                      <SeverityBadge severity={r.severity} />
                      <span className="muted" style={{ fontSize: 12 }}>{prettyDate(r.date)}</span>
                      {r.topic_label && <span className="chip">{r.topic_label}</span>}
                    </div>
                    <p className="result-snippet">{snippet(r)}</p>
                    <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginTop: 6 }}>
                      {(r.themes || []).map((t) => <ThemeBadge key={t} theme={t} />)}
                    </div>
                  </div>
                  <span className="result-open"><Icon name="external" size={15} /></span>
                </button>
              );
            })}
          </div>
        </div>
      )}
    </>
  );
}

function snippet(r) {
  const text = r.snippet || r.narrative || "";
  return text.length > 260 ? text.slice(0, 259).trimEnd() + "…" : text;
}
