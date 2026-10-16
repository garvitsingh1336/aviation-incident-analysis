"""Stage 9: Relationship analysis.

Finds themes that frequently occur *together* in the same report.  Because a
single report can describe several contributing factors at once (e.g. weather
that leads to a loss of control), theme presence is detected from the narrative
text via the safety taxonomy.  The result is a co-occurrence network: nodes are
themes, edges carry the co-occurrence count and a *lift* score (how much more
often two themes appear together than chance would predict).
"""
from __future__ import annotations

from collections import Counter
from itertools import combinations
from typing import Dict, List

from .factors import THEME_KEYWORDS


def _themes_in_text(text: str) -> List[str]:
    low = text.lower()
    present = []
    for theme, cues in THEME_KEYWORDS.items():
        if any(cue in low for cue in cues):
            present.append(theme)
    return present


def analyse_relationships(texts: List[str], min_count: int = 4) -> Dict:
    n = len(texts)
    node_counts: Counter = Counter()
    pair_counts: Counter = Counter()

    per_report_themes = []
    for text in texts:
        themes = _themes_in_text(text)
        per_report_themes.append(themes)
        for th in themes:
            node_counts[th] += 1
        for a, b in combinations(sorted(set(themes)), 2):
            pair_counts[(a, b)] += 1

    nodes = [{"id": th, "count": int(c)} for th, c in node_counts.items()]

    edges = []
    for (a, b), c in pair_counts.items():
        if c < min_count:
            continue
        # lift = P(A,B) / (P(A) * P(B))
        pa = node_counts[a] / n
        pb = node_counts[b] / n
        pab = c / n
        lift = pab / (pa * pb) if pa and pb else 0.0
        # Jaccard as an easy-to-read strength on 0..1.
        union = node_counts[a] + node_counts[b] - c
        jaccard = c / union if union else 0.0
        edges.append({
            "source": a, "target": b, "count": int(c),
            "lift": round(lift, 2), "jaccard": round(jaccard, 3),
        })
    edges.sort(key=lambda e: e["count"], reverse=True)

    return {
        "nodes": sorted(nodes, key=lambda d: d["count"], reverse=True),
        "edges": edges,
        "per_report_themes": per_report_themes,
    }
