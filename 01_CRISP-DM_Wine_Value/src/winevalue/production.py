"""Phase 6 (CRISP-DM 6.1): the deployed Value Finder models, fitted exactly as in the Phase 5 lockbox run.

``build(prep)`` refits the frozen selections (``config.SELECTED_DM1/DM2/DM3``) on all development rows with the Phase 4
procedure (``evaluate.run_split`` / ``app_mappings``): the same inner groups, alpha tuning, out-of-fold calibration,
P(90+) map and band width. It does NOT refit on the lockbox critics (§5.3 condition 1): the deployed artifact is the one
whose lockbox predictions were measured, and ``reproduces_lockbox`` checks that row by row.

``prepare_new(df)`` turns raw retailer inputs (note, origin, grape label, vintage, price) into model inputs with the same
row-wise rules as ``prepare.prepare``. ``ValueFinder.score`` returns every BSC4 output; ``similar`` the 5 most similar
reviewed wines.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge

from . import config
from .cv import development, inner_groups, oof_predict, top_guess_fold
from .data import extract_vintage
from .descriptors import item_matrix
from .evaluate import CAL_ALL
from .features import QUALITY_INPUTS_V2, RANKER_INPUTS_V2, build_preprocessor
from .grapes import grape_canonical, wine_colour
from .models import GroupMeanBaseline
from .prepare import PSEUDO_PROVINCE, _norm
from .scoring import fit_calibration, probability_map, ridge_fit_predict, tune_ridge
from .text_audit import strip_leaks

# ---- display and verdict rules, fixed before any pilot data (report §6.1) ----
# Percentile bands of the ranker against development ≤ $25 candidates (one-wine view). The cut-offs are fixed, but the share
# of candidates above them is not: 6-20% above the 90th percentile per development fold, 30% on the lockbox's new writers
# (notebook 6.1c, phase6_shortlist_tiers.csv). So the shortlist view uses the rank WITHIN the buying round (ROUND_TIERS).
APP_SHORTLIST_TIERS = ((0.10, "Above the development 90th percentile"), (0.20, "Above the development 80th percentile"))
APP_SHORTLIST_OTHER = "Below the development 80th percentile"
APP_TIER_SHORT = {"Above the development 90th percentile": "Top 10% (dev.)", "Above the development 80th percentile": "Top 20% (dev.)",
                  "Below the development 80th percentile": "Lower", "Not a ≤ $25 candidate": "Over $25"}
def percentile_text(share_above: float, in_pool: bool) -> tuple[str, str]:
    """The one-wine view's ranker label (Phase 6 critic round 2 issue 8): a number against development candidates, not a
    "top 10%" tier. Returns (short metric value, sentence)."""
    if not in_pool or share_above is None or np.isnan(share_above):
        return "Over $25", "Not a ≤ $25 candidate, so not ranked for the shortlist"
    p = int(np.clip(np.floor(100 * (1 - share_above)), 0, 99))
    return f"{p} / 100 (dev.)", f"Ranks above {p}% of development ≤ $25 candidates"


APP_TIER_CAVEAT = ("Compared with development ≤ $25 candidates. Notes by new writers clear these cut-offs far more often (30% of "
                   "candidates were above the 90th percentile for four held-out critics), so pick samples by the rank within "
                   "your buying round, not by this label.")
ROUND_TIERS = ((0.10, "Sample first (top 10% of this round)"), (0.20, "Worth sampling (top 20% of this round)"))
ROUND_OTHER = "Lower priority"
APP_BAND_CAVEAT = "Estimated, internal only. May be less accurate for Italian wines and for writers unlike those in training."
APP_P90_CAVEAT = "Relative indicator, not a probability: it over-predicted the 90+ rate by 10 points on held-out critics."
APP_VALUE_BASE = ("For comparison, about 1 in 5 reviewed ≤ $25 wines is a value wine (10-22% by writer pool in development, "
                  "22% for four held-out critics).")
APP_DISAGREE = ("The value verdict ignores price as a quality signal (it reads only the note, origin and grape); the shortlist "
                "and P(90+) also use price. When they disagree, the shortlist is the better-tested output.")
SIMILAR_K = 5


# Origin, grape and winery columns mapped to the training spellings before scoring (Phase 6 critic rounds 3 and 4): a value
# that is not an exact training spelling is matched by ``match_key`` (case, spaces, apostrophes, accents, punctuation), then
# by these country aliases. Only aliases whose target is a training country are listed (England is not in the development
# data). ``winery`` feeds the "winery track record" rule, the strongest comparator in the BO1 gate (critic round 4 issue 1).
CANONICAL_COLUMNS = ("country", "province", "variety", "region_1", "winery")
COUNTRY_ALIASES = {"usa": "US", "u s": "US", "u s a": "US", "united states": "US", "united states of america": "US",
                   "czechia": "Czech Republic", "north macedonia": "Macedonia", "bosnia": "Bosnia and Herzegovina"}
_PART_SEP = r"(\s*[-,/]\s*)"     # blend separators, as in ``grapes.wine_colour``


def match_key(s) -> pd.Series:
    """``pilot.name_key`` (spaces, curly quotes, case), plus accents folded and punctuation treated as a space: the key by
    which a new spelling is matched to a training spelling. Used only for values that are not an exact training spelling."""
    import unicodedata
    from .pilot import name_key
    k = name_key(s).map(lambda v: "".join(ch for ch in unicodedata.normalize("NFKD", v) if not unicodedata.combining(ch)))
    return k.str.replace(r"[^\w]+", " ", regex=True).str.strip()


def _lexicon_varieties() -> list[str]:
    """Grape names the grape lexicon knows (``grapes``), so a lexicon-only grape typed in another case still gets its
    canonical grape and colour (critic round 4 issue 2). Training spellings take precedence."""
    from . import grapes
    return sorted(set(grapes.SYNONYMS) | set(grapes.SYNONYMS.values()) | grapes.RED | grapes.WHITE | grapes.SPARKLING
                  | grapes.FORTIFIED)


def _winery_key(winery: pd.Series, country: pd.Series) -> pd.Series:
    """A winery is matched only within its country (critic round 5 issue 2: "Patria", Italy, is not "Pátria", Portugal)."""
    return match_key(winery).set_axis(winery.index) + "|" + match_key(country.fillna("Unknown")).set_axis(winery.index)


def training_spellings(dev: pd.DataFrame) -> dict:
    """Per ``CANONICAL_COLUMNS`` column: the development spellings and, per ``match_key`` (for ``winery``: per match key
    and country), the most frequent of them."""
    out = {}
    for c in CANONICAL_COLUMNS:
        if c == "winery":
            w = dev[["winery", "country"]].dropna(subset=["winery"])
            n = w.value_counts()
            keys = _winery_key(pd.Series([i[0] for i in n.index]), pd.Series([i[1] for i in n.index])).to_numpy()
            sp = [i[0] for i in n.index]
            spellings = sorted(set(sp))
        else:
            n = dev[c].fillna("Unknown").value_counts()
            keys, sp, spellings = match_key(pd.Series(n.index)).to_numpy(), list(n.index), sorted(n.index)
        by_key = {}
        for key, v in zip(keys, sp):
            by_key.setdefault(key, v)
        out[c] = {"spellings": spellings, "by key": by_key}
    return out


def _by_key(c: str, cat: dict) -> dict:
    if c != "variety":
        return cat["by key"]
    lex = _lexicon_varieties()
    return {**dict(zip(match_key(pd.Series(lex)), lex)), **cat["by key"]}


def _case_fold(s: pd.Series) -> pd.Series:
    return s.astype(str).str.casefold().str.split().str.join(" ")


_BY_CASE: dict = {}


def _by_case(cat: dict) -> dict:
    """Case-insensitive training spelling -> spelling, for keys that only one training spelling has (the 24 training
    wineries spelled two ways in case only, e.g. "StoneCap" and "Stonecap", are left out: they are two wineries to the
    frozen rule). Built once per spelling list (about 15,000 wineries) and cached, so a one-wine query stays fast (BSC4).
    The cache holds the list itself and checks identity, so a new list that reuses a freed id is never served an old
    lookup (critic round 6 issue 6)."""
    sp_list = cat["spellings"]
    hit = _BY_CASE.get(id(sp_list))
    if hit is None or hit[0] is not sp_list:
        sp = pd.Series(sp_list, dtype=object)
        f = _case_fold(sp)
        dup = set(f[f.duplicated(keep=False)])
        hit = (sp_list, {k: v for k, v in zip(f, sp) if k not in dup})
        _BY_CASE[id(sp_list)] = hit
    return hit[1]


def canonical_inputs(d: pd.DataFrame, categories: dict) -> pd.DataFrame:
    """Map ``CANONICAL_COLUMNS`` to training spellings (exact spellings are left alone, so a training-like row is
    unchanged). The value as given is kept in ``<col> (as given)``. A grape label that does not match as a whole is matched
    part by part at blend separators ("pinot gris-gewürztraminer"). Values with no match stay as given; ``monitoring``
    flags unseen countries and counts unseen wineries."""
    import re
    d = d.copy()
    for c, cat in (categories or {}).items():
        if c not in d:
            continue
        known = set(cat["spellings"])
        x = d[c].astype(object)
        miss = x.notna() & ~x.isin(known)
        if f"{c} (as given)" not in d:
            d[f"{c} (as given)"] = x
        if not miss.any():
            continue
        by_key = _by_key(c, cat)
        key = (_winery_key(x[miss], d.loc[miss, "country"]) if c == "winery" and "country" in d
               else match_key(x[miss]).set_axis(x[miss].index))
        if c == "country":
            alias = dict(zip(match_key(pd.Series(list(COUNTRY_ALIASES))), COUNTRY_ALIASES.values()))
            key = key.map(lambda k: match_key(pd.Series([alias[k]])).iloc[0] if k in alias else k)
        mapped = key.map(by_key)
        if c == "winery":
            # A variant in letter case only is the training spelling it equals case-insensitively, if exactly one does,
            # whatever the country: the frozen "winery track record" rule reads the winery by name alone, so this makes
            # "NEUMEISTER" score exactly as "Neumeister" does (re-execution 10). It comes before the in-country match so
            # a case variant never gets a different record from its exact spelling. Accent and punctuation variants
            # are still matched only within the country ("Patria", Italy, does not become "Pátria", Portugal).
            case = _case_fold(x[miss]).map(_by_case(cat))
            mapped = case.where(case.notna(), mapped)
        if c == "variety":
            def parts(v):
                bits = re.split(_PART_SEP, v)
                return "".join(b if i % 2 else by_key.get(match_key(pd.Series([b])).iloc[0], b) for i, b in enumerate(bits))
            left = mapped.isna()
            mapped[left] = x[miss][left].astype(str).map(parts)
        d.loc[miss, c] = mapped.fillna(x[miss])
    return d


def prepare_new(df: pd.DataFrame, vf: "ValueFinder | None" = None) -> pd.DataFrame:
    """Model inputs for new wines, row by row, with ``prepare.prepare``'s rules. Required: ``note`` (or ``description``),
    ``country``, ``variety``. Optional: ``province``, ``region_1``, ``designation``, ``winery``, ``title``, ``vintage``
    (else parsed from ``title``), ``price``, ``source`` (note source, for the pilot), ``wine_id``.

    With the deployed ``vf``, origin and grape names are first mapped to the training spellings (``canonical_inputs``).
    Prices are converted to 2017 dollars with ``config.PRICE_DEFLATOR`` (the price as given is kept in
    ``price (as given)``); the ≤ $25 pool, the ranker's log price and the verdict all use the converted price."""
    d = df.copy()
    if "description" not in d:
        d["description"] = d["note"]
    for c in ["title", "winery", "designation", "province", "region_1", "price", "vintage", "source"]:
        if c not in d:
            d[c] = np.nan
    for c in ["title", "winery", "designation", "description", "province", "region_1", "variety", "country"]:
        x = _norm(d[c].astype(object).where(d[c].notna(), None))
        d[c] = x.where(x.notna() & x.ne(""), np.nan)
    d["note"] = _norm(strip_leaks(d["description"]))
    for c in ["country", "province", "variety", "region_1"]:
        d[c] = d[c].fillna("Unknown")
    if vf is not None:
        d = canonical_inputs(d, getattr(vf, "categories", None))
    # Case-insensitive here (exact in prepare.py): the same rows on all 118,378 prepared rows, but a country that is
    # unseen in training (so not mapped) and written in another case still matches its province (round-4 check)
    from .pilot import name_key
    pseudo = (d["province"].str.contains(PSEUDO_PROVINCE, regex=True, case=False)
              | (name_key(d["province"]) == name_key(d["country"])))
    d["province_model"] = d["province"].where(~pseudo, "Unknown province")
    d["has_region_1"] = d["region_1"].ne("Unknown")
    d["has_designation"] = d["designation"].notna()
    d["winery_key"] = d["winery"].fillna("").str.casefold()
    d["grape"] = grape_canonical(d["variety"])
    d["label_differs"] = d["grape"] != d["variety"]
    d["colour"] = wine_colour(d["variety"], d["title"], d["winery"], d["description"])
    v = pd.to_numeric(d["vintage"], errors="coerce")
    d["vintage"] = v.where(v.notna(), extract_vintage(d["title"], d["winery"]) if d["title"].notna().any() else np.nan).astype(float)
    d["is_nonvintage"] = d["vintage"].isna()
    d["n_words"] = d["note"].str.split().str.len().fillna(0).astype(int)
    if "price (as given)" not in d:                 # idempotent: preparing a prepared frame never deflates twice
        d["price (as given)"] = pd.to_numeric(d["price"], errors="coerce")
    d["price"] = d["price (as given)"] * config.PRICE_DEFLATOR
    d["in_value_pool"] = d["price"].le(config.VALUE_MAX_PRICE)
    return d


