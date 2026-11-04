import numpy as np

from kddenergy import config as c
from kddenergy.data import generation_wide, load_generation, thermal_series


def test_holdouts_are_after_development():
    assert max(c.DEV_ORIGINS) < min(c.SEALED_ORIGINS)
    assert c.DISCOVERY_END == c.SEALED_ORIGINS[0]


def test_thermal_splice_matches_both_eras():
    w = generation_wide(load_generation())
    th = thermal_series(w)
    old = w[c.THERMAL_TECH_2008_2015].sum(axis=1, min_count=1)
    new = w[c.THERMAL_FUEL_2016_ON]
    for ref in (old, new):
        m = ref.notna() & (ref > 1e5)
        assert abs(np.median(th[m] / ref[m]) - 1) < 1e-3


def test_canada_equals_sum_of_provinces():
    w = generation_wide(load_generation())[c.TOTAL_GEN].unstack("geography")
    prov = w.drop(columns="Canada")
    full = prov.notna().all(axis=1)
    assert np.allclose(prov[full].sum(axis=1), w.loc[full, "Canada"])


def test_default_loaders_enforce_the_seal():
    from kddenergy.data import load_availability, load_backtest, load_flows
    for f in (load_generation, load_flows, load_availability):
        assert f()["month"].max() <= c.DISCOVERY_END
    assert not set(load_backtest()["forecast_origin"]) & set(c.SEALED_ORIGINS)
    assert load_generation(allow_sealed=True)["month"].max() > c.DISCOVERY_END


def test_thermal_identity_exceptions_are_known_and_small():
    w = generation_wide(load_generation(allow_sealed=True))
    th = thermal_series(w)
    ref = w[c.THERMAL_TECH_2008_2015].sum(axis=1, min_count=1).fillna(w[c.THERMAL_FUEL_2016_ON])
    diff = (th - ref).dropna().abs()
    assert (diff > 1).sum() <= 8 and diff.max() <= 4_000
