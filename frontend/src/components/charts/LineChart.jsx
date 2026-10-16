import { useState } from "react";
import { useSize } from "../../lib/useSize.js";
import { niceTicks, linePath, areaPath } from "../../lib/svg.js";
import { useTip, Tip } from "../Tooltip.jsx";

/** Single-series line with a 10% area wash — for "total by year" style trends. */
export default function LineChart({
  years,
  values,
  color = "var(--accent)",
  height = 240,
  label = "Reports",
}) {
  const [ref, W] = useSize();
  const { tip, show, hide } = useTip();
  const [hoverI, setHoverI] = useState(null);

  const m = { top: 16, right: 20, bottom: 30, left: 40 };
  const plotW = Math.max(60, W - m.left - m.right);
  const plotH = height - m.top - m.bottom;
  const n = years.length;
  const xFor = (i) => m.left + (n <= 1 ? plotW / 2 : (i / (n - 1)) * plotW);
  const ticks = niceTicks(Math.max(1, ...values), 5);
  const top = ticks[ticks.length - 1] || 1;
  const yFor = (v) => m.top + plotH - (v / top) * plotH;

  const pts = values.map((v, i) => [xFor(i), yFor(v)]);

  function onMove(e) {
    const rect = e.currentTarget.getBoundingClientRect();
    let i = Math.round(((e.clientX - rect.left - m.left) / plotW) * (n - 1));
    i = Math.max(0, Math.min(n - 1, i));
    setHoverI(i);
    show(e, (
      <>
        <div className="tt-title">{years[i]}</div>
        <div className="tt-row">
          <span className="k">
            <span className="sw" style={{ background: color }} />
            {label}
          </span>
          <span className="v">{values[i]}</span>
        </div>
      </>
    ));
  }

  return (
    <div ref={ref} style={{ width: "100%" }}>
      <svg className="chart" width={W} height={height} role="img">
        {ticks.map((t, i) => (
          <g key={i}>
            <line className="grid-line" x1={m.left} x2={m.left + plotW} y1={yFor(t)} y2={yFor(t)} />
            <text x={m.left - 8} y={yFor(t)} textAnchor="end" dominantBaseline="middle">
              {t}
            </text>
          </g>
        ))}
        {years.map((yr, i) => (
          <text key={i} x={xFor(i)} y={height - 10} textAnchor="middle">
            {yr}
          </text>
        ))}
        <path d={areaPath(pts, yFor(0))} fill={color} opacity="0.12" />
        <path d={linePath(pts)} fill="none" stroke={color} strokeWidth="2"
          strokeLinejoin="round" strokeLinecap="round" />
        {pts.map((p, i) => (
          <circle key={i} cx={p[0]} cy={p[1]} r={hoverI === i ? 5 : 3.5} fill={color}
            stroke="var(--surface-1)" strokeWidth="2" />
        ))}
        {/* direct label on the final point */}
        {pts.length > 0 && (
          <text
            className="val-label"
            x={pts[pts.length - 1][0]}
            y={pts[pts.length - 1][1] - 12}
            textAnchor="end"
            style={{ fontWeight: 600 }}
          >
            {values[values.length - 1]}
          </text>
        )}
        {hoverI !== null && (
          <line x1={xFor(hoverI)} x2={xFor(hoverI)} y1={m.top} y2={m.top + plotH}
            stroke="var(--baseline)" strokeWidth="1" strokeDasharray="3 3" />
        )}
        <rect x={m.left} y={m.top} width={plotW} height={plotH} fill="transparent"
          onMouseMove={onMove} onMouseLeave={() => { setHoverI(null); hide(); }} />
      </svg>
      <Tip tip={tip} />
    </div>
  );
}
