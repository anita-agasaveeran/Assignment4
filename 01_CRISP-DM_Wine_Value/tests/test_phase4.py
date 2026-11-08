import numpy as np
import pandas as pd
import pytest

from winevalue import config
from winevalue.clustering import choose_dm3, choose_k_seeds, matched_jaccard
from winevalue.cv import inner_groups, outer_split
from winevalue.descriptors import item_matrix, mine_rules, rule_stats_on
from winevalue.evaluate import meets_bsc1, meets_dm1
from winevalue.similarity import synthetic_copies, synthetic_recall


def _prep():
    rows = []
    for i, f in enumerate([0, 0, 1, 1, 2, 2, 3, 3, 4, 4, -1, -1, -1, -1]):
        rows.append({"fold": f, "is_lockbox": f == 2, "title": f"t{i}", "points": 85 + i % 5})
    df = pd.DataFrame(rows, index=pd.Index(range(100, 114), name="review_id"))
    df.loc[113, "title"] = "t6"            # an anonymous copy of a fold-3 title
    df.loc[112, "title"] = df.loc[111, "title"] = "anon-shared"
    return df


def test_outer_split_excludes_lockbox_heldout_and_attributed_anonymous():
    df = _prep()
    drop = {f: pd.Index([110]) for f in config.OUTER_FOLDS}
    train, test = outer_split(df, 3, drop)
    assert not train["is_lockbox"].any() and not test["is_lockbox"].any()
    assert set(train["fold"]) == {-1, 0, 1, 4} and 110 not in train.index
    assert set(test.index) == {107}          # 106's title "t6" also appears in training (anonymous copy): R-3 drops it
    with pytest.raises(ValueError):
        outer_split(df, config.LOCKBOX_FOLD, drop)


def test_inner_groups_keep_anonymous_titles_together():
    train, _ = outer_split(_prep(), 3, {f: pd.Index([]) for f in config.OUTER_FOLDS})
    g = inner_groups(train)
    assert set(g.unique()) <= {0, 1, 4}
    assert g[111] == g[112]                  # same anonymous title -> same inner fold
    assert (g[train["fold"] >= 0] == train.loc[train["fold"] >= 0, "fold"]).all()


def test_matched_jaccard_and_multi_split_rule():
    a = [["x", "y"], ["p", "q"]]
    assert matched_jaccard(a, a[::-1]).tolist() == [1.0, 1.0]
    rows = []
    for k, n_pass, share in [(6, 10, 0.05), (7, 8, 0.02), (8, 7, 0.02), (9, 10, 0.005)]:
        rows += [{"method": "nmf", "k": k, "split": i, "min J": 0.6 if i < n_pass else 0.1, "mean J": 0.7, "passes": i < n_pass,
                  "smallest share": share} for i in range(10)]
    row = choose_k_seeds(pd.DataFrame(rows)).iloc[0]
    assert row["k"] == 7 and row["passes rule"]          # 8 misses the seed bar, 9 misses the share bar
    t = pd.DataFrame({"passes rule": [True, True, False], "critic-disjoint mean J": [0.2, 0.3, 0.9], "name": list("abc")})
    assert choose_dm3(t)["name"] == "b"                  # the failed setting can't win on critic-disjoint stability
    assert choose_dm3(t.assign(**{"passes rule": False})) is None


def test_critic_disjoint_splits_share_no_fold_and_skip_anonymous():
    from winevalue.clustering import critic_disjoint_splits
    f = pd.Series([0, 1, 3, 4, -1, 0, 3])
    for a, b in critic_disjoint_splits(f):
        assert not (a & b).any() and not (a | b)[4]


