import pandas as pd

from winevalue.data import load_raw
from winevalue.splits import N_FOLDS, assign_folds, critic_folds


def test_critic_folds_deterministic_and_balanced():
    names = pd.Series(["a"] * 50 + ["b"] * 30 + ["c"] * 20 + ["d"] * 20 + [None] * 5)
    m1, lb1 = critic_folds(names, n_folds=2, min_lockbox_critics=2)
    m2, lb2 = critic_folds(names, n_folds=2, min_lockbox_critics=2)
    assert (m1, lb1) == (m2, lb2)
    # largest-first greedy: a(50)->0, b(30)->1, c(20)->1, d(20)->0
    assert m1 == {"a": 0, "b": 1, "c": 1, "d": 0}
    assert sorted(pd.Series(names.dropna().map(m1)).value_counts()) == [50, 70]


def test_every_critic_in_exactly_one_fold_and_anonymous_excluded():
    df = load_raw()
    folds = assign_folds(df)
    assert set(folds.unique()) == set(range(N_FOLDS)) | {-1}
    assert (folds[df["taster_name"].isna()] == -1).all()
    per_critic = pd.DataFrame({"t": df["taster_name"], "f": folds}).dropna().groupby("t")["f"].nunique()
    assert (per_critic == 1).all()


def test_lockbox_has_several_critics():
    df = load_raw()
    mapping, lockbox = critic_folds(df["taster_name"])
    assert sum(f == lockbox for f in mapping.values()) >= 3
