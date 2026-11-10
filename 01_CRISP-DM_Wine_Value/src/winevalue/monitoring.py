"""Phase 6 (CRISP-DM 6.2): per-round data-quality flags and input-drift checks (``deployment/monitoring_plan.md``).

- ``check_schema(df)``: a candidate file must have a note (``note`` or ``description``), ``country``, ``variety`` and
  ``price`` columns; otherwise scoring is refused with the missing columns named.
- ``row_values(vf, d)``: per prepared row, the quantities the drift indicators average.
- ``indicators(rows)``: the drift indicators of one set of rows (one buying round, or a reference set).
- ``alerts(ind)``: which indicators are outside ``config.MONITOR_ALERTS``.
- ``row_flags(d)``: per-row data-quality flags (short note, no price, duplicate within the round, leak text removed).
- ``round_report(vf, cand)``: all of the above for one buying round (``deployment/score.py`` writes it next to the scores).
- ``relative_alerts(ind, history)`` / ``in_reference``: the self-referenced rule (a round's share above the development P90
  against the median of its last 3 accepted rounds).
- ``round_size(v)``: candidates per simulated round so that it holds about ``PILOT_ROUND_CANDIDATES`` ≤ $25 candidates (A7).
- ``alert_rates(vf, frames)``: how often each alert would fire on simulated A7-sized rounds drawn from reference rows
  (the false-alert rate on data like the training or the lockbox data).
- ``detection_rates(vf, raw, PERTURBATIONS)``: the same on rounds of deliberately broken candidate files (truncated
  notes, unknown words, price inflation, unlisted grapes, unrecognised countries, promotional phrasing): how often a
  broken feed is caught.
- ``oof_ranker_values`` / ``ranker_rounds`` / ``choose_lower_limits``: the two ranker-level indicators on OUT-OF-FOLD
  development scores in winery-clustered rounds, and the pre-stated rule that sets their lower alert limits.
- ``business_kpi(scored)``: the buying team's own outcome, once scores arrive: value wines per sampled wine.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import config

REQUIRED = ("country", "variety", "price")


def check_schema(df: pd.DataFrame) -> None:
    missing = [c for c in REQUIRED if c not in df.columns]
    if "note" not in df.columns and "description" not in df.columns:
        missing.insert(0, "note (or description)")
    if missing:
        raise ValueError(f"candidate file is missing required column(s): {', '.join(missing)}")


def _grapes_seen(vf) -> set:
    enc = vf.quality_pre.named_transformers_["cat"]           # one-hot columns: country, province_model, grape, colour
    rare = enc.infrequent_categories_[2]
    return set(enc.categories_[2]) - set(() if rare is None else rare)


def country_unseen(vf, d: pd.DataFrame) -> pd.Series:
    """True where the (canonicalised) country is not a development country: the models treat it as unknown origin."""
    known = set((getattr(vf, "categories", None) or {}).get("country", {}).get("spellings", ()))
    if not known:
        return pd.Series(False, index=d.index)
    return ~d["country"].isin(known)


def winery_unseen(vf, d: pd.DataFrame) -> pd.Series:
    """True where the (canonicalised) winery is missing or not a development winery: the "winery track record" rule,
    the BO1 gate's strongest comparator, then falls back to the overall mean (critic round 4 issue 1)."""
    known = set((getattr(vf, "categories", None) or {}).get("winery", {}).get("spellings", ()))
    if not known or "winery" not in d:
        return pd.Series(False, index=d.index)
    return ~d["winery"].isin(known)


