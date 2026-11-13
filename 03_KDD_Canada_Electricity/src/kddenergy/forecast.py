"""K4 - forecasting monthly availability at December origins, 12-month horizon (the dataset's backtest design)."""

from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing

from . import config as c


def availability_matrix(avail: pd.DataFrame) -> pd.DataFrame:
    A = avail.pivot(index="month", columns="geography", values="availability_mwh")
    A.index = pd.PeriodIndex(A.index, freq="M")
    return A


def seasonal_naive(h: pd.Series, tgt: pd.PeriodIndex) -> np.ndarray:
    return np.array([h.get(t - 12, np.nan) for t in tgt])


def avg3_growth(h: pd.Series, tgt: pd.PeriodIndex) -> np.ndarray:
    avg3 = np.array([np.nanmean([h.get(t - 12 * k, np.nan) for k in (1, 2, 3)]) for t in tgt])
    return avg3 * np.sqrt(h.iloc[-12:].sum() / h.iloc[-24:-12].sum())


def ets_damped_log(h: pd.Series, tgt: pd.PeriodIndex) -> np.ndarray:
    """Holt-Winters on log availability: damped additive trend, additive seasonality; fit on 2016-01 onward."""
    y = h[h.index >= pd.Period(c.CONSISTENT_START, "M")].astype(float)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        m = ExponentialSmoothing(np.log(y.to_numpy()), trend="add", damped_trend=True, seasonal="add",
                                 seasonal_periods=12, initialization_method="estimated").fit()
    steps = [(t - y.index[-1]).n for t in tgt]
    fc = m.forecast(max(steps))
    return np.exp(fc[np.array(steps) - 1])


METHODS = {"snaive": seasonal_naive, "avg3_growth": avg3_growth, "ets_damped_log": ets_damped_log}


def backtest(A: pd.DataFrame, origins, geos=c.GEOS, horizon: int = c.FORECAST_HORIZON, methods=METHODS) -> list[dict]:
    """One row per (origin, geography): actuals and every method's forecasts. Targets beyond the data end are
    dropped (origin 2025-12 forecasts Jan-Aug 2026 only). Same skip rule as the front pass."""
    rows = []
    last = A.index.max()
    for o in origins:
        op = pd.Period(o, "M")
        tgt = pd.period_range(op + 1, min(op + horizon, last), freq="M")
        hist = A.loc[:op]
        for g in geos:
            y, h = A.loc[tgt, g], hist[g].dropna()
            if y.isna().any() or len(h) < 36:
                continue
            r = {"origin": o, "geo": g, "months": [str(t) for t in tgt], "y": y.to_numpy()}
            for name, f in methods.items():
                r[name] = f(h, tgt)
            if "avg3_growth" in r and "ets_damped_log" in r:
                r["combo_avg3_ets"] = (r["avg3_growth"] + r["ets_damped_log"]) / 2
            rows.append(r)
    return rows


def wape(rows: list[dict], key: str) -> float:
    return 100 * sum(np.abs(r["y"] - r[key]).sum() for r in rows) / sum(r["y"].sum() for r in rows)


def wape_table(rows: list[dict], keys) -> pd.DataFrame:
    origins = list(dict.fromkeys(r["origin"] for r in rows))
    t = pd.DataFrame({k: {o: wape([r for r in rows if r["origin"] == o], k) for o in origins} for k in keys})
    t.loc["pooled"] = {k: wape(rows, k) for k in keys}
    return t


def bootstrap_ratio(rows: list[dict], model: str, base: str = "snaive", reps: int = 2000, seed: int = c.SEED):
    """Pooled WAPE ratio model / base with a (geography, origin)-pair bootstrap 90% interval."""
    rng = np.random.default_rng(seed)
    ratios = []
    for _ in range(reps):
        s = [rows[i] for i in rng.integers(0, len(rows), len(rows))]
        ratios.append(wape(s, model) / wape(s, base))
    return wape(rows, model) / wape(rows, base), np.percentile(ratios, [5, 95])
