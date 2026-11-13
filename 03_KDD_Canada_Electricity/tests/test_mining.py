"""Unit tests for the mining code on synthetic data (they never touch the sealed months)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import numpy as np
import pandas as pd

from kddenergy import config as c
from kddenergy import forecast as F
from kddenergy import mining as M


def test_pelt_finds_a_clear_mean_shift_and_is_stable():
    rng = np.random.default_rng(0)
    x = np.r_[np.zeros(60), np.full(48, 0.05)] + rng.normal(0, 0.005, 108)
    bk = M.pelt(x)
    ch = M.primary_change(x, bk)
    assert ch is not None and abs(ch["index"] - 60) <= 2 and ch["shift"] > 0
    assert M.bootstrap_stability(x, bk, ch["index"], reps=30) >= 0.9


def test_pelt_finds_nothing_in_noise_and_min_shift_applies():
    rng = np.random.default_rng(1)
    assert M.pelt(rng.normal(0, 0.01, 108)) == []
    x = np.r_[np.zeros(54), np.full(54, 0.005)] + rng.normal(0, 0.0005, 108)   # real but < 1 pp shift
    assert M.primary_change(x, M.pelt(x)) is None


def test_persistence_margin_rule():
    # mid = 0.75; margin = 0.005
    assert M.persistence(0.9, pre_mean=0.5, post_mean=1.0, last_mean=1.0)
    assert not M.persistence(0.752, pre_mean=0.5, post_mean=1.0, last_mean=1.0)    # beyond mid, but not by the margin
    assert not M.persistence(0.9, pre_mean=0.5, post_mean=1.0, last_mean=0.6)      # reversed within development
    assert M.persistence(0.40, pre_mean=0.60, post_mean=0.45, last_mean=0.44)      # falling shares work too


def test_trim_stability_is_high_for_a_clear_step_and_nan_when_cp_trimmed_away():
    rng = np.random.default_rng(3)
    x = np.r_[np.zeros(60), np.full(48, 0.05)] + rng.normal(0, 0.005, 108)
    assert M.trim_stability(x, 60) >= 0.9
    assert np.isnan(M.trim_stability(x, 1))


def test_attribution_burning_vs_denominator():
    base = {"combustion pre (GWh/mo)": 100.0, "total generation pre (GWh/mo)": 1000.0}
    burn = {**base, "combustion post (GWh/mo)": 80.0, "total generation post (GWh/mo)": 1000.0}
    deno = {**base, "combustion post (GWh/mo)": 100.0, "total generation post (GWh/mo)": 1250.0}
    assert M.attribution(burn) == (1.0, "burning")
    assert M.attribution(deno)[1] == "denominator"


def test_event_level_credit_caps_one_flag_per_event():
    ev = pd.DataFrame({"geography": ["A", "B"], "start_month": ["2020-01", "2020-06"], "end_month": ["2020-12", "2020-06"]})
    flags = [("A", "2020-03"), ("A", "2020-05"), ("A", "2020-07"), ("B", "2020-07")]
    assert M.event_level_credit(flags, ev) == 2
    r = M.score_flags(flags, {("A", f"2020-{i:02d}") for i in range(1, 13)} | {("B", "2020-07")}, ev,
                      [("A", f"2020-{i:02d}") for i in range(1, 13)])
    assert r["precision"] == 1.0 and r["event_level_precision"] == 0.5


def test_permutation_null_is_stratified_and_calibrated():
    eligible = [(g, str(p)) for g in "AB" for p in pd.period_range("2016-01", "2024-12", freq="M")]
    ev = pd.DataFrame({"geography": ["A", "A", "B"], "start_month": ["2017-03", "2019-08", "2022-02"],
                       "end_month": ["2017-03", "2019-08", "2022-02"]})
    hit = [("A", "2017-03"), ("A", "2019-08"), ("B", "2022-02")]
    p_hit, null = M.permutation_p(hit, ev, eligible, reps=300)
    assert p_hit < 0.05 and null.mean() < 0.2
    miss = [("A", "2020-11"), ("B", "2016-05"), ("B", "2023-09")]
    assert M.permutation_p(miss, ev, eligible, reps=300)[0] > 0.5


def test_ari_one_move_and_relabel():
    lab = np.array([0, 0, 0, 1, 1, 1, 2, 2, 2, 2, 0, 1, 2])
    s = M.ari_if_one_moves(lab)
    assert 0.5 < s["min"] < s["max"] < 1
    assert (M.relabel_like(lab, (lab + 1) % 3) == lab).all()


def test_flag_scoring_precision_lift_recall():
    events = pd.DataFrame({"geography": ["A"], "start_month": ["2020-04"], "end_month": ["2020-04"]})
    covered = {("A", m) for m in ["2020-03", "2020-04", "2020-05"]}
    eligible = [("A", f"2020-{i:02d}") for i in range(1, 13)]
    r = M.score_flags([("A", "2020-05"), ("A", "2020-10")], covered, events, eligible)
    assert r["precision"] == 0.5 and r["base_rate"] == 0.25 and r["lift"] == 2 and r["recall"] == 1


def test_eligible_mask_drops_registered_breaks():
    idx = pd.MultiIndex.from_tuples([("Nunavut", "2024-09"), ("Nunavut", "2024-10"), ("Yukon", "2024-10"),
                                     ("Newfoundland and Labrador", "2021-02"), ("Newfoundland and Labrador", "2021-04")],
                                    names=["geography", "month"])
    assert M.eligible_mask(idx).tolist() == [True, False, True, False, True]


def test_sigma_methods():
    x = np.r_[np.zeros(50), np.ones(50)]
    assert M.noise_sigma(x, "mad_diff") == 0 and M.noise_sigma(x, "sd") == 0.5


def test_forecasters_on_a_seasonal_series():
    idx = pd.period_range("2010-01", "2020-12", freq="M")
    y = pd.Series(100 + 10 * np.sin(2 * np.pi * idx.month / 12), index=idx)
    A = pd.DataFrame({"X": y})
    rows = F.backtest(A, ["2019-12"], geos=["X"])
    r = rows[0]
    assert np.allclose(r["snaive"], r["y"]) and np.allclose(r["avg3_growth"], r["y"])
    assert F.wape(rows, "ets_damped_log") < 1.0


def test_backtest_truncates_at_data_end():
    idx = pd.period_range("2016-01", "2026-08", freq="M")
    A = pd.DataFrame({"X": np.linspace(100, 120, len(idx))}, index=idx)
    r = F.backtest(A, ["2025-12"], geos=["X"])[0]
    assert len(r["y"]) == 8 and r["months"][-1] == "2026-08"