def row_values(vf, d: pd.DataFrame) -> pd.DataFrame:
    """Per prepared row (``production.prepare_new`` or ``prepare.prepare`` output): the quantities behind each indicator."""
    vocab = vf.quality_pre.named_transformers_["text"].vocabulary_
    toks = d["note"].fillna("").str.lower().str.findall(r"(?u)\b\w\w+\b")
    known = toks.map(lambda t: np.mean([w in vocab for w in t]) if len(t) else np.nan)
    pool = d["in_value_pool"].to_numpy(bool)
    rank = vf.rank_score(d)
    p90 = np.full(len(d), np.nan)
    if pool.any():
        p90[pool] = vf.p90_map.predict_proba(rank[pool].reshape(-1, 1))[:, 1]
    share_above = 1 - np.searchsorted(vf.pool_rank_oof, np.nan_to_num(rank), side="right") / len(vf.pool_rank_oof)
    return pd.DataFrame({"oov share": 1 - known.to_numpy(float), "n_words": d["n_words"].to_numpy(float),
                         "unmapped colour": d["colour"].eq("unmapped").to_numpy(float),
                         "unknown province": d["province_model"].eq("Unknown province").to_numpy(float),
                         "unseen country": country_unseen(vf, d).to_numpy(float),
                         "unseen winery": winery_unseen(vf, d).to_numpy(float),
                         "rare grape": (~d["grape"].isin(_grapes_seen(vf))).to_numpy(float),
                         "estimate": vf.estimate(d), "in pool": pool.astype(float),
                         "P(90+)": p90, "above dev P90": np.where(pool, (share_above < 0.10).astype(float), np.nan)}, index=d.index)


def indicators(v: pd.DataFrame) -> dict:
    return {"rows": int(len(v)),
            "share of note words outside the model vocabulary": float(np.nanmean(v["oov share"])),
            "median note length (words)": float(np.median(v["n_words"])),
            "share unmapped colour": float(v["unmapped colour"].mean()),
            "share unknown province": float(v["unknown province"].mean()),
            "share of countries unseen in training": float(v["unseen country"].mean()),
            "share of wineries unseen in training": float(v["unseen winery"].mean()) if "unseen winery" in v else np.nan,
            "share of grapes rare or unseen in training": float(v["rare grape"].mean()),
            "mean estimate": float(v["estimate"].mean()),
            "≤ $25 share": float(v["in pool"].mean()),
            "≤ $25 candidates": int(v["in pool"].sum()),
            "mean P(90+) (≤ $25)": float(np.nanmean(v["P(90+)"])) if v["in pool"].any() else np.nan,
            "share above the development 90th percentile (≤ $25)": float(np.nanmean(v["above dev P90"])) if v["in pool"].any() else np.nan}


def ranker_lower(k: str, n_pool: float) -> float | None:
    """Lower limit of ranker indicator ``k`` for a round with ``n_pool`` ≤ $25 candidates (``config.MONITOR_RANKER_LOWER``:
    the row for the largest size the round reaches), or None below ``MONITOR_RANKER_MIN_POOL`` (not read)."""
    sizes = [s for s in sorted(config.MONITOR_RANKER_LOWER) if s <= n_pool]
    if not sizes or n_pool < config.MONITOR_RANKER_MIN_POOL:
        return None
    return config.MONITOR_RANKER_LOWER[sizes[-1]][RANKER_INDICATORS.index(k)]


def alerts(ind: dict, rules: dict = config.MONITOR_ALERTS) -> list[str]:
    """The alerts a round's indicators set off. The two ranker indicators use the lower limit for the round's number of
    ≤ $25 candidates (``ranker_lower``) and are not read below ``config.MONITOR_RANKER_MIN_POOL`` of them."""
    out = []
    for k, (how, lim) in rules.items():
        x = ind.get(k, np.nan)
        if np.isnan(x):
            continue
        if how == "outside" and lim[0] == config.MONITOR_BY_ROUND_SIZE:
            lo = ranker_lower(k, ind.get("≤ $25 candidates", np.inf))
            lim = (-np.inf if lo is None else lo, lim[1])     # the upper limit is read at any round size
        if (how == "above" and x > lim) or (how == "below" and x < lim) or (how == "outside" and not lim[0] <= x <= lim[1]):
            out.append(f"{k} = {x:.3g} ({how} {lim})")
    return out


RELATIVE_INDICATOR = "share above the development 90th percentile (≤ $25)"


RELATIVE_ALERTED, ACCEPTED = "self-referenced alert", "accepted"