def test_descriptor_items_and_rule_replication():
    df = pd.DataFrame({"note": ["Ripe cherries and oak.", "Lemon, lime and slate.", "Cherry and oak spice.",
                                "Limes and lemons.", "Plum and oak."] * 40,
                       "grape": ["Pinot Noir", "Riesling", "Pinot Noir", "Riesling", "Merlot"] * 40})
    it = item_matrix(df)
    assert it.loc[0, "d:cherry"] and it.loc[3, "d:lime"] and not it.loc[4, "d:cherry"]
    rules = mine_rules(it, min_support=0.1, min_lift=1.5)
    assert ((rules["antecedents"] == "cherry") & (rules["consequents"] == "Pinot Noir")).any()
    again = rule_stats_on(it, rules)
    assert np.allclose(again["lift"], rules["lift"])


def test_synthetic_recall_finds_light_edits():
    rng = np.random.default_rng(0)
    words = [f"w{i}" for i in range(400)]
    corpus = pd.Series([" ".join(rng.choice(words, 40)) for _ in range(60)], index=range(500, 560))
    syn = synthetic_copies(corpus, n=20, rate=(0.02, 0.04), seed=1)
    res = synthetic_recall(corpus, syn)
    assert res["positives"] > 0 and res["recall"] >= 0.9 and res["passes"]


def test_target_checks():
    t = pd.DataFrame({"MAE reduction": [0.12, 0.12], "MAE reduction LB": [0.06, 0.04], "within ±2 (≤$25)": [0.65, 0.65],
                      "within gain (pp)": [6.0, 6.0], "within gain LB (pp)": [1.0, 1.0]})
    assert meets_dm1(t).tolist() == [True, False]
    s = pd.DataFrame({"P@100": [0.6, 0.6], "lift (cycles)": [1.5, 1.3], "top-10% lift LB": [1.3, 1.3]})
    assert meets_bsc1(s).tolist() == [True, False]


def test_descriptor_plurals():
    import re
    from winevalue.descriptors import term_pattern
    for term, text in [("cherry", "black cherries"), ("peach", "ripe peaches"), ("plum", "plums"), ("black currant", "black currants"),
                       ("stone fruit", "stone fruits"), ("grass", "grasses"), ("cherry", "cherry")]:
        assert re.search(term_pattern(term), text), (term, text)
    assert not re.search(term_pattern("oak"), "oaky") and not re.search(term_pattern("rose"), "rosemary")


def test_select_rule_prefers_simpler_within_tolerance():
    from winevalue.evaluate import select
    t = pd.DataFrame({"model": ["ridge", "stack"] * 2, "MAE": [1.80, 1.795, 1.80, 1.795]})
    choice, _ = select(t, "model", "MAE", pd.Series([True] * 4), higher_is_better=False)
    assert choice == "ridge"                                   # stack is better by < 0.01 -> simpler wins
    choice, s = select(t, "model", "MAE", pd.Series([False, True, True, True]), higher_is_better=False)
    assert choice == "stack" and not s.loc["ridge", "eligible"]


def test_revised_profile_stopwords_keep_flavour_words():
    from winevalue.clustering import revised_stopwords
    st = set(revised_stopwords())
    assert {"cabernet", "pinot", "chardonnay", "superb", "simple"} <= st
    assert not {"black", "orange", "melon", "cherry", "lemon"} & st


def _stack_data(n=400, seed=0):
    rng = np.random.default_rng(seed)
    words = np.array(["cherry", "oak", "lemon", "tannin", "fresh", "ripe", "plum", "spice"])
    df = pd.DataFrame({"note": [" ".join(rng.choice(words, 8)) for _ in range(n)],
                       "points": rng.integers(82, 96, n).astype(float), "fold": rng.choice([0, 1, 3, -1], n),
                       "title": [f"t{i}" for i in range(n)]}, index=pd.Index(range(1000, 1000 + n), name="review_id"))
    return df


