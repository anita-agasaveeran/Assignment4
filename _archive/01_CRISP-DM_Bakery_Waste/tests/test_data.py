import pandas as pd
import pytest

from bakery.data import EXPECTED_COLUMNS, load_raw


def test_load_raw_schema_and_types():
    df = load_raw()
    assert list(df.columns) == EXPECTED_COLUMNS
    assert len(df) == 19_321
    assert pd.api.types.is_datetime64_any_dtype(df["Date"])
    assert df["Weekend"].dtype == bool
    assert df["Festival"].isna().sum() == 0
    assert df["Promotion_Type"].isna().sum() == 0


def test_load_raw_untyped_keeps_original_values():
    df = load_raw(typed=False)
    assert set(df["Weekend"].unique()) == {"Yes", "No"}


def test_load_raw_rejects_wrong_schema(tmp_path):
    bad = tmp_path / "bad.csv"
    bad.write_text("a,b\n1,2\n")
    with pytest.raises(ValueError, match="Schema mismatch"):
        load_raw(bad)


def test_fresh_products_scope():
    from bakery.data import fresh_products
    fresh = fresh_products(load_raw())
    assert len(fresh) == 22
    assert "Chocolate Cake" in fresh and "Honey" not in fresh
