"""Phase 4 DM6 (critic calibration) and the development half of the BSC5 hypotheses H1-H6.

DM6 is ``critic_fixed_effects``: the section 1.3 model, score ~ wine attributes + critic, on all named development rows with
one common baseline. ``critic_effects`` is the separate pre-registered H4 statistic, not a critic-calibration estimate.

The hypothesis functions take an EVALUATION frame (rows scored by one critic set) with two training-derived columns added by
``add_training_columns``: ``vxc_expect`` (variety x country expectation fitted on that row's training data) and
``winery_track`` (shrunk winery mean, shrink = 20, on that row's training data). Phase 5 calls the same functions on
the lockbox with all development data as training. Uncertainty: one-sided 90% winery-cluster bootstrap (as Phase 1).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from . import config
from .metrics import cluster_bootstrap
from .models import GroupMeanBaseline


def add_training_columns(test: pd.DataFrame, train: pd.DataFrame) -> pd.DataFrame:
    out = test.copy()
    out["vxc_expect"] = GroupMeanBaseline().fit(train, train["points"]).predict(test)
    out["winery_track"] = GroupMeanBaseline(keys=("winery",), shrink=20).fit(train, train["points"]).predict(test)
    return out


def _boot(stat, df, n_boot=config.N_BOOT, seed=config.SEED):
    return cluster_bootstrap(stat, df["winery_key"].to_numpy(), n_boot=n_boot, seed=seed)


def critic_effects(df: pd.DataFrame, n_boot: int = config.N_BOOT, seed: int = config.SEED) -> pd.DataFrame:
    """DM6: per critic, mean of (score − training-fitted variety × country expectation), 95% winery-bootstrap CI."""
    rows = []
    for c, d in df[df["critic"].notna()].groupby("critic"):
        r = (d["points"] - d["vxc_expect"]).to_numpy()
        codes, uniq = pd.factorize(d["winery_key"])
        members = [np.flatnonzero(codes == i) for i in range(len(uniq))]
        rng = np.random.default_rng([seed, len(d)])
        draws = [r[np.concatenate([members[i] for i in rng.integers(0, len(members), len(members))])].mean() for _ in range(n_boot)]
        rows.append({"critic": c, "reviews": len(d), "effect": r.mean(), "CI 2.5%": np.quantile(draws, 0.025),
                     "CI 97.5%": np.quantile(draws, 0.975)})
    return pd.DataFrame(rows).sort_values("effect").reset_index(drop=True)


def _connected(critic: pd.Series, cell: pd.Series) -> pd.Series:
    """Rows in the largest connected component of the critic-cell graph (only those rows compare critics with each other)."""
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import connected_components
    c, cu = pd.factorize(critic); w, wu = pd.factorize(cell)
    n = len(cu) + len(wu)
    g = coo_matrix((np.ones(len(c)), (c, w + len(cu))), shape=(n, n))
    _, lab = connected_components(g, directed=False)
    return pd.Series(lab[c], index=critic.index) == np.bincount(lab[c]).argmax()


def critic_fixed_effects(df: pd.DataFrame, cell_keys=("variety", "country"), covariates=(), level: float = 0.95) -> pd.DataFrame:
    """DM6 (section 1.3): points = wine-cell fixed effect + covariates + critic fixed effect, OLS within cells, winery-clustered SEs.

    Only cells reviewed by at least two critics compare critics, so other rows are dropped, as are rows outside the largest
    connected critic-cell component. Effects are centred on the review-weighted mean of the critics identified.
    ``df``: named rows. Returns one row per identified critic, with the rows and partner critics that identify it.
    """
    import statsmodels.api as sm
    from scipy.stats import norm
    d = df[df["critic"].notna()].copy()
    d["cell"] = d[list(cell_keys)].fillna("NA").astype(str).agg(" | ".join, axis=1)
    for _ in range(3):                                   # dropping rows can create new single-critic cells
        d = d[d.groupby("cell")["critic"].transform("nunique") >= 2]
        d = d[_connected(d["critic"], d["cell"])]
    crit = sorted(d["critic"].unique())
    D = pd.get_dummies(d["critic"]).astype(float)[crit[1:]]
    for c in covariates:
        D[c] = d[c].astype(float)
    y = d["points"].astype(float)
    dm = lambda x: x - x.groupby(d["cell"]).transform("mean")
    fit = sm.OLS(dm(y).to_numpy(), D.apply(dm).to_numpy()).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(d["winery_key"])[0]})
    n = d["critic"].value_counts().reindex(crit).to_numpy(dtype=float)
    w = n / n.sum()
    k = len(crit) - 1
    beta = np.r_[0.0, fit.params[:k]]
    L = np.vstack([np.zeros(k), np.eye(k)]) - np.tile(w[1:], (k + 1, 1))   # beta (reference = 0) -> centred effects
    V = np.asarray(fit.cov_params())[:k, :k]
    se = np.sqrt(np.clip(np.diag(L @ V @ L.T), 0, None))
    z = norm.ppf(0.5 + level / 2)
    eff = beta - (w * beta).sum()
    cells = d.groupby("critic")["cell"].agg(set)
    partners = {c: sum(bool(cells[c] & cells[o]) for o in crit if o != c) for c in crit}
    out = pd.DataFrame({"critic": crit, "identifying reviews": n.astype(int), "partner critics": [partners[c] for c in crit],
                        "effect": eff, "SE": se, "CI low": eff - z * se, "CI high": eff + z * se})
    out.attrs.update({"rows": len(d), "cells": d["cell"].nunique(), "residual SD": float(np.sqrt(fit.scale)),
                      "SD across critics": float(eff.std(ddof=1)),
                      "SD noise-corrected": float(np.sqrt(max(eff.var(ddof=1) - np.mean(se ** 2), 0)))})
    return out.sort_values("effect").reset_index(drop=True)


def _within_group_demean(x: pd.Series, keys: list[pd.Series]) -> pd.Series:
    return x - x.groupby(keys).transform("mean")


def hypothesis_tests(df: pd.DataFrame, n_boot: int = config.N_BOOT, seed: int = config.SEED, which=None) -> pd.DataFrame:
    """H1-H6 on one evaluation frame (named critics only). 'replicates' = stated direction AND condition met."""
    d = df[df["critic"].notna()].reset_index(drop=True)
    keys = lambda x: [x["variety"].fillna("NA"), x["country"].fillna("NA")]

    def h1(i):
        s = d.iloc[i]; return spearmanr(s["n_words"], s["points"]).statistic

    priced = d[d["price"].notna()].reset_index(drop=True)

    def h2(i):
        s = priced.iloc[i]
        a = _within_group_demean(np.log(s["price"]), keys(s)); b = _within_group_demean(s["points"].astype(float), keys(s))
        return float(np.corrcoef(a, b)[0, 1])

    def h3(i):
        s = d.iloc[i]; r = _within_group_demean(s["points"].astype(float), keys(s))
        return r[s["has_designation"].to_numpy()].mean() - r[~s["has_designation"].to_numpy()].mean()

    def h4(i):
        s = d.iloc[i]
        return (s["points"] - s["vxc_expect"]).groupby(s["critic"]).mean().std(ddof=1)

    pool = d[d["in_value_pool"]].reset_index(drop=True)
    pool_val = pool["points"] >= config.VALUE_MIN_POINTS
    wr = pool[pool["colour"].isin(["white", "red"])].reset_index(drop=True)

    def h5(i):
        s = wr.iloc[i]; v = s["points"] >= config.VALUE_MIN_POINTS
        return v[s["colour"].eq("white").to_numpy()].mean() - v[s["colour"].eq("red").to_numpy()].mean()

    def h6(i):
        s = pool.iloc[i]; v = s["points"] >= config.VALUE_MIN_POINTS; strong = (s["winery_track"] >= 89).to_numpy()
        return v[strong].mean() - v[~strong].mean()

    specs = [("H1", h1, d, 0.0), ("H2", h2, priced, 0.0), ("H3", h3, d, 0.0), ("H4", h4, d, 0.5),
             ("H5", h5, wr, 0.0), ("H6", h6, pool, 0.0)]
    rows = []
    for h, stat, frame, bar in specs:
        if which is not None and h not in which:
            continue
        b = _boot(stat, frame, n_boot, seed)
        rows.append({"hypothesis": h, "statement": config.HYPOTHESES[h], "rows": len(frame), "estimate": b["estimate"],
                     "90% LB": b["lower_bound"], "bar": bar,
                     "replicates": bool(b["estimate"] > bar and b["lower_bound"] > bar)})
    out = pd.DataFrame(rows)
    out.attrs["pool value rate"] = float(pool_val.mean())
    return out