def in_reference(h: dict, min_pool: int = config.MONITOR_RELATIVE_MIN_POOL) -> bool:
    """Whether an earlier round may serve as the self-referenced rule's reference: at least ``min_pool`` ≤ $25 candidates,
    a finite share, and no self-referenced alert of its own unless the analyst has accepted the round (revision 7, critic
    round 6 issue 1: otherwise a fault that persists becomes its own reference after two rounds and the rule goes quiet)."""
    return (h.get("≤ $25 candidates", 0) >= min_pool and np.isfinite(h.get(RELATIVE_INDICATOR, np.nan))
            and (not h.get(RELATIVE_ALERTED, False) or bool(h.get(ACCEPTED, False))))


def relative_alerts(ind: dict, history: list[dict], min_pool: int = config.MONITOR_RELATIVE_MIN_POOL) -> list[str]:
    """The self-referenced rule (``config.MONITOR_RELATIVE_*``): ``history`` is the earlier rounds' indicator dicts, oldest
    first, each optionally with ``RELATIVE_ALERTED`` and ``ACCEPTED`` flags. Only rounds that pass ``in_reference``
    count, the current round needs at least ``min_pool`` ≤ $25 candidates, and the last ``MONITOR_RELATIVE_HISTORY``
    reference rounds are used. The drop (0.5) and the history length (3) are judgement calls; only ``min_pool`` comes
    from a stated rule (``choose_relative_min_pool``)."""
    ok = [h for h in history if in_reference(h, min_pool)]
    x = ind.get(RELATIVE_INDICATOR, np.nan)
    if len(ok) < config.MONITOR_RELATIVE_HISTORY or not np.isfinite(x) or ind.get("≤ $25 candidates", 0) < min_pool:
        return []
    med = float(np.median([h[RELATIVE_INDICATOR] for h in ok[-config.MONITOR_RELATIVE_HISTORY:]]))
    if x < config.MONITOR_RELATIVE_DROP * med:
        return [f"{RELATIVE_INDICATOR} = {x:.3g}, below {config.MONITOR_RELATIVE_DROP:g} × its median over the last "
                f"{config.MONITOR_RELATIVE_HISTORY} rounds ({med:.3g})"]
    return []


def share_band(baseline_share: float, current=None) -> tuple[float, float]:
    """The ≤ $25-share alert band for a retailer whose pre-tool rounds had ``baseline_share`` ≤ $25 candidates: the
    configured band if the share lies in ``config.MONITOR_SHARE_KEEP``, else re-centred on it (critic round 6 issue 9).
    A file pre-filtered at $25 (share 1.0) stays outside the band either way."""
    current = current or config.MONITOR_ALERTS["≤ $25 share"][1]
    lo, hi = config.MONITOR_SHARE_KEEP
    if lo <= baseline_share <= hi:
        return tuple(current)
    return (round(max(0.05, baseline_share - 0.20), 2), round(min(0.98, baseline_share + 0.45), 2))


def round_size(v: pd.DataFrame, pool: int = config.PILOT_ROUND_CANDIDATES) -> int:
    """Candidates to draw so that a simulated round holds about ``pool`` ≤ $25 candidates (A7: about 1,000 per round)."""
    return int(np.ceil(pool / max(float(v["in pool"].mean()), 1e-9)))


def row_flags(d: pd.DataFrame, vf=None) -> pd.DataFrame:
    """Per-row data-quality flags for one round. ``d``: ``prepare_new`` output (keeps ``description`` and ``note``)."""
    from .prepare import _norm
    from .similarity import detect_near_duplicates
    f = pd.DataFrame(index=d.index)
    f["flag: short note"] = d["n_words"] < config.MONITOR_SHORT_NOTE_WORDS
    f["flag: no price"] = d["price"].isna()
    dup = d["note"].duplicated(keep="first")
    if len(d) > 1:
        nd = detect_near_duplicates(d["note"].fillna("").reset_index(drop=True))
        if len(nd):
            dup |= pd.Series(np.isin(np.arange(len(d)), nd["j"].to_numpy()), index=d.index)
    f["flag: duplicate in round"] = dup
    f["flag: leak text removed"] = _norm(d["description"].fillna("")).ne(d["note"].fillna(""))
    if vf is not None:
        f["flag: country unseen in training"] = country_unseen(vf, d)
    return f


