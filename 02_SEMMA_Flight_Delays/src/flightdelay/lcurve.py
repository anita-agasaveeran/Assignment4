"""Learning curve for the Sample stage: model quality vs training-sample size (SAS case-for-sampling style)."""

from __future__ import annotations

import time

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss, roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from . import config
from .features import DAY_BEFORE_FEATURES, SCHEDULE_FEATURES
from .metrics import day_holdout, per_day
from .sampling import sample_keys, stratified_sample

FEATURES = SCHEDULE_FEATURES + DAY_BEFORE_FEATURES
CAT = ["carrier", "origin", "dest"]
LR_ONEHOT = ["carrier", "origin", "dest", "dep_hour", "arr_hour", "day_of_week"]
LR_NUMERIC = ["distance", "sched_elapsed_time", "origin_hour_sched", "origin_day_sched"] + DAY_BEFORE_FEATURES


ES_FRACTION, ES_PATIENCE, MAX_TREES = 0.10, 50, 3000


def _lgbm(num_leaves: int, min_child_samples: int, seed: int):
    # Number of trees is chosen by early stopping on a random 10% of the training sample's DAYS (never the validation
    # months). Revision 2: whole days, not random rows (critic round 1, M1). A fixed tree count over-fits small
    # samples and would confound sample size with regularization.
    return lgb.LGBMClassifier(n_estimators=MAX_TREES, learning_rate=0.05, num_leaves=num_leaves,
                              min_child_samples=min_child_samples, subsample=0.8, subsample_freq=1,
                              colsample_bytree=0.8, verbose=-1, random_state=seed)


def _logit():
    pre = ColumnTransformer([
        ("onehot", OneHotEncoder(handle_unknown="ignore", min_frequency=20), LR_ONEHOT),
        ("num", make_pipeline(SimpleImputer(strategy="median", add_indicator=True), StandardScaler()), LR_NUMERIC)])
    return make_pipeline(pre, LogisticRegression(C=1.0, max_iter=500))


# The front-pass LightGBM, a higher-capacity LightGBM (does a bigger model need more rows?), and a logistic regression.
MODELS = {
    "LightGBM 63 leaves": lambda seed: _lgbm(63, 100, seed),
    "LightGBM 255 leaves": lambda seed: _lgbm(255, 200, seed),
    "logistic regression": lambda seed: _logit(),
}


def window_frames(feat: pd.DataFrame, train_rng, valid_rng):
    """Training pool and full validation window, with categories fixed from the training pool's schedule."""
    tr = feat[feat["flight_date"].between(*train_rng)].copy()
    va = feat[feat["flight_date"].between(*valid_rng)].copy()
    for c in CAT:
        cats = pd.Index(sorted(tr[c].astype(str).unique()))
        tr[c] = pd.Categorical(tr[c].astype(str), categories=cats)
        va[c] = pd.Categorical(va[c].astype(str).where(va[c].astype(str).isin(cats)), categories=cats)
    tr["year_month"] = tr["flight_date"].dt.to_period("M").astype(str)
    return tr, va


def score(model_name: str, tr: pd.DataFrame, va: pd.DataFrame, seed: int = config.SEED) -> tuple[np.ndarray, int]:
    """Validation scores and the number of trees used (0 for the logistic regression)."""
    m = MODELS[model_name](seed)
    if model_name.startswith("LightGBM"):
        es = day_holdout(tr["flight_date"].to_numpy(), ES_FRACTION, seed)
        fit, stop = tr[~es], tr[es]
        m.fit(fit[FEATURES], fit[config.TARGET], eval_set=[(stop[FEATURES], stop[config.TARGET])],
              callbacks=[lgb.early_stopping(ES_PATIENCE, verbose=False)])
        return m.predict_proba(va[FEATURES], num_iteration=m.best_iteration_)[:, 1], int(m.best_iteration_)
    X = lambda d: d[LR_ONEHOT + LR_NUMERIC].astype({c: str for c in LR_ONEHOT})
    m.fit(X(tr), tr[config.TARGET])
    return m.predict_proba(X(va))[:, 1], 0


def metrics_row(y, s, dates) -> dict:
    _, lift2 = per_day(dates, y, s, 0.02)
    _, lift10 = per_day(dates, y, s, 0.10)
    return {"top2_lift": lift2.mean(), "top10_lift": lift10.mean(), "roc_auc": roc_auc_score(y, s),
            "log_loss": log_loss(y, np.clip(s, 1e-6, 1 - 1e-6))}


FULL_REPS = 3   # the full window is refit 3 times (new early-stopping split + bagging seed): the noise floor


def run(feat: pd.DataFrame, windows=None, sizes=None, reps=None, models=None, log=print) -> pd.DataFrame:
    """One row per (window, model, size, rep). Size ``"full"`` = the whole training window, refit FULL_REPS times
    with different model seeds (the logistic regression is deterministic, so once).

    Within a rep, samples are nested (same random permutation), so differences between sizes are paired.
    """
    windows = windows or config.LC_WINDOWS
    sizes = sizes or config.LC_SIZES
    reps = config.LC_REPS if reps is None else reps
    models = models or list(MODELS)
    rows = []
    for wname, (train_rng, valid_rng) in windows.items():
        tr_pool, va = window_frames(feat, train_rng, valid_rng)
        y, dates = va[config.TARGET].to_numpy(), va["flight_date"].to_numpy()
        plan = [(n, r) for r in range(reps) for n in sizes if n < len(tr_pool)] + [("full", r) for r in range(FULL_REPS)]
        keys = {}
        for n, r in plan:
            if n == "full":
                tr = tr_pool
            else:
                if r not in keys:
                    keys[r] = sample_keys(tr_pool, config.SAMPLE_STRATA, seed=config.SEED + r)
                tr = stratified_sample(tr_pool, n, config.SAMPLE_STRATA, seed=config.SEED + r, ranks=keys[r])
            for mname in models:
                if n == "full" and r > 0 and not mname.startswith("LightGBM"):
                    continue
                t0 = time.time()
                s, trees = score(mname, tr, va, seed=config.SEED + r)
                rows.append({"window": wname, "model": mname, "size": len(tr), "grid": str(n), "rep": r,
                             "pool": len(tr_pool), **metrics_row(y, s, dates), "trees": trees,
                             "seconds": time.time() - t0})
                log(f"{wname:6s} {mname:20s} n={len(tr):>9,} rep={r} lift2={rows[-1]['top2_lift']:.3f} "
                    f"auc={rows[-1]['roc_auc']:.4f} trees={trees} ({rows[-1]['seconds']:.0f}s)")
    return pd.DataFrame(rows)
