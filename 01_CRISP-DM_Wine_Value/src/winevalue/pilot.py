"""Phase 6 (CRISP-DM 6.1 / 6.2): the pilot decision protocol, frozen before any pilot data (report §5.3 conditions 3, 4, 7).

The same functions score the real pilot (``deployment/pilot_eval.py``) and the simulated pilots used to set and check
the protocol (notebook §6). A pilot table has one row per scored pilot wine with columns:

- ``points`` (critic score, once it arrives), ``sel`` (price-free score estimate), ``base`` (variety × country baseline),
  ``rank`` (shortlist ranker score), one ``rule: ...`` column per frozen simple rule;
- ``winery_key`` (bootstrap cluster), ``source`` (note source: named writer, else importer or producer), ``country``;
- ``order`` (1 = first wine whose critic score arrived; interim checks use the first n wines in this order).

Pass rules are the pre-registered ones (``config.PILOT_*``), applied per output (§1.1 amendment). Every gate is computed
on ALL pilot wines; a stop-rule withdrawal never removes wines from a gate.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import config
from .phase5 import _top_precision

POOLED = "other sources (pooled)"
STOPPED = ("stopped: fewer than {s} note sources reached {w} scored wines by {m} wines; deploy nothing; report and "
           "redesign the pilot's note sourcing")


def name_key(s) -> pd.Series:
    """How a note source or country is matched between the pilot, ``band_status.json`` and the tool: whitespace and
    mojibake normalised (``prepare._norm``), curly quotes and accents treated as an apostrophe, case folded."""
    from .prepare import _norm
    x = pd.Series(s, dtype=object).fillna("").astype(str)
    return _norm(x).str.replace("[’‘`´]", "'", regex=True).str.casefold()


def canonical_names(t: pd.DataFrame, cols=("source", "country")) -> pd.DataFrame:
    """One spelling per note source and per country, fixed at intake (Phase 6 critic round 2 issue 1), so that every
    unit, source count, status entry and tool lookup uses the same name. Spellings with the same ``name_key`` are merged
    into the most frequent one (ties: the first in sorted order); the spelling as given is kept in ``<col> (as given)``.
    Idempotent. Spellings the key can't merge (for example "Smith Imports" and "Smith Imports Ltd") stay separate, so
    ``pilot_eval.py`` prints the source list for the analyst to check."""
    t = t.copy()
    for c in cols:
        if c not in t:
            continue
        raw = t[c].fillna("unknown" if c == "source" else "Unknown").astype(str)
        key = name_key(raw).set_axis(t.index)
        canon = (pd.DataFrame({"k": key, "r": raw}).groupby(["k", "r"]).size().reset_index(name="n")
                 .sort_values(["k", "n", "r"], ascending=[True, False, True]).drop_duplicates("k").set_index("k")["r"])
        if f"{c} (as given)" not in t:
            t[f"{c} (as given)"] = raw
        t[c] = key.map(canon)
    return t


# name keys of a missing note source (Phase 6 critic rounds 3 and 4): never counted toward the source minimum, and merged
# into one "unknown" stop-rule unit at intake
UNSOURCED = {"unknown", "", "n/a", "na", "n.a.", "none", "-", "--", "—", "?", "null", "nan", "not known", "unsourced", "no source",
             "n.a", "n/k", "tbd", "tba", "various", "misc", "mixed"}


def counted_sources(src: pd.Series) -> pd.Series:
    """Scored wines per note source that counts toward ``PILOT_MIN_SOURCES``: every named source, not the rows without
    one (Phase 6 critic round 3 issue 1b). Rows without a source still form a stop-rule unit (``check_units``)."""
    vc = src.value_counts()
    return vc[~name_key(pd.Series(vc.index)).isin(UNSOURCED).to_numpy()]


def is_primary_scorer(scorer: pd.Series) -> pd.Series:
    """True for scores from ``config.PILOT_PRIMARY_SCORER`` or one of its ``PILOT_PRIMARY_SCORER_ALIASES`` (matched
    ignoring case, spaces and punctuation). ``pilot_eval.py`` prints every distinct scorer spelling for the analyst."""
    def key(x):
        return name_key(x).str.replace(r"[^0-9a-z]", "", regex=True)
    want = set(key(pd.Series([config.PILOT_PRIMARY_SCORER, *config.PILOT_PRIMARY_SCORER_ALIASES])))
    return pd.Series(key(scorer).isin(want).to_numpy(), index=scorer.index)


def source_list(t: pd.DataFrame) -> pd.DataFrame:
    """The canonical note sources with their scored wines and the spellings merged into each (``pilot_eval.py``)."""
    given = t["source (as given)"] if "source (as given)" in t else t["source"]
    return (pd.DataFrame({"source": t["source"], "given": given}).groupby("source")
            .agg(wines=("given", "size"), spellings=("given", lambda s: " | ".join(sorted(set(s)))))
            .sort_values("wines", ascending=False).reset_index())


def band_hidden(df: pd.DataFrame, status: dict | None) -> pd.Series:
    """True where the score band (and the value verdict) must be hidden, given a band status (``status_from``). The ONE
    rule used by the protocol simulation, ``pilot_eval.py``, ``score.py`` and the app. A missing note source counts as
    "unknown" and a missing country as "Unknown", as in the pilot table."""
    status = status or {}
    hide = pd.Series(bool(status.get("withdrawn everywhere")), index=df.index)
    src = name_key(df["source"].fillna("unknown") if "source" in df else pd.Series("unknown", index=df.index)).set_axis(df.index)
    named = set(name_key(status.get("sources", []))) | set(name_key(status.get("pooled sources", [])))
    hide |= src.isin(named)
    cty = name_key(df["country"].fillna("Unknown") if "country" in df else pd.Series("Unknown", index=df.index)).set_axis(df.index)
    hide |= cty.isin(set(name_key(status.get("countries", []))))
    return hide


def status_from(withdrawn: dict, pooled_members: set) -> dict:
    """The band status the tool reads: withdrawn named sources, the member sources of the pooled unit at every check where
    it fired, withdrawn countries, and whether the whole-pilot unit fired."""
    return {"withdrawn everywhere": ("pilot", "all wines") in withdrawn,
            "sources": sorted(n for (k, n) in withdrawn if k == "source" and n != POOLED),
            "pooled sources": sorted(pooled_members),
            "countries": sorted(n for (k, n) in withdrawn if k == "country")}


def _codes(d: pd.DataFrame) -> tuple[np.ndarray, int]:
    c = pd.factorize(d["winery_key"])[0]
    return c, int(c.max()) + 1


def gate(d: pd.DataFrame, n_boot: int = config.PILOT_N_BOOT, frac: float = 0.2, seed: int = config.SEED) -> dict:
    """Both parts of the pre-registered pilot gate on one set of pilot wines, with winery-cluster bootstrap LBs.
    BO2 (score band): within-±2 gain over variety × country ≥ +5 pp, 90% LB > 0. BO1 (shortlist): top-20% precision
    for 90+ ≥ 1.3× the best frozen simple rule on these wines, 90% LB > 1.0."""
    rng = np.random.default_rng([seed, 11])
    y, sel, base = (d[c].to_numpy(float) for c in ("points", "sel", "base"))
    is_val = y >= config.VALUE_MIN_POINTS
    rule_cols = [c for c in d.columns if c.startswith("rule: ")]
    S = np.vstack([d["rank"].to_numpy(float)] + [d[c].to_numpy(float) for c in rule_cols])
    d_win = (np.abs(y - sel) <= 2).astype(float) - (np.abs(y - base) <= 2).astype(float)
    codes, nc = _codes(d)
    cnt, sd = np.bincount(codes, minlength=nc), np.bincount(codes, weights=d_win, minlength=nc)
    draws = rng.integers(0, nc, size=(n_boot, nc))
    gain, gain_lb = float(d_win.mean()), float(np.quantile(sd[draws].sum(1) / cnt[draws].sum(1), 0.10))
    p = _top_precision(S, is_val, frac, rng)
    best = 1 + int(np.argmax(p[1:]))
    lift = p[0] / p[best] if p[best] > 0 else np.inf
    members = [np.flatnonzero(codes == c) for c in range(nc)]
    lifts = []
    for b in range(n_boot):
        bi = np.concatenate([members[c] for c in draws[b]])
        pb = _top_precision(S[[0, best]][:, bi], is_val[bi], frac, rng)
        lifts.append(pb[0] / pb[1] if pb[1] > 0 else np.inf)
    lift_lb = float(np.quantile(lifts, 0.10))
    return {"wines": len(d), "within gain (pp)": 100 * gain, "within gain LB (pp)": 100 * gain_lb,
            "BO2 passes": bool(gain >= config.PILOT_WITHIN_GAIN_PP and gain_lb > 0),
            "best simple rule": rule_cols[best - 1], "top-20% lift": float(lift), "top-20% lift LB": lift_lb,
            "BO1 passes": bool(lift >= config.PILOT_TOP20_LIFT and lift_lb > config.PILOT_TOP20_LIFT_LOWER)}


PAUSED = "paused by the shortlist futility check: deploy nothing; report to the buying lead and return to Phase 4"


def decision(g: dict, withdrawn_everywhere: bool = False, paused: bool = False) -> str:
    """Option F (§5.3 condition 3): what may be deployed after the final gate. A futility pause ends the pilot with no
    deployment, whatever the later wines would have shown."""
    if paused:
        return PAUSED
    if g["BO1 passes"] and g["BO2 passes"] and not withdrawn_everywhere:
        return "deploy shortlist and show score band internally"
    if g["BO1 passes"]:
        return "deploy shortlist only (band not shown)"
    return "deploy nothing; report both results and return to Phase 4"


def residual_ci(d: pd.DataFrame, n_boot: int, ci: float, rng) -> tuple[float, float, float]:
    """Mean residual (estimate - actual) and its two-sided ``ci`` winery-bootstrap interval."""
    r = d["sel"].to_numpy(float) - d["points"].to_numpy(float)
    codes, nc = _codes(d)
    cnt, sr = np.bincount(codes, minlength=nc), np.bincount(codes, weights=r, minlength=nc)
    draws = rng.integers(0, nc, size=(n_boot, nc))
    lo, hi = np.quantile(sr[draws].sum(1) / cnt[draws].sum(1), ((1 - ci) / 2, 1 - (1 - ci) / 2))
    return float(r.mean()), float(lo), float(hi)


def check_units(d: pd.DataFrame, min_wines: int = config.PILOT_STOP_MIN_WINES) -> dict[tuple[str, str], pd.Index]:
    """The units the band stop rule is checked on, given the wines scored so far: each note source with ≥ ``min_wines``;
    all smaller sources pooled into one unit (checked once it reaches ``min_wines``); each country with ≥ ``min_wines``;
    and the whole pilot."""
    units = {}
    n_src = d["source"].value_counts()
    for s in n_src.index[n_src >= min_wines]:
        units[("source", s)] = d.index[d["source"].eq(s)]
    small = d.index[d["source"].isin(n_src.index[n_src < min_wines])]
    if len(small) >= min_wines:
        units[("source", POOLED)] = small
    n_c = d["country"].value_counts()
    for c in n_c.index[n_c >= min_wines]:
        units[("country", c)] = d.index[d["country"].eq(c)]
    units[("pilot", "all wines")] = d.index
    return units


def band_check(d: pd.DataFrame, n_boot: int = config.PILOT_N_BOOT, limit: float = config.PILOT_STOP_RESIDUAL, ci: float = config.PILOT_STOP_CI,
               min_wines: int = config.PILOT_STOP_MIN_WINES, seed: int = config.SEED) -> pd.DataFrame:
    """One interim check of the band stop rule on the wines scored so far: per unit, the mean residual, its CI and
    whether the rule fires (CI wholly outside ±``limit``). The pilot-wide row needs ≥ ``min_wines`` too."""
    rng = np.random.default_rng([seed, 12])
    rows = []
    for (kind, name), idx in check_units(d, min_wines).items():
        if len(idx) < min_wines:
            continue
        m, lo, hi = residual_ci(d.loc[idx], n_boot, ci, rng)
        rows.append({"unit": kind, "name": name, "wines": len(idx), "mean residual": m, "CI low": lo, "CI high": hi,
                     "fires": bool(lo > limit or hi < -limit)})
    return pd.DataFrame(rows, columns=["unit", "name", "wines", "mean residual", "CI low", "CI high", "fires"])


def shortlist_check(d: pd.DataFrame, n_boot: int = config.PILOT_N_BOOT, seed: int = config.SEED) -> dict:
    """Interim shortlist futility check: pause if, with ≥ ``PILOT_PAUSE_MIN_WINES`` scored wines, the top-20% lift point
    estimate is below ``PILOT_PAUSE_LIFT`` (the shortlist is doing no better than the best simple rule)."""
    if len(d) < config.PILOT_PAUSE_MIN_WINES:
        return {"wines": len(d), "checked": False, "pause": False}
    g = gate(d, n_boot=n_boot, seed=seed)
    return {"wines": len(d), "checked": True, "top-20% lift": g["top-20% lift"], "top-20% lift LB": g["top-20% lift LB"],
            "pause": bool(g["top-20% lift"] < config.PILOT_PAUSE_LIFT)}


def source_intercept(d: pd.DataFrame, first: int = config.PILOT_INTERCEPT_FIRST,
                     min_wines: int = config.PILOT_INTERCEPT_MIN_WINES) -> pd.DataFrame:
    """Secondary analysis, reported only (§5.3 condition 4): for each note source with ≥ ``min_wines`` scored wines, the
    intercept is the mean residual of its first ``first`` wines (in ``order``); it is subtracted from the estimates of
    that source's LATER wines, and the within-±2 gain over the baseline is reported on those later wines with and
    without the adjustment."""
    out = []
    for s, x in d.sort_values("order").groupby("source", sort=False):
        if len(x) < min_wines:
            continue
        head, tail = x.iloc[:first], x.iloc[first:]
        icpt = float((head["sel"] - head["points"]).mean())
        y, base = tail["points"].to_numpy(float), tail["base"].to_numpy(float)
        w = lambda p: float((np.abs(y - p) <= 2).mean())
        out.append({"source": s, "wines": len(x), "intercept (first wines)": icpt, "later wines": len(tail),
                    "gain unadjusted (pp)": 100 * (w(tail["sel"].to_numpy(float)) - w(base)),
                    "gain adjusted (pp)": 100 * (w(tail["sel"].to_numpy(float) - icpt) - w(base))})
    return pd.DataFrame(out)


def run_protocol(d: pd.DataFrame, n_boot: int = config.PILOT_N_BOOT, seed: int = config.SEED) -> dict:
    """The whole protocol on one pilot table, in order of arrival. Checks every ``PILOT_CHECK_EVERY`` wines:
    the band stop rule on every unit, then
    - the decision point: the first check with ≥ ``PILOT_MIN_WINES`` wines and ≥ ``PILOT_MIN_SOURCES`` sources with
      ≥ ``PILOT_STOP_MIN_WINES`` wines each. The final gate is computed on ALL wines up to it; later wines are not used;
    - otherwise the shortlist futility check (from ``PILOT_PAUSE_MIN_WINES``). A pause ends the pilot.
    Without a decision point by ``PILOT_MAX_WINES`` wines the pilot stops with no deployment. A band withdrawal is
    permanent; the pooled unit's withdrawal covers its member sources at every check where it fired."""
    d = canonical_names(d.sort_values("order"))
    n = len(d)
    checks = list(range(config.PILOT_CHECK_EVERY, min(n, config.PILOT_MAX_WINES) + 1, config.PILOT_CHECK_EVERY))
    withdrawn, pooled, log = {}, set(), []
    paused_at = final_at = None
    for c in checks:
        sub = d.iloc[:c]
        bc = band_check(sub, n_boot=n_boot, seed=seed + c)
        n_src = sub["source"].value_counts()
        for _, r in bc[bc["fires"]].iterrows():
            withdrawn.setdefault((r["unit"], r["name"]), c)
            if r["name"] == POOLED:
                pooled |= set(n_src.index[n_src < config.PILOT_STOP_MIN_WINES])
        enough = int((counted_sources(sub["source"]) >= config.PILOT_STOP_MIN_WINES).sum())
        is_final = c >= config.PILOT_MIN_WINES and enough >= config.PILOT_MIN_SOURCES
        sc = {"checked": False, "pause": False} if is_final else shortlist_check(sub, n_boot=n_boot, seed=seed + c)
        log.append({"check at": c, "units checked": len(bc), "units firing": int(bc["fires"].sum()), "sources with enough wines": enough,
                    "decision point": is_final, "shortlist checked": sc["checked"], "shortlist pause": sc["pause"]})
        if is_final:
            final_at = c
            break
        if sc["pause"]:
            paused_at = c
            break
    end = final_at or paused_at or (checks[-1] if checks else n)
    used = d.iloc[:end]
    status = status_from(withdrawn, pooled)
    hit = band_hidden(used, status)
    g400 = gate(d.iloc[:min(n, config.PILOT_MIN_WINES)], n_boot=n_boot, seed=seed)
    g = gate(used, n_boot=n_boot, seed=seed) if final_at else g400
    comp = comparator_check(used) if final_at else {}
    if paused_at is not None:
        dec = PAUSED
    elif final_at is not None:
        dec = decision({**g, "BO1 passes": g["BO1 passes"] and comp.get("BO1 holds", True)}, status["withdrawn everywhere"])
    elif n >= config.PILOT_MAX_WINES:
        dec = STOPPED.format(s=config.PILOT_MIN_SOURCES, w=config.PILOT_STOP_MIN_WINES, m=config.PILOT_MAX_WINES)
    elif n < config.PILOT_MIN_WINES:
        dec = f"interim: fewer than the pre-registered {config.PILOT_MIN_WINES} wines, no decision"
    else:
        dec = (f"interim: fewer than {config.PILOT_MIN_SOURCES} note sources have {config.PILOT_STOP_MIN_WINES}+ scored wines; "
               f"keep collecting scores (at most {config.PILOT_MAX_WINES}), no decision")
    n_src = counted_sources(used["source"])
    # The comparator rule and the joint gate are read only at the decision point; before it (interim, paused, or stopped
    # at the cap) both are None, so an interim gate file can't say "BO1 PASS" for a shortlist the rule would block
    # (critic round 6 issue 4).
    bo1 = bool(g["BO1 passes"] and comp.get("BO1 holds", True)) if final_at is not None else None
    return {"gate": {**g, "BO1 passes (after comparator rule)": bo1}, "gate at 400 wines": g400,
            "joint gate passes": (bo1 and g["BO2 passes"]) if final_at is not None else None, "decision": dec,
            "final": final_at is not None or paused_at is not None or n >= config.PILOT_MAX_WINES, "decision at": final_at,
            "wines used": end, "band withdrawn": withdrawn, "status": status, "band withdrawn everywhere": status["withdrawn everywhere"],
            "share of wines with band withdrawn": float(hit.mean()), "band withdrawn rows": hit, "shortlist paused at": paused_at,
            "checks": pd.DataFrame(log), "sources with enough wines": int((n_src >= config.PILOT_STOP_MIN_WINES).sum()),
            "meets source minimum": bool((n_src >= config.PILOT_STOP_MIN_WINES).sum() >= config.PILOT_MIN_SOURCES),
            "source intercept": source_intercept(used), "comparator": comp}