def test_oof_predict_never_uses_a_rows_own_target():
    """Changing one row's target changes predictions only for rows in OTHER inner folds, never its own OOF score."""
    from winevalue.cv import oof_predict
    df = _stack_data()
    g = inner_groups(df)

    def fp(fit, pred):                       # the mean target of the fit rows: anything that saw a row's target moves
        return np.full(len(pred), fit["points"].mean())
    base = oof_predict(df, g, fp)
    i = df.index[7]
    changed = oof_predict(df.assign(points=df["points"].where(df.index != i, 1000.0)), g, fp)
    assert changed[i] == base[i]
    assert changed[g == g[i]].equals(base[g == g[i]])          # its whole inner fold is untouched
    assert (changed[g != g[i]] != base[g != g[i]]).all()


def test_inner_groups_place_anonymous_notes_with_their_top_guess_writer():
    df = _stack_data()
    anon = df.index[df["fold"].eq(-1)]
    top = pd.Series(3, index=anon)
    top.iloc[0] = config.LOCKBOX_FOLD        # a top guess outside the inner folds falls back to the random placement
    g = inner_groups(df, top_fold=top)
    assert (g[anon[1:]] == 3).all()
    assert g[anon[0]] in {0, 1, 3}
    assert (g[df["fold"] >= 0] == df.loc[df["fold"] >= 0, "fold"]).all()


def test_calibration_recovers_a_shift_and_slope_and_fits_only_masked_rows():
    from winevalue.scoring import fit_calibration
    s = pd.Series(np.arange(10.0))
    a, b = fit_calibration(s, 2 + 0.5 * s)
    assert np.isclose(a, 2) and np.isclose(b, 0.5)
    y = (2 + 0.5 * s).where(s < 5, 99.0)
    a, b = fit_calibration(s, y, s < 5)
    assert np.isclose(a, 2) and np.isclose(b, 0.5)


def test_select_inner_uses_inner_order_then_requires_outer_targets():
    from winevalue.evaluate import select_inner
    inner = pd.DataFrame({"fold": [0, 3], "stack": [1.60, 1.60], "ridge": [1.70, 1.70], "calibrated ridge (all OOF)": [1.605, 1.605]})
    outer = pd.DataFrame({"model": ["stack", "ridge", "calibrated ridge (all OOF)"] * 4})
    ok = pd.Series([True] * 12)
    assert select_inner(inner, outer, ok)[0] == "calibrated ridge (all OOF)"    # simpler, within 0.01 of the best
    fails = ok.copy(); fails[2] = False                                          # calibrated ridge misses a fold
    assert select_inner(inner, outer, fails)[0] == "stack"


def test_critic_fixed_effects_recover_a_planted_gap_despite_regional_beats():
    from winevalue.insights import critic_fixed_effects
    rng = np.random.default_rng(1)
    rows = []
    cells = {"A": 2.0, "B": -2.0}                       # A is a better cell; critic x mostly covers it
    for c, shares in {"x": {"A": 0.9, "B": 0.1}, "y": {"A": 0.1, "B": 0.9}}.items():
        for _ in range(4000):
            cell = "A" if rng.random() < shares["A"] else "B"
            rows.append({"critic": c, "variety": cell, "country": "US", "winery_key": str(rng.integers(500)),
                         "points": 88 + cells[cell] + (1.0 if c == "y" else 0.0) + rng.normal(0, 1)})
    out = critic_fixed_effects(pd.DataFrame(rows)).set_index("critic")
    assert abs((out.loc["y", "effect"] - out.loc["x", "effect"]) - 1.0) < 0.1   # raw means would give the wrong sign
    assert out.attrs["rows"] == 8000


def test_prune_rules_drops_rules_no_better_than_a_parent():
    from winevalue.descriptors import prune_rules
    r = pd.DataFrame({"antecedents": ["oak", "oak + pineapple", "oak + vanilla"], "consequents": ["Chardonnay"] * 3, "lift": [3.0, 5.0, 2.5]})
    assert prune_rules(r)["antecedents"].tolist() == ["oak", "oak + pineapple"]
