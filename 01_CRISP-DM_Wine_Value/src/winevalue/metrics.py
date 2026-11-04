"""Evaluation metrics for score prediction and value picks."""

from __future__ import annotations

import numpy as np


def _arrays(*xs):
    arrs = [np.asarray(x, dtype=float) for x in xs]
    if len({a.shape for a in arrs}) != 1:
        raise ValueError("Inputs must have the same shape")
    return arrs


def mae(actual, predicted) -> float:
    """Mean absolute error."""
    a, p = _arrays(actual, predicted)
    return float(np.mean(np.abs(a - p)))


def within(actual, predicted, tol: float = 2.0) -> float:
    """Share of predictions within +/- ``tol`` points of the actual score."""
    a, p = _arrays(actual, predicted)
    return float(np.mean(np.abs(a - p) <= tol))


def precision_at_k(ranking_score, is_relevant, k: int, rng: np.random.Generator | None = None) -> float:
    """Share of the top-``k`` items (by ``ranking_score``, descending) that are relevant.

    Ties: with ``rng``, tied items are ordered randomly. Use this for coarse
    scores such as price, where file order would otherwise decide (about 860
    candidates per fold cost exactly $25). Without ``rng``, original order
    decides (stable sort).
    """
    s, r = _arrays(ranking_score, is_relevant)
    if not 0 < k <= len(s):
        raise ValueError("k must be between 1 and the number of items")
    if rng is None:
        top = np.argsort(-s, kind="stable")[:k]
    else:
        top = np.lexsort((rng.random(len(s)), -s))[:k]
    return float(r[top].mean())


def cluster_bootstrap(stat, clusters, n_boot: int = 500, alpha: float = 0.10, seed: int = 0) -> dict:
    """One-sided (1 - alpha) lower bound of ``stat(idx)`` under a cluster bootstrap.

    ``stat`` takes an index array and returns a number. Whole clusters
    (e.g. wineries) are resampled with replacement.
    """
    import pandas as pd
    codes, uniq = pd.factorize(pd.Series(clusters))
    members = [np.flatnonzero(codes == c) for c in range(len(uniq))]
    rng = np.random.default_rng(seed)
    point = stat(np.arange(len(codes)))
    draws = [stat(np.concatenate([members[c] for c in rng.integers(0, len(members), len(members))]))
             for _ in range(n_boot)]
    return {"estimate": float(point), "lower_bound": float(np.quantile(draws, alpha))}
