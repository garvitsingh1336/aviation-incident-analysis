"""Stage 3: NLP preprocessing.

Provides text cleaning used by the classic (bag-of-words) topic models and
utility tokenisation.  Transformer embeddings are fed the *raw* narrative
(sentence transformers do their own normalisation), while NMF/LDA and c-TF-IDF
labelling use the cleaned form.
"""
from __future__ import annotations

import re
from functools import lru_cache
from typing import List

# A compact stop-word list plus aviation boilerplate that would otherwise
# dominate the topic keywords ("aircraft", "flight", "runway" appear everywhere).
BASE_STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "if", "then", "of", "to", "in", "on",
    "at", "by", "for", "with", "as", "was", "were", "is", "are", "be", "been",
    "being", "it", "its", "this", "that", "these", "those", "from", "into",
    "during", "after", "before", "over", "under", "out", "up", "down", "off",
    "which", "who", "whom", "had", "has", "have", "not", "no", "than", "so",
    "later", "shortly", "well", "along", "within", "without", "toward", "near",
    "when", "where", "while", "also", "would", "could", "did", "does", "one",
    "two", "number", "involved", "occurrence", "reported", "noted", "present",
    "carried", "led", "made", "following",
}

AVIATION_BOILERPLATE = {
    "aircraft", "flight", "crew", "pilot", "phase", "operated", "operator",
    "airport", "runway", "landing", "takeoff", "approach", "climb", "cruise",
    "descent", "taxi",
}

# Generic outcome / filler words that describe *consequences* rather than the
# contributing factor.  Removing them keeps topic labels focused on causes.
OUTCOME_FILLER = {
    "there", "successful", "successfully", "injuries", "injury", "found",
    "returned", "return", "executed", "beyond", "boundary", "experienced",
    "entered", "ran", "came", "rest", "occurred", "prompted", "requested",
    "substantial", "substantially", "damage", "damaged", "difficult",
    "regained", "avoided", "narrowly", "field", "open", "site", "firm",
    "soft", "escaped", "occupants", "minor", "event", "reported", "developed",
    "initiated", "carried", "continued", "selected", "managed", "declared",
    "touched", "touchdown", "down", "long", "set", "using", "later", "closed",
    "recovery", "recovered", "come", "left", "sustained", "secondary",
}

STOPWORDS = BASE_STOPWORDS | AVIATION_BOILERPLATE | OUTCOME_FILLER

_WORD_RE = re.compile(r"[a-zA-Z][a-zA-Z\-]+")


def clean_text(text: str) -> str:
    """Lowercase, strip punctuation/numbers, collapse whitespace."""
    text = text.lower()
    tokens = _WORD_RE.findall(text)
    tokens = [t for t in tokens if t not in STOPWORDS and len(t) > 2]
    return " ".join(tokens)


def clean_corpus(texts: List[str]) -> List[str]:
    return [clean_text(t) for t in texts]


@lru_cache(maxsize=1)
def sklearn_stopwords() -> frozenset:
    return frozenset(STOPWORDS)
