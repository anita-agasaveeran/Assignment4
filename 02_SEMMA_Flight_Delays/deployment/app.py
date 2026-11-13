"""Streamlit demo: "tomorrow's at-risk flights" replayed over the sealed test summer (May–Aug 2026).

    streamlit run deployment/app.py

Shows, for a chosen day, the flights the care team would have contacted (top 2% by risk, decided at 16:45 ET the
day before) and how many of them were actually disrupted. Scores come from the single Assess run.
"""
import json
from pathlib import Path

import pandas as pd
import streamlit as st

HERE = Path(__file__).resolve().parent
top = pd.read_parquet(HERE / "test_period_top5pct.parquet")
manifest = json.loads((HERE.parent / "models" / "manifest.json").read_text())
daily = pd.read_csv(HERE.parent / "reports" / "tables" / "assess_daily_lift.csv", parse_dates=["date"])

st.set_page_config(page_title="Flight disruption risk", layout="wide")
st.title("Will my flight be disrupted tomorrow?")
st.caption(f"Champion: {manifest['champion']} · decision clock {manifest['decision_clock']} · "
           f"test-summer per-day top-2% lift {manifest['test_top2_lift']:.2f}")

dates = sorted(top["flight_date"].dt.date.unique())
day = st.select_slider("Flight date (test period, May–Aug 2026)", options=dates, value=dates[len(dates) // 2])
frac = st.radio("Care-team capacity", [0.02, 0.05], format_func=lambda f: f"top {f:.0%} of the day's flights", horizontal=True)
g = top[top["flight_date"].dt.date == day]
sel = g[g["rank"] <= frac * g["n_day"]].sort_values("rank")
c1, c2, c3 = st.columns(3)
c1.metric("Flights scheduled", f"{int(g['n_day'].iloc[0]):,}")
c2.metric("Flights selected", f"{len(sel):,}")
c3.metric("Of those, actually disrupted", f"{sel['disrupted'].mean():.0%}")
show = sel.assign(risk=(sel["score"] * 100).round(1), outcome=sel["disrupted"].map({1: "disrupted", 0: "on time"}))
st.dataframe(show[["rank", "carrier", "flight_number", "origin", "dest", "sched_dep_time", "risk", "outcome",
                   "origin_d1", "flight_w4"]].rename(columns={"risk": "risk %", "origin_d1": "origin yesterday",
                                                              "flight_w4": "this flight, last 4 weeks"}),
             hide_index=True, width="stretch")
st.subheader("Per-day top-2% lift over the test summer")
st.line_chart(daily.set_index("date"))
st.caption("Lift = share disrupted among the selected flights ÷ the day's overall disruption rate. "
           "Data: US BTS On-Time Performance via Kaggle (CC0).")
