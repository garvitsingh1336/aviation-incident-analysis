import { useSize } from "../../lib/useSize.js";
import { useTip, Tip } from "../Tooltip.jsx";

/**
 * Single stacked horizontal bar for a part-to-whole split (e.g. severity mix).
 * 2px surface gaps separate touching segments; identity comes from the legend
 * below, values labelled inline only when they fit.
 */
export default function SegmentBar({ data, height = 40 }) {
  const [ref, W] = useSize();
  const { tip, show, hide } = useTip();
  const total = data.reduce((s, d) => s + d.value, 0) || 1;
  const gap = 2;

  let x = 0;
  const segs = data.map((d) => {
    const w = (d.value / total) * W;
    const seg = { ...d, x, w, pct: (d.value / total) * 100 };
    x += w;
    return seg;
  });

  return (
    <div ref={ref} style={{ width: "100%" }}>
      <svg className="chart" width={W} height={height} role="img">
        {segs.map((s, i) => {
          const w = Math.max(0, s.w - (i < segs.length - 1 ? gap : 0));
          const fits = w > 58;
          const content = (
            <>
              <div className="tt-title">{s.label}</div>
              <div className="tt-row">
                <span className="k">Reports</span>
                <span className="v">{s.value.toLocaleString("en-US")}</span>
              </div>
              <div className="tt-row">
                <span className="k">Share</span>
                <span className="v">{s.pct.toFixed(1)}%</span>
              </div>
            </>
          );
          return (
            <g key={i} onMouseMove={(e) => show(e, content)} onMouseLeave={hide}>
              <rect x={s.x} y={0} width={w} height={height} rx={4} fill={s.color} />
              {fits && (
                <>
                  <text x={s.x + 12} y={17} style={{ fill: "#fff", fontSize: 12, fontWeight: 600 }}>
                    {s.value.toLocaleString("en-US")}
                  </text>
                  <text x={s.x + 12} y={31} style={{ fill: "rgba(255,255,255,0.85)", fontSize: 11 }}>
                    {s.pct.toFixed(0)}%
                  </text>
                </>
              )}
            </g>
          );
        })}
      </svg>
      <Tip tip={tip} />
    </div>
  );
}
