"""Phase 3 (Data Preparation): one deterministic function that applies every Phase 2 decision.

``prepare(raw)`` returns the modeling table plus a step log (the cleaning report). Only text, categories and
counts are used to decide what to drop; the only score-dependent check (the barrel-sample leak) was established
on development data in Phase 2 and is applied here as a text rule.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import config
from .data import extract_vintage
from .grapes import grape_canonical, wine_colour
from .similarity import detect_near_duplicates
from .splits import assign_folds
from .text_audit import is_barrel_sample, strip_leaks

SCRAPE_YEAR = 2017
# Hand-checked implausible prices (Phase 2 §2.4c): "Château les Ormes Sorbet 2013 Médoc" $3,300,
# Blair 2013 Chardonnay $2,013 (= vintage year), Knoll Smaragd Grüner Veltliner $1,100.
IMPLAUSIBLE_PRICE_TITLES = [
    "Château les Ormes Sorbet 2013  Médoc",
    "Blair 2013 Roger Rose Vineyard Chardonnay (Arroyo Seco)",
    "Emmerich Knoll 2013 Ried Loibenberg Smaragd Grüner Veltliner (Wachau)",
]
PSEUDO_PROVINCE = r"(?:^| )Other$"
TEXT_COLS = ["title", "winery", "designation", "description", "province", "region_1", "region_2", "variety", "country"]


def _fix_mojibake(x):
    """Repair UTF-8 text that was decoded as Latin-1 ("Ã¨" -> "è") only when the round trip succeeds; anything else
    (correct text such as "Âme" or "d'Âge") is left unchanged (critic round 2 N2)."""
    if isinstance(x, str) and ("Ã" in x or "Â" in x):
        try:
            return x.encode("latin-1").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            return x
    return x


def _norm(s: pd.Series) -> pd.Series:
    """Mojibake repair + whitespace normalisation (non-breaking spaces, repeated spaces)."""
    s = s.map(_fix_mojibake)
    return s.str.replace("\xa0", " ", regex=False).str.replace(r"\s+", " ", regex=True).str.strip()


def prepare(raw: pd.DataFrame, anon_lockbox_like=None, stop_before: str | None = None):
    """Clean and construct the modeling table. ``anon_lockbox_like``: review_ids of anonymous notes attributed to a
    lockbox critic (Phase 1 R8; ``splits.anon_lockbox_like``).

    ``stop_before="near_duplicates"`` returns the DM5 evaluation corpus (after exact de-duplication, barrel-sample
    and duplicated-note removal) instead of the modeling table. Near-duplicates are removed by exact Jaccard >= TAU
    alone; the DM5(c) labelling rule is used only to *describe* those pairs.
    """
    log = []
    def step(name, before, after, note="", lockbox_before=None):
        lb = (lockbox_before - int(d["is_lockbox"].sum())) if lockbox_before is not None else None
        log.append({"step": name, "rows before": before, "rows after": after, "rows affected": before - after,
                    "lockbox rows affected": lb, "note": note})

    d = raw.copy()
    n = len(d); d = d.drop_duplicates()
    d["fold"] = assign_folds(d); d["is_lockbox"] = d["fold"].eq(config.LOCKBOX_FOLD)      # frozen mapping
    step("drop exact duplicate rows", n, len(d))
    n, lb = len(d), int(d.is_lockbox.sum()); d = d[~is_barrel_sample(d["title"], d["description"])]
    step("drop barrel samples (score written in note)", n, len(d), "Phase 2 §2.4a", lb)
    n, lb = len(d), int(d.is_lockbox.sum()); d = d[~d["description"].duplicated(keep="first")]
    step("keep one row per duplicated note", n, len(d), "Phase 2 §2.4c (text rule)", lb)
    if stop_before == "near_duplicates":
        return d, pd.DataFrame(log)
    nd = detect_near_duplicates(d["description"])
    drop = set(nd["j"])            # keep the first (lower review_id) of each near-duplicate pair
    same_fold = bool((d.loc[nd["i"], "fold"].to_numpy() == d.loc[nd["j"], "fold"].to_numpy()).all())
    n, lb = len(d), int(d.is_lockbox.sum()); d = d[~d.index.isin(drop)]
    step(f"keep one row per near-duplicate pair (exact Jaccard ≥ {config.DM5_TAU})", n, len(d),
         f"{len(nd)} pairs; all within one fold: {same_fold} (text rule)", lb)
    if anon_lockbox_like is not None:
        n, lb = len(d), int(d.is_lockbox.sum()); d = d[~d.index.isin(set(anon_lockbox_like))]
        step("drop anonymous notes attributed to a lockbox critic", n, len(d), "Phase 1 R8, p > 0.5", lb)

    for c in TEXT_COLS:
        d[c] = _norm(d[c])
    d["critic"] = _norm(d["taster_name"])                       # display name only; folds already assigned
    d["note"] = _norm(strip_leaks(d["description"]))            # model text: scores, verdict labels and prices removed
    fixed = d["title"].isin(set(_norm(pd.Series(IMPLAUSIBLE_PRICE_TITLES)))) & d["price"].notna()
    d.loc[fixed, "price"] = np.nan
    log.append({"step": "set implausible prices to missing", "rows affected": int(fixed.sum()), "note": "hand-checked, Phase 2 §2.4c"})

    for c in ["country", "province", "variety", "region_1"]:
        d[c] = d[c].fillna("Unknown")
    pseudo = d["province"].str.contains(PSEUDO_PROVINCE, regex=True) | (d["province"] == d["country"])
    d["province_model"] = d["province"].where(~pseudo, "Unknown province")
    d["has_region_1"] = d["region_1"].ne("Unknown")
    d["has_designation"] = d["designation"].notna()
    d["winery_key"] = d["winery"].str.casefold()
    d["grape"] = grape_canonical(d["variety"])
    d["label_differs"] = d["grape"] != d["variety"]              # e.g. "Pinot Grigio" label for the Pinot Gris grape
    d["colour"] = wine_colour(d["variety"], d["title"], d["winery"], d["description"])
    d["vintage"] = extract_vintage(d["title"], d["winery"])
    d["is_nonvintage"] = d["vintage"].isna()
    d["age_at_scrape"] = SCRAPE_YEAR - d["vintage"]
    d["n_words"] = d["note"].str.split().str.len()                # length of the MODEL text (leaks stripped)
    d["short_note"] = d["n_words"] < 10
    d["in_value_pool"] = d["price"].le(config.VALUE_MAX_PRICE)
    log.append({"step": "constructed attributes", "note": "note, province_model, grape, colour, vintage (rev. rule), is_nonvintage, "
                "age_at_scrape, n_words (on note), short_note, has_designation, has_region_1, winery_key, label_differs, in_value_pool"})
    keep = ["points", "description", "note", "title", "winery", "winery_key", "designation", "has_designation",
            "country", "province", "province_model", "region_1", "region_2", "has_region_1", "variety", "grape", "label_differs", "colour",
            "vintage", "is_nonvintage", "age_at_scrape", "n_words", "short_note", "price", "in_value_pool",
            "taster_name", "critic", "fold", "is_lockbox"]
    return d[keep], pd.DataFrame(log)


def outlier_report(d: pd.DataFrame, seed: int = config.SEED) -> pd.DataFrame:
    """Course-template outlier analysis on INPUT features only (no scores): IQR rules + Isolation Forest."""
    from sklearn.ensemble import IsolationForest
    out = {}
    lp = np.log(d["price"].dropna())
    q1, q3 = lp.quantile([.25, .75]); iqr = q3 - q1
    out["log price outside 1.5×IQR"] = int(((lp < q1 - 1.5 * iqr) | (lp > q3 + 1.5 * iqr)).sum())
    w = d["n_words"]; q1, q3 = w.quantile([.25, .75]); iqr = q3 - q1
    out["note length outside 1.5×IQR"] = int(((w < q1 - 1.5 * iqr) | (w > q3 + 1.5 * iqr)).sum())
    X = pd.DataFrame({"log_price": np.log(d["price"]), "n_words": d["n_words"], "age": d["age_at_scrape"]}).dropna()
    iso = IsolationForest(contamination=0.01, random_state=seed).fit(X)
    out["Isolation Forest outliers (1% contamination; price, length, age)"] = int((iso.predict(X) == -1).sum())
    return pd.Series(out).to_frame("rows")


BANNED_INPUTS = {"points", "taster_name", "critic", "taster_twitter_handle", "fold", "is_lockbox", "description"}
# An INDEPENDENT list of give-away terms (not the stripping regexes), so this check can fail
INDEPENDENT_LEAK_TERMS = r"\bpoints?\b|\bpts\b|\brated\b|\bscor(?:e|es|ed|ing)\b|[$€£]|\bbucks?\b|\bdollars?\b|best buy|editor|cellar selection|barrel sample"


def leakage_audit(d: pd.DataFrame, quality_inputs, ranker_inputs, dev_probe: bool = True) -> pd.DataFrame:
    """Phase 3 milestone. Checks that CAN fail (revision 2): independent term list, cross-fold text sharing, frozen
    lockbox membership, and a development-only probe of the tokens most associated with the score."""
    from .text_audit import CURRENCY, EXPLICIT_POINTS, SCORE_RANGE_AT_START, VERDICT_LABELS
    note = d["note"]
    indep = note.str.contains(INDEPENDENT_LEAK_TERMS, case=False, regex=True)
    shared = d.groupby("note")["fold"].nunique()
    lockbox_names = set(d.loc[d["is_lockbox"], "critic"].dropna())
    rows = [
        ("inputs: quality model excludes price, critic, target, raw text", not (set(quality_inputs) & (BANNED_INPUTS | {"price"})), ""),
        ("inputs: ranker excludes critic, target, raw text (price allowed)", not (set(ranker_inputs) & BANNED_INPUTS), ""),
        ("text: no score range / explicit score / verdict label / price (stripping regexes)",
         not (note.str.contains(SCORE_RANGE_AT_START).any() or note.str.contains(EXPLICIT_POINTS, case=False).any()
              or note.str.contains(VERDICT_LABELS, case=False).any() or note.str.contains(CURRENCY, case=False).any()), ""),
        ("text: independent give-away term list", indep.mean() < 0.01,
         f"{int(indep.sum())} notes ({indep.mean():.2%}) still match; inspected in the notebook"),
        ("text: no note text shared across folds", bool((shared <= 1).all()), f"{int((shared > 1).sum())} shared"),
        ("rows: no barrel samples", not d["title"].str.contains("barrel sample", case=False).any(), ""),
        ("folds: lockbox = the four frozen critics", lockbox_names == set(config.LOCKBOX_CRITICS), ", ".join(sorted(lockbox_names))),
        ("folds: every named critic in the frozen mapping", bool(d.loc[d.taster_name.notna(), "fold"].ge(0).all()), ""),
    ]
    if dev_probe:
        rows.append(_dev_token_probe(d))
    return pd.DataFrame(rows, columns=["check", "pass", "detail"]).assign(result=lambda t: t["pass"].map({True: "PASS", False: "FAIL"})).drop(columns="pass").set_index("check")


def _dev_token_probe(d: pd.DataFrame, top: int = 40):
    """Development data only: the tokens most correlated with the score must not include give-away terms."""
    from sklearn.feature_extraction.text import CountVectorizer
    dev = d[~d["is_lockbox"]]
    cv = CountVectorizer(min_df=200, binary=True)
    X = cv.fit_transform(dev["note"]); y = dev["points"].to_numpy(dtype=float)
    Xc = X.tocsc(); n = X.shape[0]
    mean_x = np.asarray(Xc.mean(0)).ravel(); mean_y = y.mean()
    cov = (np.asarray(Xc.T @ y).ravel() / n) - mean_x * mean_y
    corr = cov / (np.sqrt(mean_x * (1 - mean_x)) * y.std() + 1e-12)
    vocab = np.array(cv.get_feature_names_out())
    top_tokens = vocab[np.argsort(-np.abs(corr))[:top]]
    bad = [t for t in top_tokens if __import__("re").search(INDEPENDENT_LEAK_TERMS, t, flags=2)]
    return ("probe: top-40 score-correlated tokens contain no give-away term (development only)", not bad,
            ", ".join(top_tokens[:15]) + (f" | flagged: {bad}" if bad else ""))
