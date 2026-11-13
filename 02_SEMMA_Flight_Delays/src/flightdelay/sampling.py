"""SEMMA *Sample* stage: proportional stratified sampling, representativeness checks, learning curves.

Follows SAS's *Data Mining and the Case for Sampling* (the Enterprise Miner Sampling node):
stratify on a few categorical variables with many records per level, keep the population's
strata proportions, and justify the sample size by fitting models on repeated samples of
increasing size and comparing their mean accuracy with confidence limits.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats


# ---------------------------------------------------------------- sampling
def stratum_quotas(sizes: pd.Series, n: int) -> pd.Series:
    """Proportional allocation of ``n`` across strata, rounded with the largest-remainder method.

    The quotas sum to exactly ``n`` and each differs from ``n * N_h / N`` by less than 1.
    """
    exact = sizes * (n / sizes.sum())
    q = np.floor(exact).astype(int)
    short = int(n - q.sum())
    if short > 0:
        q.loc[(exact - q).sort_values(ascending=False, kind="stable").index[:short]] += 1
    return q


def sample_keys(df: pd.DataFrame, strata: list[str], seed: int) -> pd.Series:
    """Rank of each row inside its stratum under one random permutation (0 = drawn first).

    Taking ``rank < quota_h`` gives a stratified random sample; samples drawn with the same seed are
    nested (a smaller sample is a subset of a larger one), so a learning curve compares like with like.
    """
    rng = np.random.default_rng(seed)
    u = pd.Series(rng.random(len(df)), index=df.index)
    return u.groupby([df[c] for c in strata], observed=True).rank(method="first").astype(int) - 1


def stratified_sample(df: pd.DataFrame, n: int, strata: list[str], seed: int, ranks: pd.Series | None = None) -> pd.DataFrame:
    """Proportional stratified random sample of exactly ``n`` rows (without replacement)."""
    if n >= len(df):
        return df
    if ranks is None:
        ranks = sample_keys(df, strata, seed)
    gid = df.groupby(strata, observed=True, sort=True).ngroup().to_numpy()
    quota = stratum_quotas(pd.Series(np.bincount(gid)), n).to_numpy()
    return df[ranks.to_numpy() < quota[gid]]


# ---------------------------------------------------------------- representativeness
def categorical_check(sample: pd.Series, population: pd.Series, top: int | None = None) -> dict:
    """Largest gap in level shares (percentage points), total-variation distance, chi-square goodness of fit.

    The chi-square uses the population shares as expected proportions and is divided by the finite-population
    correction (1 - f), since the sample is drawn without replacement from this population.
    """
    pop = population.astype(str)
    smp = sample.astype(str)
    if top is not None:
        keep = pop.value_counts().index[:top]
        pop = pop.where(pop.isin(keep), "other")
        smp = smp.where(smp.isin(keep), "other")
    p = pop.value_counts(normalize=True)
    o = smp.value_counts().reindex(p.index, fill_value=0)
    chi2, _ = stats.chisquare(o, p * o.sum())
    fpc = 1 - len(smp) / len(pop)
    pval = stats.chi2.sf(chi2 / fpc, len(p) - 1)
    gap = (o / o.sum() - p).abs()
    return {"levels": len(p), "max |share gap| (pp)": 100 * gap.max(), "TV distance": 0.5 * gap.sum(),
            "chi-square p": pval}


def numeric_check(sample: pd.Series, population: pd.Series) -> dict:
    """Standardized mean difference (|SMD| < 0.1 = balanced, the usual rule) and two-sample KS statistic."""
    s, p = sample.dropna().astype(float), population.dropna().astype(float)
    smd = (s.mean() - p.mean()) / p.std()
    ks = stats.ks_2samp(s.to_numpy(), p.sample(min(len(p), 2_000_000), random_state=0).to_numpy()).statistic
    return {"population mean": p.mean(), "sample mean": s.mean(), "SMD": smd, "KS D": ks}


def rate_check(sample: pd.DataFrame, population: pd.DataFrame, by: str, target: str, min_n: int = 1000) -> pd.DataFrame:
    """Target rate by level in sample vs population, with a z-score for sampling without replacement
    (finite-population correction applied per level). Levels with fewer than ``min_n`` population rows are skipped.
    """
    pr = population.groupby(by, observed=True)[target].agg(["mean", "size"])
    sr = sample.groupby(by, observed=True)[target].agg(["mean", "size"])
    t = pr.join(sr, lsuffix=" population", rsuffix=" sample", how="left")
    t = t[t["size population"] >= min_n]
    fpc = 1 - t["size sample"] / t["size population"]
    se = np.sqrt(t["mean population"] * (1 - t["mean population"]) / t["size sample"] * fpc)
    t["z"] = (t["mean sample"] - t["mean population"]) / se
    return t


# ---------------------------------------------------------------- learning curve summaries
def mean_ci(x, level: float = 0.95) -> tuple[float, float, float]:
    """Mean and t-based confidence limits over repeated samples."""
    x = np.asarray(x, dtype=float)
    m = x.mean()
    if len(x) < 2:
        return m, np.nan, np.nan
    h = stats.t.ppf((1 + level) / 2, len(x) - 1) * x.std(ddof=1) / np.sqrt(len(x))
    return m, m - h, m + h
