import pandas as pd
import pytest

from winevalue.data import EXPECTED_COLUMNS, extract_vintage, load_raw


def test_load_raw_schema():
    df = load_raw()
    assert len(df) == 129_971
    assert set(df.columns) == set(EXPECTED_COLUMNS)
    assert df.index.name == "review_id" and df.index.is_unique


def test_load_raw_rejects_wrong_schema(tmp_path):
    bad = tmp_path / "bad.csv"
    bad.write_text(",a,b\n0,1,2\n")
    with pytest.raises(ValueError, match="Schema mismatch"):
        load_raw(bad)


def test_extract_vintage():
    titles = pd.Series(["Nicosia 2013 Vulkà Bianco  (Etna)", "Krug NV Brut (Champagne)",
                        "Winery 1999 Reserve", "Cuvée 2050 (Future)"])
    out = extract_vintage(titles)
    assert out.iloc[0] == 2013 and pd.isna(out.iloc[1]) and out.iloc[2] == 1999 and pd.isna(out.iloc[3])


def test_extract_vintage_strips_winery_and_takes_first_year():
    titles = pd.Series(["1912 Winemakers 2011 Vinhas Velhas Branco White (Douro)",
                        "Guidi 1929 2012 Aurea Riserva  (Vernaccia di San Gimignano)",
                        "Pascal Aufranc 2011 Vignes de 1939  (Chénas)",
                        "Gérard Bertrand 1945 Legend Vintage  (Rivesaltes)",
                        "Krug NV Brut (Champagne)", "Alvear NV Solera 1927 Pedro Ximénez (Montilla-Moriles)",
                        "Arthur Metz NV 1904 Brut (Crémant d'Alsace)"])
    wineries = pd.Series(["1912 Winemakers", "Guidi 1929", "Pascal Aufranc", "Gérard Bertrand", "Krug", "Alvear", "Arthur Metz"])
    out = extract_vintage(titles, wineries)
    assert out.iloc[:4].tolist() == [2011, 2012, 2011, 1945] and out.iloc[4:].isna().all()
    assert extract_vintage(titles).iloc[0] == 1912          # Phase 1 behaviour unchanged without winery
