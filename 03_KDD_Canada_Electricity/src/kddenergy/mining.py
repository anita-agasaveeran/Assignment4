"""KDD step 4 - Data mining for K1 (clusters), K2 (change points) and K3 (anomalies).

Every tuning choice comes from ``config`` (fixed before mining); nothing here looks at the confirmation period.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import ruptures as rpt
from sklearn.cluster import AgglomerativeClustering, KMeans
from sklearn.ensemble import IsolationForest
from sklearn.metrics import adjusted_rand_score, silhouette_score
from sklearn.preprocessing import StandardScaler

from . import config as c


# ----------------------------------------------------------------------------------------------- K1 clustering
def standardize(X: pd.DataFrame) -> np.ndarray:
    return StandardScaler().fit_transform(X.to_numpy())


def kmeans_labels(X: pd.DataFrame, k: int, seed: int = c.SEED) -> np.ndarray:
    return KMeans(n_clusters=k, n_init=c.K1_N_INIT, random_state=seed).fit_predict(standardize(X))


def ward_labels(X: pd.DataFrame, k: int) -> np.ndarray:
    return AgglomerativeClustering(n_clusters=k, linkage="ward").fit_predict(standardize(X))


def silhouette_table(X: pd.DataFrame, ks=c.K1_K_RANGE) -> pd.DataFrame:
    Z = standardize(X)
    rows = []
    for k in ks:
        km, wd = kmeans_labels(X, k), ward_labels(X, k)
        rows.append({"k": k, "silhouette_kmeans": silhouette_score(Z, km), "silhouette_ward": silhouette_score(Z, wd),
                     "ARI_kmeans_vs_ward": adjusted_rand_score(km, wd), "smallest_cluster": np.bincount(km).min()})
    return pd.DataFrame(rows).set_index("k")


def choose_k(table: pd.DataFrame) -> int:
    """Pre-registered: the k with the best k-means silhouette (ties -> smaller k)."""
    return int(table["silhouette_kmeans"].idxmax())


def ari_if_one_moves(labels: np.ndarray) -> pd.Series:
    """ARI between a labelling and every labelling that moves exactly one item to another existing cluster."""
    labels = np.asarray(labels)
    out = []
    for i in range(len(labels)):
        for k in set(labels) - {labels[i]}:
            moved = labels.copy(); moved[i] = k
            out.append(adjusted_rand_score(labels, moved))
    return pd.Series(out).describe()[["min", "50%", "max"]]


def relabel_like(ref: np.ndarray, new: np.ndarray) -> np.ndarray:
    """Map cluster ids of ``new`` onto ``ref`` by maximum overlap (for display only; ARI is label-invariant)."""
    ref, new = np.asarray(ref), np.asarray(new)
    mapping = {}
    for k in np.unique(new):
        vals, counts = np.unique(ref[new == k], return_counts=True)
        mapping[k] = vals[np.argmax(counts)]
    return np.array([mapping[k] for k in new])


# ----------------------------------------------------------------------------------------- K2 change points
def noise_sigma(x: np.ndarray, method: str = c.K2_SIGMA) -> float:
    """'mad_diff' (primary): robust white-noise scale from first differences, 1.4826 MAD(diff) / sqrt(2).
    'sd' (sensitivity): standard deviation of the series itself (includes the shifts, so far more conservative)."""
    x = np.asarray(x, float)
    if method == "sd":
        return float(np.std(x))
    d = np.diff(x)
    return float(1.4826 * np.median(np.abs(d - np.median(d))) / np.sqrt(2))


def pelt(x: np.ndarray, sigma: float | None = None, method: str = c.K2_SIGMA) -> list[int]:
    """PELT mean-shift change points (indices where a new segment starts), penalty 3 log n on x / sigma."""
    x = np.asarray(x, float)
    s = sigma or noise_sigma(x, method) or 1.0
    algo = rpt.Pelt(model=c.K2_MODEL, min_size=c.K2_MIN_SIZE, jump=1).fit((x / s).reshape(-1, 1))
    return algo.predict(pen=c.K2_PEN_FACTOR * np.log(len(x)))[:-1]


def segment_means(x: np.ndarray, bkps: list[int]) -> list[tuple[int, int, float]]:
    edges = [0, *bkps, len(x)]
    return [(a, b, float(np.mean(x[a:b]))) for a, b in zip(edges[:-1], edges[1:])]


def primary_change(x: np.ndarray, bkps: list[int]) -> dict | None:
    """The change point with the largest |post - pre| shift between adjacent segments, if >= K2_MIN_SHIFT_PP."""
    segs = segment_means(np.asarray(x, float), bkps)
    best = None
    for (a, b, m0), (_, e, m1) in zip(segs[:-1], segs[1:]):
        if best is None or abs(m1 - m0) > abs(best["shift"]):
            best = {"index": b, "pre_start": a, "post_end": e, "pre_mean": m0, "post_mean": m1, "shift": m1 - m0}
    if best is None or abs(best["shift"]) * 100 < c.K2_MIN_SHIFT_PP:
        return None
    return best


def bootstrap_stability(x: np.ndarray, bkps: list[int], cp: int, reps: int = c.K2_BOOT_REPS,
                        block: int = c.K2_BOOT_BLOCK, tol: int = c.K2_CHANGEPOINT_TOL_MONTHS,
                        seed: int = c.SEED) -> float:
    """Share of moving-block bootstrap replicates (residuals around the fitted segment means, re-added to the fit)
    in which PELT finds a change point within +/- tol months of ``cp``."""
    x = np.asarray(x, float)
    n = len(x)
    fit = np.concatenate([np.full(b - a, m) for a, b, m in segment_means(x, bkps)])
    resid = x - fit
    sigma = noise_sigma(x)
    rng = np.random.default_rng(seed)
    starts_max = n - block + 1
    hits = 0
    for _ in range(reps):
        starts = rng.integers(0, starts_max, int(np.ceil(n / block)))
        rb = np.concatenate([resid[s:s + block] for s in starts])[:n]
        found = pelt(fit + rb, sigma)
        hits += any(abs(f - cp) <= tol for f in found)
    return hits / reps


def trim_stability(x: np.ndarray, cp: int, trims=c.K2_TRIMS, tol: int = c.K2_CHANGEPOINT_TOL_MONTHS,
                   method: str = c.K2_SIGMA) -> float:
    """Non-model-based date stability: PELT on the observed series with `a` months trimmed from the start and `b`
    from the end, for every (a, b) in trims x trims; share of sub-series with a change point within +/- tol of cp.
    Sub-series that no longer contain cp (+/- tol) are skipped."""
    x = np.asarray(x, float)
    n, hits, runs = len(x), 0, 0
    for a in trims:
        for b in trims:
            if not (a + tol <= cp <= n - b - tol):
                continue
            found = [f + a for f in pelt(x[a:n - b], method=method)]
            runs += 1
            hits += any(abs(f - cp) <= tol for f in found)
    return hits / runs if runs else float("nan")


def persistence(conf_mean: float, pre_mean: float, post_mean: float, last_mean: float,
                min_margin: float = c.K2_MIN_SHIFT_PP / 200) -> bool:
    """Margin test (config): the 2025-26 mean is beyond the pre/post midpoint, on the post side, by >= half the
    minimum shift, and the last development segment had not reversed past the midpoint."""
    d, mid = np.sign(post_mean - pre_mean), (pre_mean + post_mean) / 2
    return bool(d * (conf_mean - mid) >= min_margin and d * (last_mean - mid) > 0)


def attribution(ctrl: dict) -> tuple[float, str]:
    """Share of dln(combustion share) explained by dln(combustion GWh); 'burning' if >= 0.5 else 'denominator'."""
    dc = np.log(ctrl["combustion post (GWh/mo)"] / ctrl["combustion pre (GWh/mo)"])
    dt = np.log(ctrl["total generation post (GWh/mo)"] / ctrl["total generation pre (GWh/mo)"])
    ds = dc - dt
    frac = dc / ds if ds else float("nan")
    return float(frac), ("burning" if frac >= 0.5 else "denominator")


def change_controls(panel: pd.DataFrame, geo: str, months: list[str], ch: dict) -> dict:
    """Pre/post mean monthly GWh of combustion, total generation, hydro + nuclear and net imports."""
    g = panel.loc[geo]
    pre = g.loc[months[ch["pre_start"]]:months[ch["index"] - 1]]
    post = g.loc[months[ch["index"]]:months[ch["post_end"] - 1]]
    out = {}
    for name, f in {"combustion": lambda d: d["combustion"], "total generation": lambda d: d["gen_total"],
                    "hydro + nuclear": lambda d: d["hydro"] + d["nuclear"], "wind + solar": lambda d: d["wind"] + d["solar"],
                    "net imports": lambda d: d["receipts"] - d["deliveries"]}.items():
        out[f"{name} pre (GWh/mo)"] = f(pre).mean() / 1e3
        out[f"{name} post (GWh/mo)"] = f(post).mean() / 1e3
    return out


# ------------------------------------------------------------------------------------------------ K3 anomalies
def eligible_mask(index: pd.MultiIndex) -> np.ndarray:
    geo, month = index.get_level_values("geography"), index.get_level_values("month")
    brk = np.array([(g in c.DATA_BREAKS and m >= c.DATA_BREAKS[g]) or
                    (g in c.BREAK_WINDOWS and c.BREAK_WINDOWS[g][0] <= m <= c.BREAK_WINDOWS[g][1])
                    for g, m in zip(geo, month)])
    return np.isin(geo, c.K3_GEOS) & ~brk


def fit_isolation_forest(z: pd.DataFrame, seed: int = c.SEED) -> IsolationForest:
    return IsolationForest(n_estimators=c.K3_IF_TREES, random_state=seed).fit(z.to_numpy())


def anomaly_scores(z: pd.DataFrame, model: IsolationForest) -> pd.DataFrame:
    """Primary: Isolation Forest on the STL z's (higher = more anomalous). Comparison: max |z| over series."""
    return pd.DataFrame({"iforest": -model.score_samples(z.to_numpy()), "max_abs_z": z.abs().max(axis=1).to_numpy()},
                        index=z.index)


