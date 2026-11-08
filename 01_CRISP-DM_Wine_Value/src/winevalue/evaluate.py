"""Phase 4 outer-fold runs and metrics (development data only; Phase 5 reuses the same functions on the lockbox).

``run_fold`` fits every pre-registered candidate on one outer split and returns predictions; ``score_table`` and
``shortlist_table`` turn them into the DM1 / BSC2 and DM2 / BSC1 metrics with winery-clustered lower bounds.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import config
from .cv import inner_groups, inner_splits, oof_predict, outer_split
from .metrics import cluster_bootstrap, mae, within
from .models import GroupMeanBaseline, mask_evaluative, mask_terms
from .rules import SIMPLE_RULES, simple_rule_scores
from .scoring import ORIGIN, fit_calibration, fit_stack, inner_calibrated_mae, probability_map, ridge_fit_predict, top_coef_terms, tune_ridge
from .text_audit import strict_price_mask
from .value import cluster_bootstrap_lift, simulate_cycles

BASELINE = "variety × country"
CAL_ALL, CAL_NAMED = "calibrated ridge (all OOF)", "calibrated ridge (named OOF)"
STACK_NO_ORIGIN = "stack, no origin"
SCORE_CANDIDATES = ("ridge", CAL_ALL, CAL_NAMED, "stack", STACK_NO_ORIGIN)
MASKS = {
    "frozen list": lambda s, terms: mask_evaluative(s),
    "round-1 list": lambda s, terms: mask_terms(s, config.EVALUATIVE_TERMS_V1),
    "frozen list + strict price mask": lambda s, terms: mask_evaluative(strict_price_mask(s)),
    "top 200 ridge words": lambda s, terms: mask_terms(s, terms),     # stress test, reported only (critic round 1 #14)
}


def score_candidates(train: pd.DataFrame, test: pd.DataFrame, groups: pd.Series, alpha: float, which=SCORE_CANDIDATES) -> dict:
    """Fit DM1 candidates. Returns predictions on ``test``, inner critic-held-out MAE per inner fold, and fit details."""
    fp = ridge_fit_predict(alpha)
    oof, score = oof_predict(train, groups, fp), fp(train, test)
    y = train["points"].astype(float)
    named = train["fold"] >= 0
    cal = {CAL_ALL: fit_calibration(oof, y), CAL_NAMED: fit_calibration(oof, y, named)}
    preds = {"ridge": score}
    inner = {"ridge": {g: mae(iv["points"], oof.loc[iv.index]) for g, _, iv in
                       ((g, a, b[b["fold"] >= 0]) for g, a, b in inner_splits(train, groups))}}
    for name, (a, b) in cal.items():
        preds[name] = a + b * score
        inner[name] = inner_calibrated_mae(train, groups, oof, named_only=name == CAL_NAMED)
    info = {"calibration": cal, "oof": oof}
    for name, exclude in (("stack", ()), (STACK_NO_ORIGIN, ORIGIN)):
        if name in which:
            preds[name], info[name] = fit_stack(train, test, groups, alpha, exclude=exclude, oof=oof, test_score=score)
            inner[name] = info[name]["inner"]
    return {"preds": {k: v for k, v in preds.items() if k in which}, "inner": {k: v for k, v in inner.items() if k in which}, "info": info}


def run_fold(prep: pd.DataFrame, fold: int, anon_drop: dict, top_fold: pd.Series, masks: bool = True) -> dict:
    """All Phase 4 candidates on one outer fold. Returns predictions on the test rows and fitting info."""
    train, test = outer_split(prep, fold, anon_drop)
    groups = inner_groups(train, top_fold=top_fold)
    out = {"fold": fold, "train": train, "test": test, "info": {}}
    alpha, tab = tune_ridge(train, groups)
    alpha_p, tab_p = tune_ridge(train, groups, with_price=True)
    out["info"].update({"ridge alpha": alpha, "ridge tuning": tab, "ranker ridge alpha": alpha_p, "ranker ridge tuning": tab_p})
    base = score_candidates(train, test, groups, alpha)
    preds = {"global mean": np.full(len(test), train["points"].mean()),
             BASELINE: GroupMeanBaseline().fit(train, train["points"]).predict(test), **base["preds"]}
    out["inner"] = pd.DataFrame(base["inner"]).assign(fold=fold)
    out["info"].update(base["info"])
    if masks:
        terms = top_coef_terms(train, alpha)
        out["info"]["top terms"] = terms
        for name, m in MASKS.items():
            tr_m, te_m = train.assign(note=m(train["note"], terms)), test.assign(note=m(test["note"], terms))
            r = score_candidates(tr_m, te_m, groups, alpha, which=("ridge", config.SELECTED_DM1, "stack"))
            preds.update({f"{k}, masked ({name})": v for k, v in r["preds"].items()})
    out["score_preds"] = pd.DataFrame(preds, index=test.index)
    rank_fp = ridge_fit_predict(alpha_p, with_price=True)
    rank = {"ridge + log price": rank_fp(train, test)}
    oof, score = base["info"]["oof"], base["preds"]["ridge"]
    rank["stack P(90+) + log price"], out["info"]["rank stack"] = fit_stack(train, test, groups, alpha, task="binary", with_price=True, oof=oof, test_score=score)
    rank["stack P(90+) + log price + winery record"], out["info"]["rank stack winery"] = fit_stack(
        train, test, groups, alpha, task="binary", with_price=True, with_winery=True, oof=oof, test_score=score)
    out["rank_scores"] = pd.DataFrame(rank, index=test.index)
    out["app_maps"] = app_mappings(train, test, groups, rank_fp, rank["ridge + log price"], base)
    return out


def app_mappings(train, test, groups, rank_fp, rank_score, base) -> dict:
    """The BSC4 outputs, fixed before Phase 5. P(90+): logistic map of the selected ranker's out-of-fold score, fitted on
    all <= $25 training rows. Score band: selected score +/- the SCORE_BAND_COVERAGE quantile of the absolute out-of-fold
    error on named training rows (critic-held-out, so it reflects a new writer). Both are checked on the held-out fold."""
    named = train["fold"] >= 0
    oof_rank = oof_predict(train, groups, rank_fp)
    pool = train["in_value_pool"]
    pm = probability_map(oof_rank[pool], (train.loc[pool, "points"] >= config.VALUE_MIN_POINTS))
    te_pool = test["in_value_pool"].to_numpy()
    prob = pm.predict_proba(np.asarray(rank_score)[te_pool].reshape(-1, 1))[:, 1]
    yv = (test["points"].to_numpy()[te_pool] >= config.VALUE_MIN_POINTS).astype(float)
    a, b = base["info"]["calibration"][CAL_ALL]
    cal_oof = a + b * base["info"]["oof"]
    sel = a + b * base["preds"]["ridge"]
    half = float(np.quantile(np.abs(train.loc[named, "points"].astype(float) - cal_oof[named]), config.SCORE_BAND_COVERAGE))
    return {"P(90+)": prob, "is value": yv, "Brier": float(((prob - yv) ** 2).mean()), "Brier base rate": float(((yv.mean() - yv) ** 2).mean()),
            "mean P(90+)": float(prob.mean()), "value rate": float(yv.mean()), "band half-width": half,
            "band coverage": float((np.abs(test["points"].to_numpy(float) - sel) <= half).mean())}


def score_table(run: dict, seed: int = config.SEED) -> pd.DataFrame:
    """DM1 / DM1b / BSC2 metrics per model for one fold."""
    te, P = run["test"], run["score_preds"]
    y = te["points"].to_numpy(dtype=float)
    win = te["winery_key"].to_numpy()
    cand = te["in_value_pool"].to_numpy()
    c_idx = np.flatnonzero(cand)
    base = P[BASELINE].to_numpy()
    rows = []
    for name in P.columns:
        p = P[name].to_numpy()
        row = {"fold": run["fold"], "model": name, "MAE": mae(y, p), "bias (pred − actual)": float(np.mean(p - y)),
               "within ±2 (≤$25)": within(y[cand], p[cand])}
        if name not in (BASELINE, "global mean"):
            red = cluster_bootstrap(lambda i: 1 - mae(y[i], p[i]) / mae(y[i], base[i]), win, n_boot=config.N_BOOT, seed=seed)
            gain = cluster_bootstrap(lambda i: within(y[c_idx][i], p[c_idx][i]) - within(y[c_idx][i], base[c_idx][i]),
                                     win[c_idx], n_boot=config.N_BOOT, seed=seed)
            row.update({"MAE reduction": red["estimate"], "MAE reduction LB": red["lower_bound"],
                        "within gain (pp)": 100 * gain["estimate"], "within gain LB (pp)": 100 * gain["lower_bound"]})
        rows.append(row)
    return pd.DataFrame(rows)


def shortlist_table(run: dict, seed: int = config.SEED) -> tuple[pd.DataFrame, pd.DataFrame]:
    """DM2 / BSC1 metrics for one fold: simulated P@k for every rule and ranker, and lifts vs the best simple rule."""
    tr, te = run["train"], run["test"]
    pool = te[te["in_value_pool"]]
    is_val = (pool["points"] >= config.VALUE_MIN_POINTS).to_numpy()
    scores = simple_rule_scores(tr, pool)
    scores["text score (no price)"] = run["score_preds"].loc[pool.index, "ridge"].to_numpy()
    for c in run["rank_scores"].columns:
        scores[c] = run["rank_scores"].loc[pool.index, c].to_numpy()
    f = run["fold"]
    sims = []
    for n in (500, config.CANDIDATES_PER_CYCLE, 2000):
        for k in (50, config.SHORTLIST_K, 200):
            r = simulate_cycles(scores, is_val, n_candidates=n, k=k, n_cycles=config.N_SIM_CYCLES, seed=config.SEED + f)
            sims.append({"fold": f, "candidates": n, "k": k, **r.mean().to_dict()})
    sims = pd.DataFrame(sims)
    main = sims[(sims.candidates == config.CANDIDATES_PER_CYCLE) & (sims.k == config.SHORTLIST_K)].iloc[0]
    best = max(SIMPLE_RULES, key=lambda r: main[r])
    rows = []
    for name in run["rank_scores"].columns:
        lift = cluster_bootstrap_lift(scores[name], scores[best], is_val, pool["winery_key"], frac=0.1,
                                      n_boot=config.N_BOOT, seed=seed)
        rows.append({"fold": f, "ranker": name, "pool": len(pool), "value base rate": is_val.mean(),
                     "best simple rule": best, "best simple P@100": main[best], "P@100": main[name],
                     "lift (cycles)": main[name] / main[best], "top-10% lift": lift["lift"], "top-10% lift LB": lift["lower_bound"]})
    return pd.DataFrame(rows), sims


def per_critic_table(run: dict, model: str) -> pd.DataFrame:
    """MAE reduction against the baseline, per critic in the held-out fold (critics with at least 30 test rows)."""
    te, P = run["test"], run["score_preds"]
    rows = []
    for c, d in te.groupby("critic"):
        if len(d) >= 30:
            y, p, b = d["points"].to_numpy(float), P.loc[d.index, model].to_numpy(), P.loc[d.index, BASELINE].to_numpy()
            rows.append({"fold": run["fold"], "critic": c, "rows": len(d), "baseline MAE": mae(y, b), "MAE": mae(y, p),
                         "MAE reduction": 1 - mae(y, p) / mae(y, b), "bias": float(np.mean(p - y))})
    return pd.DataFrame(rows)


def shortlist_mix(run: dict, ranker: str = "ridge + log price", frac: float = 0.1) -> tuple[pd.DataFrame, dict]:
    """Who writes the wines at the top of the ranked pool, and P@100 if each critic's mean pool score were known (oracle).
    A constant writer offset can't change the order inside a one-writer pool, but it can in a mixed one."""
    pool = run["test"][run["test"]["in_value_pool"]]
    s = run["rank_scores"].loc[pool.index, ranker]
    top = pool.loc[s.sort_values(ascending=False, kind="stable").index[:int(round(frac * len(pool)))]]
    t = pd.DataFrame({"pool share": pool["critic"].value_counts(normalize=True), "top 10% share": top["critic"].value_counts(normalize=True),
                      "value rate": (pool["points"] >= config.VALUE_MIN_POINTS).groupby(pool["critic"]).mean()}).fillna(0)
    t = t.assign(fold=run["fold"]).reset_index(names="critic").sort_values("pool share", ascending=False)
    is_val = (pool["points"] >= config.VALUE_MIN_POINTS).to_numpy()
    centred = s - s.groupby(pool["critic"]).transform("mean") + pool.groupby("critic")["points"].transform("mean") - pool["points"].mean()
    r = simulate_cycles({"as run": s.to_numpy(), "oracle critic level": centred.to_numpy()}, is_val, n_candidates=config.CANDIDATES_PER_CYCLE,
                        k=config.SHORTLIST_K, n_cycles=config.N_SIM_CYCLES, seed=config.SEED + run["fold"]).mean().to_dict()
    return t, {"fold": run["fold"], "value base rate": float(is_val.mean()), **r}


