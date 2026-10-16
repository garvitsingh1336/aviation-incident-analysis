import { useSize } from "../../lib/useSize.js";
import { barPath } from "../../lib/svg.js";
import { useTip, Tip } from "../Tooltip.jsx";

/**
 * Horizontal bar chart — one categorical axis, magnitude on x.
 * data: [{ label, value, color, sub?, tip? }]
 * Marks: ≤20px thick, 4px rounded data-end, value labelled at the tip
 * (direct labels before gridlines), recessive baseline, hover tooltip.
 */
export default function HBar({
  data,
  labelWidth = 168,
  rowHeight = 32,
  barHeight = 18,
  format = (v) => v.toLocaleString("en-US"),
  onSelect,
  unit = "",
}) {
  const [ref, W] = useSize();
  const { tip, show, hide } = useTip();

  const rightPad = 52;
  const x0 = labelWidth;
  const plotW = Math.max(40, W - x0 - rightPad);
  const max = Math.max(1, ...data.map((d) => d.value));
  const H = data.length * rowHeight + 8;

  return (
    <div ref={ref} style={{ width: "100%" }}>
      <svg className="chart" width={W} height={H} role="img">
        {/* baseline */}
        <line className="baseline" x1={x0} y1={4} x2={x0} y2={H - 4} />
        {data.map((d, i) => {
          const y = i * rowHeight + 8;
          const w = (d.value / max) * plotW;
          const cy = y + barHeight / 2;
          const content = d.tip || (
            <>
              <div className="tt-title">{d.label}</div>
              <div className="tt-row">
                <span className="k">Count</span>
                <span className="v">
                  {format(d.value)}
                  {unit ? ` ${unit}` : ""}
                </span>
              </div>
              {d.sub && (
                <div className="secondary" style={{ marginTop: 4, fontSize: 11.5 }}>
                  {d.sub}
                </div>
              )}
            </>
          );
          return (
            <g
              key={i}
              className="mark"
              style={{ cursor: onSelect ? "pointer" : "default" }}
              onMouseMove={(e) => show(e, content)}
              onMouseLeave={hide}
              onClick={onSelect ? () => onSelect(d) : undefined}
            >
              {/* full-row hit target */}
              <rect x={0} y={y - 6} width={W} height={rowHeight} fill="transparent" />
              <text
                x={x0 - 12}
                y={cy}
                textAnchor="end"
                dominantBaseline="middle"
                style={{ fill: "var(--text-secondary)", fontSize: 12 }}
              >
                {clip(d.label, labelWidth)}
              </text>
              <path d={barPath(x0 + 1, y, Math.max(w, 2), barHeight, 4, "right")} fill={d.color} />
              <text
                className="val-label"
                x={x0 + Math.max(w, 2) + 8}
                y={cy}
                dominantBaseline="middle"
              >
                {format(d.value)}
              </text>
            </g>
          );
        })}
      </svg>
      <Tip tip={tip} />
    </div>
  );
}

function clip(s, px) {
  const max = Math.floor(px / 6.6);
  return s.length > max ? s.slice(0, max - 1) + "…" : s;
}
