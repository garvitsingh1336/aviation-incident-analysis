import { useState, useMemo } from "react";
import { useSize } from "../../lib/useSize.js";
import { useTip, Tip } from "../Tooltip.jsx";

/**
 * Circular co-occurrence network. Nodes are contributing-factor themes (size =
 * how many reports mention the theme, colour = the theme's fixed slot); edges
 * are pairwise co-occurrences (width = joint count). Hover a node to isolate
 * its links; hover an edge for count / lift / Jaccard. Edge width is the only
 * quantitative channel, explained in the caption.
 */
export default function Network({ nodes, edges, colorOf, codeOf, height = 420 }) {
  const [ref, W] = useSize();
  const { tip, show, hide } = useTip();
  const [hoverNode, setHoverNode] = useState(null);

  const cx = W / 2;
  const cy = height / 2;
  const R = Math.max(80, Math.min(W, height) / 2 - 78);
  const maxCount = Math.max(1, ...nodes.map((n) => n.count));
  const maxEdge = Math.max(1, ...edges.map((e) => e.count));

  const pos = useMemo(() => {
    const map = {};
    const n = nodes.length;
    nodes.forEach((node, i) => {
      const a = -Math.PI / 2 + (i / n) * 2 * Math.PI;
      map[node.id] = { x: cx + R * Math.cos(a), y: cy + R * Math.sin(a), a };
    });
    return map;
  }, [nodes, cx, cy, R]);

  const nodeR = (c) => 8 + (c / maxCount) * 15;
  const edgeW = (c) => 1.5 + (c / maxEdge) * 9;

  return (
    <div ref={ref} style={{ width: "100%" }}>
      <svg className="chart" width={W} height={height} role="img">
        {/* edges */}
        {edges.map((e, i) => {
          const s = pos[e.source];
          const t = pos[e.target];
          if (!s || !t) return null;
          const active =
            hoverNode === null || e.source === hoverNode || e.target === hoverNode;
          const mx = (s.x + t.x) / 2 + (cx - (s.x + t.x) / 2) * 0.25;
          const my = (s.y + t.y) / 2 + (cy - (s.y + t.y) / 2) * 0.25;
          const content = (
            <>
              <div className="tt-title">
                {e.source} ↔ {e.target}
              </div>
              <div className="tt-row"><span className="k">Co-occurrences</span><span className="v">{e.count}</span></div>
              <div className="tt-row"><span className="k">Lift</span><span className="v">{e.lift.toFixed(2)}×</span></div>
              <div className="tt-row"><span className="k">Jaccard</span><span className="v">{e.jaccard.toFixed(3)}</span></div>
            </>
          );
          return (
            <path
              key={i}
              d={`M${s.x},${s.y} Q${mx},${my} ${t.x},${t.y}`}
              fill="none"
              stroke="var(--baseline)"
              strokeWidth={edgeW(e.count)}
              strokeLinecap="round"
              opacity={active ? (e.lift >= 1.15 ? 0.85 : 0.5) : 0.08}
              style={{ transition: "opacity 0.12s" }}
              onMouseMove={(ev) => show(ev, content)}
              onMouseLeave={hide}
            />
          );
        })}
        {/* nodes */}
        {nodes.map((node) => {
          const p = pos[node.id];
          if (!p) return null;
          const active = hoverNode === null || hoverNode === node.id ||
            edges.some((e) => (e.source === node.id && e.target === hoverNode) ||
              (e.target === node.id && e.source === hoverNode));
          const outward = p.x >= cx ? 1 : -1;
          const content = (
            <>
              <div className="tt-title">{node.id}</div>
              <div className="tt-row"><span className="k">Reports mentioning</span><span className="v">{node.count}</span></div>
            </>
          );
          return (
            <g key={node.id} opacity={active ? 1 : 0.2}
              style={{ transition: "opacity 0.12s", cursor: "pointer" }}
              onMouseEnter={() => setHoverNode(node.id)}
              onMouseLeave={() => { setHoverNode(null); hide(); }}
              onMouseMove={(e) => show(e, content)}>
              <circle cx={p.x} cy={p.y} r={nodeR(node.count)} fill={colorOf(node.id)}
                stroke="var(--surface-1)" strokeWidth="2" />
              <text
                x={p.x + outward * (nodeR(node.count) + 6)}
                y={p.y}
                textAnchor={outward === 1 ? "start" : "end"}
                dominantBaseline="middle"
                style={{ fill: "var(--text-primary)", fontSize: 11.5, fontWeight: 600 }}>
                {codeOf(node.id)}
              </text>
            </g>
          );
        })}
      </svg>
      <Tip tip={tip} />
    </div>
  );
}
