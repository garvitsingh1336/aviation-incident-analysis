import { severityColor, themeColor } from "../lib/palette.js";

export function Card({ title, hint, sub, children, className = "", style }) {
  return (
    <div className={`card ${className}`} style={style}>
      {(title || hint) && (
        <div className="card-head">
          {title && <h3>{title}</h3>}
          {hint && <span className="hint">{hint}</span>}
        </div>
      )}
      {sub && <div className="card-sub">{sub}</div>}
      {children}
    </div>
  );
}

export function StatTile({ label, value, meta, hero = false }) {
  return (
    <div className="tile">
      <div className="label">{label}</div>
      <div className={`value ${hero ? "hero" : ""}`}>{value}</div>
      {meta && <div className="meta">{meta}</div>}
    </div>
  );
}

export function SeverityBadge({ severity }) {
  if (!severity) return <span className="muted">—</span>;
  return (
    <span className="badge">
      <span className="dot" style={{ background: severityColor(severity) }} />
      {severity}
    </span>
  );
}

export function ThemeBadge({ theme, onClick }) {
  return (
    <span
      className="badge"
      style={onClick ? { cursor: "pointer" } : undefined}
      onClick={onClick}
    >
      <span className="dot" style={{ background: themeColor(theme) }} />
      {theme}
    </span>
  );
}

export function Chips({ items }) {
  return (
    <div className="chips">
      {items.map((it, i) => (
        <span className="chip" key={i}>
          {it}
        </span>
      ))}
    </div>
  );
}

export function BarMeter({ value, max, color = "var(--accent)" }) {
  const w = max > 0 ? Math.max(2, (value / max) * 100) : 0;
  return (
    <div className="bar-track">
      <div className="bar-fill" style={{ width: `${w}%`, background: color }} />
    </div>
  );
}

export function StageTag({ children }) {
  return <div className="stage-tag">{children}</div>;
}

export function ViewHead({ stage, title, children }) {
  return (
    <div className="view-head">
      {stage && <StageTag>{stage}</StageTag>}
      <h2>{title}</h2>
      {children && <p>{children}</p>}
    </div>
  );
}

export function Loading({ label = "Loading analysis…" }) {
  return (
    <div className="center-pad">
      <div className="spinner" />
      <div>{label}</div>
    </div>
  );
}

export function ErrorState({ error, onRetry }) {
  return (
    <div className="error-box">
      <b>Couldn’t load data.</b>
      <div className="secondary" style={{ margin: "6px 0 12px" }}>
        {String(error?.message || error)}
      </div>
      <div className="secondary" style={{ fontSize: 12 }}>
        Make sure the backend is running:&nbsp;
        <code>cd backend &amp;&amp; python run.py</code>
      </div>
      {onRetry && (
        <button className="btn" style={{ marginTop: 12 }} onClick={onRetry}>
          Retry
        </button>
      )}
    </div>
  );
}

/** Legend with click-to-focus. `active` is a Set of keys currently shown. */
export function Legend({ items, active, onToggle }) {
  return (
    <div className="legend">
      {items.map((it) => {
        const on = !active || active.has(it.key);
        return (
          <button
            key={it.key}
            className={`item ${on ? "" : "muted"}`}
            onClick={onToggle ? () => onToggle(it.key) : undefined}
            style={{ cursor: onToggle ? "pointer" : "default" }}
          >
            <span className="swatch" style={{ background: it.color }} />
            {it.label}
          </button>
        );
      })}
    </div>
  );
}
