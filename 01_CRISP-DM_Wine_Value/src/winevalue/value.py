"""Value shortlist evaluation (Phase 1 definitions, used again in Phases 4-5).

- ``simulate_cycles``: expected precision@k over random buying cycles of
  ``n_candidates`` (BSC1 point estimate). Cycle membership comes from its own
  RNG stream, and each rule has its own tie-break stream (keyed by rule name).
  So a rule's result doesn't depend on which other rules are evaluated alongside it.
- ``precision_top_frac``: precision in the top ``frac`` of a pool. Used for
  per-critic reporting and the bootstrap.
- ``cluster_bootstrap_lift``: one-sided lower bound of the lift of one rule
  over another, resampling *wineries* (BSC1 uncertainty condition).
"""

from __future__ import annotations

import zlib

import numpy as np
import pandas as pd

from .metrics import precision_at_k


def simulate_cycles(rule_scores: dict[str, np.ndarray], is_value: np.ndarray, n_candidates: int,
                    k: int, n_cycles: int = 200, seed: int = 0) -> pd.DataFrame:
    """Precision@k of each rule over ``n_cycles`` random cycles of ``n_candidates`` pool wines."""
    is_value = np.asarray(is_value, dtype=float)
    n_pool = len(is_value)
    if n_candidates > n_pool:
        raise ValueError(f"pool has only {n_pool} wines, fewer than n_candidates={n_candidates}")
    cycle_rng = np.random.default_rng([seed, 0])      # which wines are in each cycle
    cycles = [cycle_rng.choice(n_pool, size=n_candidates, replace=False) for _ in range(n_cycles)]
    out = {}
    for name, sc in rule_scores.items():
        tie_rng = np.random.default_rng([seed, 1, zlib.crc32(name.encode())])   # one tie stream per rule
        sc = np.asarray(sc)
        out[name] = [precision_at_k(sc[idx], is_value[idx], k, rng=tie_rng) for idx in cycles]
    return pd.DataFrame(out)


def precision_top_frac(score, is_value, frac: float = 0.1, rng: np.random.Generator | None = None) -> float:
    """Precision among the top ``frac`` of the pool (at least 1 wine)."""
    k = max(1, int(round(frac * len(score))))
    return precision_at_k(score, is_value, k, rng=rng)


def cluster_bootstrap_lift(score_a, score_b, is_value, clusters, frac: float = 0.1,
                           n_boot: int = 500, alpha: float = 0.10, seed: int = 0) -> dict:
    """Lift = precision_top_frac(a) / precision_top_frac(b), with a one-sided (1 - alpha) lower bound.

    Resamples whole clusters (e.g. wineries) with replacement, so wines from the
    same producer move together.
    """
    a, b, v = (np.asarray(x, dtype=float) for x in (score_a, score_b, is_value))
    codes, uniq = pd.factorize(pd.Series(clusters))
    members = [np.flatnonzero(codes == c) for c in range(len(uniq))]
    rng = np.random.default_rng(seed)
    point = precision_top_frac(a, v, frac, rng) / precision_top_frac(b, v, frac, rng)
    lifts = []
    for _ in range(n_boot):
        idx = np.concatenate([members[c] for c in rng.integers(0, len(members), len(members))])
        pb = precision_top_frac(b[idx], v[idx], frac, rng)
        lifts.append(precision_top_frac(a[idx], v[idx], frac, rng) / pb if pb > 0 else np.inf)
    return {"lift": point, "lower_bound": float(np.quantile(lifts, alpha))}