def comparator_check(used: pd.DataFrame, n_boot: int = config.PILOT_N_BOOT, seed: int = config.SEED) -> dict:
    """The BO1 comparator's coverage (Phase 6 critic round 4 issue 1). The strongest simple rule, "winery track record",
    knows only wineries in the training data; an unknown winery gets the overall mean, which weakens the comparator and
    makes the lift easier to reach. Pre-registered: if fewer than ``PILOT_MIN_WINERY_COVERAGE`` of the wines used at the
    decision point have a training winery, the shortlist part of the gate must ALSO pass on those matched wines alone
    (at least ``PILOT_CHECK_EVERY`` of them), else the shortlist is not deployed. Without a ``winery seen`` column
    (simulated pools, all from training-era data) the check does not apply."""
    if "winery seen" not in used:
        return {}
    seen = used["winery seen"].astype(bool)
    cov = float(seen.mean()) if len(used) else float("nan")
    matched = gate(used[seen], n_boot=n_boot, seed=seed) if seen.sum() >= config.PILOT_CHECK_EVERY else None
    degraded = bool(cov < config.PILOT_MIN_WINERY_COVERAGE)
    return {"winery coverage": cov, "comparator degraded": degraded, "matched-winery gate": matched,
            "BO1 holds": (not degraded) or bool(matched and matched["BO1 passes"])}