@dataclass
class ProfileModel:
    """DM3 (lexicon NMF, k = 8) as ``clustering.fit_profile_model`` fits it, in a picklable form."""
    tfidf: object
    nmf: object
    vocabulary: np.ndarray
    names: dict = field(default_factory=dict)

    @classmethod
    def fit(cls, dev: pd.DataFrame, k: int, seed: int = config.SEED) -> "ProfileModel":
        from sklearn.decomposition import NMF
        from sklearn.feature_extraction.text import TfidfTransformer
        items = item_matrix(dev, grapes=[])
        tf = TfidfTransformer(sublinear_tf=True).fit(items.to_numpy(dtype=float))
        X = tf.transform(items.to_numpy(dtype=float)).tocsr()
        keep = np.asarray(X.sum(1)).ravel() > 0
        m = NMF(n_components=k, init="nndsvda", random_state=seed, max_iter=400).fit(X[keep])
        return cls(tf, m, np.array([c[2:] for c in items.columns]))

    def weights(self, d: pd.DataFrame) -> np.ndarray:
        return self.nmf.transform(self.tfidf.transform(item_matrix(d, grapes=[]).to_numpy(dtype=float)).tocsr())

    def assign(self, d: pd.DataFrame) -> pd.Series:
        Xn = self.tfidf.transform(item_matrix(d, grapes=[]).to_numpy(dtype=float)).tocsr()
        lab = self.nmf.transform(Xn).argmax(1)
        lab[np.asarray(Xn.sum(1)).ravel() == 0] = -1
        return pd.Series(lab, index=d.index)

    def top_terms(self, n: int = config.DM3_TOP_TERMS) -> list[list[str]]:
        return [list(self.vocabulary[np.argsort(-row)[:n]]) for row in self.nmf.components_]


