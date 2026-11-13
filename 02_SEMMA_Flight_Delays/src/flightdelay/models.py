"""SEMMA *Model*: the SAS Enterprise Miner model nodes (Regression, Decision Tree, Neural Network) + gradient boosting."""

from __future__ import annotations

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier

from . import config
from .metrics import day_holdout
from .modify import V3_CATEGORICAL, V3_FEATURES, V3_NUMERIC

ONEHOT = V3_CATEGORICAL + ["dep_hour"]
COUNTS = ["origin_hour_sched", "origin_day_sched", "dest_hour_sched", "carrier_day_sched", "origin_d1_n", "flight_w4_n"]
OTHER_NUM = [c for c in V3_NUMERIC if c not in COUNTS]


def preprocessor(scale: bool = True) -> ColumnTransformer:
    """Modify-stage transform for the non-boosting models: levels with fewer than 1,000 rows IN THE FIT SAMPLE pooled
    into an 'infrequent' bucket (unseen levels go there too); right-skewed counts log1p-transformed; numerics
    median-imputed (a safeguard: the v3 inputs have no missing values) and standardized."""
    tail = [SimpleImputer(strategy="median")] + ([StandardScaler()] if scale else [])
    return ColumnTransformer([
        ("cat", OneHotEncoder(min_frequency=1000, handle_unknown="infrequent_if_exist"), ONEHOT),
        ("counts", make_pipeline(FunctionTransformer(np.log1p), *tail), COUNTS),
        ("num", make_pipeline(*tail), OTHER_NUM)])


def make(name: str, seed: int = config.SEED, **kw):
    if name == "logistic regression":
        return make_pipeline(preprocessor(), LogisticRegression(C=kw.get("C", 1.0), max_iter=1000))
    if name == "decision tree":
        return make_pipeline(preprocessor(scale=False), DecisionTreeClassifier(
            max_depth=kw.get("max_depth", 12), min_samples_leaf=kw.get("min_samples_leaf", 500), random_state=seed))
    if name == "neural network":
        return make_pipeline(preprocessor(), MLPClassifier(
            hidden_layer_sizes=kw.get("hidden", (64, 32)), alpha=kw.get("alpha", 1e-4), batch_size=2048,
            learning_rate_init=1e-3, random_state=seed))      # epochs: day-grouped selection in fit()
    if name == "gradient boosting":
        return lgb.LGBMClassifier(n_estimators=3000, learning_rate=kw.get("lr", 0.05), num_leaves=kw.get("num_leaves", 63),
                                  min_child_samples=kw.get("min_child_samples", 200), subsample=0.8, subsample_freq=1,
                                  colsample_bytree=0.8, verbose=-1, random_state=seed)
    raise ValueError(name)


def as_categorical(df: pd.DataFrame, cats: dict | None = None):
    """Pandas categoricals for LightGBM, with categories fixed from the training frame (unseen -> NaN)."""
    df = df.copy()
    cats = cats or {c: pd.Index(sorted(df[c].astype(str).unique())) for c in V3_CATEGORICAL}
    for c in V3_CATEGORICAL:
        s = df[c].astype(str)
        df[c] = pd.Categorical(s.where(s.isin(cats[c])), categories=cats[c])
    return df, cats


def fit(name: str, tr: pd.DataFrame, seed: int = config.SEED, **kw):
    """Fit one model; gradient boosting stops early on a random 10% of the training DAYS (never validation months)."""
    m = make(name, seed, **kw)
    y = tr[config.TARGET].to_numpy()
    if name == "gradient boosting":
        X, cats = as_categorical(tr[V3_FEATURES])
        es = day_holdout(tr["flight_date"].to_numpy(), 0.10, seed)
        m.fit(X[~es], y[~es], eval_set=[(X[es], y[es])], callbacks=[lgb.early_stopping(50, verbose=False)])
        m.cats_ = cats
        return m
    X = tr[V3_FEATURES].astype({c: str for c in V3_CATEGORICAL})
    if name == "neural network":
        return _fit_mlp_day_grouped(m, X, y, tr["flight_date"].to_numpy(), seed)
    return m.fit(X, y)