def round_report(vf, cand: pd.DataFrame, history: list[dict] | None = None) -> tuple[pd.DataFrame, dict]:
    """Flags per row and the round's drift report (indicators, alerts, flag counts). ``history``: the earlier rounds'
    indicator dicts, oldest first, for the self-referenced rule (``relative_alerts``)."""
    check_schema(cand)
    d = vf.prepare(cand)
    flags = row_flags(d, vf)
    ind = indicators(row_values(vf, d))
    from .production import CANONICAL_COLUMNS
    renamed = {c: int((d[c].ne(d[f"{c} (as given)"]) & d[f"{c} (as given)"].notna()).sum()) for c in CANONICAL_COLUMNS
               if f"{c} (as given)" in d}
    rel = relative_alerts(ind, history or [])
    return flags, {"indicators": ind, "alerts": alerts(ind) + rel, RELATIVE_ALERTED: bool(rel), ACCEPTED: False,
                   "flag counts": {k: int(v.sum()) for k, v in flags.items()},
                   "names mapped to training spellings": renamed, "price deflator": config.PRICE_DEFLATOR}


def alert_rates(vf, frames: dict[str, pd.DataFrame], size: int | None = None, n_rounds: int = 500, seed: int = config.SEED,
                values: dict[str, pd.DataFrame] | None = None, history: pd.DataFrame | None = None) -> pd.DataFrame:
    """Share of simulated buying rounds in which each alert, the self-referenced rule, and any alert fire. A round is
    ``size`` rows drawn without replacement from a reference frame; by default as many as hold about
    ``PILOT_ROUND_CANDIDATES`` ≤ $25 candidates (A7; ``round_size``). The self-referenced rule compares each round with
    3 earlier rounds drawn from ``history`` (row values of a normal feed), or from the same frame if None.
    ``values``: precomputed ``row_values`` per frame (used instead of ``frames``)."""
    rng = np.random.default_rng([seed, 18])
    out = {}
    for name, d in (values or frames).items():
        v = d if values else row_values(vf, d)
        h = v if history is None else history
        n = min(size or round_size(h), len(v))
        nh = min(size or round_size(h), len(h))
        fired = {k: 0 for k in config.MONITOR_ALERTS}
        rel = anyf = 0
        for _ in range(n_rounds):
            ind = indicators(v.iloc[rng.choice(len(v), size=n, replace=False)])
            past = [indicators(h.iloc[rng.choice(len(h), size=nh, replace=False)]) for _ in range(config.MONITOR_RELATIVE_HISTORY)]
            a, r = alerts(ind), relative_alerts(ind, past)
            for k in fired:
                fired[k] += any(x.startswith(k + " =") for x in a)
            rel += bool(r)
            anyf += bool(a or r)
        out[name] = {**{k: f / n_rounds for k, f in fired.items()}, "self-referenced drop": rel / n_rounds,
                     "any alert": anyf / n_rounds, "candidates per round": n}
    return pd.DataFrame(out).T


# ---- detection: deliberately broken candidate files (Phase 6 critic round 2 issue 6; fixed before the simulation ran) ----
_PROMO = " An outstanding, exceptional wine of superb quality and a must-buy for any cellar."


def _truncate(n):
    return lambda d, rng: d.assign(description=d["description"].fillna("").str.split().str[:n].str.join(" "))


def _unknown(share):
    def f(d, rng):
        def one(note):
            w = note.split()
            hit = rng.random(len(w)) < share
            return " ".join(f"qzx{rng.integers(10**6)}" if h else x for x, h in zip(w, hit))
        return d.assign(description=d["description"].fillna("").map(one))
    return f


def _price(factor):
    return lambda d, rng: d.assign(price=d["price"] * factor)


def _countries(share):
    def f(d, rng):
        hit = rng.random(len(d)) < share
        return d.assign(country=np.where(hit, [f"Unlisted country {i % 20}" for i in range(len(d))], d["country"]))
    return f


