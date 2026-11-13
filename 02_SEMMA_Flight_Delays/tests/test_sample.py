import numpy as np
import pandas as pd

from flightdelay import config
from flightdelay.metrics import block_bootstrap, per_day
from flightdelay.sampling import mean_ci, sample_keys, stratified_sample, stratum_quotas


def _pop(n=20_000, seed=0):
    rng = np.random.default_rng(seed)
    return pd.DataFrame({"year_month": rng.choice(["2025-01", "2025-02", "2025-03"], n, p=[0.5, 0.3, 0.2]),
                         "carrier": rng.choice(["AA", "DL", "WN", "ZZ"], n, p=[0.4, 0.3, 0.29, 0.01]),
                         "disrupted": (rng.random(n) < 0.24).astype("int8"), "x": rng.normal(size=n)})


def test_quotas_sum_exactly_and_are_proportional():
    sizes = pd.Series([1000, 333, 7, 1])
    q = stratum_quotas(sizes, 100)
    assert q.sum() == 100
    assert (np.abs(q - sizes * 100 / sizes.sum()) < 1).all()


def test_stratified_sample_has_exact_size_and_strata_shares():
    pop = _pop()
    s = stratified_sample(pop, 2_000, config.SAMPLE_STRATA, seed=1)
    assert len(s) == 2_000 and s.index.is_unique and s.index.isin(pop.index).all()
    share_pop = pop.groupby(config.SAMPLE_STRATA).size() / len(pop)
    share_smp = (s.groupby(config.SAMPLE_STRATA).size() / len(s)).reindex(share_pop.index, fill_value=0)
    assert (np.abs(share_smp - share_pop) * len(s) < 1 + 1e-9).all()      # within one record of proportional


def test_samples_with_one_seed_are_nested():
    pop = _pop()
    keys = sample_keys(pop, config.SAMPLE_STRATA, seed=3)
    small = stratified_sample(pop, 500, config.SAMPLE_STRATA, seed=3, ranks=keys)
    large = stratified_sample(pop, 5_000, config.SAMPLE_STRATA, seed=3, ranks=keys)
    assert small.index.isin(large.index).all()


def test_different_seeds_draw_different_samples():
    pop = _pop()
    a = stratified_sample(pop, 1_000, config.SAMPLE_STRATA, seed=1)
    b = stratified_sample(pop, 1_000, config.SAMPLE_STRATA, seed=2)
    assert len(a.index.intersection(b.index)) < 300                      # ~5% overlap expected


def test_per_day_matches_front_pass_loop_with_ties():
    rng = np.random.default_rng(0)
    dates = np.repeat(pd.date_range("2025-01-01", periods=5).to_numpy(), 200)
    y, s = (rng.random(1000) < 0.25).astype(float), np.round(rng.random(1000), 1)
    prec, lift = per_day(dates, y, s, 0.10)
    for i, day in enumerate(np.unique(dates)):
        m = dates == day
        top = np.argsort(-s[m], kind="stable")[:20]
        assert np.isclose(prec[i], y[m][top].mean()) and np.isclose(lift[i], y[m][top].mean() / y[m].mean())


def test_block_bootstrap_and_mean_ci_bracket_the_mean():
    x = np.random.default_rng(1).normal(1.0, 0.2, 120)
    lo, hi = block_bootstrap(x)
    m, l2, h2 = mean_ci(x)
    assert lo < x.mean() < hi and l2 < m < h2


def test_sample_rule_constants_are_sane():
    assert list(config.LC_SIZES) == sorted(config.LC_SIZES) and config.LC_REPS >= 3
    assert "disrupted" in config.SAMPLE_STRATA and "flight_date" not in config.SAMPLE_STRATA


def test_day_holdout_holds_out_whole_days_only():
    from flightdelay.metrics import day_holdout
    dates = np.repeat(pd.date_range("2025-01-01", periods=50).to_numpy(), 30)
    m = day_holdout(dates, 0.10, seed=1)
    held = set(dates[m]); kept = set(dates[~m])
    assert len(held) == 5 and not held & kept
