"""Phase 5 (CRISP-DM 5.1): the single lockbox evaluation of the models frozen in Phase 4 (commit ``config.PHASE4_COMMIT``).

``evaluate(train, test, ...)`` computes every pre-registered target and sensitivity for one (training, test) pair. It is
the SAME code for the dress rehearsal (an outer development fold, which must reproduce Phase 4's numbers) and for the
lockbox (training = all development rows, test = the lockbox minus titles seen in training, R-3). ``lockbox_split`` is
the only function that reads lockbox rows, and it refuses while ``config.LOCKBOX_UNSEALED`` is False.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import config
from . import evaluate as ev
from .cv import development, inner_groups, oof_predict
from .descriptors import item_matrix, mine_rules, rule_stats_on
from .insights import add_training_columns, critic_fixed_effects, hypothesis_tests
from .metrics import cluster_bootstrap, mae, within
from .rules import SIMPLE_RULES, simple_rule_scores
from .scoring import fit_calibration, ridge_fit_predict
from .splits import drop_titles_seen_in_training
from .value import cluster_bootstrap_lift


def lockbox_split(prep: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Training = all development rows; test = the lockbox minus titles seen in training (R-3)."""
    if not config.LOCKBOX_UNSEALED:
        raise PermissionError("The lockbox is sealed (config.LOCKBOX_UNSEALED is False).")
    dev = development(prep)
    return dev, drop_titles_seen_in_training(prep[prep["is_lockbox"]], dev)


def subset_run(run: dict, mask: pd.Series) -> dict:
    """A run restricted to test rows where ``mask`` is True (training unchanged)."""
    idx = run["test"].index[mask.reindex(run["test"].index).fillna(False).to_numpy(dtype=bool)]
    return {**run, "test": run["test"].loc[idx], "score_preds": run["score_preds"].loc[idx], "rank_scores": run["rank_scores"].loc[idx]}


def subset_metrics(run: dict, best_rule: str, n_boot: int = config.N_BOOT, seed: int = config.SEED) -> dict:
    """DM1 / BSC2 and top-10% shortlist metrics on any test subset (no cycle simulation, so small pools work)."""
    te, P = run["test"], run["score_preds"]
    y, sel, base = te["points"].to_numpy(float), P[config.SELECTED_DM1].to_numpy(), P[ev.BASELINE].to_numpy()
    red = cluster_bootstrap(lambda i: 1 - mae(y[i], sel[i]) / mae(y[i], base[i]), te["winery_key"].to_numpy(), n_boot=n_boot, seed=seed)
    pool = te[te["in_value_pool"]]
    out = {"rows": len(te), "MAE": mae(y, sel), "bias": float(np.mean(sel - y)), "MAE reduction": red["estimate"], "MAE reduction LB": red["lower_bound"],
           "pool": len(pool)}
    if len(pool) >= 30:
        cand = te["in_value_pool"].to_numpy()
        out.update({"within ±2 (≤$25)": within(y[cand], sel[cand]), "within gain (pp)": 100 * (within(y[cand], sel[cand]) - within(y[cand], base[cand]))})
        is_val = (pool["points"] >= config.VALUE_MIN_POINTS).to_numpy()
        rules = simple_rule_scores(run["train"], pool)
        rk = run["rank_scores"].loc[pool.index, config.SELECTED_DM2].to_numpy()
        k = max(1, int(round(0.1 * len(pool))))
        top = lambda s: float(is_val[np.argsort(-np.asarray(s), kind="stable")[:k]].mean())
        try:                                    # undefined when the rule's top 10% holds no value wine (small pools)
            lift = cluster_bootstrap_lift(rk, rules[best_rule], is_val, pool["winery_key"], frac=0.1, n_boot=n_boot, seed=seed)
        except ZeroDivisionError:
            lift = {"lift": np.nan, "lower_bound": np.nan}
        out.update({"value base rate": float(is_val.mean()), "ranker top-10% precision": top(rk), "rule top-10% precision": top(rules[best_rule]),
                    "top-10% lift": lift["lift"], "top-10% lift LB": lift["lower_bound"]})
    return out


