/**
 * Validated colour system for the dashboard.
 *
 * The hex values live in theme.css as CSS custom properties (one set for light,
 * one for dark) so a single theme toggle re-colours every chart.  This module
 * maps DOMAIN ENTITIES (themes, severities) to *stable* colour slots and returns
 * `var(--…)` strings that SVG marks consume via inline styles.
 *
 * Colour rules honoured here (see the data-viz method):
 *  - Categorical hues are assigned in a FIXED order, never cycled.
 *  - Colour follows the entity, never its rank — a theme keeps its slot no
 *    matter how the data is filtered or sorted.
 *  - The 8-slot categorical ramp passes the CVD / normal-vision gates on the
 *    adjacent pairlist in both modes (validated with scripts/validate_palette.js).
 *  - Severity uses the first three slots, which additionally pass the ALL-PAIRS
 *    gate (needed for the scatter map where colour is the only channel); it is
 *    always shown beside a text label or legend.
 *  - Status colours (increasing / decreasing / stable) are reserved and ship
 *    with an icon + label, never colour alone.
 */

// Number of categorical slots defined in theme.css (--series-1 … --series-8).
export const N_SERIES = 8;

export const seriesVar = (slot) => `var(--series-${((slot - 1) % N_SERIES) + 1})`;

// --- Contributing-factor themes -------------------------------------------- //
// Canonical order MUST match backend THEME_KEYWORDS so each theme is pinned to
// one slot for the life of the app.
export const THEME_ORDER = [
  "Weather & Environment",
  "Powerplant & Fuel",
  "Human Factors & ATC",
  "Runway & Ground Ops",
  "Mechanical & Systems",
  "Loss of Control & Terrain",
  "Wildlife",
];

const THEME_SLOT = Object.fromEntries(THEME_ORDER.map((t, i) => [t, i + 1]));

export function themeColor(theme) {
  const slot = THEME_SLOT[theme];
  return slot ? seriesVar(slot) : "var(--muted)";
}

// --- Severity -------------------------------------------------------------- //
// Ordinal, but rendered as three distinct validated hues (slots 1–3) so it is
// legible as colour-alone on the scatter; always paired with a label elsewhere.
export const SEVERITY_ORDER = ["Incident", "Serious Incident", "Accident"];

const SEVERITY_SLOT = {
  Incident: 1,
  "Serious Incident": 2,
  Accident: 3,
};

export function severityColor(severity) {
  const slot = SEVERITY_SLOT[severity];
  return slot ? seriesVar(slot) : "var(--muted)";
}

// --- Sequential ramp (discrete bins) --------------------------------------- //
// Used by the co-occurrence heat-map.  Six bins of one blue hue, light→dark;
// values are normalised to [0,1] then bucketed.  CSS vars --seq-0 … --seq-5.
export const N_SEQ_BINS = 6;

export function sequentialBin(value, max) {
  if (!max || max <= 0) return "var(--seq-0)";
  const t = Math.max(0, Math.min(1, value / max));
  const bin = Math.min(N_SEQ_BINS - 1, Math.floor(t * N_SEQ_BINS));
  return `var(--seq-${bin})`;
}

// Ink colour that stays legible on a given sequential bin.  theme.css defines
// --seq-ink-0 … --seq-ink-5 per mode (dark bins take white ink, light bins take
// dark ink — and the mapping flips in dark mode where the ramp is inverted).
export function sequentialInk(value, max) {
  if (!max || max <= 0) return "var(--seq-ink-0)";
  const t = Math.max(0, Math.min(1, value / max));
  const bin = Math.min(N_SEQ_BINS - 1, Math.floor(t * N_SEQ_BINS));
  return `var(--seq-ink-${bin})`;
}

// --- Status (trend direction) ---------------------------------------------- //
export const STATUS = {
  increasing: { varName: "var(--status-critical)", icon: "▲", label: "Increasing" },
  decreasing: { varName: "var(--status-good)", icon: "▼", label: "Decreasing" },
  stable: { varName: "var(--muted)", icon: "▬", label: "Stable" },
};