def top_flags(score: pd.Series, n: int) -> pd.Index:
    return score.sort_values(ascending=False, kind="mergesort").index[:n]


def _event_windows(events: pd.DataFrame, window: int) -> list[tuple[str, pd.Period, pd.Period]]:
    return [(r.geography, pd.Period(r.start_month, "M") - window, pd.Period(r.end_month, "M") + window)
            for r in events.itertuples()]


def event_level_credit(flags, events: pd.DataFrame, window: int = c.K3_MATCH_MONTHS) -> int:
    """Max number of flags that can be credited if each event credits at most one flag (bipartite matching)."""
    wins = _event_windows(events, window)
    cand = [[j for j, (g, lo, hi) in enumerate(wins) if g == fg and lo <= pd.Period(fm, "M") <= hi] for fg, fm in flags]
    match: dict[int, int] = {}

    def augment(i, seen):
        for j in cand[i]:
            if j not in seen:
                seen.add(j)
                if j not in match or augment(match[j], seen):
                    match[j] = i
                    return True
        return False
    return sum(augment(i, set()) for i in range(len(flags)))


def permutation_p(flags, events: pd.DataFrame, eligible: list, reps: int = c.K3_PERM_REPS, seed: int = c.SEED,
                  window: int = c.K3_MATCH_MONTHS) -> tuple[float, np.ndarray]:
    """Geography-stratified circular-shift null for event-level precision."""
    flags = list(flags)
    obs = event_level_credit(flags, events, window) / len(flags)
    by_geo: dict[str, list[str]] = {}
    for g, m in eligible:
        by_geo.setdefault(g, []).append(m)
    for g in by_geo:
        by_geo[g] = sorted(by_geo[g])
    pos = {(g, m): i for g, ms in by_geo.items() for i, m in enumerate(ms)}
    rng = np.random.default_rng(seed)
    null = np.empty(reps)
    for r in range(reps):
        shift = {g: rng.integers(0, len(ms)) for g, ms in by_geo.items()}
        sh = [(g, by_geo[g][(pos[(g, m)] + shift[g]) % len(by_geo[g])]) for g, m in flags]
        null[r] = event_level_credit(sh, events, window) / len(flags)
    return float(np.mean(null >= obs)), null


def score_flags(flags, covered: set, events: pd.DataFrame, eligible: list, window: int = c.K3_MATCH_MONTHS) -> dict:
    """Precision, base rate, lift and event recall for a set of (geography, month) flags."""
    flags = list(flags)
    hits = [f in covered for f in flags]
    base = np.mean([gm in covered for gm in eligible])
    hit_events = 0
    for r in events.itertuples():
        lo, hi = pd.Period(r.start_month, "M") - window, pd.Period(r.end_month, "M") + window
        hit_events += any(g == r.geography and lo <= pd.Period(m, "M") <= hi for g, m in flags)
    prec = float(np.mean(hits)) if flags else float("nan")
    credit = event_level_credit(flags, events, window) if flags else 0
    return {"flags": len(flags), "event_level_credit": credit,
            "event_level_precision": credit / len(flags) if flags else float("nan"),
            "matched": int(sum(hits)), "precision": prec, "base_rate": float(base),
            "lift": prec / base if base else float("nan"), "events": len(events), "events_hit": hit_events,
            "recall": hit_events / len(events) if len(events) else float("nan")}