def _country_case(d, rng):
    alias = {"US": "USA"}
    return d.assign(country=d["country"].map(lambda c: alias.get(c, str(c).upper()) if pd.notna(c) else c))


def _grapes(share):
    def f(d, rng):
        hit = rng.random(len(d)) < share
        return d.assign(variety=np.where(hit, [f"Unlisted grape {i % 50}" for i in range(len(d))], d["variety"]))
    return f


PERTURBATIONS = {
    "none (lockbox as is)": lambda d, rng: d,
    # revision 7 (critic round 6 issue 2): two milder truncations than the self-referenced rule was designed against
    "notes truncated to 40 words": _truncate(40),
    "notes truncated to 35 words": _truncate(35),
    "notes truncated to 30 words": _truncate(30),
    "notes truncated to 25 words": _truncate(25),
    "notes truncated to 15 words": _truncate(15),
    "2% of note words unknown": _unknown(0.02),
    "5% of note words unknown": _unknown(0.05),
    "20% of note words unknown (another language, in part)": _unknown(0.20),
    "prices × 1.1": _price(1.1),
    "prices × 1.3": _price(1.3),
    "prices × 1.5": _price(1.5),
    "10% of grapes unlisted": _grapes(0.10),
    "countries upper-case, US as USA (should change nothing)": _country_case,
    "5% of countries unrecognised": _countries(0.05),
    "promotional sentence added to every note": lambda d, rng: d.assign(description=d["description"].fillna("") + _PROMO),
    # revision 6 (critic round 5 issue 1): a candidate file filtered at $25 before scoring
    "file pre-filtered at $25 (only ≤ $25 wines sent)": lambda d, rng: d[pd.to_numeric(d["price"], errors="coerce") <= config.VALUE_MAX_PRICE],
}


def detection_rates(vf, raw: pd.DataFrame, perturbations: dict = PERTURBATIONS, size: int | None = None, n_rounds: int = 200,
                    seed: int = config.SEED) -> pd.DataFrame:
    """For each perturbation of the raw candidate file ``raw`` (``description``, ``country``, ``variety``, ``price``, ...):
    the share of simulated rounds in which each alert, the self-referenced rule (against 3 rounds of the unaltered file),
    and any alert fire; plus the perturbed pool's indicator values, so a miss can be read against the limits. A round has
    the same number of candidates for every perturbation: by default as many as hold about ``PILOT_ROUND_CANDIDATES``
    ≤ $25 candidates in the unaltered file (A7)."""
    rng = np.random.default_rng([seed, 21])
    vals, ind = {}, {}
    for name, f in perturbations.items():
        v = row_values(vf, vf.prepare(f(raw.copy(), rng)))
        vals[name] = v
        ind[name] = indicators(v)
    base = next(iter(vals.values()))                   # the first perturbation is "none"
    rates = alert_rates(vf, {}, size=size or round_size(base), n_rounds=n_rounds, seed=seed, values=vals, history=base)
    pool = pd.DataFrame(ind).T.drop(columns="rows").add_prefix("pool value: ")
    return rates.join(pool)


# ---- the ranker-level lower limits, set on out-of-fold development rounds (Phase 6 critic round 3 issue 3) ----
RANKER_INDICATORS = ("mean P(90+) (≤ $25)", "share above the development 90th percentile (≤ $25)")


def oof_ranker_values(vf, prep: pd.DataFrame, fold_preds: pd.DataFrame, col: str = "ridge + log price") -> dict[str, pd.DataFrame]:
    """Per development fold: P(90+) and "above the development P90" from the OUT-OF-FOLD ranker of Phase 4
    (``phase4_fold_predictions.csv.gz``, the fold held out), mapped through the deployed P(90+) map and percentile table,
    for ≤ $25 rows, with their winery (for clustered rounds)."""
    fp = fold_preds.set_index("review_id")
    out = {}
    for f, g in fp.groupby("fold"):
        rows = prep.loc[g.index]
        pool = rows["in_value_pool"].to_numpy(bool)
        r = g[col].to_numpy(float)[pool]
        out[f"development fold {f}"] = pd.DataFrame({
            "P(90+)": vf.p90_map.predict_proba(r.reshape(-1, 1))[:, 1],
            "above dev P90": (1 - np.searchsorted(vf.pool_rank_oof, r, side="right") / len(vf.pool_rank_oof) < 0.10).astype(float),
            "winery_key": rows["winery_key"].to_numpy()[pool]}, index=g.index[pool])
    return out


