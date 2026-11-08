"""Phase 4 models for DM1 (price-free score), DM1b (masked) and DM2 (ranker).

Candidates (``config`` Phase 4 block; history in reports/phase4_run_log.md):
- ``ridge``: TF-IDF on ``note`` + one-hot origin / grape / colour + numerics -> ridge; alpha tuned on inner folds.
- ``calibrated ridge``: a + b * ridge score, with (a, b) fitted by OLS on out-of-fold ridge scores. Out-of-fold scores are
  critic-held-out, so (a, b) carry the average gap between a new writer's scores and what other writers' notes predict.
- ``stack``: LightGBM on the out-of-fold ridge score plus structured inputs (with or without origin). Regressor for DM1,
  classifier P(90+) for DM2. The "ridge score" is the FULL ridge (text + structured inputs), not text alone.
- ranker variants add log price, and optionally the winery track record (known at decision time; the frozen simple
  rules use it too). The quality model never sees price, critic or winery (R-2).

All tuning is scored on NAMED inner validation rows, which are critic-held-out by construction.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression, Ridge

from . import config
from .cv import inner_splits, oof_predict
from .features import QUALITY_INPUTS_V2, RANKER_INPUTS_V2, build_preprocessor
from .metrics import mae
from .models import GroupMeanBaseline

STACK_CATS = ["country", "province_model", "grape", "colour"]
STACK_NUMS = ["vintage", "n_words", "is_nonvintage", "has_designation", "has_region_1", "label_differs"]
ORIGIN = ("country", "province_model")


def _pool_precision(iva: pd.DataFrame, p: np.ndarray, frac: float = 0.1) -> float:
    """Value precision in the top ``frac`` of the inner validation pool (named, <= $25) by score."""
    pool = iva["in_value_pool"].to_numpy()
    y = (iva["points"].to_numpy()[pool] >= config.VALUE_MIN_POINTS)
    s = np.asarray(p)[pool]
    k = max(1, int(round(frac * len(s))))
    return float(y[np.argsort(-s, kind="stable")[:k]].mean())


# ---------- ridge ----------
def tune_ridge(train: pd.DataFrame, groups: pd.Series, alphas=config.RIDGE_ALPHAS, with_price: bool = False,
               text_col: str = "note") -> tuple[float, pd.DataFrame]:
    """Inner critic-held-out score per alpha (named rows only). DM1 quality model: MAE. Ranker (``with_price``): value
    precision in the top 10% of the inner pool, because only the order within a pool matters. Returns (best alpha, table)."""
    inputs = (RANKER_INPUTS_V2 if with_price else QUALITY_INPUTS_V2)
    rows = []
    for g, itr, iva in inner_splits(train, groups):
        iva = iva[iva["fold"] >= 0]
        pre = build_preprocessor(with_price)
        Xtr, Xva = pre.fit_transform(_cols(itr, inputs, text_col)), pre.transform(_cols(iva, inputs, text_col))
        for a in alphas:
            p = Ridge(alpha=a).fit(Xtr, itr["points"]).predict(Xva)
            rows.append({"inner fold": g, "alpha": a, "score": _pool_precision(iva, p) if with_price else mae(iva["points"], p)})
    table = pd.DataFrame(rows).pivot(index="alpha", columns="inner fold", values="score")
    table["mean"] = table.mean(axis=1)
    return float(table["mean"].idxmax() if with_price else table["mean"].idxmin()), table


def _cols(df, inputs, text_col):
    cols = [text_col if c == "note" else c for c in inputs]
    out = df[cols]
    return out.rename(columns={text_col: "note"}) if text_col != "note" else out


def ridge_fit_predict(alpha: float, with_price: bool = False, text_col: str = "note"):
    inputs = RANKER_INPUTS_V2 if with_price else QUALITY_INPUTS_V2

    def fp(fit_rows: pd.DataFrame, pred_rows: pd.DataFrame) -> np.ndarray:
        pre = build_preprocessor(with_price)
        X = pre.fit_transform(_cols(fit_rows, inputs, text_col))
        m = Ridge(alpha=alpha).fit(X, fit_rows["points"])
        return m.predict(pre.transform(_cols(pred_rows, inputs, text_col)))
    return fp


def top_coef_terms(train: pd.DataFrame, alpha: float, n: int = 100) -> list[str]:
    """The ``n`` most positive and ``n`` most negative single-word TF-IDF coefficients of the ridge on ``train``."""
    pre = build_preprocessor(False)
    X = pre.fit_transform(train[QUALITY_INPUTS_V2])
    coef = pd.Series(Ridge(alpha=alpha).fit(X, train["points"]).coef_, index=pre.get_feature_names_out())
    words = coef[coef.index.str.startswith("text__") & ~coef.index.str.contains(" ")]
    words.index = words.index.str.replace("text__", "", regex=False)
    words = words[words.index.str.fullmatch(r"[a-z'-]{3,}")].sort_values()
    return list(words.index[:n]) + list(words.index[-n:])


# ---------- calibration ----------
def fit_calibration(oof: pd.Series, y: pd.Series, rows: pd.Series | None = None) -> tuple[float, float]:
    """OLS y = a + b * oof on ``rows`` (boolean mask; default all). Returns (a, b)."""
    o, t = (oof, y) if rows is None else (oof[rows], y[rows])
    b, a = np.polyfit(o.to_numpy(dtype=float), t.to_numpy(dtype=float), 1)
    return float(a), float(b)


def inner_calibrated_mae(train: pd.DataFrame, groups: pd.Series, oof: pd.Series, named_only: bool) -> dict:
    """Inner critic-held-out MAE of a calibrated score: for each inner fold, (a, b) from the OTHER folds' OOF rows,
    applied to that fold's named rows (R-3 as ``inner_splits``)."""
    out = {}
    for g, itr, iva in inner_splits(train, groups):
        iva = iva[iva["fold"] >= 0]
        fit = itr.index[itr["fold"] >= 0] if named_only else itr.index
        a, b = fit_calibration(oof.loc[fit], train.loc[fit, "points"].astype(float))
        out[g] = mae(iva["points"], a + b * oof.loc[iva.index])
    return out