def read_profile_names(naming_dir) -> dict[int, str]:
    """Display names for primary profiles A1..A8: both blind reviewers' names (BSC3, reports/bsc3_naming)."""
    from .phase5 import read_naming
    names = {}
    tabs = [read_naming(naming_dir / f"reviewer{r}.md") for r in (1, 2)]
    for t in tabs:
        for _, r in t[t["profile"].str.startswith("A")].iterrows():
            names.setdefault(int(r["profile"][1:]) - 1, []).append(r["name"])
    return {k: " / ".join(v) for k, v in names.items()}


@dataclass
class ValueFinder:
    quality_pre: object
    quality_ridge: object
    calibration: tuple
    band_half_width: float
    ranker_pre: object
    ranker_ridge: object
    p90_map: object
    pool_rank_oof: np.ndarray            # sorted out-of-fold ranker scores of ≤ $25 development rows (shortlist tiers)
    profiles: ProfileModel
    info: dict
    rule_models: dict = field(default_factory=dict)   # frozen simple rules and the variety × country baseline, fitted on development rows
    categories: dict = field(default_factory=dict)    # training spellings of CANONICAL_COLUMNS (``training_spellings``)

    def prepare(self, df: pd.DataFrame) -> pd.DataFrame:
        """``prepare_new`` with this artifact's training spellings: the one way raw inputs reach the models."""
        return prepare_new(df, self)

    # ---- scoring ----
    def estimate(self, d: pd.DataFrame) -> np.ndarray:
        """DM1: calibrated ridge (all OOF), price-free."""
        a, b = self.calibration
        return a + b * self.quality_ridge.predict(self.quality_pre.transform(d[QUALITY_INPUTS_V2]))

    def ridge_score(self, d: pd.DataFrame) -> np.ndarray:
        return self.quality_ridge.predict(self.quality_pre.transform(d[QUALITY_INPUTS_V2]))

    def rank_score(self, d: pd.DataFrame) -> np.ndarray:
        """DM2: ridge + log price (needs a price; rows without one get NaN)."""
        out = np.full(len(d), np.nan)
        ok = d["price"].notna().to_numpy()
        if ok.any():
            out[ok] = self.ranker_ridge.predict(self.ranker_pre.transform(d.loc[ok, RANKER_INPUTS_V2]))
        return out

    def score(self, df: pd.DataFrame, prepared: bool = False) -> pd.DataFrame:
        """Every BSC4 output for each wine. ``df``: raw inputs (``prepare_new``) unless ``prepared``."""
        d = df if prepared else self.prepare(df)
        est = self.estimate(d)
        rank = self.rank_score(d)
        pool = d["in_value_pool"].to_numpy()
        p90 = np.full(len(d), np.nan)
        if pool.any():
            p90[pool] = self.p90_map.predict_proba(rank[pool].reshape(-1, 1))[:, 1]
        pct = np.where(pool, 1 - np.searchsorted(self.pool_rank_oof, np.nan_to_num(rank), side="right") / len(self.pool_rank_oof), np.nan)
        prof = self.profiles.assign(d).to_numpy()
        out = pd.DataFrame({"estimate": est, "band low": est - self.band_half_width, "band high": est + self.band_half_width,
                            "rank score": rank, "P(90+)": p90, "share of candidates ranked above": pct, "profile": prof}, index=d.index)
        out["price (2017 $)"] = d["price"].to_numpy(float)        # what the ≤ $25 pool and the verdict use (critic round 4 #4)
        out["shortlist tier"] = [self.tier(p, ok) for p, ok in zip(pct, pool)]
        out["value verdict"] = [self.verdict(e, pr) for e, pr in zip(est, d["price"].to_numpy(float))]
        out["profile name"] = [self.profiles.names.get(int(p), "no flavour terms found") if p >= 0 else "no flavour terms found" for p in prof]
        return out

    @staticmethod
    def tier(share_above: float, in_pool: bool) -> str:
        if not in_pool:
            return "Not a ≤ $25 candidate"
        for cut, label in APP_SHORTLIST_TIERS:
            if share_above < cut:
                return label
        return APP_SHORTLIST_OTHER

    def verdict(self, est: float, price: float) -> str:
        """Value verdict (R-2: from the PRICE-FREE estimate, compared with the $25 bar)."""
        if np.isnan(price):
            return "No price given: no value verdict"
        if price > config.VALUE_MAX_PRICE:
            return f"Above ${config.VALUE_MAX_PRICE:.0f}: not a value candidate"
        if est - self.band_half_width >= config.VALUE_MIN_POINTS:
            return "Likely value: whole estimated band is 90+"
        if est >= config.VALUE_MIN_POINTS:
            return "Probable value: estimate is 90+"
        if est + self.band_half_width >= config.VALUE_MIN_POINTS:
            return "Long shot: only the top of the band reaches 90"
        return "Unlikely value: band stays below 90"

    def baseline(self, d: pd.DataFrame) -> np.ndarray:
        """The variety × country baseline the pilot gate compares the band with."""
        return self.rule_models["variety × country"].predict(d)

    def rule_scores(self, d: pd.DataFrame) -> dict[str, np.ndarray]:
        """The frozen simple-rule set (``rules.simple_rule_scores``) with the development-fitted tables."""
        winery = self.rule_models["winery"].predict(d)
        price = d["price"].to_numpy(dtype=float)
        return {"price (pricier first)": price, "winery track record": winery,
                "province track record": self.rule_models["province"].predict(d),
                "variety × country": self.baseline(d), "winery track record, then price": winery + price / 1e4}

    def shortlist(self, df: pd.DataFrame, k: int = config.SHORTLIST_K, prepared: bool = False) -> pd.DataFrame:
        """BO1: rank the ≤ $25 candidates of one buying round by the ranker; the top ``k`` are the shortlist."""
        s = self.score(df, prepared)
        s = s[s["shortlist tier"] != "Not a ≤ $25 candidate"].sort_values("rank score", ascending=False, kind="stable")
        s.insert(0, "rank", np.arange(1, len(s) + 1))
        s["on shortlist"] = s["rank"] <= k
        frac = s["rank"].to_numpy() / max(len(s), 1)
        s["round tier"] = [next((lab for cut, lab in ROUND_TIERS if f <= cut), ROUND_OTHER) for f in frac]
        return s


