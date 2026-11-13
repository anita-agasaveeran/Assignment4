"""Decision metrics: per-day top-k precision / lift and a 7-day block bootstrap (moved here from the front pass)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .config import SEED


def per_day(dates, y, s, frac: float):
    """Per-day top-``frac`` precision and lift (precision / that day's rate), one value per day.

    Within each day, flights are ranked by score (ties keep input order) and the top
    ``max(1, round(frac * n_day))`` are selected. Days with no disruptions are skipped (lift undefined).
    Vectorized version of the front-pass loop; identical results.
    """
    y = np.asarray(y, dtype=float)
    s = np.asarray(s, dtype=float)
    day_codes, _ = pd.factorize(np.asarray(dates), sort=True)
    order = np.lexsort((-s, day_codes))                       # by day, then score descending (stable)
    d_sorted, y_sorted = day_codes[order], y[order]
    n_day = np.bincount(day_codes)
    starts = np.concatenate([[0], np.cumsum(n_day)[:-1]])
    pos = np.arange(len(y)) - starts[d_sorted]                # rank within day
    k = np.maximum(1, np.rint(frac * n_day).astype(int))      # np.rint == Python round (half to even)
    top = pos < k[d_sorted]
    hits = np.bincount(d_sorted[top], weights=y_sorted[top], minlength=len(n_day))
    rate = np.bincount(day_codes, weights=y, minlength=len(n_day)) / n_day
    prec = hits / k
    keep = rate > 0
    return prec[keep], prec[keep] / rate[keep]


def block_bootstrap(x, block: int = 7, n: int = 2000, seed: int = SEED, level: float = 0.90):
    """Interval of the mean of a daily series, resampling ``block``-day blocks (daily rates are autocorrelated)."""
    x = np.asarray(x, dtype=float)
    rng = np.random.default_rng(seed)
    blocks = [x[i:i + block] for i in range(0, len(x), block)]
    means = [np.concatenate([blocks[j] for j in rng.integers(0, len(blocks), len(blocks))]).mean() for _ in range(n)]
    a = (1 - level) / 2
    return np.quantile(means, [a, 1 - a])


def day_holdout(dates, frac: float = 0.10, seed: int = SEED) -> np.ndarray:
    """Row mask selecting a random ``frac`` of whole DAYS (critic round 1, M1).

    Early stopping on random rows from the same days rewards memorising each day's level (day-level inputs take one
    value per day), so the holdout must be grouped by day.
    """
    days = np.unique(np.asarray(dates))
    rng = np.random.default_rng(seed)
    held = rng.choice(days, size=max(1, int(round(frac * len(days)))), replace=False)
    return np.isin(np.asarray(dates), held)
