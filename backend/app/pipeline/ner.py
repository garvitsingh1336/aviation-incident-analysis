"""Stage 4: Named Entity Recognition.

Extracts useful entities (aircraft, airports, locations, organisations) from the
report narratives.  Primary engine is spaCy; a rule/gazetteer based extractor is
used when the spaCy pipeline is unavailable so the stage still produces results.
"""
from __future__ import annotations

import re
from collections import Counter, defaultdict
from typing import Dict, List

from ..core.capabilities import capabilities
from .. import config

# Regexes / gazetteers for the rule-based path and for augmenting spaCy.
ICAO_RE = re.compile(r"\b[KP][A-Z]{3}\b")
AIRCRAFT_MAKERS = [
    "Boeing", "Airbus", "Cessna", "Piper", "Beechcraft", "Bombardier",
    "Embraer", "Gulfstream", "Diamond", "Cirrus", "Robinson", "ATR",
]
AIRCRAFT_RE = re.compile(
    r"\b(" + "|".join(AIRCRAFT_MAKERS) + r")\b[\w\-\s]{0,12}?(\d{2,4}[A-Za-z\-]*)?",
)

# Map spaCy entity labels onto the categories that matter for aviation reports.
SPACY_CATEGORY = {
    "GPE": "location",
    "LOC": "location",
    "ORG": "organisation",
    "FAC": "facility",
    "PRODUCT": "equipment",
    "NORP": "organisation",
    "DATE": "date",
    "TIME": "time",
}


def _categorise_rule_based(text: str) -> List[Dict[str, str]]:
    ents = []
    for code in set(ICAO_RE.findall(text)):
        ents.append({"text": code, "type": "airport"})
    for m in AIRCRAFT_RE.finditer(text):
        maker = m.group(0).strip()
        if maker and maker[0].isupper():
            ents.append({"text": maker, "type": "aircraft"})
    return ents


class NERExtractor:
    def __init__(self):
        self.caps = capabilities()
        self._nlp = None
        if self.caps["spacy_model"]:
            import spacy

            # Only the NER component is needed; disable the rest for speed.
            self._nlp = spacy.load(
                config.SPACY_MODEL, disable=["lemmatizer", "textcat"]
            )

    def extract(self, text: str) -> List[Dict[str, str]]:
        ents: List[Dict[str, str]] = []
        if self._nlp is not None:
            doc = self._nlp(text)
            for ent in doc.ents:
                cat = SPACY_CATEGORY.get(ent.label_)
                if cat and cat not in ("date", "time"):
                    ents.append({"text": ent.text.strip(), "type": cat})
        # Always augment with aviation-specific rules (ICAO codes, makers).
        ents.extend(_categorise_rule_based(text))
        # De-duplicate within a single report.
        seen = set()
        unique = []
        for e in ents:
            key = (e["text"].lower(), e["type"])
            if key not in seen and len(e["text"]) > 1:
                seen.add(key)
                unique.append(e)
        return unique


def run_ner(texts: List[str]):
    """Return ``(per_report_entities, aggregate_by_type)``."""
    extractor = NERExtractor()
    per_report: List[List[Dict[str, str]]] = []
    by_type: Dict[str, Counter] = defaultdict(Counter)

    for text in texts:
        ents = extractor.extract(text)
        per_report.append(ents)
        for e in ents:
            by_type[e["type"]][e["text"]] += 1

    aggregate = {
        etype: [{"text": t, "count": c} for t, c in counter.most_common(15)]
        for etype, counter in by_type.items()
    }
    return per_report, aggregate