def build(prep: pd.DataFrame, naming_dir=None, verbose: bool = True) -> ValueFinder:
    """Refit the frozen selections on all development rows, exactly as the Phase 5 lockbox run did."""
    import time
    from .clustering import fit_profile_model  # noqa: F401  (the reference implementation ProfileModel mirrors)
    from .splits import anon_attribution
    t0 = time.time()
    log = (lambda m: print(f"[{time.time() - t0:5.0f} s] {m}", flush=True)) if verbose else (lambda m: None)
    dev = development(prep)
    top_fold = top_guess_fold(anon_attribution(prep))
    groups = inner_groups(dev, top_fold=top_fold)
    alpha, _ = tune_ridge(dev, groups); log(f"quality alpha {alpha}")
    alpha_p, _ = tune_ridge(dev, groups, with_price=True); log(f"ranker alpha {alpha_p}")
    y = dev["points"].astype(float)
    oof = oof_predict(dev, groups, ridge_fit_predict(alpha)); log("quality OOF")
    a, b = fit_calibration(oof, y)
    named = dev["fold"] >= 0
    half = float(np.quantile(np.abs(y[named] - (a + b * oof[named])), config.SCORE_BAND_COVERAGE))
    rank_fp = ridge_fit_predict(alpha_p, with_price=True)
    oof_rank = oof_predict(dev, groups, rank_fp); log("ranker OOF")
    pool = dev["in_value_pool"]
    pm = probability_map(oof_rank[pool], dev.loc[pool, "points"] >= config.VALUE_MIN_POINTS)
    qp = build_preprocessor(False); qr = Ridge(alpha=alpha).fit(qp.fit_transform(dev[QUALITY_INPUTS_V2]), dev["points"])
    rp = build_preprocessor(True); rr = Ridge(alpha=alpha_p).fit(rp.fit_transform(dev[RANKER_INPUTS_V2]), dev["points"])
    log("final ridges")
    prof = ProfileModel.fit(dev, config.SELECTED_DM3[1])
    if naming_dir is not None:
        prof.names = read_profile_names(naming_dir)
    log("profiles")
    info = {"training rows": len(dev), "quality alpha": alpha, "ranker alpha": alpha_p, "calibration": (a, b), "band half-width": half,
            "selected": (config.SELECTED_DM1, config.SELECTED_DM2, config.SELECTED_DM3), "frozen code": config.PHASE4_COMMIT,
            "calibration key": CAL_ALL}
    rules = {"variety × country": GroupMeanBaseline().fit(dev, y), "winery": GroupMeanBaseline(keys=("winery",)).fit(dev, y),
             "province": GroupMeanBaseline(keys=("province",)).fit(dev, y)}
    return ValueFinder(qp, qr, (a, b), half, rp, rr, pm, np.sort(oof_rank[pool].to_numpy()), prof, info, rules,
                       training_spellings(dev))


