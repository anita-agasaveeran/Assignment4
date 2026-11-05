import pandas as pd

from winevalue.grapes import grape_canonical, wine_colour
from winevalue.text_audit import flag_score_leaks, is_barrel_sample, strip_leaks


def test_score_leaks_detected_and_stripped():
    d = pd.Series(["90-92. Barrel sample. Ripe fruit.", "88—90 Barrel sample.", "98-100 Barrel sample.",
                   "Rated 92 points last year; for an under-$15 red.", "A 90-point wine, a Best Buy at 10 bucks.",
                   "14-15% alcohol, aged 18-24 months.", "Crisp lemon."])
    f = flag_score_leaks(d)
    assert f["score_range_at_start"].tolist() == [True, True, True, False, False, False, False]
    assert f["explicit_points"].tolist() == [False, False, False, True, True, False, False]
    assert f["verdict_label"].tolist() == [False, False, False, False, True, False, False]
    assert f["currency_amount"].tolist() == [False, False, False, True, True, False, False]
    s = strip_leaks(d)
    assert not any(x in s[0] + s[1] + s[2] + s[3] + s[4] for x in ["92", "90", "100", "$15", "Best Buy", "10 bucks"])
    assert s[5] == "14-15% alcohol, aged 18-24 months." and s[6] == "Crisp lemon."
    assert is_barrel_sample(pd.Series(["X 2015 Barrel Sample", "Y 2015"]), pd.Series(["a", "b"])).tolist() == [True, False]


def test_synonyms_and_colours():
    v = pd.Series(["Shiraz", "Pinot Grigio", "Syrah", "Red Blend", "Champagne Blend", "Rosato", "Port", "Mystery Grape",
                   "Tempranillo Blend", "Grenache-Syrah", "Pinot Noir", "Chardonnay", "Turbiana"])
    t = pd.Series([None] * 10 + ["Domaine X 2016 Rosé of Pinot Noir (Sonoma)", "Maison Y NV Brut (Champagne)", None])
    assert grape_canonical(v).tolist()[:3] == ["Syrah", "Pinot Gris", "Syrah"] and grape_canonical(v).iloc[12] == "Verdicchio"
    assert wine_colour(v, t).tolist() == ["red", "white", "red", "red", "sparkling", "rosé", "fortified", "unmapped",
                                          "red", "red", "rosé", "sparkling", "white"]