def _fit_mlp_day_grouped(pipe, X, y, dates, seed, max_epochs: int = 20, patience: int = 2):
    """Neural network with epochs chosen on a held-out 10% of whole DAYS (critic round 2, N1).

    sklearn's built-in ``early_stopping`` holds out random rows from the same days (the M1 flaw), so it is replaced by
    epochs of ``partial_fit`` over shuffled mini-batches (continuous Adam), keeping the epoch with the lowest log-loss on
    the held-out days.
    """
    import copy
    import warnings
    from sklearn.exceptions import ConvergenceWarning
    from sklearn.metrics import log_loss
    from sklearn.pipeline import Pipeline
    pre, mlp = pipe.steps[0][1], pipe.steps[-1][1]
    es = day_holdout(dates, 0.10, seed)
    Xf, Xh = pre.fit_transform(X[~es]), pre.transform(X[es])
    yf = y[~es]
    rng, classes, bs = np.random.RandomState(seed), np.array([0, 1]), mlp.batch_size
    best, bad = (np.inf, None, 0), 0
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ConvergenceWarning)
        for ep in range(1, max_epochs + 1):
            # one epoch = one pass of partial_fit over freshly shuffled mini-batches; Adam's state carries over
            # (critic round 3, R3-1: fit() with warm_start restarted Adam and reused the same batch order each epoch)
            perm = rng.permutation(Xf.shape[0])
            for b in range(0, len(perm), bs):
                idx = perm[b:b + bs]
                mlp.partial_fit(Xf[idx], yf[idx], classes=classes)
            ll = log_loss(y[es], mlp.predict_proba(Xh)[:, 1])
            if ll < best[0]:
                best, bad = (ll, copy.deepcopy(mlp), ep), 0
            else:
                bad += 1
                if bad >= patience:
                    break
    out = Pipeline([("pre", pre), ("mlp", best[1])])
    out.best_epoch_ = best[2]
    return out


def predict(m, df: pd.DataFrame) -> np.ndarray:
    if isinstance(m, lgb.LGBMClassifier):
        X, _ = as_categorical(df[V3_FEATURES], m.cats_)
        return m.predict_proba(X, num_iteration=m.best_iteration_)[:, 1]
    return m.predict_proba(df[V3_FEATURES].astype({c: str for c in V3_CATEGORICAL}))[:, 1]


def rules(tr: pd.DataFrame, va: pd.DataFrame) -> dict:
    """The two simple benchmark rules (schedule rule refit on ``tr``; day-before rule needs no fit).

    Revision 2 (critic m9): the day-before rule uses yesterday's rates on the single 16:45 ET clock (``*_d1``). The
    front-pass version (local 17:00, which sees Pacific arrivals up to 19:59 ET) is kept as a third, reported-only
    scorer; T1/T2 use the better of the first two."""
    hist = tr.groupby(["carrier", "dep_hour"], observed=True)[config.TARGET].mean()
    idx = pd.MultiIndex.from_arrays([va["carrier"].astype(str), va["dep_hour"]])
    hist.index = pd.MultiIndex.from_arrays([hist.index.get_level_values(0).astype(str), hist.index.get_level_values(1)])
    sched = hist.reindex(idx).fillna(tr[config.TARGET].mean()).to_numpy()
    dayb = va[["origin_d1", "dest_d1", "carrier_d1"]].mean(axis=1).to_numpy()
    dayb_v2 = va[["origin_prev_day", "dest_prev_day", "carrier_prev_day"]].mean(axis=1).fillna(tr[config.TARGET].mean()).to_numpy()
    return {"schedule rule": sched, "day-before rule": dayb, "day-before rule (v2 local clock)": dayb_v2}


BENCHMARK_RULES = ["schedule rule", "day-before rule"]