def _maxdiff(a, b) -> float:
    """Largest absolute difference between two prediction vectors; infinite if their lengths differ, if a value is
    missing in one but not the other, or if nothing is compared (so a NaN can never pass as "reproduced")."""
    a, b = np.asarray(a, dtype=float).ravel(), np.asarray(b, dtype=float).ravel()
    if a.shape != b.shape:
        return float("inf")
    na, nb = np.isnan(a), np.isnan(b)
    if (na != nb).any() or (~na).sum() == 0:
        return float("inf")
    return float(np.abs(a[~na] - b[~na]).max())


def reproduces_lockbox(vf: ValueFinder, prep: pd.DataFrame, saved: pd.DataFrame, tol: float = 1e-8,
                       raw: pd.DataFrame | None = None) -> pd.Series:
    """§5.3 condition 1: the deployed models' lockbox predictions against ``phase5_lockbox_predictions.csv.gz``.
    Returns the largest absolute difference per output (infinite on a length or missing-value mismatch)."""
    te = prep.reindex(saved.index)
    if te["in_value_pool"].isna().any():
        return pd.Series(float("inf"), index=["ridge", config.SELECTED_DM1, config.SELECTED_DM2, "P(90+)"]).rename("max abs difference")
    pool = te["in_value_pool"].to_numpy(bool)
    priced = te["price"].notna().to_numpy()
    rank = vf.rank_score(te)
    p90 = vf.p90_map.predict_proba(rank[pool].reshape(-1, 1))[:, 1]
    diffs = {"ridge": _maxdiff(vf.ridge_score(te), saved["ridge"]),
             config.SELECTED_DM1: _maxdiff(vf.estimate(te), saved[config.SELECTED_DM1]),
             # the deployed ranker does not rank wines without a price (they are never ≤ $25 candidates); Phase 5's file
             # holds an imputed-price score for them, so the ranker is compared on the priced rows only
             config.SELECTED_DM2: _maxdiff(rank[priced], saved.loc[priced, config.SELECTED_DM2]),
             "P(90+)": _maxdiff(p90, saved.loc[pool, "P(90+)"])}
    if raw is None:
        from .data import load_raw
        raw = load_raw()
    diffs[SERVING_PATH] = _serving_path(vf, te, saved, raw.reindex(saved.index))
    return pd.Series(diffs).rename("max abs difference")