def probability_map(score: pd.Series, y90: pd.Series) -> LogisticRegression:
    """P(90+) from a ranker score, by logistic calibration on out-of-fold scores."""
    return LogisticRegression(C=1e6, max_iter=1000).fit(score.to_numpy().reshape(-1, 1), y90.to_numpy().astype(int))


# ---------- stacked gradient boosting ----------
def _stack_frame(df: pd.DataFrame, ridge_score, cats_from: pd.DataFrame | None, extra: dict | None = None,
                 with_price: bool = False) -> pd.DataFrame:
    X = pd.DataFrame({"ridge_score": np.asarray(ridge_score, dtype=float)}, index=df.index)
    for c in STACK_CATS:
        cats = (cats_from if cats_from is not None else df)[c].astype("category").cat.categories
        X[c] = pd.Categorical(df[c], categories=cats)
    for c in STACK_NUMS:
        X[c] = df[c].astype(float)
    if with_price:
        X["log_price"] = np.log(df["price"].astype(float))
    for k, v in (extra or {}).items():
        X[k] = np.asarray(v, dtype=float)
    return X


def winery_track(fit_rows: pd.DataFrame, pred_rows: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """Shrunk winery mean score (as the frozen rule, shrink = 20) and the number of training reviews."""
    m = GroupMeanBaseline(keys=("winery_key",), shrink=20).fit(fit_rows, fit_rows["points"])
    n = pred_rows["winery_key"].map(fit_rows["winery_key"].value_counts()).fillna(0).to_numpy()
    return m.predict(pred_rows), n


def fit_stack(train: pd.DataFrame, test: pd.DataFrame, groups: pd.Series, alpha: float, task: str = "regression",
              with_price: bool = False, with_winery: bool = False, exclude=(), grid=config.LGBM_GRID,
              seed: int = config.SEED, oof: pd.Series | None = None, test_score: np.ndarray | None = None):
    """Fit the stack on ``train`` and predict ``test``. task: 'regression' (points) or 'binary' (points >= 90).

    ``oof`` / ``test_score``: precomputed price-free ridge scores (computed here if absent). ``exclude``: columns left out.
    Leaves and trees are chosen on a pooled inner curve (named validation rows: MAE, or log loss for 'binary').
    Returns (test predictions, info with the chosen point, the inner curve and the inner score per fold).
    """
    import lightgbm as lgb
    text_fp = ridge_fit_predict(alpha)                       # price-free ridge score, always
    tr_text = oof_predict(train, groups, text_fp) if oof is None else oof
    te_text = text_fp(train, test) if test_score is None else test_score
    extra_tr, extra_te = {}, {}
    if with_winery:
        tr_w, tr_n = pd.Series(np.nan, index=train.index), pd.Series(np.nan, index=train.index)
        for g in sorted(groups.unique()):
            m = groups == g
            w, n = winery_track(train[~m], train[m]); tr_w[m], tr_n[m] = w, n
        te_w, te_n = winery_track(train, test)
        extra_tr, extra_te = {"winery_track": tr_w, "winery_n": tr_n}, {"winery_track": te_w, "winery_n": te_n}
    Xtr = _stack_frame(train, tr_text, train, extra_tr, with_price).drop(columns=list(exclude))
    Xte = _stack_frame(test, te_text, train, extra_te, with_price).drop(columns=list(exclude))
    y = train["points"].to_numpy(dtype=float)
    if task == "binary":
        y = (y >= config.VALUE_MIN_POINTS).astype(int)
        Model = lgb.LGBMClassifier
    else:
        Model = lgb.LGBMRegressor
    yi = pd.Series(y, index=train.index)
    params0 = {**config.LGBM_FIXED, "random_state": seed}
    rows = []
    for gi, gp in enumerate(grid):
        for g, itr, iva in inner_splits(train, groups):
            iva = iva[iva["fold"] >= 0]
            m = Model(**params0, **gp).fit(Xtr.loc[itr.index], yi[itr.index])
            for k in config.LGBM_TREE_GRID:
                if task == "binary":
                    p = np.clip(m.predict_proba(Xtr.loc[iva.index], num_iteration=k)[:, 1], 1e-9, 1 - 1e-9)
                    t = yi[iva.index].to_numpy()
                    s = float(-(t * np.log(p) + (1 - t) * np.log(1 - p)).mean())
                else:
                    s = mae(yi[iva.index], m.predict(Xtr.loc[iva.index], num_iteration=k))
                rows.append({"grid": gi, "trees": k, "inner fold": g, "score": s})
    curve = pd.DataFrame(rows).pivot_table(index=["grid", "trees"], columns="inner fold", values="score")
    curve["mean"] = curve.mean(axis=1)
    gi, trees = curve["mean"].idxmin()
    gp = grid[int(gi)]
    final = Model(**{**params0, "n_estimators": int(trees)}, **gp).fit(Xtr, y)
    pred = final.predict_proba(Xte)[:, 1] if task == "binary" else final.predict(Xte)
    imp = pd.Series(final.booster_.feature_importance("gain"), index=Xtr.columns)
    return pred, {"curve": curve, "chosen": gp, "n_estimators": int(trees), "inner": curve.loc[(gi, trees)].drop("mean").to_dict(),
                  "inner mean": float(curve.loc[(gi, trees), "mean"]), "importance": imp / imp.sum()}