def without_length(run: dict, top_fold: pd.Series) -> dict:
    """Exploratory sensitivity: the selected calibrated ridge refit without note length (``n_words``)."""
    tr, te = run["train"], run["test"]
    groups = inner_groups(tr, top_fold=top_fold)
    fp = ridge_fit_predict(run["info"]["ridge alpha"], exclude=("n_words",))
    oof, score = oof_predict(tr, groups, fp), fp(tr, te)
    a, b = fit_calibration(oof, tr["points"].astype(float))
    y, p, base = te["points"].to_numpy(float), a + b * score, run["score_preds"][ev.BASELINE].to_numpy()
    return {"MAE": mae(y, p), "MAE reduction": 1 - mae(y, p) / mae(y, base), "bias": float(np.mean(p - y))}


def targets(score: pd.DataFrame, short: pd.DataFrame) -> pd.DataFrame:
    """Pass / fail for the measured targets: DM1, DM1b, BSC2 (selected DM1 model) and BSC1 (selected ranker)."""
    s = score.set_index("model")
    m = s.loc[config.SELECTED_DM1]
    masked = s.loc[f"{config.SELECTED_DM1}, masked (frozen list)", "MAE"] - m["MAE"] if f"{config.SELECTED_DM1}, masked (frozen list)" in s.index else np.nan
    r = short.set_index("ranker").loc[config.SELECTED_DM2]
    rows = [
        ("DM1", "MAE reduction vs variety × country ≥ 10%, LB > 5%", f"{m['MAE reduction']:.1%} (LB {m['MAE reduction LB']:.1%})",
         m["MAE reduction"] >= config.TARGET_MAE_REDUCTION and m["MAE reduction LB"] > config.TARGET_MAE_REDUCTION_LOWER),
        ("DM1b", "masked MAE increase ≤ 0.15", "not run" if np.isnan(masked) else f"{masked:+.3f}",
         None if np.isnan(masked) else bool(masked <= config.TARGET_MASKED_MAE_INCREASE)),
        ("BSC2", "within ±2 ≥ 0.60, gain ≥ +5 pp, gain LB > 0", f"{m['within ±2 (≤$25)']:.3f}, {m['within gain (pp)']:+.1f} pp (LB {m['within gain LB (pp)']:+.1f})",
         m["within ±2 (≤$25)"] >= config.TARGET_WITHIN_TOL and m["within gain (pp)"] >= 100 * config.TARGET_WITHIN_GAIN_PP and m["within gain LB (pp)"] > 0),
        ("BSC1", "P@100 ≥ 0.55, ≥ 1.4× best simple rule, top-10% lift LB ≥ 1.2", f"{r['P@100']:.3f}, {r['lift (cycles)']:.2f}× ({r['best simple rule']}), LB {r['top-10% lift LB']:.2f}",
         r["P@100"] >= config.TARGET_PRECISION_FLOOR and r["lift (cycles)"] >= config.TARGET_PRECISION_LIFT and r["top-10% lift LB"] >= config.TARGET_LIFT_LOWER),
    ]
    return pd.DataFrame(rows, columns=["criterion", "target", "result", "passes"])


