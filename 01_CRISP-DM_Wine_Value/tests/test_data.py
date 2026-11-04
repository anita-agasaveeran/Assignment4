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
