"""Leakage and identity checks on the tasting-note text (Phase 2; applied in Phase 3)."""

from __future__ import annotations

import pandas as pd

_SCORE = r"(?:8\d|9\d|100)"
# A note that opens with the score range, e.g. "90-92. Barrel sample.", "88—90", "98-100" (Voss barrel samples).
# Both ends restricted to plausible scores, so "14-15% alcohol" or "18-24 months" can't match.
SCORE_RANGE_AT_START = rf"^\s*\(?{_SCORE}\s*[-–—]\s*{_SCORE}\)?(?=\W)"
# Explicit score mentions: "rated 92 points", "a 90-point wine", "90+ rating", "worth 100 points", "scored 87"
EXPLICIT_POINTS = (rf"\b{_SCORE}\s*\+?\s*-?\s*(?:points?|pts)\b|\b{_SCORE}\+\s*rating\b"
                   rf"|\b(?:rated|rating|scored?|scores|earned|earns|worth)\s+(?:a\s+|an\s+)?{_SCORE}\b")
# WineEnthusiast's own value / verdict labels inside notes
VERDICT_LABELS = r"\bBest Buy\b|\bEditors?'? Choice\b|\bCellar Selection\b"
# Prices in the text ("an under-$15 red", "10 bucks"): price must not enter the price-free model (R-2)
CURRENCY = r"[$€£]\s?\d+(?:[.,]\d+)?|\b\d+\s*bucks\b"


def flag_score_leaks(desc: pd.Series) -> pd.DataFrame:
    return pd.DataFrame({
        "score_range_at_start": desc.str.contains(SCORE_RANGE_AT_START, regex=True),
        "explicit_points": desc.str.contains(EXPLICIT_POINTS, case=False, regex=True),
        "verdict_label": desc.str.contains(VERDICT_LABELS, case=False, regex=True),
        "currency_amount": desc.str.contains(CURRENCY, case=False, regex=True),
    })


def is_barrel_sample(title: pd.Series, desc: pd.Series) -> pd.Series:
    """Pre-release barrel-sample reviews: a different review type (not what a <= $25 buyer receives)."""
    return title.str.contains("barrel sample", case=False) | desc.str.contains(SCORE_RANGE_AT_START, regex=True)


def strip_leaks(desc: pd.Series) -> pd.Series:
    """Remove leading score ranges, explicit scores and verdict labels; replace prices (Phase 3, all models)."""
    out = desc.str.replace(SCORE_RANGE_AT_START, " ", regex=True)
    out = out.str.replace(EXPLICIT_POINTS, " ", case=False, regex=True)
    out = out.str.replace(VERDICT_LABELS, " ", case=False, regex=True)
    return out.str.replace(CURRENCY, " _price_ ", case=False, regex=True)
