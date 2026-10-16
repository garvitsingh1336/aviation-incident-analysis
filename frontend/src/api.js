/**
 * Thin API client for the FastAPI backend.
 *
 * In development Vite proxies /api to http://127.0.0.1:8000 (see vite.config.js);
 * in production the SPA is served by the same FastAPI app, so a relative /api
 * base works in both cases.
 */

const BASE = "/api";

async function get(path, params) {
  const url = new URL(BASE + path, window.location.origin);
  if (params) {
    for (const [k, v] of Object.entries(params)) {
      if (v !== undefined && v !== null && v !== "") url.searchParams.set(k, v);
    }
  }
  const res = await fetch(url.pathname + url.search, {
    headers: { Accept: "application/json" },
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch (_) {
      /* ignore */
    }
    throw new Error(`${res.status} ${detail}`);
  }
  return res.json();
}

async function post(path) {
  const res = await fetch(BASE + path, { method: "POST" });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
}

export const api = {
  health: () => get("/health"),
  overview: () => get("/overview"),
  topics: () => get("/topics"),
  clusters: () => get("/clusters"),
  factors: () => get("/factors"),
  relationships: () => get("/relationships"),
  trends: () => get("/trends"),
  entities: () => get("/entities"),
  scatter: () => get("/scatter"),
  reports: (params) => get("/reports", params),
  report: (idx) => get(`/reports/${idx}`),
  search: (q, k = 10) => get("/search", { q, k }),
  rebuild: () => post("/rebuild"),
};
