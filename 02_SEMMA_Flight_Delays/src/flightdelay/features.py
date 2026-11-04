"""Features known at the decision time (17:00 local the day before), front pass v2.

Removed after critic round 1: ``leg_of_day`` (derived from ``tail_number``, whose missingness encodes
cancellation, and which records the aircraft actually flown) and ``month`` (encodes one year's weather).
"""

from __future__ import annotations

import pandas as pd

from .config import CARRIER_GROUP, DECISION_CUTOFF_HHMM


def schedule_features(d: pd.DataFrame) -> pd.DataFrame:
    """Features from the published schedule only.

    Call this on the FULL de-duplicated schedule, BEFORE any population filter (e.g. dropping tail-less
    cancellations), or the congestion counts would shrink on heavy-cancellation days (a dormant leak).
    """
    d = d.copy()
    d["carrier"] = d["airline_code"].astype(str).replace(CARRIER_GROUP)
    d["dep_hour"] = (d["sched_dep_time"] // 100).clip(0, 23)
    d["arr_hour"] = (d["sched_arr_time"] // 100).clip(0, 23)
    d["origin_hour_sched"] = d.groupby(["flight_date", "origin", "dep_hour"], observed=True)["flight_number"].transform("size")
    d["origin_day_sched"] = d.groupby(["flight_date", "origin"], observed=True)["flight_number"].transform("size")
    return d


def known_by_cutoff(d: pd.DataFrame, cutoff: int = DECISION_CUTOFF_HHMM) -> pd.Series:
    """Flights whose outcome is known by ``cutoff`` on their own date: scheduled to arrive the same day by then."""
    same_day = d["sched_arr_time"] >= d["sched_dep_time"]
    return same_day & (d["sched_arr_time"] <= cutoff)


def previous_day_rates(d: pd.DataFrame, target: str = "disrupted", cutoff: int = DECISION_CUTOFF_HHMM) -> pd.DataFrame:
    """Yesterday's disruption rate at origin, destination and carrier, from flights known by the cutoff.

    Build this on the FULL timeline before splitting, so the first day of each partition gets values.
    """
    if "carrier" not in d:
        d = d.assign(carrier=d["airline_code"].astype(str).replace(CARRIER_GROUP))
    known = d[known_by_cutoff(d, cutoff)]
    out = d
    for key, name in [("origin", "origin_prev_day"), ("dest", "dest_prev_day"), ("carrier", "carrier_prev_day")]:
        g = known.groupby([key, "flight_date"], observed=True)[target].mean().rename(name).reset_index()
        g["flight_date"] = g["flight_date"] + pd.Timedelta(days=1)
        out = out.merge(g, on=[key, "flight_date"], how="left")
    return out


SCHEDULE_FEATURES = ["day_of_week", "dep_hour", "arr_hour", "carrier", "origin", "dest", "distance",
                     "sched_elapsed_time", "origin_hour_sched", "origin_day_sched"]
DAY_BEFORE_FEATURES = ["origin_prev_day", "dest_prev_day", "carrier_prev_day"]
