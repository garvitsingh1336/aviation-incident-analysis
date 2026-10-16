/** SVG geometry helpers shared by the chart components. */

/** "Nice" axis ticks: rounded step covering [0, max], ~count divisions. */
export function niceTicks(max, count = 5) {
  if (!max || max <= 0) return [0];
  const raw = max / count;
  const mag = Math.pow(10, Math.floor(Math.log10(raw)));
  const norm = raw / mag;
  let step;
  if (norm < 1.5) step = 1;
  else if (norm < 3) step = 2;
  else if (norm < 7) step = 5;
  else step = 10;
  step *= mag;
  const ticks = [];
  for (let t = 0; t <= max + 1e-9; t += step) ticks.push(Math.round(t * 1000) / 1000);
  if (ticks[ticks.length - 1] < max) ticks.push(ticks[ticks.length - 1] + step);
  return ticks;
}

export const niceMax = (max, count = 5) => {
  const t = niceTicks(max, count);
  return t[t.length - 1] || 1;
};

/**
 * Path for a bar with two rounded corners on the DATA end only (square at the
 * baseline), per the mark spec.  `side` = which end is the data end.
 */
export function barPath(x, y, w, h, r, side = "right") {
  r = Math.max(0, Math.min(r, w / 2, h / 2));
  if (w <= 0 || h <= 0) return "";
  switch (side) {
    case "right": // horizontal bar growing right; round right corners
      return `M${x},${y} H${x + w - r} A${r},${r} 0 0 1 ${x + w},${y + r} V${y + h - r} A${r},${r} 0 0 1 ${x + w - r},${y + h} H${x} Z`;
    case "top": // vertical column growing up; round top corners
      return `M${x},${y + h} V${y + r} A${r},${r} 0 0 1 ${x + r},${y} H${x + w - r} A${r},${r} 0 0 1 ${x + w},${y + r} V${y + h} Z`;
    default:
      return `M${x},${y} h${w} v${h} h${-w} Z`;
  }
}

/** Smooth-ish polyline path (straight segments, rounded joins via stroke). */
export function linePath(points) {
  if (!points.length) return "";
  return points.map((p, i) => `${i === 0 ? "M" : "L"}${p[0]},${p[1]}`).join(" ");
}

/** Closed area path from a top polyline down to a baseline y. */
export function areaPath(points, baselineY) {
  if (!points.length) return "";
  const top = points.map((p, i) => `${i === 0 ? "M" : "L"}${p[0]},${p[1]}`).join(" ");
  const last = points[points.length - 1];
  const first = points[0];
  return `${top} L${last[0]},${baselineY} L${first[0]},${baselineY} Z`;
}

/** Area band between an upper and lower polyline (for stacked areas). */
export function bandPath(upper, lower) {
  if (!upper.length) return "";
  const top = upper.map((p, i) => `${i === 0 ? "M" : "L"}${p[0]},${p[1]}`).join(" ");
  const bottom = lower
    .slice()
    .reverse()
    .map((p) => `L${p[0]},${p[1]}`)
    .join(" ");
  return `${top} ${bottom} Z`;
}
