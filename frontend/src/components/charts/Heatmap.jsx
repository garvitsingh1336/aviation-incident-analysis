import { useSize } from "../../lib/useSize.js";
import { sequentialBin, sequentialInk } from "../../lib/palette.js";
import { useTip, Tip } from "../Tooltip.jsx";

/**
 * Square matrix heat-map (co-occurrence). One blue hue, light→dark (sequential
 * = magnitude); 2px surface gaps between cells; values printed when the cell is
 * large enough, full detail in the tooltip. Axis labels use short codes with a
 * legend supplied by the parent.
 */
export default function Heatmap({ codes, fullLabels, value, max, tipOf, cellMax = 60 }) {
  const [ref, W] = useSize();
  const { tip, show, hide } = useTip();
  const n = codes.length;
  const labelCol = 46;
  const headRow = 24;
  const cell = Math.max(28, Math.min(cellMax, (W - labelCol) / n));
  const gridH = cell * n;
  const H = headRow + gridH + 6;

  return (
    <div ref={ref} style={{ width: "100%" }}>
      <svg className="chart" width={W} height={H} role="img">
        {/* column codes */}
        {codes.map((c, j) => (
          <text key={j} x={labelCol + j * cell + cell / 2} y={headRow - 8} textAnchor="middle"
            style={{ fill: "var(--text-secondary)", fontSize: 11, fontWeight: 600 }}>
            {c}
          </text>
        ))}
        {/* row codes */}
        {codes.map((c, i) => (
          <text key={i} x={labelCol - 10} y={headRow + i * cell + cell / 2} textAnchor="end"
            dominantBaseline="middle"
            style={{ fill: "var(--text-secondary)", fontSize: 11, fontWeight: 600 }}>
            {c}
          </text>
        ))}
        {codes.map((_, i) =>
          codes.map((__, j) => {
            const v = value(i, j);
            const x = labelCol + j * cell;
            const y = headRow + i * cell;
            const isDiag = i === j;
            const fill = isDiag ? "var(--surface-2)" : sequentialBin(v, max);
            const content = tipOf(i, j);
            return (
              <g key={`${i}-${j}`} onMouseMove={(e) => show(e, content)} onMouseLeave={hide}>
                <rect x={x + 1} y={y + 1} width={cell - 2} height={cell - 2} rx={3} fill={fill} />
                {!isDiag && v > 0 && cell >= 34 && (
                  <text x={x + cell / 2} y={y + cell / 2} textAnchor="middle" dominantBaseline="middle"
                    style={{ fill: sequentialInk(v, max), fontSize: 11.5, fontWeight: 600,
                      fontVariantNumeric: "tabular-nums" }}>
                    {v}
                  </text>
                )}
                {isDiag && (
                  <text x={x + cell / 2} y={y + cell / 2} textAnchor="middle" dominantBaseline="middle"
                    style={{ fill: "var(--muted)", fontSize: 11 }}>
                    —
                  </text>
                )}
              </g>
            );
          })
        )}
      </svg>
      <Tip tip={tip} />
    </div>
  );
}