def as_pilot_table(rows: pd.DataFrame, country: pd.Series, source_col: str = "critic") -> pd.DataFrame:
    """A ``phase5.pilot_rows`` table in pilot format: ``source`` from the writer column, ``country`` joined by index."""
    return canonical_names(rows.assign(source=rows[source_col].fillna("unknown"), country=country.reindex(rows.index).fillna("Unknown")))


def simulate_protocol(rows: pd.DataFrame, n: int = config.PILOT_MAX_WINES, n_sims: int = 200, n_boot: int = config.PILOT_N_BOOT,
                      seed: int = config.SEED) -> dict:
    """Simulated pilots: up to ``n`` wines drawn from ``rows`` (pilot format) in random arrival order, the full protocol
    run on each (it stops at its decision point, a pause, or ``PILOT_MAX_WINES``). Returns the share of pilots in which
    each event happens. The gate columns are on the first 400 wines, comparable with Phase 5; the deploy columns follow
    the protocol's decision."""
    rng = np.random.default_rng([seed, 13])
    m = min(n, len(rows))
    # A wine "needs" the band withdrawn if its note source's or its country's mean residual in the WHOLE pool is beyond
    # ±PILOT_STOP_RESIDUAL (the level error the stop rule is meant to catch).
    resid = rows["sel"] - rows["points"]
    lim = config.PILOT_STOP_RESIDUAL
    offset = (resid.groupby(rows["source"]).transform("mean").abs() > lim) | (resid.groupby(rows["country"]).transform("mean").abs() > lim)
    res = []
    for i in range(n_sims):
        idx = rng.choice(len(rows), size=m, replace=False)
        d = rows.iloc[idx].assign(order=np.arange(1, m + 1))
        r = run_protocol(d, n_boot=n_boot, seed=seed + i)
        hit, off = r["band withdrawn rows"], offset.loc[r["band withdrawn rows"].index]
        g4 = r["gate at 400 wines"]
        res.append({"BO2 passes (first 400)": g4["BO2 passes"], "BO1 passes (first 400)": g4["BO1 passes"],
                    "joint passes (first 400)": g4["BO1 passes"] and g4["BO2 passes"],
                    "decision point reached": r["decision at"] is not None, "wines at decision": r["decision at"],
                    "band withdrawn somewhere": bool(r["band withdrawn"]), "band withdrawn everywhere": r["band withdrawn everywhere"],
                    "share of wines with band withdrawn": r["share of wines with band withdrawn"],
                    "band hidden: wines in an offset unit": float(hit[off].mean()) if off.any() else np.nan,
                    "band hidden: other wines": float(hit[~off].mean()) if (~off).any() else np.nan,
                    "shortlist paused": r["shortlist paused at"] is not None,
                    "stopped without enough sources": r["decision"].startswith("stopped"),
                    "deploy shortlist": r["decision"].startswith("deploy shortlist"),
                    "show band": r["decision"].startswith("deploy shortlist and show"),
                    "sources with enough wines": r["sources with enough wines"]})
    t = pd.DataFrame(res)
    out = {"wines drawn": m, "simulations": n_sims, "wines in an offset unit (pool share)": float(offset.mean()),
           **{k: float(t[k].mean()) for k in t.columns if k not in ("sources with enough wines", "wines at decision")}}
    out["median wines at decision"] = float(t["wines at decision"].median()) if t["wines at decision"].notna().any() else np.nan
    out["median sources with enough wines"] = float(t["sources with enough wines"].median())
    return out