SERVING_PATH = "serving path (raw inputs, prepare_new)"
RAW_INPUT_COLS = ["description", "country", "province", "variety", "region_1", "designation", "winery", "title", "price", "vintage"]
# The raw-file columns a retailer's candidate file can hold (no ``vintage`` column: it is parsed from the title, as in Phase 3)
RAW_FILE_COLS = ["description", "country", "province", "variety", "region_1", "designation", "winery", "title", "price"]


def _serving_path(vf: "ValueFinder", te: pd.DataFrame, saved: pd.DataFrame, raw: pd.DataFrame) -> float:
    """The same lockbox reproduction through the path the tool serves, from the RAW review file (``data.load_raw``; no
    vintage column, unnormalised strings) -> ``vf.prepare`` -> score, with the price deflator at 1.0 (the lockbox prices
    are 2017 prices): the largest difference over the four outputs, or infinity if the ≤ $25 pool differs (critic rounds
    4 and 5). Phase 3 set a few hand-checked implausible prices to missing (``IMPLAUSIBLE_PRICE_TITLES``); a raw file
    still has them, so the ranker is compared on the rows Phase 3 priced, none of which is a ≤ $25 candidate otherwise."""
    if raw[RAW_FILE_COLS[0]].isna().all():
        return float("inf")
    old = config.PRICE_DEFLATOR
    config.PRICE_DEFLATOR = 1.0
    try:
        d = vf.prepare(raw[RAW_FILE_COLS])
    finally:
        config.PRICE_DEFLATOR = old
    pool = d["in_value_pool"].to_numpy(bool)
    if not np.array_equal(pool, te["in_value_pool"].to_numpy(bool)):
        return float("inf")
    priced = te["price"].notna().to_numpy()
    rank = vf.rank_score(d)
    p90 = vf.p90_map.predict_proba(rank[pool].reshape(-1, 1))[:, 1]
    return float(max(_maxdiff(vf.ridge_score(d), saved["ridge"]), _maxdiff(vf.estimate(d), saved[config.SELECTED_DM1]),
                     _maxdiff(rank[priced], saved.loc[priced, config.SELECTED_DM2]), _maxdiff(p90, saved.loc[pool, "P(90+)"])))


