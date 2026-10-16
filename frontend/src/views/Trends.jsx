import { useState } from "react";
import { api } from "../api.js";
import { useApi } from "../lib/useApi.js";
import { themeColor, THEME_ORDER, STATUS } from "../lib/palette.js";
import { Card, ViewHead, Loading, ErrorState, Legend } from "../components/ui.jsx";
import StackedArea from "../components/charts/StackedArea.jsx";

export default function Trends() {
  const { data, loading, error, reload } = useApi(() => api.trends(), []);
  const [mode, setMode] = useState("stacked");
  const [active, setActive] = useState(null); // null = all

  if (loading) return <Loading />;
  if (error) return <ErrorState error={error} onRetry={reload} />;

  const { years, series, signals } = data;
  const ordered = [...series].sort(
    (a, b) => THEME_ORDER.indexOf(a.theme) - THEME_ORDER.indexOf(b.theme)
  );
  const mapped = ordered.map((s) => ({
    key: s.theme,
    label: s.theme,
    color: themeColor(s.theme),
    values: s.values,
  }));
  const activeSet = active || new Set(mapped.map((m) => m.key));
  const shown = mapped.filter((m) => activeSet.has(m.key));

  const toggle = (key) => {
    const next = new Set(activeSet);
    if (next.has(key)) next.delete(key);
    else next.add(key);
    if (next.size === 0) return; // keep at least one
    setActive(next);
  };

  return (
    <>
      <ViewHead stage="Stage 10 · Trend Analysis" title="How contributing factors evolve">
        Yearly volume of each safety theme across the corpus window. Switch to line mode to read a
        single theme’s trajectory; use the legend to focus on specific themes.
      </ViewHead>

      <Card
        title={mode === "stacked" ? "Theme composition by year" : "Theme trajectories"}
        hint="hover for a yearly breakdown"
        sub="Stacked mode shows the changing mix; line mode compares individual themes on one scale."
        style={{ marginBottom: 16 }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
          <div className="btn-group">
            <button className={mode === "stacked" ? "active" : ""} onClick={() => setMode("stacked")}>Stacked area</button>
            <button className={mode === "line" ? "active" : ""} onClick={() => setMode("line")}>Lines</button>
          </div>
        </div>
        <StackedArea years={years} series={shown} mode={mode} height={340} />
        <Legend
          items={mapped.map((m) => ({ key: m.key, label: m.label, color: m.color }))}
          active={activeSet}
          onToggle={toggle}
        />
      </Card>

      <Card title="Trend signals" hint="first half vs second half of the window"
        sub="Direction compares the theme’s report count in the earlier vs later years.">
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Safety theme</th>
                <th>Direction</th>
                <th className="num">Early years</th>
                <th className="num">Later years</th>
                <th className="num">Change</th>
              </tr>
            </thead>
            <tbody>
              {[...signals].sort((a, b) => (b.second_half - b.first_half) - (a.second_half - a.first_half)).map((s) => {
                const st = STATUS[s.direction] || STATUS.stable;
                const delta = s.second_half - s.first_half;
                return (
                  <tr key={s.theme}>
                    <td>
                      <span className="badge">
                        <span className="dot" style={{ background: themeColor(s.theme) }} />
                        {s.theme}
                      </span>
                    </td>
                    <td>
                      <span style={{ display: "inline-flex", alignItems: "center", gap: 6, color: st.varName, fontWeight: 600 }}>
                        <span>{st.icon}</span> {st.label}
                      </span>
                    </td>
                    <td className="num mono">{s.first_half}</td>
                    <td className="num mono">{s.second_half}</td>
                    <td className="num mono">{delta > 0 ? `+${delta}` : delta}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </Card>
    </>
  );
}
