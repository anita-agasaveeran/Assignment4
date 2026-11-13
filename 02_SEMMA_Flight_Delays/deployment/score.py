"""Batch scoring (the Python version of SAS Enterprise Miner's Score node).

Ranks every scheduled flight on DATE by disruption risk, using only information known at 16:45 US Eastern the day
before: the published schedule for DATE plus outcomes of earlier days, read from the BTS flights table.

    python deployment/score.py --date 2026-07-04 [--top 0.02] [--out ranked.csv]

The run must have the flight table locally (or it is fetched from Kaggle) and ``models/champion.joblib``.
"""
import argparse
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR / "src"))

import joblib                                   # noqa: E402
import numpy as np                              # noqa: E402
import pandas as pd                             # noqa: E402

from flightdelay import models, modify          # noqa: E402
from flightdelay.data import load_flights       # noqa: E402

HISTORY_DAYS = 40                               # longest window is D-29..D-2; extra days are a safety margin


def score_date(date: str, top: float = 0.02) -> pd.DataFrame:
    day = pd.Timestamp(date)
    raw = load_flights(columns=modify.RAW_COLUMNS)
    raw["row_id"] = np.arange(len(raw), dtype="int32")
    raw = raw[raw["flight_date"].between(day - pd.Timedelta(days=HISTORY_DAYS), day)].copy()
    if not (raw["flight_date"] == day).any():
        raise SystemExit(f"no scheduled flights on {date} in the table")
    # Day D's own outcomes must never reach a feature: blank them before building (they're unknown at decision time).
    on_day = raw["flight_date"] == day
    raw["disrupted"] = raw["disrupted"].astype(float)
    raw.loc[on_day, ["arr_del15", "cancelled", "diverted", "disrupted"]] = np.nan
    # Every scheduled flight is scored: whether a tail number gets assigned is itself day-D information.
    fr = modify.build_frame(raw, keep_tailless=True)
    fr = fr[fr["flight_date"] == day].copy()
    model = joblib.load(PROJECT_DIR / "models" / "champion.joblib")
    fr["risk"] = models.predict(model, fr)
    fr = fr.sort_values("risk", ascending=False)
    k = max(1, int(round(top * len(fr))))
    fr["selected"] = np.arange(len(fr)) < k
    return fr[["flight_date", "carrier", "flight_number", "origin", "dest", "sched_dep_time", "sched_arr_time", "risk", "selected"]]


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    ap.add_argument("--top", type=float, default=0.02)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    ranked = score_date(a.date, a.top)
    out = a.out or f"ranked_{a.date}.csv"
    ranked.to_csv(out, index=False)
    print(f"{len(ranked):,} flights on {a.date}; {int(ranked.selected.sum())} selected (top {a.top:.0%}) → {out}")
    print(ranked.head(10).to_string(index=False))
