import { api } from "../api.js";
import { useApi } from "../lib/useApi.js";
import { commas } from "../lib/format.js";
import { seriesVar } from "../lib/palette.js";
import { Card, StatTile, ViewHead, Loading, ErrorState } from "../components/ui.jsx";
import HBar from "../components/charts/HBar.jsx";

// Canonical entity types → fixed categorical slot + human label. Colour follows
// the entity type, never its rank, and the order is stable across renders.
const ENTITY_TYPES = [
  { key: "aircraft", label: "Aircraft types", slot: 1 },
  { key: "organisation", label: "Organisations & operators", slot: 2 },
  { key: "airport", label: "Airports", slot: 3 },
  { key: "location", label: "Locations", slot: 4 },
  { key: "equipment", label: "Equipment & components", slot: 5 },
  { key: "facility", label: "Facilities", slot: 6 },
];

const TOP_N = 10;

export default function Entities() {
  const { data, loading, error, reload } = useApi(() => api.entities(), []);

  if (loading) return <Loading />;
  if (error) return <ErrorState error={error} onRetry={reload} />;

  const present = ENTITY_TYPES.map((t) => ({ ...t, items: data[t.key] || [] })).filter(
    (t) => t.items.length > 0
  );

  const distinct = present.reduce((s, t) => s + t.items.length, 0);
  const mentions = present.reduce(
    (s, t) => s + t.items.reduce((a, e) => a + (e.count || 0), 0),
    0
  );
  const top = present
    .flatMap((t) => t.items.map((e) => ({ ...e, type: t.label })))
    .sort((a, b) => b.count - a.count)[0];

  return (
    <>
      <ViewHead stage="Stage 4 · Named Entity Recognition" title="Who and what the reports name">
        A transformer-based NER model tags each narrative, and the mentions are aggregated across the
        corpus. These entities ground the abstract topics in concrete aircraft, operators, airports
        and equipment — and feed the semantic search and relationship views.
      </ViewHead>

      <div className="grid cols-4" style={{ marginBottom: 16 }}>
        <StatTile label="Entity types" value={present.length} />
        <StatTile label="Distinct entities" value={commas(distinct)} meta="unique mentions across the corpus" />
        <StatTile label="Total mentions" value={commas(mentions)} />
        <StatTile label="Most mentioned" value={top ? top.text : "—"}
          meta={top ? `${commas(top.count)} · ${top.type}` : undefined} />
      </div>

      <div className="grid cols-2">
        {present.map((t) => {
          const rows = [...t.items]
            .sort((a, b) => b.count - a.count)
            .slice(0, TOP_N)
            .map((e) => ({ label: e.text, value: e.count, color: seriesVar(t.slot) }));
          return (
            <Card key={t.key} title={t.label} hint={`${commas(t.items.length)} distinct`}
              sub={`Top ${Math.min(TOP_N, t.items.length)} by number of reports mentioning them.`}>
              <HBar data={rows} format={commas} labelWidth={168} unit="mentions" />
            </Card>
          );
        })}
      </div>
    </>
  );
}
