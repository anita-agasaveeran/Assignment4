"""Forecast-accuracy and business metrics used in Modeling and Evaluation."""

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


def wape(actual, predicted) -> float:
    """Weighted absolute percentage error: sum|a - p| / sum(a), in percent."""
    a, p = _arrays(actual, predicted)
    denom = np.sum(np.abs(a))
    if denom == 0:
        raise ValueError("WAPE is undefined when total actual demand is zero")
    return float(100 * np.sum(np.abs(a - p)) / denom)


def waste_units(demand, baked) -> float:
    """Units baked but not sold: sum(max(baked - demand, 0))."""
    d, b = _arrays(demand, baked)
    return float(np.sum(np.clip(b - d, 0, None)))


def fill_rate(demand, baked) -> float:
    """Share of demand that was met: sum(min(baked, demand)) / sum(demand)."""
    d, b = _arrays(demand, baked)
    total = np.sum(d)
    if total == 0:
        raise ValueError("Fill rate is undefined when total demand is zero")
    return float(np.sum(np.minimum(b, d)) / total)


def waste_rate(demand, baked) -> float:
    """Unsold share of what was baked: waste_units / sum(baked)."""
    d, b = _arrays(demand, baked)
    total = np.sum(b)
    if total == 0:
        raise ValueError("Waste rate is undefined when nothing was baked")
    return waste_units(d, b) / float(total)
