"""Phase 6 (CRISP-DM 6.1 / 6.2) measurements for notebook §6: the pilot protocol simulations, the masked ranker scores
(Phase 5 critic round 3 issue 8), the value-verdict tiers, the BSC4 timing and the monitoring reference values.

Protocol parameters are SET on development folds only; lockbox rows are reported for information.
"""

from __future__ import annotations

import time

import numpy as np
import pandas as pd

from . import config, phase5, pilot, production

MASKED = f"{config.SELECTED_DM1}, masked (frozen list)"


def pilot_tables(dev_runs: dict, lb_run: dict) -> tuple[dict, dict]:
    """Pilot-format tables (unmasked and masked) for each development fold and the lockbox; masked tables use the masked
    score model and the masked ranker refit (``phase5.masked_ranker``)."""
    plain, masked = {}, {}
    for name, run in [*((f"development fold {f}", r) for f, r in dev_runs.items()), ("lockbox, mixed writers", lb_run)]:
        country = run["test"]["country"]
        plain[name] = pilot.as_pilot_table(phase5.pilot_rows(run), country)
        masked[name] = pilot.as_pilot_table(phase5.pilot_rows(run, MASKED, rank=phase5.masked_ranker(run)), country)
    return plain, masked


def masked_ranker_scores(dev_runs: dict, lb_run: dict) -> pd.DataFrame:
    """Saved so the masked BO1 rows of Phase 5 can be recomputed from files (critic round 3 issue 8)."""
    parts = [pd.DataFrame({"fold": f, "ridge + log price, masked (frozen list)": phase5.masked_ranker(r)}) for f, r in dev_runs.items()]
    parts.append(pd.DataFrame({"fold": config.LOCKBOX_FOLD, "ridge + log price, masked (frozen list)": phase5.masked_ranker(lb_run)}))
    return pd.concat(parts).rename_axis("review_id").reset_index()


def pause_table(plain: dict, masked: dict, n_sims: int = 1000, n_boot: int = config.PILOT_N_BOOT) -> pd.DataFrame:
    """Single-look pause rates per interim size. Development and lockbox pools (false pauses: the shortlist works there),
    plus DETECTION pools where it fails: each development pool with the ranker replaced by random noise ("null ranker"),
    and the lockbox's Jenssen-only pool (the one writer whose shortlist failed in Phase 5). Detection pools are named
    "check: ..." so the pause-size rule (``chosen_pause_min``) never sees them."""
    rows = {**plain, **{f"{k}, masked": v for k, v in masked.items()}}
    rng = np.random.default_rng([config.SEED, 19])
    for k, v in plain.items():
        if k.startswith("development"):
            rows[f"check: null ranker, {k}"] = v.assign(rank=rng.random(len(v)))
    lb = plain["lockbox, mixed writers"]
    rows["check: lockbox, Jeff Jenssen only"] = lb[lb["source"].eq("Jeff Jenssen")]
    return pd.concat({k: pilot.pause_rates(v, n_sims=n_sims, n_boot=n_boot) for k, v in rows.items()}, names=["pool"]).reset_index(level=0)


def chosen_pause_min(pauses: pd.DataFrame) -> int | None:
    """``pilot.choose_pause_min_wines`` on the development pools only (unmasked and masked)."""
    dev = pauses[pauses["pool"].str.startswith("development")]
    return pilot.choose_pause_min_wines({k: g.drop(columns="pool") for k, g in dev.groupby("pool")})


def protocol_table(plain: dict, masked: dict, n_sims: int = 200, n_boot: int = config.PILOT_N_BOOT) -> pd.DataFrame:
    rows = {**plain, **{f"{k}, masked": v for k, v in masked.items()}}
    return pd.DataFrame({k: pilot.simulate_protocol(v, n_sims=n_sims, n_boot=n_boot) for k, v in rows.items()}).T


def seed_spread(plain: dict, masked: dict, seeds=(1, 2, 3), n_sims: int = 200, n_boot: int = config.PILOT_N_BOOT) -> pd.DataFrame:
    """Phase 6 critic round 1 issue 6: how much the gate's simulated pass rates (first 400 wines, as in Phase 5's
    ``pilot_pass_rate``) move between random seeds alone."""
    rows = {**plain, **{f"{k}, masked": v for k, v in masked.items()}}
    out = []
    for k, v in rows.items():
        for sd in seeds:
            r = phase5.pilot_pass_rate(v, n_sims=n_sims, n_boot=n_boot, seed=sd)
            out.append({"pool": k, "seed": sd, "BO2 pass rate": r["BO2 pass rate"], "BO1 pass rate": r["BO1 pass rate"]})
    return pd.DataFrame(out)


