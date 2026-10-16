"""REST API for the aviation incident analysis dashboard."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from ..core.capabilities import capabilities, engine_summary
from ..core.store import store

router = APIRouter(prefix="/api")


@router.get("/health")
def health():
    loaded = store.analysis is not None
    return {
        "status": "ok",
        "analysis_loaded": loaded,
        "capabilities": capabilities(),
        "engines": engine_summary(),
        "generated_at": store.analysis["meta"]["generated_at"] if loaded else None,
    }


@router.get("/overview")
def overview():
    a = store.analysis
    return {
        "meta": a["meta"],
        "stats": a["stats"],
        "top_factors": a["factors"]["factors"][:8],
        "themes": a["factors"]["themes"],
        "trends": {
            "years": a["trends"]["years"],
            "total_by_year": a["trends"]["total_by_year"],
            "signals": a["trends"]["signals"][:6],
        },
        "topics_comparison": a["topics_comparison"],
    }


@router.get("/topics")
def topics():
    a = store.analysis
    return {
        "primary": {
            "engine": a["topics"]["engine"],
            "topics": a["topics"]["topics"],
        },
        "lda": a["lda"],
        "comparison": a["topics_comparison"],
    }


@router.get("/clusters")
def clusters():
    return store.analysis["clusters"]


@router.get("/factors")
def factors():
    return store.analysis["factors"]


@router.get("/relationships")
def relationships():
    return store.analysis["relationships"]


@router.get("/trends")
def trends():
    return store.analysis["trends"]


@router.get("/entities")
def entities():
    return store.analysis["entities"]


@router.get("/scatter")
def scatter():
    """Compact per-report coordinates for the semantic map."""
    pts = [
        {
            "idx": r["idx"], "x": r["x"], "y": r["y"],
            "topic_id": r["topic_id"], "topic_label": r["topic_label"],
            "cluster_id": r["cluster_id"], "severity": r["severity"],
            "report_id": r["report_id"],
        }
        for r in store.reports()
    ]
    return {"points": pts}


@router.get("/reports")
def list_reports(
    topic_id: Optional[int] = None,
    cluster_id: Optional[int] = None,
    theme: Optional[str] = None,
    severity: Optional[str] = None,
    year: Optional[int] = None,
    q: Optional[str] = Query(None, description="case-insensitive substring match"),
    limit: int = 25,
    offset: int = 0,
):
    rows = store.reports()

    def keep(r) -> bool:
        if topic_id is not None and r["topic_id"] != topic_id:
            return False
        if cluster_id is not None and r["cluster_id"] != cluster_id:
            return False
        if theme is not None and theme not in (r.get("themes") or []):
            return False
        if severity is not None and r.get("severity") != severity:
            return False
        if year is not None and r.get("year") != year:
            return False
        if q and q.lower() not in r["narrative"].lower():
            return False
        return True

    filtered = [r for r in rows if keep(r)]
    total = len(filtered)
    page = filtered[offset: offset + limit]
    items = [
        {
            "idx": r["idx"], "report_id": r["report_id"], "date": r["date"],
            "severity": r["severity"], "topic_label": r["topic_label"],
            "cluster_id": r["cluster_id"], "themes": r["themes"],
            "aircraft_type": r["aircraft_type"], "airport": r["airport"],
            "location": r["location"], "phase_of_flight": r["phase_of_flight"],
            "snippet": r["narrative"][:220] + ("..." if len(r["narrative"]) > 220 else ""),
        }
        for r in page
    ]
    return {"total": total, "limit": limit, "offset": offset, "items": items}


@router.get("/reports/{idx}")
def get_report(idx: int):
    r = store.report(idx)
    if r is None:
        raise HTTPException(status_code=404, detail="report not found")
    return {"report": r, "similar": store.similar(idx, top_k=6)}


@router.get("/search")
def search(q: str = Query(..., min_length=2), k: int = 10):
    return {"query": q, "results": store.search(q, top_k=k)}


@router.post("/rebuild")
def rebuild():
    meta = store.rebuild()
    return {"status": "rebuilt", "meta": meta}
