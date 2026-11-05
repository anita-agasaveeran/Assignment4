import pandas as pd
import pytest

from winevalue.data import load_raw
from winevalue.features import QUALITY_INPUTS_V2, RANKER_INPUTS_V2, build_preprocessor
from winevalue.prepare import leakage_audit, prepare


@pytest.fixture(scope="module")
def prepared():
    return prepare(load_raw())       # without the anonymous-attribution step, for speed


def test_prepare_applies_phase2_decisions(prepared):
    d, log = prepared
    assert not d["title"].str.contains("barrel sample", case=False).any()
    assert not d["description"].duplicated().any()
    assert set(d["colour"].unique()) <= {"red", "white", "rosé", "sparkling", "fortified", "unmapped"}
    assert d.loc[d["title"].str.startswith("1912 Winemakers"), "vintage"].ge(2000).all()
    assert d["price"].max() <= 2500
    assert (log["rows affected"].fillna(0) >= 0).all()


def test_leakage_audit_passes(prepared):
    d, _ = prepared
    audit = leakage_audit(d, QUALITY_INPUTS_V2, RANKER_INPUTS_V2)
    assert (audit["result"] == "PASS").all(), audit


def test_preprocessor_fits_on_a_sample(prepared):
    d, _ = prepared
    s = d.sample(3000, random_state=0)
    X = build_preprocessor(with_price=True).fit_transform(s[RANKER_INPUTS_V2])
    assert X.shape[0] == 3000
