import pandas as pd

from winevalue.similarity import (content_word_difference, detect_near_duplicates, is_true_duplicate,
                                  synthetic_copies)

NOTE = "Ripe black cherry and plum aromas lead to a supple palate with soft tannins and a long savory finish of spice."


def test_detector_finds_a_near_copy_and_ignores_unrelated_notes():
    texts = pd.Series({1: NOTE, 2: NOTE.replace("plum", "cassis"), 3: "Crisp lemon zest, wet stone and a bracing saline finish here."})
    found = detect_near_duplicates(texts)
    assert set(map(tuple, found[["i", "j"]].to_numpy())) == {(1, 2)}


def test_synthetic_copies_are_reproducible_and_edit_some_words():
    texts = pd.Series([NOTE + f" Note {i}." for i in range(50)])
    a, b = synthetic_copies(texts, n=20, seed=1), synthetic_copies(texts, n=20, seed=1)
    assert a.equals(b) and (a["jaccard"] < 1).all() and a["jaccard"].median() > 0.4


def test_labelling_rule():
    base = {"winery": "Huia", "title": "Huia 2012 Sauvignon Blanc (Marlborough)", "variety": "Sauvignon Blanc", "vintage": 2012}
    a = pd.Series({**base, "description": NOTE})
    recycled = pd.Series({"winery": "Wairau River", "title": "Wairau River 2012 Sauvignon Blanc", "variety": "Sauvignon Blanc",
                          "vintage": 2012, "description": NOTE.replace("Ripe", "Bright")})
    different = pd.Series({"winery": "Other", "title": "Other 2015 Pinot Noir", "variety": "Pinot Noir", "vintage": 2015,
                           "description": "Ripe black cherry aromas lead to a firm, tannic palate needing time; earthy, with dried herbs and leather."})
    assert content_word_difference(NOTE, NOTE.replace("Ripe", "Bright")) == 2      # sentence-initial words DO count
    assert content_word_difference(NOTE + " From Huia.", NOTE + " From Wairau.") == 0   # mid-sentence names don't
    assert is_true_duplicate(a, recycled) and not is_true_duplicate(a, different)
    # self-contained: same answer with or without a 'vintage' field
    assert is_true_duplicate(a.drop("vintage"), recycled.drop("vintage")) == is_true_duplicate(a, recycled)