def evaluate(train: pd.DataFrame, test: pd.DataFrame, top_fold: pd.Series, label: int, sensitivity_ids=(), masks: bool = True,
             dm3_assign=None, dm4_rules: pd.DataFrame | None = None, dm4_grapes=None, run: dict | None = None) -> dict:
    """Every Phase 5 measurement on one (training, test) pair. ``sensitivity_ids``: anonymous notes dropped in the
    pre-registered sensitivity refit. ``dm3_assign``: profile assignment fitted on development notes. ``run``: an already
    computed ``run_split`` result for the same pair (saves a refit)."""
    run = ev.run_split(train, test, top_fold, label, masks) if run is None else run
    score = ev.score_table(run)
    short, sims = ev.shortlist_table(run)
    best = short.set_index("ranker").loc[config.SELECTED_DM2, "best simple rule"]
    out = {"run": run, "score": score, "short": short, "sims": sims, "targets": targets(score, short), "best rule": best,
           "app": {k: v for k, v in run["app_maps"].items() if not isinstance(v, np.ndarray)}}
    te = run["test"]
    # per critic: selected vs plain ridge, and top-10% shortlist precision in each critic's own pool
    by = ev.per_critic_table(run, "ridge").merge(ev.per_critic_table(run, config.SELECTED_DM1), on=["fold", "critic", "rows"], suffixes=(" ridge", " calibrated"))
    out["by critic"] = by
    out["critic pools"] = pd.DataFrame({c: subset_metrics(subset_run(run, te["critic"].eq(c)), best) for c in te["critic"].dropna().unique()}).T
    big = te["critic"].value_counts().index[0]
    out["subsets"] = pd.DataFrame({"all": subset_metrics(run, best), f"without {big}": subset_metrics(subset_run(run, te["critic"].ne(big)), best),
                                   "Italy": subset_metrics(subset_run(run, te["country"].eq("Italy")), best),
                                   "not Italy": subset_metrics(subset_run(run, te["country"].ne("Italy")), best)}).T
    out["mix"] = ev.shortlist_mix(run, config.SELECTED_DM2)
    out["without length"] = without_length(run, top_fold)
    if len(sensitivity_ids):
        tr2 = train[~train.index.isin(sensitivity_ids)]
        r2 = ev.run_split(tr2, drop_titles_seen_in_training(test, tr2), top_fold, label, masks=False)
        s2, (sh2, _) = ev.score_table(r2), ev.shortlist_table(r2)
        out["sensitivity ids"] = {"dropped": int(train.index.isin(sensitivity_ids).sum()), "score": s2, "short": sh2, "targets": targets(s2, sh2)}
    # DM4: development rules re-measured on the test rows (text and grape only)
    if dm4_rules is not None:
        lifts = rule_stats_on(item_matrix(te, dm4_grapes), dm4_rules)
        out["dm4"] = dm4_rules.join(lifts, rsuffix=" (test)")
    # BSC3 shares on the test notes, from the development-fitted primary profile model
    if dm3_assign is not None:
        lab = dm3_assign(te)
        out["dm3 shares"] = lab[lab >= 0].value_counts(normalize=True).sort_index()
        out["dm3 unassigned"] = float((lab < 0).mean())
    # H1-H6 on the test rows, scored with this training data; DM6 with the test critics added
    out["hypotheses"] = hypothesis_tests(add_training_columns(te, train))
    both = pd.concat([train[train["critic"].notna()], te[te["critic"].notna()]])
    out["dm6"] = critic_fixed_effects(both)
    return out


def read_naming(path) -> pd.DataFrame:
    """Parse a BSC3 reviewer file (markdown table: Profile | Name | Confidence | Reasoning)."""
    rows = [l.strip().strip("|").split("|") for l in open(path, encoding="utf-8") if l.startswith("| ") and not l.startswith("| Profile")]
    t = pd.DataFrame([[c.strip() for c in r[:3]] for r in rows if len(r) >= 3], columns=["profile", "name", "confidence"])
    t["confidence"] = pd.to_numeric(t["confidence"], errors="coerce")
    t["named"] = (t["confidence"] >= config.BSC3_MIN_CONFIDENCE) & ~t["name"].str.lower().str.contains("cannot name")
    return t


