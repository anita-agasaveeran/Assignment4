import numpy as np
import pandas as pd
import pytest

from winevalue.models import mask_evaluative
from winevalue.rules import SIMPLE_RULES, simple_rule_scores
from winevalue.value import cluster_bootstrap_lift, precision_top_frac, simulate_cycles


def test_cycles_do_not_depend_on_rule_set():
    rng = np.random.default_rng(0)
    v = (rng.random(3000) < 0.2).astype(float)
    a = rng.random(3000)
    r1 = simulate_cycles({"a": a}, v, 500, 50, n_cycles=20, seed=7)
    r2 = simulate_cycles({"z": rng.random(3000), "a": a, "flat": np.zeros(3000)}, v, 500, 50, n_cycles=20, seed=7)
    assert np.allclose(r1["a"], r2["a"])
    # a heavily tied rule (like price) is also unaffected by its neighbours
    tied = np.round(rng.random(3000) * 3)
    t1 = simulate_cycles({"price": tied}, v, 500, 50, n_cycles=20, seed=7)
    t2 = simulate_cycles({"x": a, "price": tied}, v, 500, 50, n_cycles=20, seed=7)
    assert np.allclose(t1["price"], t2["price"])


def test_simple_rule_scores_cover_frozen_set():
    tr = pd.DataFrame({"winery": ["W1", "W1", "W2"], "province": ["P", "P", "Q"], "variety": ["V"] * 3,
                       "country": ["C"] * 3, "points": [92, 90, 84], "price": [20.0, 22.0, 15.0]})
    pool = pd.DataFrame({"winery": ["W1", "W3"], "province": ["P", "Q"], "variety": ["V", "V"],
                         "country": ["C", "C"], "price": [18.0, 25.0]})
    sc = simple_rule_scores(tr, pool)
    assert tuple(sc) == SIMPLE_RULES
    assert sc["winery track record"][0] > sc["winery track record"][1]   # known good winery vs unseen
    assert sc["winery track record, then price"][0] > sc["winery track record, then price"][1]


def test_bootstrap_lift_detects_better_rule():
    rng = np.random.default_rng(1)
    v = (rng.random(5000) < 0.2).astype(float)
    good, bad = v + rng.normal(0, 0.5, 5000), rng.random(5000)
    res = cluster_bootstrap_lift(good, bad, v, clusters=rng.integers(0, 800, 5000), n_boot=200, seed=2)
    assert res["lift"] > 2 and res["lower_bound"] > 1.5
    assert precision_top_frac(v, v, 0.1) == 1.0


def test_mask_evaluative_drink_windows_and_words():
    out = mask_evaluative(pd.Series(["Elegant and balanced. Drink 2018–2025.", "Fine tannins; drink from 2020"]))
    assert "2018" not in out[0] and "Elegant" not in out[0] and "balanced" not in out[0]
    assert "Fine tannins" in out[1] and "2020" not in out[1]