def _wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    p = k / n
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return float(c - h), float(c + h)


def pause_rates(rows: pd.DataFrame, sizes=(100, 200, 300), n_sims: int = 1000, n_boot: int = config.PILOT_N_BOOT,
                seed: int = config.SEED) -> pd.DataFrame:
    """How often a single interim shortlist check would pause, per number of scored wines, for two candidate triggers:
    the lift point estimate below 1.0 (futility) and its 90% LB below 1.0. With a 95% Wilson interval for the first."""
    rng = np.random.default_rng([seed, 14])
    out = []
    for n in sizes:
        m = min(n, len(rows))
        pt, lb = [], []
        for i in range(n_sims):
            g = gate(rows.iloc[rng.choice(len(rows), size=m, replace=False)], n_boot=n_boot, seed=seed + i)
            pt.append(g["top-20% lift"] < config.PILOT_PAUSE_LIFT); lb.append(g["top-20% lift LB"] < config.PILOT_PAUSE_LIFT)
        lo, hi = _wilson(int(np.sum(pt)), n_sims)
        out.append({"wines": m, "simulations": n_sims, "pause if lift < 1.0": float(np.mean(pt)), "95% CI low": lo, "95% CI high": hi,
                    "pause if lift LB < 1.0": float(np.mean(lb))})
    return pd.DataFrame(out)


