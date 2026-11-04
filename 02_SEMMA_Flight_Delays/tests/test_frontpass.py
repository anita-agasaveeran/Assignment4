import numpy as np
import pandas as pd
import pytest

from flightdelay import config
from flightdelay.data import assert_no_test_targets, period
from flightdelay.features import (DAY_BEFORE_FEATURES, SCHEDULE_FEATURES, known_by_cutoff,
                                  previous_day_rates, schedule_features)


def _toy():
    return pd.DataFrame({
        "flight_date": pd.to_datetime(["2025-01-01"] * 4 + ["2025-01-02"] * 2),
        "airline_code": ["AA", "AA", "HA", "AA", "AA", "AS"], "flight_number": [1, 2, 3, 4, 5, 6],
        "origin": ["A", "A", "B", "A", "A", "B"], "dest": ["B", "B", "A", "B", "B", "A"],
        "sched_dep_time": [800, 1500, 2300, 1000, 900, 900], "sched_arr_time": [1000, 1900, 600, 1200, 1100, 1100],
        "distance": 500, "sched_elapsed_time": 120, "day_of_week": 3, "disrupted": [1, 1, 1, 0, 0, 0]})


def test_partition_is_contiguous_and_ordered():
    assert config.TRAIN_END < config.VALID_START <= config.VALID_END < config.TEST_START
    s = pd.Series(pd.to_datetime(["2025-06-01", "2026-02-01", "2026-07-01", "2024-12-31"]))
    assert period(s).tolist() == ["train", "valid", "test", "outside"]


def test_cutoff_excludes_late_and_red_eye_flights():
    d = _toy()
    assert known_by_cutoff(d).tolist() == [True, False, False, True, True, True]


def test_previous_day_rates_use_only_flights_known_by_cutoff():
    out = previous_day_rates(_toy())
    day2 = out[out.flight_date == "2025-01-02"]
    assert day2["origin_prev_day"].iloc[0] == 0.5     # flights 1 (late=1) and 4 (0); flight 2 lands after 17:00
    assert out.loc[out.flight_date == "2025-01-01", "origin_prev_day"].isna().all()


def test_carrier_group_maps_ha_to_as():
    assert set(schedule_features(_toy())["carrier"]) == {"AA", "AS"}


def test_seal_guard():
    ok = pd.DataFrame({"flight_date": pd.to_datetime(["2026-04-30"])})
    assert_no_test_targets(ok)
    with pytest.raises(ValueError):
        assert_no_test_targets(pd.DataFrame({"flight_date": pd.to_datetime(["2026-05-01"])}))


def test_no_feature_is_a_flight_day_outcome_or_tail_derived():
    feats = set(SCHEDULE_FEATURES + DAY_BEFORE_FEATURES)
    assert not feats & set(config.FLIGHT_DAY_OUTCOME_COLUMNS)
    assert not {"leg_of_day", "tail_number", "month"} & feats


def test_feature_missingness_does_not_encode_the_target():
    d = previous_day_rates(schedule_features(_toy()))
    for f in SCHEDULE_FEATURES + DAY_BEFORE_FEATURES:
        miss = d[f].isna()
        if 0 < miss.sum() < len(d):
            # a missingness pattern that separates the target perfectly would be a leak
            assert not (d.loc[miss, "disrupted"].nunique() == 1 and d.loc[~miss, "disrupted"].nunique() == 1
                        and d.loc[miss, "disrupted"].iloc[0] != d.loc[~miss, "disrupted"].iloc[0]), f


def test_schedule_counts_are_built_before_population_filter():
    d = _toy().assign(tail_number=["N1", None, "N3", "N4", "N5", "N6"])
    full = schedule_features(d)
    filtered_after = full[full["tail_number"].notna()]
    assert filtered_after.loc[filtered_after.flight_date == "2025-01-01", "origin_day_sched"].max() == 3   # counts include the tail-less flight
