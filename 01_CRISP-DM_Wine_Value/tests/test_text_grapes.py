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


def test_colour_override_ignores_winery_and_vineyard_names():
    v = pd.Series(["Malbec", "Sangiovese Grosso", "Nebbiolo", "Chardonnay", "Tempranillo", "Touriga Nacional",
                   "Pinot Noir", "Port", "Muscat Canelli", "Black Muscat"])
    t = pd.Series(["Château du Port 2012 Prestige (Cahors)", "Cava d'Onice 2011  Brunello di Montalcino",
                   "Fratelli Dardi 2010 Dardi Le Rose  (Barolo)", "Blair 2013 Roger Rose Vineyard Chardonnay (Arroyo Seco)",
                   "Bodega X 2012 Tinto Fino (Ribera del Duero)", "Rui Roboredo Madeira 2013 Red (Douro)",
                   "Sokol 2015 Rosé of Pinot Noir (Oregon)", "Graham's NV Six Grapes Reserve  (Port)", "Y 2015 Canelli (Napa)", "Z 2015 (CA)"])
    w = pd.Series(["Château du Port", "Cava d'Onice", "Fratelli Dardi", "Blair", "Bodega X", "Rui Roboredo Madeira",
                   "Sokol", "Graham's", "Y", "Z"])
    assert wine_colour(v, t, w).tolist() == ["red", "red", "red", "white", "red", "red", "rosé", "fortified", "white", "red"]


def test_widened_leak_patterns_and_colour_amendments():
    d = pd.Series(["Two Best Buys in a row.", "An Editor's Choice.", "A steal for six bucks.", "This loses a few points for the finish.",
                   "Ripe and round, at the price a winner."])
    s = strip_leaks(d)
    assert "Best Buys" not in s[0] and "Editor" not in s[1] and "six bucks" not in s[2] and "points" not in s[3]
    assert s[4] == "Ripe and round, at the price a winner."        # price-relative wording is a documented residual
    c = strip_leaks(pd.Series(["Too ripe to score higher.", "Alcohol rated at 12.5%."]))
    assert "score" not in c[0] and c[1] == "Alcohol rated at 12.5%."
    v = pd.Series(["Zinfandel", "Pinot Noir", "Bordeaux-style Red Blend", "Merlot", "Chardonnay", "Syrah"])
    t = pd.Series(["Thurston Wolfe 2010 Port Zinfandel (Washington)", "Analemma 2012 Blanc de Noir Pinot Noir (Columbia Gorge)",
                   "Château X 2014 Clairet (Bordeaux Clairet)", "Château La Rose de Pez 2010 (Saint-Estèphe)",
                   "Y 2014 Sparkling Hill Vineyard Chardonnay (Okanagan)", "Z 2012 Tawny Ridge Syrah (Paso Robles)"])
    w = pd.Series(["Thurston Wolfe", "Analemma", "Château X", "Château La Rose de Pez", "Y", "Z"])
    assert wine_colour(v, t, w).tolist() == ["fortified", "white", "rosé", "red", "white", "red"]


def test_blanc_de_noir_yields_to_sparkling_cues():
    # Phase 3 revision 3 (critic round 2 N1): titles taken from the rows the revision-2 rule mislabelled
    t = pd.Series(["Simonnet-Febvre NV Brut P100 Blanc de Noirs  (Crémant de Bourgogne)",
                   "Schramsberg 2004 Brut Late Disgorged Blanc de Noir Pinot Noir (North Coast)",
                   "Le Marchesine 2012 Blanc de Noirs Pinot Nero (Franciacorta)",
                   "Dão Sul 2010 Cabriz Blanc de Noirs Bruto Touriga Nacional (Dão)",
                   "Gloria Ferrer NV Blanc de Noirs Sparkling (Carneros)",
                   "Château Frank 2008 Blanc de Noirs  (Finger Lakes)",
                   "Inman Family 2012 OGV Estate Blanc de Noir Pinot Noir (Russian River Valley)",
                   "Paul Anheuser 2015 Blanc de Noir Pinot Noir (Nahe)",
                   "Château de Gaudou 2012 Blanc de Noir Malbec (Vin de France)"])
    w = pd.Series(["Simonnet-Febvre", "Schramsberg", "Le Marchesine", "Dão Sul", "Gloria Ferrer", "Château Frank",
                   "Inman Family", "Paul Anheuser", "Château de Gaudou"])
    v = pd.Series(["Pinot Noir", "Pinot Noir", "Pinot Nero", "Touriga Nacional", "Sparkling Blend", "Champagne Blend",
                   "Pinot Noir", "Pinot Noir", "Malbec"])
    n = pd.Series(["", "", "", "", "", "", "Spent three years on the yeast, made in a traditional style.",
                   "Dry and crisp, with red-apple fruit.", "This dry white wine, made from red Malbec grapes."])
    assert wine_colour(v, t, w, n).tolist() == ["sparkling"] * 7 + ["white", "white"]


def test_round2_text_fixes():
    from winevalue.prepare import _fix_mojibake
    from winevalue.text_audit import strict_price_mask
    # N2: correct text with "Â" is left alone; genuine mojibake is repaired
    assert _fix_mojibake("10 Ans d'Âge") == "10 Ans d'Âge"
    assert _fix_mojibake("Âme de la Vigne") == "Âme de la Vigne"
    assert _fix_mojibake("crÃ¨me") == "crème"
    # N3: descriptive "a point" kept; verdict "a point" and "more points" removed; "bucks the trend" is not a price
    s = strip_leaks(pd.Series(["A point of crisp acidity.", "It loses a point for heat.", "Would earn more points.",
                               "This one bucks the trend.", "For ten bucks you get a lot."]))
    assert "point of crisp" in s[0] and "point" not in s[1] and "points" not in s[2]
    assert "bucks the trend" in s[3] and "_price_" in s[4]
    # N9: the strict DM1b mask removes the placeholder and price-relative wording
    m = strict_price_mask(pd.Series(["Real bang for the buck at this price point; _price_ well spent."]))
    assert m[0] == "Real ; well spent."
