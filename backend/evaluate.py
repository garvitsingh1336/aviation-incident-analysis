"""Stage 14: Testing & Evaluation.

A self-contained, offline evaluation harness for the analysis pipeline. It loads
the very same :class:`AnalysisStore` the API uses, verifies the pipeline produced
structurally-coherent output, and reports intrinsic, label-free quality metrics
plus semantic-search sanity checks.

    cd backend
    python evaluate.py

Exit code is non-zero if any hard check fails, so it doubles as a CI smoke test.
Output is plain ASCII so it renders correctly in any console.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Make the `app` package importable regardless of the current directory.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.core.capabilities import capabilities, engine_summary  # noqa: E402
from app.core.store import store  # noqa: E402


# --------------------------------------------------------------------------- #
# Tiny result collector
# --------------------------------------------------------------------------- #
class Results:
    PASS, FAIL, INFO = "PASS", "FAIL", "info"

    def __init__(self) -> None:
        self.rows: list[tuple[str, str, str]] = []
        self.failures = 0

    def check(self, cond: bool, name: str, ok: str = "", bad: str = "") -> bool:
        status = self.PASS if cond else self.FAIL
        if not cond:
            self.failures += 1
        self.rows.append((status, name, ok if cond else bad))
        return cond

    def info(self, name: str, detail: str = "") -> None:
        self.rows.append((self.INFO, name, detail))

    def section(self, title: str) -> None:
        self.rows.append(("", "== " + title + " ==", ""))

    def render(self) -> None:
        tag = {self.PASS: "[PASS]", self.FAIL: "[FAIL]", self.INFO: "[ -- ]", "": ""}
        print()
        for status, name, detail in self.rows:
            if status == "":
                print("\n" + name)
                continue
            line = f"  {tag[status]}  {name}"
            if detail:
                line += f"  ->  {detail}"
            print(line)
        print()
        total_checks = sum(1 for s, _, _ in self.rows if s in (self.PASS, self.FAIL))
        passed = total_checks - self.failures
        verdict = "ALL CHECKS PASSED" if self.failures == 0 else f"{self.failures} CHECK(S) FAILED"
        print("-" * 60)
        print(f"  {passed}/{total_checks} checks passed   |   {verdict}")
        print("-" * 60)


# --------------------------------------------------------------------------- #
# Semantic-search sanity probes: conceptual query -> words we expect to see in a
# topically-relevant hit (matched against narrative / topic label / themes).
# --------------------------------------------------------------------------- #
SEARCH_PROBES = [
    ("bird strike shortly after takeoff", ["bird", "wildlife", "strike", "takeoff", "climb"]),
    ("engine failure forcing an emergency landing", ["engine", "power", "failure", "emergency", "forced"]),
    ("poor visibility and fog on approach", ["visibility", "fog", "weather", "ceiling", "ifr", "cloud"]),
    ("runway incursion and ground conflict", ["runway", "incursion", "ground", "taxi", "taxiway"]),
    ("loss of control in icing conditions", ["ice", "icing", "control", "stall", "weather"]),
]


def _hit_is_relevant(report: dict, keywords: list[str]) -> bool:
    hay = " ".join([
        (report.get("narrative") or ""),
        (report.get("topic_label") or ""),
        " ".join(report.get("themes") or []),
    ]).lower()
    return any(kw in hay for kw in keywords)


def main() -> int:
    r = Results()

    print("Loading analysis store (building artifacts if absent)...")
    store.ensure_loaded()
    a = store.analysis

    # --- Artifacts / engines ---------------------------------------------- #
    r.section("Artifacts & engines")
    r.check(a is not None, "analysis artifact loaded", bad="store.analysis is None")
    caps = capabilities()
    engines = engine_summary()
    for stage, desc in engines.items():
        r.info(f"engine.{stage}", desc)
    r.info("forced_lightweight", str(caps.get("forced_lightweight")))

    # --- Corpus ------------------------------------------------------------ #
    r.section("Corpus")
    reports = store.reports()
    stats = a.get("stats", {})
    r.check(len(reports) > 0, "corpus is non-empty", ok=f"{len(reports)} reports")
    r.check(
        stats.get("total_reports", 0) == len(reports),
        "stats.total_reports matches report count",
        ok=f"{stats.get('total_reports')} reports",
        bad=f"stats={stats.get('total_reports')} vs actual={len(reports)}",
    )
    dr = stats.get("date_range")
    if dr:
        r.info("date range", f"{dr[0]} .. {dr[1]}")

    # --- Topic modelling (BERTopic vs LDA baseline) ------------------------ #
    r.section("Topic modelling (Stage 6)")
    tc = a.get("topics_comparison", {})
    r.info("primary engine", str(tc.get("primary_engine")))
    r.check(tc.get("primary_topics", 0) > 0, "primary model found topics",
            ok=f"{tc.get('primary_topics')} topics")
    r.check(tc.get("lda_topics", 0) > 0, "LDA baseline found topics",
            ok=f"{tc.get('lda_topics')} topics")
    if tc.get("lda_perplexity") is not None:
        r.info("LDA perplexity", f"{tc.get('lda_perplexity'):.1f} (lower is better)")

    # --- Clustering -------------------------------------------------------- #
    r.section("Clustering (Stage 7)")
    sil = stats.get("silhouette")
    r.check(
        isinstance(sil, (int, float)) and -1.0 <= float(sil) <= 1.0,
        "silhouette score in valid range [-1, 1]",
        ok=f"silhouette = {sil:.3f}" if isinstance(sil, (int, float)) else "",
        bad=f"silhouette = {sil!r}",
    )
    n_clusters = stats.get("n_clusters", 0)
    r.check(n_clusters and n_clusters > 1, "more than one cluster", ok=f"{n_clusters} clusters")

    # --- Contributing factors & themes ------------------------------------ #
    r.section("Contributing factors (Stage 8) & themes")
    factors = (a.get("factors") or {}).get("factors") or []
    r.check(len(factors) > 0, "contributing factors discovered", ok=f"{len(factors)} factors")
    r.check(stats.get("n_themes", 0) > 0, "safety themes present", ok=f"{stats.get('n_themes')} themes")
    if factors:
        top = factors[0]
        r.info("top factor", f"{top.get('label')} ({top.get('theme')}, n={top.get('count')})")

    # --- Relationships & trends ------------------------------------------- #
    r.section("Relationships (Stage 9) & trends (Stage 10)")
    rel = a.get("relationships") or {}
    r.check(bool(rel), "co-occurrence relationships present")
    trends = a.get("trends") or {}
    r.check(len(trends.get("years", [])) > 0, "trend years present",
            ok=f"{len(trends.get('years', []))} years")
    r.info("trend signals", str(len(trends.get("signals", []))))

    # --- Named entities ---------------------------------------------------- #
    r.section("Named-entity recognition (Stage 4)")
    entities = a.get("entities") or {}
    present = [k for k, v in entities.items() if v]
    r.check(len(present) > 0, "entities extracted", ok=", ".join(present))

    # --- Semantic search (Stage 12) --------------------------------------- #
    r.section("Semantic search (Stage 12)")
    relevant_count = 0
    for query, keywords in SEARCH_PROBES:
        hits = store.search(query, top_k=5)
        returned = r.check(len(hits) > 0, f'query returns results: "{query}"',
                           ok=f"{len(hits)} hits", bad="no results")
        if not returned:
            continue
        top3 = hits[:3]
        rel_hit = any(_hit_is_relevant(h.get("report") or {}, keywords) for h in top3)
        best = hits[0]
        best_rep = best.get("report") or {}
        label = best_rep.get("topic_label") or best_rep.get("report_id") or f"#{best.get('idx')}"
        marker = "relevant" if rel_hit else "no keyword match in top-3"
        r.info(f'  top hit for "{query}"', f'{label}  (score {best.get("score")})  [{marker}]')
        relevant_count += 1 if rel_hit else 0

    rate = relevant_count / len(SEARCH_PROBES)
    r.info("search relevance", f"{relevant_count}/{len(SEARCH_PROBES)} queries relevant in top-3 ({rate:.0%})")

    # --- Nearest-neighbour similarity ------------------------------------- #
    r.section("Nearest-neighbour similarity")
    if reports:
        idx0 = reports[0]["idx"]
        sim = store.similar(idx0, top_k=6)
        r.check(len(sim) > 0, "similar-report lookup returns neighbours", ok=f"{len(sim)} neighbours")
        r.check(all(s["idx"] != idx0 for s in sim), "a report is not its own neighbour")

    r.render()
    return 1 if r.failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