class SimilarWines:
    """'5 similar wines' (BSC4): cosine similarity of TF-IDF note vectors against the reviewed catalogue. Built at app
    start from the catalogue notes (not saved: it is large and quick to rebuild). Near-duplicate listings (DM5: exact
    Jaccard ≥ τ on 5-word shingles) are flagged separately."""

    def __init__(self, catalogue: pd.DataFrame):
        from sklearn.feature_extraction.text import TfidfVectorizer
        self.cat = catalogue.reset_index()
        self.vec = TfidfVectorizer(min_df=3, sublinear_tf=True, stop_words="english", max_features=50_000, dtype=np.float32)
        self.X = self.vec.fit_transform(self.cat["note"])

    def query(self, note: str, k: int = SIMILAR_K, colour: str | None = None) -> pd.DataFrame:
        """The ``k`` most similar reviewed notes; with ``colour``, only wines of that colour (red, white, ...)."""
        from .similarity import jaccard, shingles
        q = self.vec.transform([note])
        sim = (self.X @ q.T).toarray().ravel()
        if colour is not None and colour != "unmapped":
            same = self.cat["colour"].eq(colour).to_numpy()
            if same.sum() > k:
                sim = np.where(same, sim, -1.0)
        top = np.argpartition(-sim, range(k + 1))[: k + 1]
        top = top[np.argsort(-sim[top])]
        top = [i for i in top if self.cat.at[i, "note"] != note][:k]
        out = self.cat.iloc[top].copy()
        out["similarity"] = sim[top]
        qs = shingles(note)
        out["near-duplicate listing"] = [jaccard(qs, shingles(n)) >= config.DM5_TAU for n in out["note"]]
        return out


def catalogue(prep: pd.DataFrame) -> pd.DataFrame:
    """The reviewed wines shown as 'similar wines' (every prepared review; display columns only)."""
    cols = ["title", "points", "price", "country", "province", "variety", "colour", "winery", "critic", "note"]
    return prep[cols]