def business_summary(res: dict, hyp_dev: pd.DataFrame, naming: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """BSC1-BSC5 and DM4 pass / fail on the test rows (BSC4 is the Phase 6 demo; its P(90+) and band are reported)."""
    t = res["targets"].copy()
    shares = res["dm3 shares"]
    k = len(shares)
    prim = {r: n[n["profile"].str.startswith("A")] for r, n in naming.items()}
    rates = {r: float(n["named"].mean()) for r, n in prim.items()}
    bsc3 = (6 <= k <= 15) and bool((shares >= config.DM3_MIN_SHARE).all()) and all(v >= config.BSC3_MIN_NAMED for v in rates.values())
    d = res["dm4"]
    kept = int((d["lift (test)"] >= config.DM4_LOCKBOX_MIN_LIFT).sum())
    h = hyp_dev[["hypothesis", "replicates"]].merge(res["hypotheses"][["hypothesis", "replicates"]], on="hypothesis", suffixes=(" dev", " test"))
    both = h["replicates dev"] & h["replicates test"]
    bsc5 = int(both.sum()) >= config.BSC5_MIN_REPLICATED and bool(both[h["hypothesis"].isin(["H5", "H6"])].any())
    extra = pd.DataFrame([
        ("BSC3", "6–15 profiles each ≥ 1% of test notes; each reviewer names ≥ 80% (confidence ≥ 3) on the primary set",
         f"{k} profiles, smallest {shares.min():.1%}; named " + ", ".join(f"{r} {v:.0%}" for r, v in rates.items()), bsc3),
        ("DM4", f"≥ {config.DM4_MIN_RULES} development rules keep lift ≥ {config.DM4_LOCKBOX_MIN_LIFT}", f"{kept} of {len(d)}", kept >= config.DM4_MIN_RULES),
        ("BSC5", "≥ 4 of H1–H6 replicate in both development and test, including H5 or H6",
         f"{int(both.sum())} of 6 ({', '.join(h.loc[both, 'hypothesis'])})", bsc5),
    ], columns=t.columns)
    return pd.concat([t, extra], ignore_index=True)


# ---------- post hoc (added after unsealing; descriptive, changes no model, rule or selection) ----------
def lockbox_predictions(res: dict) -> pd.DataFrame:
    """Row-level lockbox predictions of every model, with the columns needed to recompute any Phase 5 table."""
    run = res["run"]
    te = run["test"]
    keep = ["critic", "country", "colour", "grape", "price", "points", "in_value_pool", "winery_key", "title"]
    out = te[keep].join(run["score_preds"]).join(run["rank_scores"])
    out["P(90+)"] = np.nan
    out.loc[te.index[te["in_value_pool"].to_numpy()], "P(90+)"] = run["app_maps"]["P(90+)"]
    return out


def pilot_rows(run: dict, sel_col: str = config.SELECTED_DM1, rank: pd.Series | None = None) -> pd.DataFrame:
    """<= $25 test rows with what the pilot gate compares: selected score, baseline, ranker and every simple rule.
    ``rank`` replaces the selected ranker's scores (e.g. the masked refit from ``masked_ranker``)."""
    te = run["test"]
    pool = te[te["in_value_pool"]]
    rank = run["rank_scores"][config.SELECTED_DM2] if rank is None else rank
    d = pd.DataFrame({"points": pool["points"].astype(float), "sel": run["score_preds"].loc[pool.index, sel_col],
                      "base": run["score_preds"].loc[pool.index, ev.BASELINE],
                      "rank": rank.loc[pool.index],
                      "winery_key": pool["winery_key"], "critic": pool["critic"]}, index=pool.index)
    for k, v in simple_rule_scores(run["train"], pool).items():
        d[f"rule: {k}"] = v
    return d


def _top_precision(scores: np.ndarray, is_val: np.ndarray, frac: float, rng) -> np.ndarray:
    """Top-``frac`` precision for each row of a (n_scores, n) array, ties broken at random."""
    k = max(1, int(round(frac * scores.shape[1])))
    jitter = rng.random(scores.shape)
    order = np.lexsort((jitter, -scores), axis=1)[:, :k]
    return is_val[order].mean(axis=1)


def pilot_pass_rate(rows: pd.DataFrame, n: int = config.PILOT_MIN_WINES, n_sims: int = 200, n_boot: int = 200,
                    frac: float = 0.2, seed: int = config.SEED, bo1: bool = True) -> dict:
    """Simulated pilots: ``n`` wines drawn without replacement from ``rows`` (``pilot_rows``), scored with the
    pre-registered gate (``config.PILOT_*``). BO2: within-±2 gain over variety × country >= +5 pp with winery-clustered
    90% LB > 0. BO1: ranker top-20% precision >= 1.3x the best simple rule on that pilot, LB > 1.0. LBs from ``n_boot``
    winery-cluster resamples. Returns pass rates and mean point estimates."""
    rng = np.random.default_rng([seed, 5])
    rule_cols = [c for c in rows.columns if c.startswith("rule: ")]
    y, sel, base = (rows[c].to_numpy(float) for c in ("points", "sel", "base"))
    is_val = y >= config.VALUE_MIN_POINTS
    S = np.vstack([rows["rank"].to_numpy(float)] + [rows[c].to_numpy(float) for c in rule_cols])
    d_win = (np.abs(y - sel) <= 2).astype(float) - (np.abs(y - base) <= 2).astype(float)
    codes_all = pd.factorize(rows["winery_key"])[0]
    m = min(n, len(rows))
    res = {"bo2": [], "bo1": [], "gain": [], "gain LB": [], "lift": [], "lift LB": []}
    for _ in range(n_sims):
        idx = rng.choice(len(rows), size=m, replace=False)
        codes = pd.factorize(codes_all[idx])[0]
        nc = codes.max() + 1
        cnt, sd = np.bincount(codes, minlength=nc), np.bincount(codes, weights=d_win[idx], minlength=nc)
        draws = rng.integers(0, nc, size=(n_boot, nc))
        boot_gain = sd[draws].sum(1) / cnt[draws].sum(1)
        gain, gain_lb = d_win[idx].mean(), np.quantile(boot_gain, 0.10)
        res["gain"].append(gain); res["gain LB"].append(gain_lb)
        res["bo2"].append(gain >= config.PILOT_WITHIN_GAIN_PP and gain_lb > 0)
        if bo1:
            v = is_val[idx]
            p = _top_precision(S[:, idx], v, frac, rng)
            best = 1 + int(np.argmax(p[1:]))
            lift = p[0] / p[best] if p[best] > 0 else np.inf
            members = [np.flatnonzero(codes == c) for c in range(nc)]
            lifts = []
            for b in range(n_boot):
                bi = np.concatenate([members[c] for c in draws[b]])
                pb = _top_precision(S[[0, best]][:, idx][:, bi], v[bi], frac, rng)
                lifts.append(pb[0] / pb[1] if pb[1] > 0 else np.inf)
            lift_lb = float(np.quantile(lifts, 0.10))
            res["lift"].append(lift); res["lift LB"].append(lift_lb)
            res["bo1"].append(lift >= config.PILOT_TOP20_LIFT and lift_lb > config.PILOT_TOP20_LIFT_LOWER)
    out = {"wines": m, "BO2 pass rate": float(np.mean(res["bo2"])), "mean gain (pp)": 100 * float(np.mean(res["gain"])),
           "mean gain LB (pp)": 100 * float(np.mean(res["gain LB"]))}
    if bo1:
        out.update({"BO1 pass rate": float(np.mean(res["bo1"])), "both pass rate": float(np.mean(np.array(res["bo1"]) & np.array(res["bo2"]))),
                    "median top-20% lift": float(np.median(res["lift"])), "median lift LB": float(np.median(res["lift LB"]))})
    return out


def gain_vs_offset(rows: pd.DataFrame, offsets=np.arange(-2.0, 2.01, 0.25)) -> pd.DataFrame:
    """Within-±2 gain over variety × country if every selected score were shifted by one constant offset (as a note source's shared level error would)."""
    y, sel, base = (rows[c].to_numpy(float) for c in ("points", "sel", "base"))
    wb = (np.abs(y - base) <= 2).mean()
    return pd.DataFrame({"offset": offsets, "mean residual": [float(np.mean(sel + o - y)) for o in offsets],
                         "within gain (pp)": [100 * ((np.abs(y - sel - o) <= 2).mean() - wb) for o in offsets]})


def masked_ranker(run: dict, mask_name: str = "frozen list") -> pd.Series:
    """The selected ranker (ridge + log price) refit on masked training notes and scored on masked test notes, exactly as
    the masked score models are built in ``evaluate.run_split`` (same alpha, same mask functions)."""
    tr, te = run["train"], run["test"]
    m, terms = ev.MASKS[mask_name], run["info"].get("top terms", ())
    fp = ridge_fit_predict(run["info"]["ranker ridge alpha"], with_price=True)
    return pd.Series(fp(tr.assign(note=m(tr["note"], terms)), te.assign(note=m(te["note"], terms))), index=te.index)


def stop_rule_rate(rows: pd.DataFrame, n: int = config.PILOT_STOP_MIN_WINES, n_sims: int = 200, n_boot: int = 200,
                   limit: float = config.PILOT_STOP_RESIDUAL, ci: float = config.PILOT_STOP_CI, seed: int = config.SEED) -> dict:
    """How often the score-band stop rule fires for a note source: ``n`` wines drawn from ``rows`` (``pilot_rows``), stop
    if the two-sided ``ci`` winery-bootstrap interval of the mean residual (selected - actual) lies wholly outside
    +/- ``limit``. Also returns the source's true mean residual and within-±2 gain, so firing can be compared with need."""
    rng = np.random.default_rng([seed, 7])
    y, sel, base = (rows[c].to_numpy(float) for c in ("points", "sel", "base"))
    r = sel - y
    codes_all = pd.factorize(rows["winery_key"])[0]
    m = min(n, len(rows))
    q = ((1 - ci) / 2, 1 - (1 - ci) / 2)
    fired, means = [], []
    for _ in range(n_sims):
        idx = rng.choice(len(rows), size=m, replace=False)
        codes = pd.factorize(codes_all[idx])[0]
        nc = codes.max() + 1
        cnt, sr = np.bincount(codes, minlength=nc), np.bincount(codes, weights=r[idx], minlength=nc)
        draws = rng.integers(0, nc, size=(n_boot, nc))
        lo, hi = np.quantile(sr[draws].sum(1) / cnt[draws].sum(1), q)
        fired.append(lo > limit or hi < -limit); means.append(r[idx].mean())
    gain = 100 * ((np.abs(r) <= 2).mean() - (np.abs(y - base) <= 2).mean())
    return {"wines per check": m, "rule fires": float(np.mean(fired)), "median mean residual": float(np.median(means)),
            "source mean residual": float(r.mean()), "source ±2 gain (pp)": float(gain)}


def within_group_diff(d: pd.DataFrame, group: str, flag: str, outcome: str, cluster: str = "winery_key",
                      n_boot: int = config.N_BOOT, seed: int = config.SEED) -> pd.DataFrame:
    """Per ``group``: mean ``outcome`` when ``flag`` is True minus when False, with a one-sided 90% cluster-bootstrap LB
    (resamples where one side is empty are dropped)."""
    out = []
    for g, x in d.groupby(group):
        f, v = x[flag].to_numpy(bool), x[outcome].to_numpy(float)

        def stat(i):
            a, b = f[i], ~f[i]
            return v[i][a].mean() - v[i][b].mean() if a.any() and b.any() else np.nan
        codes = pd.factorize(x[cluster])[0]
        members = [np.flatnonzero(codes == c) for c in range(codes.max() + 1)]
        rng = np.random.default_rng(seed)
        draws = [stat(np.concatenate([members[c] for c in rng.integers(0, len(members), len(members))])) for _ in range(n_boot)]
        out.append({group: g, "flagged": int(f.sum()), "others": int((~f).sum()), "difference": stat(np.arange(len(x))),
                    "90% LB": float(np.nanquantile(draws, 0.10))})
    return pd.DataFrame(out)
