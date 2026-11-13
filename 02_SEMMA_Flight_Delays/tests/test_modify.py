import numpy as np
import pandas as pd

from flightdelay import modify


def _days(n=10, per_day=4, seed=0):
    rng = np.random.default_rng(seed)
    dates = np.repeat(pd.date_range("2025-07-01", periods=n), per_day)
    return pd.DataFrame({"flight_date": dates, "origin": np.tile(["A", "B"], n * per_day // 2),
                         "disrupted": rng.integers(0, 2, n * per_day)})


def test_trailing_rate_never_uses_day_d_or_later():
    d = _days()
    base, _ = modify.trailing_rate(d, ["origin"], 2, 7)
    d2 = d.copy()
    last = d2.flight_date == d2.flight_date.max()
    d2.loc[last, "disrupted"] = 1 - d2.loc[last, "disrupted"]          # change the outcome of the last day only
    again, _ = modify.trailing_rate(d2, ["origin"], 2, 7)
    assert np.allclose(base, again)                                     # nothing on any day changes
    one, _ = modify.trailing_rate(d2, ["origin"], 1, 1)
    d3 = d2.copy(); d3.loc[d3.flight_date == "2025-07-09", "disrupted"] = 1
    two, _ = modify.trailing_rate(d3, ["origin"], 1, 1)
    changed = ~np.isclose(one, two)
    assert set(d3.loc[changed, "flight_date"]) <= {pd.Timestamp("2025-07-10")}   # only the next day sees it


def test_trailing_rate_window_and_shrinkage():
    d = _days(n=10, per_day=2)
    d["disrupted"] = 1
    r, n = modify.trailing_rate(d, ["origin"], 2, 3)
    day5 = (d.flight_date == "2025-07-05").to_numpy()
    assert (n[day5] == 2).all()                                          # days 07-02 and 07-03, one flight each per origin
    assert np.allclose(r[day5], (2 + modify.PRIOR_N * modify.PRIOR_RATE) / (2 + modify.PRIOR_N))


def test_clock_is_eastern_with_margin():
    july = pd.Series(pd.to_datetime(["2025-07-01"] * 3))
    off = modify.offset_from_et_hours(pd.Series(["CA", "AZ", "NY"]), july)
    assert off.tolist() == [-3.0, -3.0, 0.0]                            # AZ has no DST: same as PDT in summer
    jan = modify.offset_from_et_hours(pd.Series(["AZ"]), pd.Series(pd.to_datetime(["2025-01-15"])))
    assert jan.tolist() == [-2.0]
    el_paso = modify.offset_from_et_hours(pd.Series(["TX"]), pd.Series(pd.to_datetime(["2025-07-01"])), pd.Series(["ELP"]))
    assert el_paso.tolist() == [-2.0]                                   # split-zone override: Mountain, not Central
    # arrival in ET = departure in ET + scheduled elapsed time
    d = pd.DataFrame({"sched_dep_time": [1000, 1000, 1000, 1000, 2200],
                      "sched_elapsed_time": [220, 230, 400, 55, 300],
                      "origin_offset_et": [-3.0, -3.0, 0.0, 0.0, -6.0]})
    # 10:00 PDT = 13:00 ET + 3h40 = 16:40 (known); + 3h50 = 16:50 (not); 10:00 ET + 6h40 = 16:40 (known);
    # ATL->BHM-style short westbound hop 10:00 ET + 55 min (known even though local arrival < local departure);
    # 22:00 HST departure = 04:00 ET next day: never known on its own date
    assert modify.known_by_clock(d).tolist() == [True, False, True, True, False]


def _raw(n_days=40, seed=0):
    rng = np.random.default_rng(seed)
    rows = []
    for day in pd.date_range("2025-03-01", periods=n_days):
        for k, (o, de, st_o, st_d, dep) in enumerate([("AAA", "BBB", "NY", "CA", 800), ("BBB", "AAA", "CA", "NY", 900),
                                                       ("AAA", "BBB", "NY", "CA", 1500), ("BBB", "AAA", "CA", "NY", 2300)]):
            rows.append({"flight_date": day, "day_of_week": day.day_of_week + 1, "airline_code": "AA", "tail_number": "N1",
                         "flight_number": k + 1, "origin": o, "dest": de, "origin_state": st_o, "dest_state": st_d,
                         "sched_dep_time": dep, "sched_arr_time": (dep + 300) % 2400, "sched_elapsed_time": 300,
                         "distance": 2400, "disrupted": int(rng.random() < 0.3)})
    d = pd.DataFrame(rows)
    d["row_id"] = np.arange(len(d))
    return d


def test_build_frame_inputs_never_see_their_own_day_or_later():
    raw = _raw()
    base = modify.build_frame(raw).set_index("row_id")[modify.V3_NUMERIC]
    # (1) truncating later days leaves earlier rows unchanged
    cut = modify.build_frame(raw[raw.flight_date <= "2025-03-25"]).set_index("row_id")[modify.V3_NUMERIC]
    assert np.allclose(base.loc[cut.index].to_numpy(), cut.to_numpy())
    # (2) flipping day D's outcomes changes no day-D input
    day = pd.Timestamp("2025-03-20")
    flipped = raw.copy(); m = flipped.flight_date == day
    flipped.loc[m, "disrupted"] = 1 - flipped.loc[m, "disrupted"]
    again = modify.build_frame(flipped).set_index("row_id")[modify.V3_NUMERIC]
    ids = raw.loc[raw.flight_date <= day, "row_id"]
    assert np.allclose(base.loc[ids].to_numpy(), again.loc[ids].to_numpy())


def test_v3_counts_are_built_before_the_population_filter():
    raw = _raw(n_days=3)
    raw.loc[raw.index[0], "tail_number"] = None                          # one tail-less (cancelled) flight
    fr = modify.build_frame(raw)
    first = fr[fr.flight_date == "2025-03-01"]
    assert first["carrier_day_sched"].max() == 4                         # the tail-less flight still counts
