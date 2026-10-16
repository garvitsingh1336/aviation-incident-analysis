import { useState, useCallback } from "react";

/** Fixed-position hover tooltip shared by every chart. */
export function useTip() {
  const [tip, setTip] = useState(null);
  const show = useCallback((e, content) => {
    setTip({ x: e.clientX, y: e.clientY, content });
  }, []);
  const hide = useCallback(() => setTip(null), []);
  return { tip, show, hide };
}

export function Tip({ tip }) {
  if (!tip) return null;
  const nearRight = tip.x > window.innerWidth - 300;
  const nearBottom = tip.y > window.innerHeight - 160;
  const style = {
    left: nearRight ? undefined : tip.x + 14,
    right: nearRight ? window.innerWidth - tip.x + 14 : undefined,
    top: nearBottom ? undefined : tip.y + 14,
    bottom: nearBottom ? window.innerHeight - tip.y + 14 : undefined,
  };
  return (
    <div className="tt" style={style}>
      {tip.content}
    </div>
  );
}

/** Convenience row for tooltip contents. */
export function TipRow({ swatch, k, v }) {
  return (
    <div className="tt-row">
      <span className="k">
        {swatch && <span className="sw" style={{ background: swatch }} />}
        {k}
      </span>
      <span className="v">{v}</span>
    </div>
  );
}