def ablation(prep: pd.DataFrame, fold: int, attribution: pd.DataFrame, anon_drop: dict, top_fold: pd.Series, alpha: float,
             control_seeds=(0, 1, 2)) -> pd.DataFrame:
    """What the per-fold R8 filter does, measured properly, on one outer fold. Variants of the training set:
    design (p > 0.5 dropped); no filter; all top-guess notes dropped (the CV analogue of the Phase 5 sensitivity); and a
    matched control that drops as many anonymous notes NOT attributed to the fold, matched on province. The control
    separates the style leak from plain data loss. Each variant refits its baseline and calibration."""
    from .cv import development
    from .splits import drop_titles_seen_in_training
    dev = development(prep)
    held = dev[dev["fold"] == fold]
    pool_tr = dev[dev["fold"] != fold]
    dropped = anon_drop[fold]
    is_top = top_fold.reindex(dev.index).eq(fold)
    variants = {"per-fold R8 (design)": pool_tr[~pool_tr.index.isin(dropped)], "no filter": pool_tr,
                "all top-guess notes dropped": pool_tr[~pool_tr.index.isin(is_top.index[is_top])],
                "named folds only": pool_tr[pool_tr["fold"] >= 0]}
    others = pool_tr[pool_tr["fold"].eq(-1) & ~is_top.reindex(pool_tr.index)]
    need = dev.loc[dropped.intersection(dev.index), "province_model"].value_counts()
    for s in control_seeds:
        rng = np.random.default_rng([config.SEED, fold, s])
        take = []
        for prov, n in need.items():
            c = others.index[others["province_model"].eq(prov)].to_numpy()
            take.append(rng.choice(c, size=min(n, len(c)), replace=False))
        variants[f"matched control {s}"] = pool_tr[~pool_tr.index.isin(np.concatenate(take))]
    rows = []
    for name, tr in variants.items():
        te = drop_titles_seen_in_training(held, tr)
        groups = inner_groups(tr, top_fold=top_fold)
        fp = ridge_fit_predict(alpha)
        oof, score = oof_predict(tr, groups, fp), fp(tr, te)
        a, b = fit_calibration(oof, tr["points"].astype(float))
        vc = GroupMeanBaseline().fit(tr, tr["points"]).predict(te)
        y = te["points"].to_numpy(float)
        for model, p in (("ridge", score), ("calibrated ridge", a + b * score)):
            rows.append({"fold": fold, "training set": name, "model": model, "train rows": len(tr), "test rows": len(te), "baseline MAE": mae(y, vc),
                         "MAE": mae(y, p), "MAE reduction": 1 - mae(y, p) / mae(y, vc), "bias": float(np.mean(p - y))})
    return pd.DataFrame(rows)


