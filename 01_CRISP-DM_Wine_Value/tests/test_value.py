import numpy as np
import pytest

from winevalue.models import mask_terms
from winevalue.splits import drop_titles_seen_in_training
from winevalue.value import simulate_cycles


def test_simulate_cycles_perfect_and_random_rules():
    rng = np.random.default_rng(0)
    is_value = (rng.random(2000) < 0.2).astype(float)
    res = simulate_cycles({"oracle": is_value, "flat": np.zeros(2000)}, is_value,
                          n_candidates=500, k=50, n_cycles=30, seed=1)
    assert (res["oracle"] == 1.0).all()
    assert res["flat"].mean() == pytest.approx(0.2, abs=0.05)
    with pytest.raises(ValueError):
        simulate_cycles({"x": is_value}, is_value, n_candidates=5000, k=10)


def test_mask_terms_whole_words_only():
    import pandas as pd
    out = mask_terms(pd.Series(["A superb wine, finely made. Drink now.", "Superbly simple"]),
                     ["superb", "fine", "drink now", "simple"])
    assert out[0].count("_masked_") == 2 and "finely" in out[0]
    assert "Superbly" in out[1] and out[1].count("_masked_") == 1


def test_drop_titles_seen_in_training():
    import pandas as pd
    tr = pd.DataFrame({"title": ["A", "B"]}); te = pd.DataFrame({"title": ["B", "C"]})
    assert drop_titles_seen_in_training(te, tr)["title"].tolist() == ["C"]
