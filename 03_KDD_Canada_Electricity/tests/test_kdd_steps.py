import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import numpy as np
import pandas as pd
import pytest

from kddenergy import config as c
from kddenergy.preprocess import catalogue_months, clean, integration_checks, load_event_catalogue
from kddenergy.selection import build_panel
from kddenergy.transform import add_features, calendar_climatology, cluster_features, deseasonalize, robust_z


@pytest.fixture(scope="module")
def panel():
    return clean(build_panel())[0]


def test_selection_is_sealed_consistent_era_and_excludes_canada(panel):
    m = panel.index.get_level_values("month")
    assert m.min() == c.CONSISTENT_START and m.max() == c.DISCOVERY_END
    assert set(panel.index.get_level_values("geography")) == set(c.GEOS)
    assert len(panel) == 13 * 108


def test_clean_panel_has_no_missing_and_integrates(panel):
    assert not panel.isna().any().any()
    chk = integration_checks(panel)
    assert chk["max |generation table - flows table|"] == 0
    assert chk["geo-months with |availability identity residual| > 1"] == 1     # BC 2019-02, flagged not fixed
    assert chk["max |receipt parts - total receipts|"] == 0


def test_territories_are_isolated_grids(panel):
    for t in c.TERRITORIES:
        assert (panel.loc[t, ["receipts", "deliveries"]] == 0).all().all()
        assert np.allclose(panel.loc[t, "gen_total"], panel.loc[t, "availability"])


def test_shares_are_fractions(panel):
    f = add_features(panel)
    s = f[["hydro_share", "nuclear_share", "windsolar_share", "combustion_share"]].sum(axis=1)
    assert ((s > 0.95) & (s < 1.05)).mean() > 0.99


def test_cluster_features_are_calendar_balanced(panel):
    # duplicating Jan-Aug of a window must not change the balanced features
    a = cluster_features(panel, "2023-01", "2023-12")
    m = panel.index.get_level_values("month")
    year = panel[m.str[:4] == "2023"]
    dup = panel[m.isin([f"2023-{i:02d}" for i in range(1, 9)])].copy()
    dup.index = pd.MultiIndex.from_arrays([dup.index.get_level_values(0),
                                           dup.index.get_level_values(1).str.replace("2023", "2022")], names=dup.index.names)
    both = pd.concat([year, dup]).sort_index()
    b = cluster_features(both, "2022-01", "2023-12")
    assert np.allclose(a.to_numpy(), b.to_numpy())


def test_deseasonalize_removes_climatology(panel):
    s = add_features(panel)["combustion_share"]
    d = deseasonalize(s, calendar_climatology(s))
    assert np.allclose(calendar_climatology(d).to_numpy(), 0, atol=1e-12)


def test_robust_z_handles_constant_series():
    assert np.all(robust_z(np.ones(5)) == 0)


def test_event_catalogue_is_frozen_and_expandable():
    cat = load_event_catalogue()          # raises if the file changed after freezing
    assert (cat["period"] == "discovery").all() and cat["end_month"].max() <= c.DISCOVERY_END
    months = catalogue_months(cat.iloc[[0]], window=1)
    assert ("Alberta", "2016-04") in months and ("Alberta", "2016-07") in months and len(months) == 4


def test_stl_z_scale_uses_only_months_up_to_scale_end(panel):
    from kddenergy.transform import stl_z_table
    f = add_features(panel)
    z1 = stl_z_table(f, scale_end="2024-12")
    # corrupting a month AFTER scale_end in a copy must not change z of earlier months beyond the STL refit itself:
    # with scale_end equal to the last month, scale comes from all months, so compare against a shorter scale window
    z2 = stl_z_table(f, scale_end="2020-12")
    assert z1.shape == z2.shape and not np.allclose(z1.to_numpy(), z2.to_numpy())
    med = z2.xs("Ontario", level="geography").loc[:"2020-12", "log_availability"]
    assert abs(np.median(med)) < 1e-9 and abs(1.4826 * np.median(np.abs(med)) - 1) < 1e-9


def test_onesided_stl_uses_no_future_data(panel):
    from kddenergy.transform import stl_z_onesided
    f = add_features(panel.loc[["Yukon", "Ontario"]])
    z = stl_z_onesided(f, ["2024-11"], scale_end="2023-12")
    g = f.copy(); g.loc[("Ontario", "2024-12"), "log_availability"] += 5   # change the future
    assert np.allclose(z.to_numpy(), stl_z_onesided(g, ["2024-11"], scale_end="2023-12").to_numpy())