def ranker_rounds(values: dict[str, pd.DataFrame], size: int = 1000, n_rounds: int = 500, seed: int = config.SEED) -> pd.DataFrame:
    """Round-level values of the two ranker indicators in winery-clustered rounds: whole wineries drawn at random until
    the round has ``size`` candidates (a retailer's round lists several wines per producer)."""
    rng = np.random.default_rng([seed, 22])
    out = []
    for name, v in values.items():
        groups = v.groupby("winery_key").indices
        keys = np.array(list(groups))
        for i in range(n_rounds):
            idx, n = [], 0
            for k in keys[rng.permutation(len(keys))]:
                idx.append(groups[k]); n += len(groups[k])
                if n >= size:
                    break
            x = v.iloc[np.concatenate(idx)]
            out.append({"pool": name, "round": i, "candidates": len(x), RANKER_INDICATORS[0]: float(x["P(90+)"].mean()),
                        RANKER_INDICATORS[1]: float(x["above dev P90"].mean())})
    return pd.DataFrame(out)


def relative_drop_rates(rounds: pd.DataFrame) -> pd.Series:
    """False-alert rate of the self-referenced rule on consecutive simulated rounds (``ranker_rounds`` output, per size and
    pool): round i alerts if its share above the development P90 is below ``MONITOR_RELATIVE_DROP`` × the median of the
    last 3 earlier rounds that did not alert themselves (``in_reference``: no analyst accepts a simulated alert)."""
    k, m = RANKER_INDICATORS[1], config.MONITOR_RELATIVE_HISTORY
    def rate(g):
        ref, hits, n = [], 0, 0
        for x in g[k].to_numpy():
            if len(ref) >= m:
                n += 1
                hit = x < config.MONITOR_RELATIVE_DROP * float(np.median(ref[-m:]))
                hits += hit
                if hit:
                    continue                  # an alerted round stays out of the reference
            ref.append(x)
        return float(hits / n) if n else float("nan")
    keys = ["size", "pool"] if "size" in rounds else ["pool"]
    return rounds.groupby(keys).apply(rate).rename("self-referenced drop")


def choose_relative_min_pool(rates: pd.Series, max_false: float = config.MONITOR_RELATIVE_MAX_FALSE) -> int | None:
    """Pre-stated rule: the smallest tabulated round size from which (that size and every larger one) the self-referenced
    rule's false-alert rate (``relative_drop_rates``) is at most ``max_false`` in every development fold."""
    worst = rates.groupby(level="size").max().sort_index()
    ok = [s for s in worst.index if (worst.loc[s:] <= max_false).all()]
    return int(min(ok)) if ok else None


def choose_lower_limit_table(values: dict[str, pd.DataFrame], sizes=None, q: float = config.MONITOR_LOWER_LIMIT_QUANTILE,
                             seed: int = config.SEED) -> tuple[dict[int, tuple[float, float]], pd.DataFrame]:
    """``choose_lower_limits`` on winery-clustered out-of-fold rounds of each size (number of ≤ $25 candidates) in
    ``config.MONITOR_RANKER_LOWER``: the table, and the rounds (with a ``size`` column)."""
    sizes = sorted(sizes or config.MONITOR_RANKER_LOWER)
    tab, all_rounds = {}, []
    for s in sizes:
        r = ranker_rounds(values, size=s, seed=seed)
        lim = choose_lower_limits(r, q)
        tab[s] = tuple(lim[k] for k in RANKER_INDICATORS)
        all_rounds.append(r.assign(size=s))
    return tab, pd.concat(all_rounds, ignore_index=True)


