import { useMemo } from "react";
import { useSize } from "../../lib/useSize.js";
import { useTip, Tip } from "../Tooltip.jsx";

/**
 * 2D semantic map. Each point is one report positioned by the UMAP/SVD
 * projection of its embedding; colour encodes severity (three validated hues,
 * legend supplied by the parent). r≥4 marks carry a 2px surface ring so
 * overlaps stay legible. Hover for details, click to open the report.
 */
export default function Scatter({ points, colorOf, onSelect, height = 460, tipOf }) {
  const [ref, W] = useSize();
  const { tip, show, hide } = useTip();

  const m = 18;
  const { xFor, yFor } = useMemo(() => {
    const xs = points.map((p) => p.x);
    const ys = points.map((p) => p.y);
    const minX = Math.min(...xs), maxX = Math.max(...xs);
    const minY = Math.min(...ys), maxY = Math.max(...ys);
    const padX = (maxX - minX) * 0.04 || 1;
    const padY = (maxY - minY) * 0.04 || 1;
    const plotW = Math.max(60, W - m * 2);
    const plotH = height - m * 2;
    return {
      xFor: (x) => m + ((x - minX + padX) / (maxX - minX + 2 * padX)) * plotW,
      yFor: (y) => m + plotH - ((y - minY + padY) / (maxY - minY + 2 * padY)) * plotH,
    };
  }, [points, W, height]);

  return (
    <div ref={ref} style={{ width: "100%" }}>
      <svg className="chart" width={W} height={height} role="img"
        style={{ background: "var(--surface-2)", borderRadius: 10 }}>
        {points.map((p) => {
          const c = colorOf(p);
          const content = tipOf ? tipOf(p) : (
            <>
              <div className="tt-title">{p.report_id}</div>
              <div className="tt-row">
                <span className="k">Topic</span>
                <span className="v" style={{ maxWidth: 150, textAlign: "right" }}>{p.topic_label}</span>
              </div>
              <div className="tt-row">
                <span className="k">Cluster</span>
                <span className="v">#{p.cluster_id}</span>
              </div>
              <div className="tt-row">
                <span className="k"><span className="sw" style={{ background: c }} />Severity</span>
                <span className="v">{p.severity}</span>
              </div>
            </>
          );
          return (
            <circle
              key={p.idx}
              cx={xFor(p.x)}
              cy={yFor(p.y)}
              r="4.5"
              fill={c}
              stroke="var(--surface-1)"
              strokeWidth="1.5"
              style={{ cursor: onSelect ? "pointer" : "default" }}
              onMouseMove={(e) => show(e, content)}
              onMouseLeave={hide}
              onClick={onSelect ? () => onSelect(p.idx) : undefined}
            />
          );
        })}
      </svg>
      <Tip tip={tip} />
    </div>
  );
}
