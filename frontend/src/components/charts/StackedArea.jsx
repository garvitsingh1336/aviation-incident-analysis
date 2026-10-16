import { useState } from "react";
import { useSize } from "../../lib/useSize.js";
import { niceTicks, bandPath, linePath } from "../../lib/svg.js";
import { useTip, Tip } from "../Tooltip.jsx";

/**
 * Themes-over-time chart. mode="stacked" shows the evolving composition
 * (near-solid bands separated by a 2px surface gap); mode="line" overlays one
 * 2px line per theme. A shared crosshair + tooltip reports every active series
 * at the hovered year. Identity is carried by the always-present legend.
 *
 * series: [{ key, label, color, values:[…] }] aligned to `years`.
 */
export default function StackedArea({ years, series, mode = "stacked", height = 320 }) {
  const [ref, W] = useSize();
  const { tip, show, hide } = useTip();
  const [hoverI, setHoverI] = useState(null);

  const m = { top: 14, right: 18, bottom: 30, left: 44 };
  const plotW = Math.max(60, W - m.left - m.right);
  const plotH = height - m.top - m.bottom;
  const n = years.length;
  const xFor = (i) => m.left + (n <= 1 ? plotW / 2 : (i / (n - 1)) * plotW);

  // y-scale
  let ymax;
  if (mode === "stacked") {
    ymax = Math.max(
      1,
      ...years.map((_, i) => series.reduce((s, ser) => s + ser.values[i], 0))
    );
  } else {
    ymax = Math.max(1, ...series.flatMap((s) => s.values));
  }
  const ticks = niceTicks(ymax, 5);
  const top = ticks[ticks.length - 1] || ymax;
  const yFor = (v) => m.top + plotH - (v / top) * plotH;

  // stacked bands
  const bands = [];
  if (mode === "stacked") {
    const cum = new Array(n).fill(0);
    for (const ser of series) {
      const lower = years.map((_, i) => [xFor(i), yFor(cum[i])]);
      const upper = years.map((_, i) => {
        cum[i] += ser.values[i];
        return [xFor(i), yFor(cum[i])];
      });
      bands.push({ ...ser, upper, lower });
    }
  }

  function onMove(e) {
    const rect = e.currentTarget.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    let i = Math.round(((mx - m.left) / plotW) * (n - 1));
    i = Math.max(0, Math.min(n - 1, i));
    setHoverI(i);
    const rows = series
      .map((s) => ({ s, v: s.values[i] }))
      .sort((a, b) => b.v - a.v);
    const total = series.reduce((acc, s) => acc + s.values[i], 0);
    show(e, (
      <>
        <div className="tt-title">{years[i]}</div>
        {rows.map(({ s, v }) => (
          <div className="tt-row" key={s.key}>
            <span className="k">
              <span className="sw" style={{ background: s.color }} />
              {s.label}
            </span>
            <span className="v">{v}</span>
          </div>
        ))}
        <div className="tt-row" style={{ borderTop: "1px solid var(--border)", marginTop: 4, paddingTop: 4 }}>
          <span className="k">Total</span>
          <span className="v">{total}</span>
        </div>
      </>
    ));
  }
  function onLeave() {
    setHoverI(null);
    hide();
  }

  return (
    <div ref={ref} style={{ width: "100%" }}>
      <svg className="chart" width={W} height={height} role="img">
        {/* gridlines + y ticks */}
        {ticks.map((t, i) => (
          <g key={i}>
            <line className="grid-line" x1={m.left} x2={m.left + plotW} y1={yFor(t)} y2={yFor(t)} />
            <text x={m.left - 8} y={yFor(t)} textAnchor="end" dominantBaseline="middle">
              {t}
            </text>
          </g>
        ))}
        {/* x labels */}
        {years.map((yr, i) => (
          <text key={i} x={xFor(i)} y={height - 10} textAnchor="middle">
            {yr}
          </text>
        ))}
        <line className="baseline" x1={m.left} x2={m.left + plotW} y1={yFor(0)} y2={yFor(0)} />

        {/* marks */}
        {mode === "stacked" &&
          bands.map((b) => (
            <g key={b.key}>
              <path d={bandPath(b.upper, b.lower)} fill={b.color} opacity="0.9" />
              {/* 2px surface gap along the top boundary of each band */}
              <path d={linePath(b.upper)} fill="none" stroke="var(--surface-1)" strokeWidth="2" />
            </g>
          ))}
        {mode === "line" &&
          series.map((s) => {
            const pts = years.map((_, i) => [xFor(i), yFor(s.values[i])]);
            return (
              <g key={s.key}>
                <path
                  d={linePath(pts)}
                  fill="none"
                  stroke={s.color}
                  strokeWidth="2"
                  strokeLinejoin="round"
                  strokeLinecap="round"
                />
                {pts.map((p, i) => (
                  <circle key={i} cx={p[0]} cy={p[1]} r="3" fill={s.color}
                    stroke="var(--surface-1)" strokeWidth="1.5" />
                ))}
              </g>
            );
          })}

        {/* crosshair */}
        {hoverI !== null && (
          <line
            x1={xFor(hoverI)}
            x2={xFor(hoverI)}
            y1={m.top}
            y2={m.top + plotH}
            stroke="var(--baseline)"
            strokeWidth="1"
            strokeDasharray="3 3"
          />
        )}

        {/* hit layer */}
        <rect
          x={m.left}
          y={m.top}
          width={plotW}
          height={plotH}
          fill="transparent"
          onMouseMove={onMove}
          onMouseLeave={onLeave}
        />
      </svg>
      <Tip tip={tip} />
    </div>
  );
}