def choose_pause_min_wines(rates: dict[str, pd.DataFrame], max_rate: float = config.PILOT_PAUSE_MAX_FALSE) -> int | None:
    """Pre-stated rule (set on development folds only): the smallest interim size at which the futility trigger pauses
    at most ``max_rate`` of simulated pilots in EVERY development pool (where the shortlist works)."""
    t = pd.concat(rates, names=["pool"]).reset_index(level=0)
    ok = t.groupby("wines")["pause if lift < 1.0"].max()
    ok = ok[ok <= max_rate]
    return int(ok.index.min()) if len(ok) else None


# ---------- real pilot data (deployment/pilot_eval.py) ----------
def from_raw(df: pd.DataFrame, vf) -> pd.DataFrame:
    """Raw pilot rows (scoring inputs + ``points``, ``source``, ``order``) -> pilot format, scored with the deployed
    ``ValueFinder``. Only ≤ $25 wines with a critic score are kept (the pilot is on ≤ $25 notes)."""
    d = vf.prepare(df)
    d = d[d["in_value_pool"] & d["points"].notna()]
    t = pd.DataFrame({"points": d["points"].astype(float), "sel": vf.estimate(d), "base": vf.baseline(d), "rank": vf.rank_score(d),
                      "winery_key": d["winery_key"].where(d["winery_key"].ne(""), d.index.astype(str)),
                      "source": d["source"].fillna("unknown").astype(str), "country": d["country"], "order": d["order"]}, index=d.index)
    t["source (as given)"] = t["source"]
    t.loc[name_key(t["source"]).set_axis(t.index).isin(UNSOURCED), "source"] = "unknown"   # one unit for every missing source
    wineries = set((getattr(vf, "categories", None) or {}).get("winery", {}).get("spellings", ()))
    if wineries:
        t["winery"] = d["winery"]
        t["winery seen"] = d["winery"].isin(wineries)
    for k, v in vf.rule_scores(d).items():
        t[f"rule: {k}"] = v
    t["scorer"] = d["scorer"].astype(object) if "scorer" in d else config.PILOT_PRIMARY_SCORER
    if "sampled" in d:
        from .monitoring import _flag
        t["sampled"] = _flag(d["sampled"], "sampled")       # one strict parser for every yes/no column (critic round 6 issue 5)
    return canonical_names(t)


