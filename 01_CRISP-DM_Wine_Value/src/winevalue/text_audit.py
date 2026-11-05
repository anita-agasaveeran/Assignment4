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
VERDICT_LABELS = r"\bBest Buys?\b|\bEditor'?s?'? Choice\b|\bCellar Selections?\b"
# Commentary about the score itself ("loses a few points", "would score much higher", "an extra point")
# "a point" alone is mostly descriptive ("a point of crisp acidity", "to a point"), so it is removed only after a
# verdict verb (critic round 2 N3).
SCORE_COMMENTARY = (r"\b(?:few|several|couple of|extra|more|additional|another)\s+(?:few\s+)?points?\b"
                    r"|\b(?:gains?|gained|loses?|lost|losing|earns?|earned|deserves?|docked|costs?)\s+(?:it\s+|him\s+|her\s+)?(?:a|an|one)\s+points?\b"
                    r"|\bpoints?\s+(?:higher|lower)\b"
                    # any score / rating word states the critic's verdict ("too ripe to score higher", "the score would
                    # soar", "has rated the same"); "alcohol rated at 12.5%" is kept
                    r"|\bscor(?:e|es|ed|ing)\b|\b(?:under-?|over-?)?rated\b(?!\s+at\b)")
# Prices in the text ("an under-$15 red", "10 bucks"): price must not enter the price-free model (R-2)
_NUMWORDS = r"(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|fifteen|twenty|thirty|forty|fifty)"
CURRENCY = (rf"[$€£]\s?\d+(?:[.,]\d+)?|\b\d+\s*(?:bucks?|dollars?)\b"
            rf"|\b{_NUMWORDS}(?:[- ]\w+)?[- ](?:bucks?|dollars?)\b(?!\s+(?:the|a|this)\s+trend)")
# Price-relative wording ("at the price", "value-priced"): a known R-2 residual, masked only in the stricter DM1b check
PRICE_RELATIVE = (r"\bat (?:this|the|that) price(?:[- ]point)?\b|\bvalue[- ]priced\b|\bfor the price\b|\bpriced (?:right|well)\b|\bgreat value\b|\bbargain\b"
                  r"|\bbang for (?:the|your) bucks?\b|\bprice[- ]point\b|\bQPR\b")   # + "bang for the buck", "price point", QPR (round 2 N3)
PRICE_TOKEN = "_price_"   # placeholder left by strip_leaks; removed together with PRICE_RELATIVE in the strict DM1b mask (N9)


def strict_price_mask(note: pd.Series) -> pd.Series:
    """Stricter R-2 / DM1b check (Phase 4 sensitivity): also remove price-relative wording and the ``_price_`` placeholder."""
    out = note.str.replace(PRICE_RELATIVE, " ", case=False, regex=True)
    return out.str.replace(PRICE_TOKEN, " ", regex=False).str.replace(r"\s+", " ", regex=True).str.strip()


def flag_score_leaks(desc: pd.Series) -> pd.DataFrame:
    return pd.DataFrame({
        "score_range_at_start": desc.str.contains(SCORE_RANGE_AT_START, regex=True),
        "explicit_points": desc.str.contains(EXPLICIT_POINTS, case=False, regex=True),
        "verdict_label": desc.str.contains(VERDICT_LABELS, case=False, regex=True),
        "score_commentary": desc.str.contains(SCORE_COMMENTARY, case=False, regex=True),
        "currency_amount": desc.str.contains(CURRENCY, case=False, regex=True),
    })


def is_barrel_sample(title: pd.Series, desc: pd.Series) -> pd.Series:
    """Pre-release barrel-sample reviews: a different review type (not what a <= $25 buyer receives)."""
    return (title.str.contains("barrel sample", case=False) | desc.str.contains("barrel sample", case=False)
            | desc.str.contains(SCORE_RANGE_AT_START, regex=True))


def strip_leaks(desc: pd.Series) -> pd.Series:
    """Remove leading score ranges, explicit scores and verdict labels; replace prices (Phase 3, all models)."""
    out = desc.str.replace(SCORE_RANGE_AT_START, " ", regex=True)
    out = out.str.replace(EXPLICIT_POINTS, " ", case=False, regex=True)
    out = out.str.replace(VERDICT_LABELS, " ", case=False, regex=True)
    out = out.str.replace(SCORE_COMMENTARY, " ", case=False, regex=True)
    return out.str.replace(CURRENCY, " _price_ ", case=False, regex=True)
