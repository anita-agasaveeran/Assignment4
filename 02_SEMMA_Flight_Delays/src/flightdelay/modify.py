"""SEMMA *Modify*: the v3 feature set, every input known at 17:00 US Eastern the day before the flight.

* One national decision clock (critic round 2, N3): a previous-day flight counts as "known" only if its scheduled
  arrival, converted to Eastern time, is at or before 16:45 ET (17:00 minus a 15-minute reporting margin).
  Time zones come from the destination state (the airport file has no time-zone column), DST-aware via zoneinfo.
* History features are TRAILING windows of past outcomes (d-1 cut at the clock; d-2 and earlier complete), so they
  are leakage-safe by construction and need no train-only target encoding: a rate for day D only uses days < D.
* Rates are shrunk toward a constant prior (the 2025 training base rate) with weight ``PRIOR_N``.
"""

from __future__ import annotations

from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
from pandas.tseries.holiday import USFederalHolidayCalendar

from .config import TARGET

CLOCK_ET_MIN = 17 * 60 - 15            # 16:45 ET
PRIOR_RATE, PRIOR_N = 0.237, 20         # training-period base rate; pseudo-count for shrinkage

STATE_TZ = {**{s: "America/New_York" for s in "CT DE DC FL GA IN KY ME MD MA MI NH NJ NY NC OH PA RI SC VT VA WV".split()},
            **{s: "America/Chicago" for s in "AL AR IL IA KS LA MN MS MO NE ND OK SD TN TX WI".split()},
            **{s: "America/Denver" for s in "CO ID MT NM UT WY".split()},
            "AZ": "America/Phoenix", **{s: "America/Los_Angeles" for s in "CA NV OR WA".split()},
            "AK": "America/Anchorage", "HI": "Pacific/Honolulu", "PR": "America/Puerto_Rico",
            "VI": "America/St_Thomas", "TT": "Pacific/Guam", "GU": "Pacific/Guam", "MP": "Pacific/Saipan", "AS": "Pacific/Pago_Pago"}
# Airports in split-zone states that are NOT in their state's majority zone (revision 2, critic m1).
AIRPORT_TZ = {"ELP": "America/Denver", "RAP": "America/Denver", "DIK": "America/Denver", "BFF": "America/Denver",
              "PNS": "America/Chicago", "VPS": "America/Chicago", "ECP": "America/Chicago", "IMT": "America/Chicago",
              "ESC": "America/Chicago", "IWD": "America/Chicago", "EVV": "America/Chicago", "PAH": "America/Chicago",
              "TYS": "America/New_York", "TRI": "America/New_York", "CHA": "America/New_York", "LWS": "America/Los_Angeles"}


def offset_from_et_hours(states: pd.Series, dates: pd.Series, airports: pd.Series | None = None) -> np.ndarray:
    """Local minus Eastern time, in hours, for each (zone, date) (e.g. California in July: -3). The zone comes from
    the airport override table if listed, else from the state."""
    zones = states.astype(str).map(lambda x: STATE_TZ.get(x, "America/New_York"))
    if airports is not None:
        over = airports.astype(str).map(AIRPORT_TZ)
        zones = over.where(over.notna(), zones)
    key = pd.DataFrame({"s": zones.to_numpy(), "d": pd.to_datetime(dates).dt.normalize().to_numpy()})
    uniq = key.drop_duplicates()
    et = ZoneInfo("America/New_York")
    def off(s, d):
        tz = ZoneInfo(s)
        noon = pd.Timestamp(d).to_pydatetime().replace(hour=12)
        return (noon.replace(tzinfo=tz).utcoffset() - noon.replace(tzinfo=et).utcoffset()).total_seconds() / 3600
    uniq = uniq.assign(off=[off(s, d) for s, d in zip(uniq.s, uniq.d)])
    return key.merge(uniq, on=["s", "d"], how="left")["off"].to_numpy()