def _gate_or_none(d: pd.DataFrame, n_boot: int, seed: int) -> dict | None:
    """The gate on a sensitivity subset, or None below ``PILOT_CHECK_EVERY`` wines (too few to read)."""
    return gate(d, n_boot=n_boot, seed=seed) if len(d) >= config.PILOT_CHECK_EVERY else None


def _no_primary(t_all: pd.DataFrame) -> dict:
    """``evaluate_raw`` when no row is from the primary scorer: nothing to judge (critic round 4 issue 6)."""
    gate = {"wines": 0, "final": False, "decision": f"no scores from {config.PILOT_PRIMARY_SCORER}: nothing to judge",
            "wines received": 0, "wines from other scorers (sensitivity only)": len(t_all),
            "primary scorer": config.PILOT_PRIMARY_SCORER, "price deflator": config.PRICE_DEFLATOR}
    empty = pd.DataFrame(columns=["unit", "name", "withdrawn at check"])
    return {"gate": gate, "checks": pd.DataFrame(), "withdrawn": empty, "intercept": pd.DataFrame(), "status": status_from({}, set()),
            "table": t_all.iloc[:0], "band withdrawn rows": pd.Series(dtype=bool), "sources": source_list(t_all.iloc[:0]),
            "sensitivity": {"all scorers": _gate_or_none(t_all, config.PILOT_N_BOOT, config.SEED), "per scorer": None,
                            "unsampled wines": None, "unsampled wines used": None}}


