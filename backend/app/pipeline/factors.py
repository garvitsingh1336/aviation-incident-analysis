"""Stage 8: Contributing-factor analysis.

The synopsis is explicit that the system finds *potential* contributing factors
as patterns in the data — not official causes.  Each discovered topic is treated
as a candidate recurring factor and enriched with size, share, a severity
breakdown and representative reports.  Topics are additionally mapped onto a
high-level aviation-safety taxonomy so the dashboard can roll individual topics
up into familiar themes (Weather, Mechanical, Human Factors, ...).
"""
from __future__ import annotations

from collections import Counter, defaultdict
from typing import Dict, List, Optional

import numpy as np

# High-level safety themes and the keyword cues that map a topic onto them.
# Cues are intentionally *discriminative* (specific words / bigrams) so a report
# is not tagged with every theme — otherwise co-occurrence lift washes out to 1.
THEME_KEYWORDS = {
    "Weather & Environment": ["visibility", "fog", "ceiling", "crosswind",
                               "wind shear", "gust", "icing", "ice accret",
                               "freezing", "mist", "precipitation"],
    "Powerplant & Fuel": ["engine", "thrust", "oil pressure", "fuel",
                           "starvation", "exhaustion", "carburettor", "rpm"],
    "Human Factors & ATC": ["fatigue", "workload", "distraction", "readback",
                             "miscommunication", "controller", "complacency",
                             "frequency", "duty day", "clearance"],
    "Runway & Ground Ops": ["runway excursion", "overran", "overrun",
                             "incursion", "taxiway", "hold-short", "hold short",
                             "braking", "anti-skid", "ground-loop"],
    "Mechanical & Systems": ["maintenance", "component", "corrosion",
                             "cracking", "landing gear", "hydraulic", "flap",
                             "steering", "gear-up", "gear collapse", "gear failed"],
    "Loss of Control & Terrain": ["stall", "spin", "disorientation", "terrain",
                                   "uncommanded roll", "minimum safe altitude",
                                   "controlled-flight", "spatial"],
    "Wildlife": ["bird", "wildlife", "flock"],
}


def _match_theme(keywords: List[str]) -> str:
    scores = Counter()
    kwset = " ".join(keywords).lower()
    for theme, cues in THEME_KEYWORDS.items():
        for cue in cues:
            if cue in kwset:
                scores[theme] += 1
    if not scores:
        return "Other"
    return scores.most_common(1)[0][0]


def analyse_factors(topics_primary: Dict, doc_topics: List[int],
                   severities: List[Optional[str]],
                   true_factors: Optional[List[str]] = None) -> Dict:
    doc_topics_arr = np.asarray(doc_topics)
    total = len(doc_topics)
    sev_arr = np.array([s if s else "Unknown" for s in severities])

    factors = []
    theme_counts: Counter = Counter()
    theme_topics: Dict[str, list] = defaultdict(list)

    for topic in topics_primary["topics"]:
        tid = topic["topic_id"]
        if tid == -1:
            continue
        member_mask = doc_topics_arr == tid
        count = int(member_mask.sum())
        if count == 0:
            continue
        kw = [w for w, _ in topic["keywords"]]
        theme = _match_theme(kw)
        theme_counts[theme] += count
        theme_topics[theme].append(topic["label"])

        sev_break = Counter(sev_arr[member_mask].tolist())
        factors.append({
            "factor_id": tid,
            "label": topic["label"],
            "theme": theme,
            "keywords": kw[:8],
            "count": count,
            "share": round(100.0 * count / total, 1),
            "severity_breakdown": dict(sev_break),
            "representative_idx": topic.get("representative_idx", []),
        })

    factors.sort(key=lambda d: d["count"], reverse=True)

    themes = [
        {
            "theme": theme,
            "count": int(cnt),
            "share": round(100.0 * cnt / total, 1),
            "topics": theme_topics[theme],
        }
        for theme, cnt in theme_counts.most_common()
    ]

    result = {"factors": factors, "themes": themes, "total_reports": total}

    # Optional unsupervised-vs-truth sanity check for the synthetic corpus.
    if true_factors is not None:
        result["evaluation"] = _evaluate_alignment(
            doc_topics_arr, true_factors, factors
        )
    return result


def _evaluate_alignment(doc_topics: np.ndarray, true_factors: List[str],
                       factors: List[Dict]) -> Dict:
    """For each discovered topic, the most common ground-truth factor among its
    members and the purity of that match.  Purely diagnostic (synthetic data)."""
    rows = []
    purities = []
    for f in factors:
        members = np.where(doc_topics == f["factor_id"])[0]
        truths = Counter()
        for i in members:
            for t in str(true_factors[i]).split(";"):
                t = t.strip()
                if t:
                    truths[t] += 1
        if not truths:
            continue
        top_truth, top_n = truths.most_common(1)[0]
        purity = top_n / len(members)
        purities.append(purity)
        rows.append({
            "topic_label": f["label"],
            "dominant_true_factor": top_truth,
            "purity": round(purity, 2),
        })
    return {
        "mean_purity": round(float(np.mean(purities)), 3) if purities else None,
        "per_topic": rows,
        "note": "Diagnostic only — compares unsupervised topics against the "
                "synthetic corpus's latent factor labels.",
    }