def hhmm_to_min(x) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    return (x // 100) * 60 + x % 100


def known_by_clock(d: pd.DataFrame) -> np.ndarray:
    """Flights whose outcome is known by 16:45 ET on their own (local departure) date.

    Revision 2 (critic m1): scheduled arrival in ET = scheduled departure converted to ET + scheduled elapsed time,
    which handles the date line and short westbound hops (local arrival earlier than local departure).
    """
    dep_et = hhmm_to_min(d["sched_dep_time"]) - 60 * d["origin_offset_et"].to_numpy()
    arr_et = dep_et + d["sched_elapsed_time"].to_numpy(dtype=float)
    return arr_et <= CLOCK_ET_MIN


def _dense_cumsum(d: pd.DataFrame, keys: list[str], dates: pd.DatetimeIndex, mask=None):
    """Per key x day: cumulative sums of target and counts over a dense day axis (index 0 = before first day)."""
    src = d if mask is None else d[mask]
    g = src.groupby(keys + ["flight_date"], observed=True)[TARGET].agg(["sum", "count"])
    kidx = pd.MultiIndex.from_frame(d[keys].drop_duplicates()) if len(keys) > 1 else pd.Index(d[keys[0]].unique())
    k = pd.Index(kidx).get_indexer(g.index.droplevel("flight_date") if len(keys) > 1 else g.index.get_level_values(0))
    t = dates.get_indexer(g.index.get_level_values("flight_date"))
    S = np.zeros((len(kidx), len(dates) + 1), dtype=np.float64)
    N = np.zeros_like(S)
    np.add.at(S, (k, t + 1), g["sum"].to_numpy())
    np.add.at(N, (k, t + 1), g["count"].to_numpy())
    return pd.Index(kidx), S.cumsum(1), N.cumsum(1)


def trailing_rate(d: pd.DataFrame, keys: list[str], first_lag: int, last_lag: int, mask=None, dates=None):
    """Shrunken disruption rate and count over days D-last_lag .. D-first_lag for each row's key (rows on day D)."""
    dates = dates if dates is not None else pd.DatetimeIndex(np.sort(d["flight_date"].unique()))
    assert len(dates) < 2 or (np.diff(dates.values).astype("timedelta64[D]").astype(int) == 1).all(), "date axis must be contiguous"
    kidx, CS, CN = _dense_cumsum(d, keys, dates, mask)
    row_k = kidx.get_indexer(pd.MultiIndex.from_frame(d[keys]) if len(keys) > 1 else d[keys[0]])
    row_t = dates.get_indexer(d["flight_date"]) + 1                      # cumsum column of day D itself
    hi = np.clip(row_t - first_lag, 0, None)
    lo = np.clip(row_t - last_lag - 1, 0, None)
    s = CS[row_k, hi] - CS[row_k, lo]
    n = CN[row_k, hi] - CN[row_k, lo]
    return (s + PRIOR_N * PRIOR_RATE) / (n + PRIOR_N), n


def days_to_holiday(dates: pd.Series) -> np.ndarray:
    hol = USFederalHolidayCalendar().holidays("2024-12-01", "2026-12-31").to_numpy()
    dd = pd.to_datetime(dates).to_numpy()[:, None]
    return np.min(np.abs((dd - hol[None, :]) / np.timedelta64(1, "D")), axis=1).clip(0, 14)


def build_v3(d: pd.DataFrame) -> pd.DataFrame:
    """Add v3 features to a frame that already has the front-pass schedule features (``schedule_features``) and
    ``origin_state`` / ``dest_state``. Build on the FULL schedule and timeline, before any population filter."""
    d = d.copy()
    d["dest_offset_et"] = offset_from_et_hours(d["dest_state"], d["flight_date"], d["dest"])
    d["origin_offset_et"] = offset_from_et_hours(d["origin_state"], d["flight_date"], d["origin"])
    d["route"] = d["origin"].astype(str) + "-" + d["dest"].astype(str)
    d["flight_key"] = d["carrier"].astype(str) + d["flight_number"].astype(str) + d["origin"].astype(str)
    d["nation"] = "US"
    d["dest_hour_sched"] = d.groupby(["flight_date", "dest", "arr_hour"], observed=True)["flight_number"].transform("size")
    d["carrier_day_sched"] = d.groupby(["flight_date", "carrier"], observed=True)["flight_number"].transform("size")
    d["days_to_holiday"] = days_to_holiday(d["flight_date"])
    d["dep_min_et"] = hhmm_to_min(d["sched_dep_time"]) - 60 * d["origin_offset_et"]   # national position in the day
    dates = pd.DatetimeIndex(np.sort(d["flight_date"].unique()))
    known = known_by_clock(d)
    # yesterday, cut at 16:45 ET
    for key, name in [(["origin"], "origin"), (["dest"], "dest"), (["carrier"], "carrier"), (["nation"], "nation")]:
        d[f"{name}_d1"], d[f"{name}_d1_n"] = trailing_rate(d, key, 1, 1, mask=known, dates=dates)
    # complete days d-2 .. d-7 (one week) and d-2 .. d-29 (four weeks)
    for key, name in [(["origin"], "origin"), (["dest"], "dest"), (["carrier"], "carrier"), (["nation"], "nation")]:
        d[f"{name}_w1"], _ = trailing_rate(d, key, 2, 7, dates=dates)
    for key, name in [(["route"], "route"), (["carrier", "dep_hour"], "carrier_hour"), (["origin", "dep_hour"], "origin_hour"),
                      (["flight_key"], "flight")]:
        d[f"{name}_w4"], d[f"{name}_w4_n"] = trailing_rate(d, key, 2, 29, dates=dates)
    return d.drop(columns=["nation"])


V3_NUMERIC = ["dep_hour", "arr_hour", "day_of_week", "distance", "sched_elapsed_time", "dep_min_et",
              "origin_hour_sched", "origin_day_sched", "dest_hour_sched", "carrier_day_sched", "days_to_holiday",
              "origin_d1", "dest_d1", "carrier_d1", "nation_d1", "origin_d1_n",
              "origin_w1", "dest_w1", "carrier_w1", "nation_w1",
              "route_w4", "carrier_hour_w4", "origin_hour_w4", "flight_w4", "flight_w4_n"]
V3_CATEGORICAL = ["carrier", "origin", "dest"]
V3_FEATURES = V3_NUMERIC + V3_CATEGORICAL


RAW_COLUMNS = ["flight_date", "day_of_week", "airline_code", "tail_number", "flight_number", "origin", "dest",
               "origin_state", "dest_state", "sched_dep_time", "sched_arr_time", "arr_del15", "cancelled", "diverted",
               "sched_elapsed_time", "distance"]


def build_frame(raw: pd.DataFrame, keep_tailless: bool = False) -> pd.DataFrame:
    """Full Modify pipeline on a raw flights frame (with ``row_id``): de-duplicate; schedule counts, front-pass
    previous-day rates (kept for the day-before benchmark rule) and v3 features on the FULL schedule; then the
    scored-population filter (assumption A-pop) and the drop of the 18 bad ``sched_elapsed_time`` rows."""
    from .features import DEDUP_KEY, previous_day_rates, schedule_features
    d = raw.drop_duplicates(DEDUP_KEY)
    d = build_v3(previous_day_rates(schedule_features(d)))
    keep = d["sched_elapsed_time"].gt(0) & (d["tail_number"].notna() | keep_tailless)
    d = d[keep].reset_index(drop=True)
    d["tailless"] = d["tail_number"].isna()
    for c in V3_CATEGORICAL:
        d[c] = d[c].astype(str)
    return d
