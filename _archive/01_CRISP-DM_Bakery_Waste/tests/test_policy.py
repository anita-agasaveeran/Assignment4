import numpy as np
import pandas as pd
import pytest

from bakery.features import CHAIN, add_trailing_mean, demand_grid
from bakery.policy import critical_ratio, fit_multiplier, simulate_plan, trailing_mean_rule


def _orders():
    return pd.DataFrame({
        "Date": pd.to_datetime(["2024-01-01", "2024-01-01", "2024-01-03"]),
        "Store_ID": ["S1", "S2", "S1"], "Product": ["A", "A", "B"], "Quantity": [2, 3, 4]})


def test_demand_grid_fills_zero_days_and_pools():
    g = demand_grid(_orders())
    assert len(g) == 3 * 2 * 2                    # 3 dates x 2 stores x 2 products
    assert g["demand"].sum() == 9 and (g["demand"] == 0).sum() == 9
    p = demand_grid(_orders(), pooled=True)
    assert set(p["Location"]) == {CHAIN}
    assert p.loc[(p.Date == "2024-01-01") & (p.Product == "A"), "demand"].item() == 5


def test_trailing_mean_uses_only_past_days():
    g = add_trailing_mean(demand_grid(_orders()), window=2)
    s1a = g[(g.Location == "S1") & (g.Product == "A")]["trailing_mean"].tolist()
    assert np.isnan(s1a[0]) and np.isnan(s1a[1]) and s1a[2] == pytest.approx(1.0)


def test_simulate_plan_accounting():
    r = simulate_plan(demand=[3, 0, 5], baked=[4, 2, 1], unit_margin=10, unit_cost=6)
    assert (r.sold, r.wasted) == (4, 3)
    assert r.fill_rate == pytest.approx(4 / 8)
    assert r.net_contribution == pytest.approx(4 * 10 - 3 * 6)


def test_simulate_plan_preorders():
    # make-to-order: nothing baked, half of demand retained as pre-orders
    mto = simulate_plan(demand=[4, 2], baked=0, unit_margin=10, unit_cost=6, preorder_retention=0.5)
    assert (mto.sold_preorder, mto.wasted, mto.net_contribution) == (3, 0, 30)
    # hybrid: bake 1, unmet 3 -> 1.5 pre-ordered
    hy = simulate_plan(demand=[4], baked=[1], unit_margin=10, unit_cost=6, preorder_retention=0.5)
    assert hy.sold == pytest.approx(2.5) and hy.fill_rate == pytest.approx(2.5 / 4)
    with pytest.raises(ValueError):
        simulate_plan([1], [1], 1, 1, preorder_retention=1.5)


def test_rule_and_multiplier():
    assert trailing_mean_rule([1.2, 0.0], 2).tolist() == [3.0, 0.0]
    f = pd.DataFrame({"demand": [2, 2, 2], "trailing_mean": [2.0, 2.0, 2.0],
                      "unit_margin": 5.0, "unit_cost": 5.0})
    # several k round up to the same bake quantity; the smallest one is returned
    assert trailing_mean_rule(f["trailing_mean"], fit_multiplier(f)).tolist() == [2.0, 2.0, 2.0]
    assert fit_multiplier(f, target_fill=1.0) == pytest.approx(0.55)
    assert np.isnan(fit_multiplier(f.assign(trailing_mean=0.0), target_fill=0.5))


def test_critical_ratio():
    assert critical_ratio(3, 1) == 0.75
    with pytest.raises(ValueError):
        critical_ratio(0, 0)