def evaluate_raw(df: pd.DataFrame, vf, n_boot: int = config.PILOT_N_BOOT, seed: int = config.SEED) -> dict:
    """The protocol on real pilot rows (``run_protocol``): the gate (final at the decision point, after a pause, or at
    ``PILOT_MAX_WINES``; interim before that), every check, the withdrawn units, the band status file content and the
    secondary source-intercept table.

    Only scores from ``config.PILOT_PRIMARY_SCORER`` enter the protocol (without a ``scorer`` column every score is taken
    to be one; a blank ``scorer`` is not). Sensitivities, reported only: the gate on all scorers, the mean residual per
    scorer, and, with a ``sampled`` column (the team sampled or listed the wine), the gate on the unsampled wines up to the
    decision point. Rows without a note source stay in every gate and stop-rule unit but never count as a source."""
    t_all = from_raw(df, vf)
    primary = (is_primary_scorer(t_all["scorer"].fillna("").astype(str)) if "scorer" in t_all
               else pd.Series(True, index=t_all.index))
    t = t_all[primary]
    if t.empty:
        return _no_primary(t_all)
    r = run_protocol(t, n_boot=n_boot, seed=seed)
    used = t.sort_values("order").iloc[:r["wines used"]]
    res = (t_all["sel"] - t_all["points"])
    window = t_all[t_all["order"] <= used["order"].max()]          # every scorer, over the same arrival window
    comp = r["comparator"] or (comparator_check(used, n_boot, seed) if "winery seen" in used else {})
    sens = {"all scorers": _gate_or_none(window, n_boot, seed), "all scorers: wines": len(window),
            "matched-winery wines": comp.get("matched-winery gate"),
            "per scorer": (pd.DataFrame({"scorer": t_all.get("scorer", pd.Series(config.PILOT_PRIMARY_SCORER, index=t_all.index)).fillna("(none)"), "r": res})
                           .groupby("scorer")["r"].agg(wines="size", **{"mean residual": "mean"}).reset_index()),
            "unsampled wines": (_gate_or_none(used[~used["sampled"]], n_boot, seed) if "sampled" in used else None),
            "unsampled wines used": int((~used["sampled"]).sum()) if "sampled" in used else None}
    w = pd.DataFrame([{"unit": k[0], "name": k[1], "withdrawn at check": v} for k, v in r["band withdrawn"].items()],
                     columns=["unit", "name", "withdrawn at check"])
    gate = {**r["gate"], "joint gate passes": r["joint gate passes"], "final": r["final"], "decision": r["decision"],
            "decision at": r["decision at"], "wines used": r["wines used"], "wines received": len(t),
            "shortlist paused at": r["shortlist paused at"], "band withdrawn everywhere": r["band withdrawn everywhere"],
            "share of wines with band withdrawn": r["share of wines with band withdrawn"],
            "sources with enough wines": r["sources with enough wines"], "meets the source minimum": r["meets source minimum"],
            "primary scorer": config.PILOT_PRIMARY_SCORER, "wines from other scorers (sensitivity only)": int((~primary).sum()),
            "wines without a note source": int(name_key(t["source"]).isin(UNSOURCED).sum()),
            "price deflator": config.PRICE_DEFLATOR,
            "winery coverage (BO1 comparator)": comp.get("winery coverage"),
            "comparator degraded": comp.get("comparator degraded"),
            "minimum winery coverage": config.PILOT_MIN_WINERY_COVERAGE}
    return {"gate": gate, "checks": r["checks"], "withdrawn": w, "intercept": r["source intercept"], "status": r["status"],
            "table": t, "band withdrawn rows": r["band withdrawn rows"], "sources": source_list(t), "sensitivity": sens}
