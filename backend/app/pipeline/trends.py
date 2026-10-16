"""Stage 10: Trend analysis.

Compares theme frequency across time periods (years) so the dashboard can show
whether a theme is becoming more or less common in the corpus, and gives a
simple increasing/decreasing signal per theme by comparing the first and second
halves of the timeline.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Optional


def analyse_trends(years: List[Optional[int]],
                  per_report_themes: List[List[str]]) -> Dict:
    valid_years = sorted({int(y) for y in years if y and not _isnan(y)})
    if not valid_years:
        return {"years": [], "series": [], "total_by_year": [], "signals": []}

    by_theme: Dict[str, Dict[int, int]] = defaultdict(lambda: defaultdict(int))
    total_by_year: Dict[int, int] = defaultdict(int)

    for y, themes in zip(years, per_report_themes):
        if not y or _isnan(y):
            continue
        y = int(y)
        total_by_year[y] += 1
        for th in themes:
            by_theme[th][y] += 1

    series = []
    signals = []
    mid = valid_years[len(valid_years) // 2]
    for theme, counts in by_theme.items():
        values = [counts.get(y, 0) for y in valid_years]
        first = sum(v for y, v in counts.items() if y < mid)
        second = sum(v for y, v in counts.items() if y >= mid)
        if second > first * 1.15:
            direction = "increasing"
        elif second < first * 0.85:
            direction = "decreasing"
        else:
            direction = "stable"
        series.append({"theme": theme, "values": values, "total": sum(values)})
        signals.append({
            "theme": theme, "direction": direction,
            "first_half": int(first), "second_half": int(second),
        })

    series.sort(key=lambda s: s["total"], reverse=True)
    signals.sort(key=lambda s: s["first_half"] + s["second_half"], reverse=True)

    return {
        "years": valid_years,
        "series": series,
        "total_by_year": [total_by_year.get(y, 0) for y in valid_years],
        "signals": signals,
    }


def _isnan(x) -> bool:
    try:
        return x != x  # noqa: PLR0124 - NaN check without importing math
    except Exception:
        return False