def withdrawn_units(rows: pd.DataFrame, n_sims: int = 100, n_boot: int = config.PILOT_N_BOOT, seed: int = config.SEED) -> pd.Series:
    """Which units the band stop rule withdraws, as a share of simulated pilots (full protocol, up to PILOT_MAX_WINES)."""
    rng = np.random.default_rng([seed, 15])
    hits = []
    for i in range(n_sims):
        d = rows.iloc[rng.choice(len(rows), size=min(config.PILOT_MAX_WINES, len(rows)), replace=False)]
        d = d.assign(order=np.arange(1, len(d) + 1))
        hits += [f"{k[0]}: {k[1]}" for k in pilot.run_protocol(d, n_boot=n_boot, seed=seed + i)["band withdrawn"]]
    return (pd.Series(hits, dtype=object).value_counts() / n_sims).rename("share of pilots")


def tier_table(vf, plain: dict, masked: dict) -> pd.DataFrame:
    """Phase 6 critic round 1 issue 4: share of ≤ $25 candidates above the development 90th / 80th percentile of the
    ranker's out-of-fold scores, and the value rate in each band, per pool. The cut-offs are fixed; the shares are not."""
    rows = {**plain, "lockbox, mixed writers, masked": masked["lockbox, mixed writers"]}
    out = []
    for k, d in rows.items():
        share = 1 - np.searchsorted(vf.pool_rank_oof, d["rank"].to_numpy(float), side="right") / len(vf.pool_rank_oof)
        v = (d["points"] >= config.VALUE_MIN_POINTS).to_numpy()
        top10, top20 = share < 0.10, (share >= 0.10) & (share < 0.20)
        out.append({"pool": k, "wines": len(d), "value rate": v.mean(), "share above dev. P90": top10.mean(),
                    "share above dev. P80": (share < 0.20).mean(), "value rate above P90": v[top10].mean(),
                    "value rate P80-P90": v[top20].mean(), "value rate below P80": v[share >= 0.20].mean()})
    return pd.DataFrame(out)


def unit_truth(rows: pd.DataFrame, min_rows: int = 150) -> pd.DataFrame:
    """Each source's and country's true mean residual and within-±2 gain in the whole pool (what the rule should catch)."""
    g = rows.assign(resid=rows["sel"] - rows["points"],
                    win=(np.abs(rows["points"] - rows["sel"]) <= 2).astype(float) - (np.abs(rows["points"] - rows["base"]) <= 2))
    out = []
    for kind in ("source", "country"):
        t = g.groupby(kind).agg(wines=("resid", "size"), **{"mean residual": ("resid", "mean"), "±2 gain (pp)": ("win", "mean")})
        t["±2 gain (pp)"] *= 100
        out.append(t[t["wines"] >= min_rows].assign(unit=kind).reset_index(names="name"))
    return pd.concat(out, ignore_index=True)[["unit", "name", "wines", "mean residual", "±2 gain (pp)"]]


def verdict_table(vf, dev_runs: dict, lb_run: dict) -> pd.DataFrame:
    """Value rate by value-verdict tier: development outer folds (new-writer estimates) and the lockbox, ≤ $25 rows."""
    out = []
    for name, run in [*((f"development fold {f}", r) for f, r in dev_runs.items()), ("lockbox", lb_run)]:
        te = run["test"][run["test"]["in_value_pool"]]
        est = run["score_preds"].loc[te.index, config.SELECTED_DM1].to_numpy()
        v = pd.Series([vf.verdict(e, p).split(":")[0] for e, p in zip(est, te["price"].to_numpy(float))], index=te.index)
        t = pd.DataFrame({"verdict": v, "value": te["points"] >= config.VALUE_MIN_POINTS}).groupby("verdict")["value"].agg(["size", "mean"])
        out.append(t.rename(columns={"size": "wines", "mean": "value rate"}).assign(rows=name).reset_index())
    return pd.concat(out, ignore_index=True)[["rows", "verdict", "wines", "value rate"]]


def lockbox_pilot_standin(prep: pd.DataFrame, lb_index: pd.Index, n: int = config.PILOT_MIN_WINES, seed: int = config.SEED) -> pd.DataFrame:
    """A dry-run pilot file in the real pilot format: ``n`` ≤ $25 lockbox wines (raw inputs, critic score, critic as the
    note source, random arrival order). Lockbox rows were already scored in Phase 5; this tests the tooling only."""
    lb = prep.loc[lb_index]
    lb = lb[lb["in_value_pool"]]
    rng = np.random.default_rng([seed, 16])
    pick = lb.iloc[rng.choice(len(lb), size=n, replace=False)]
    cols = ["description", "country", "province", "variety", "region_1", "designation", "winery", "title", "price", "points"]
    return pick[cols].assign(source=pick["critic"], order=np.arange(1, n + 1)).rename_axis("wine_id").reset_index()