def choose_lower_limits(rounds: pd.DataFrame, q: float = config.MONITOR_LOWER_LIMIT_QUANTILE) -> dict[str, float]:
    """Pre-stated rule (development folds only): each ranker indicator's lower alert limit is the ``q`` quantile of its
    round values in the development fold where that quantile is lowest, rounded DOWN to 0.01. So in every development
    fold at most about ``q`` of normal rounds alert low on that indicator."""
    return {k: float(np.floor(100 * rounds.groupby("pool")[k].quantile(q).min()) / 100) for k in RANKER_INDICATORS}


def ranker_alert_rates(rounds: pd.DataFrame, rules: dict = config.MONITOR_ALERTS) -> pd.DataFrame:
    """Share of the rounds from ``ranker_rounds`` in which each ranker alert fires (low or high), per pool."""
    t = {}
    for name, g in rounds.groupby(["size", "pool"] if "size" in rounds else "pool"):
        row, anyf = {}, np.zeros(len(g), bool)
        for k in RANKER_INDICATORS:
            hi = rules[k][1][1]
            lo = np.array([ranker_lower(k, n) if ranker_lower(k, n) is not None else -np.inf for n in g["candidates"]])
            low, high = g[k].to_numpy() < lo, g[k].to_numpy() > hi
            row[f"{k}: low"], row[f"{k}: high"] = float(low.mean()), float(high.mean())
            anyf |= low | high
        row["any ranker alert"] = float(anyf.mean())
        t[name] = row
    out = pd.DataFrame(t).T
    out.index.names = ["size", "pool"] if "size" in rounds else ["pool"]
    return out


_TRUE, _FALSE = {"1", "true", "yes", "y", "t"}, {"0", "false", "no", "n", "f", ""}


def _flag(x: pd.Series, name: str) -> pd.Series:
    """A yes/no column as read from a CSV (booleans, 0/1, or yes/no/true/false strings; blank = no). Anything else is
    refused rather than guessed (critic round 5 issue 5: ``astype(bool)`` made every "no" a yes)."""
    def one(v):
        if isinstance(v, (bool, np.bool_)):
            return bool(v)
        if v is None or (isinstance(v, float) and np.isnan(v)):
            return False
        k = str(v).strip().casefold()
        if k in _TRUE or (k.replace(".0", "") == "1"):
            return True
        if k in _FALSE or (k.replace(".0", "") == "0"):
            return False
        raise ValueError(f"column {name!r}: cannot read {v!r} as yes/no")
    return x.map(one).astype(bool)


def business_kpi(scored: pd.DataFrame) -> dict:
    """The buying team's outcome (BO1's purpose), from a quarter's logged candidates with ``sampled`` (the team sampled
    the wine) and ``points`` (critic score, once published): among SAMPLED wines that were later reviewed, the share
    scoring 90+, and the samples spent per value wine found. Compared with the same figures from the rounds before the
    tool (monitoring plan §3). Flags are read with ``_flag``. With a ``shortlist used`` column (the round's samples were picked with the shortlist; logged
    per round from rollout step 1, critic round 4 issue 7), the same figures are also given for rounds with and without it.
    The baseline is this function on the pre-tool rounds' sampling records (rollout step 0). The with/without split is
    descriptive: buyers chose when to use the shortlist, so it is not evidence of an effect."""
    scored = scored.assign(sampled=_flag(scored["sampled"], "sampled"))
    if "shortlist used" in scored:
        scored = scored.assign(**{"shortlist used": _flag(scored["shortlist used"], "shortlist used")})

    def kpi(x):
        s = x[x["sampled"] & x["points"].notna()]
        hit = s["points"] >= config.VALUE_MIN_POINTS
        return {"sampled and reviewed": int(len(s)), "value wines": int(hit.sum()),
                "share 90+": float(hit.mean()) if len(s) else float("nan"),
                "samples per value wine": float(len(s) / hit.sum()) if hit.sum() else float("inf")}
    out = kpi(scored)
    if "shortlist used" in scored:
        used = scored["shortlist used"]
        out["rounds with the shortlist"], out["rounds without it"] = kpi(scored[used]), kpi(scored[~used])
    return out