def meets_dm1(t: pd.DataFrame) -> pd.Series:
    """Per (model, fold): DM1 and BSC2 targets (development analogue of the Phase 5 test)."""
    return ((t["MAE reduction"] >= config.TARGET_MAE_REDUCTION) & (t["MAE reduction LB"] > config.TARGET_MAE_REDUCTION_LOWER)
            & (t["within ±2 (≤$25)"] >= config.TARGET_WITHIN_TOL) & (t["within gain (pp)"] >= 100 * config.TARGET_WITHIN_GAIN_PP)
            & (t["within gain LB (pp)"] > 0))


def meets_bsc1(t: pd.DataFrame) -> pd.Series:
    return ((t["P@100"] >= config.TARGET_PRECISION_FLOOR) & (t["lift (cycles)"] >= config.TARGET_PRECISION_LIFT)
            & (t["top-10% lift LB"] >= config.TARGET_LIFT_LOWER))


def select(table: pd.DataFrame, name_col: str, metric: str, meets: pd.Series, higher_is_better: bool,
           tol: float = 0.01) -> tuple[str, pd.DataFrame]:
    """Rule of 2026-11-04: among candidates meeting the targets in EVERY fold, the best mean ``metric``; within
    ``tol`` of the best, the simplest (``config.SIMPLICITY_ORDER``) wins. Returns (choice, summary). DM2 still uses it;
    DM1 uses ``select_inner`` since revision 2."""
    t = table.assign(meets=meets.to_numpy())
    s = t.groupby(name_col).agg(mean=(metric, "mean"), folds_meeting=("meets", "sum"), folds=("meets", "size"))
    s["eligible"] = s["folds_meeting"] == s["folds"]
    e = s[s["eligible"]]
    if e.empty:
        return None, s
    best = e["mean"].max() if higher_is_better else e["mean"].min()
    close = e[(e["mean"] >= best - tol) if higher_is_better else (e["mean"] <= best + tol)]
    order = {m: i for i, m in enumerate(config.SIMPLICITY_ORDER)}
    choice = min(close.index, key=lambda m: order.get(m, len(order)))
    return choice, s


def select_inner(inner: pd.DataFrame, outer: pd.DataFrame, meets: pd.Series, tol: float = 0.01) -> tuple[str, pd.DataFrame]:
    """DM1 rule of revision 2 (config): lowest mean inner critic-held-out MAE, within ``tol`` the simplest; the winner must
    then meet the targets in every outer fold, else the next candidate is taken. ``inner``: one row per (fold, inner fold),
    one column per candidate. ``outer``: score_table rows with a ``model`` column."""
    means = inner.drop(columns="fold").groupby(inner["fold"]).mean().mean().sort_values()
    met = outer.assign(meets=meets.to_numpy()).groupby("model")["meets"].sum()
    order = {m: i for i, m in enumerate(config.SIMPLICITY_ORDER)}
    table = pd.DataFrame({"mean inner MAE": means, "outer folds meeting targets": met.reindex(means.index)})
    remaining = list(means.index)
    while remaining:
        best = means[remaining].min()
        choice = min((m for m in remaining if means[m] <= best + tol), key=lambda m: order.get(m, len(order)))
        if table.loc[choice, "outer folds meeting targets"] == len(config.OUTER_FOLDS):
            return choice, table
        remaining.remove(choice)
    return None, table
