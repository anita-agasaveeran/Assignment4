import pytest

from winevalue.metrics import mae, precision_at_k, within


def test_mae_and_within():
    assert mae([88, 90], [87, 93]) == 2.0
    assert within([88, 90, 92], [87, 93, 92], tol=2) == pytest.approx(2 / 3)


def test_precision_at_k():
    assert precision_at_k([0.9, 0.1, 0.5, 0.7], [1, 1, 0, 1], k=2) == 1.0
    assert precision_at_k([0.9, 0.1, 0.5, 0.7], [1, 1, 0, 1], k=3) == pytest.approx(2 / 3)
    with pytest.raises(ValueError):
        precision_at_k([1], [1], k=2)


def test_precision_at_k_random_ties():
    import numpy as np
    scores, rel = [1, 1, 1, 1], [1, 0, 1, 0]
    assert precision_at_k(scores, rel, k=2) == 0.5          # stable: first two
    vals = {precision_at_k(scores, rel, k=1, rng=np.random.default_rng(s)) for s in range(20)}
    assert vals == {0.0, 1.0}                               # random tie order varies


def test_cluster_bootstrap_lower_bound_below_estimate():
    import numpy as np
    from winevalue.metrics import cluster_bootstrap
    x = np.random.default_rng(0).normal(1.0, 1.0, 2000)
    res = cluster_bootstrap(lambda i: x[i].mean(), clusters=np.arange(2000) // 4, n_boot=200)
    assert res["lower_bound"] < res["estimate"] and res["lower_bound"] > 0.9