def timing(vf, sim, notes: pd.DataFrame, n: int = 50, seed: int = config.SEED) -> pd.Series:
    """BSC4: seconds per one-wine query (score + 5 similar wines), on ``n`` random rows of ``notes`` (raw inputs)."""
    rng = np.random.default_rng([seed, 17])
    rows = notes.iloc[rng.choice(len(notes), size=n, replace=False)]
    secs = []
    for _, r in rows.iterrows():
        t0 = time.perf_counter()
        d = vf.prepare(r.to_frame().T.reset_index(drop=True))
        vf.score(d, prepared=True)
        sim.query(d["note"].iloc[0], colour=d["colour"].iloc[0])
        secs.append(time.perf_counter() - t0)
    s = pd.Series(secs)
    return pd.Series({"queries": n, "median s": s.median(), "95th percentile s": s.quantile(0.95), "max s": s.max(),
                      "share under 3 s": float((s < 3).mean())})


def monitoring_reference(vf, frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Reference values for the input-drift checks of the monitoring plan (§6.2), per set of prepared rows
    (``monitoring.indicators``, the same code that checks each buying round)."""
    from . import monitoring
    return pd.DataFrame({name: monitoring.indicators(monitoring.row_values(vf, d)) for name, d in frames.items()}).T


def _lag_cdf(t: float, median: float, p90_ratio: float = config.PILOT_LAG_P90_RATIO) -> float:
    """A10: share of a round's eventual reviews published within ``t`` months (log-normal; 90th percentile = ratio × median)."""
    from scipy.stats import lognorm
    return float(lognorm.cdf(t, s=np.log(p90_ratio) / 1.2816, scale=median)) if t > 0 else 0.0


def expected_share(month: float, median: float, cap: int = config.PILOT_CAP_MONTHS) -> float:
    """S(T): expected scored wines by month T after round 1, per unit of (candidates per round × yield). One round a
    month (A9) at months 0, 1, ..., cap − 1."""
    return sum(_lag_cdf(month - r, median) for r in range(min(int(month) + 1, cap)))


def pilot_timeline(yields=(0.05, 0.10, 0.20), lag_medians=(2, 3, 6), per_round: int = config.PILOT_ROUND_CANDIDATES,
                   need: int = config.PILOT_MIN_WINES, cap: int = config.PILOT_CAP_MONTHS,
                   check_month: int = config.PILOT_FALLBACK_MONTH) -> pd.DataFrame:
    """Phase 6 critic round 2 issue 2: when 400 scored wines arrive, under the review yield (A8) and lag (A10), and whether
    that is before the cap. Also the fallback rule's projection factor S(cap)/S(check_month): at month 6 the analyst
    multiplies the scored wines so far by it; a projection below 400 triggers the panel fallback. The source minimum
    (A11) is not modelled here: it is checked on round 1's candidates."""
    rows = []
    for y in yields:
        for m in lag_medians:
            n = {T: per_round * y * expected_share(T, m, cap) for T in range(1, cap + 1)}
            hit = next((T for T, v in n.items() if v >= need), None)
            rows.append({"review yield (A8)": y, "median lag, months (A10)": m, f"scored by month {check_month}": n[check_month],
                         f"scored by month {cap}": n[cap], "month 400 reached": hit, "before the cap": hit is not None,
                         "fallback projection factor": expected_share(cap, m, cap) / expected_share(check_month, m, cap)})
    return pd.DataFrame(rows)


def source_minimum_probability(shares=(0.125, 0.15, 0.175, 0.20), sizes=(400, 500, 600), n_sources: int = config.PILOT_MIN_SOURCES,
                               min_wines: int = config.PILOT_STOP_MIN_WINES) -> pd.DataFrame:
    """Phase 6 critic round 3 issue 4: the chance that 3 note sources, each supplying exactly ``share`` of the scored
    wines (the rest from sources that never reach the minimum), all have ≥ ``min_wines`` by ``size`` scored wines, i.e.
    the decision point's source condition at the A11 floor. Exact multinomial sum (no simulation noise)."""
    from scipy.stats import binom
    assert n_sources == 3, "exact sum written for three sources"
    rows = []
    for s in shares:
        for n in sizes:
            x1 = np.arange(min_wines, n + 1)
            p1 = binom.pmf(x1, n, s)
            tot = 0.0
            for a, pa in zip(x1, p1):
                rest = n - a
                q = s / (1 - s)                       # source 2 given source 1's count
                x2 = np.arange(min_wines, rest + 1)
                if not len(x2):
                    continue
                p2 = binom.pmf(x2, rest, q)
                r3 = s / (1 - 2 * s)                  # source 3 given sources 1 and 2
                p3 = binom.sf(min_wines - 1, rest - x2, r3)
                tot += pa * float((p2 * p3).sum())
            rows.append({"share per source (A11 floor)": s, "scored wines": n, "P(all sources ≥ 50)": tot})
    return pd.DataFrame(rows)


def choose_source_share(probs: pd.DataFrame, need: int = config.PILOT_MIN_WINES, target: float = config.PILOT_SOURCE_SHARE_POWER) -> float:
    """Pre-stated rule: the A11 floor is the smallest share at which the source condition holds by ``need`` scored wines
    with probability ≥ ``target``."""
    t = probs[(probs["scored wines"] == need) & (probs["P(all sources ≥ 50)"] >= target)]
    return float(t["share per source (A11 floor)"].min())
