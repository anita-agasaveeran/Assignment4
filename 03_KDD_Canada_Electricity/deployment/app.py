"""Canadian electricity knowledge dashboard (KDD project 3, step 6: using the knowledge).

Run:  streamlit run 03_KDD_Canada_Electricity/deployment/app.py
Data: deployment/artifacts/ (rebuild with deployment/refresh.py).
"""

import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ART = Path(__file__).resolve().parent / "artifacts"
KNOW = Path(__file__).resolve().parent / "knowledge.json"
ATTR = ("Source: adapted from Statistics Canada, Tables 25-10-0015-01 and 25-10-0016-01, Statistics Canada Open "
        "Licence. This does not constitute an endorsement by Statistics Canada.")
ABBR = {"Newfoundland and Labrador": "NL", "Prince Edward Island": "PE", "Nova Scotia": "NS", "New Brunswick": "NB",
        "Quebec": "QC", "Ontario": "ON", "Manitoba": "MB", "Saskatchewan": "SK", "Alberta": "AB",
        "British Columbia": "BC", "Yukon": "YT", "Northwest Territories": "NT", "Nunavut": "NU"}

st.set_page_config(page_title="Canada electricity knowledge", layout="wide")


@st.cache_data
def load():
    d = {n: pd.read_csv(ART / f"{n}.csv") for n in ("panel", "clusters", "changepoints", "anomalies", "forecast")}
    d["meta"] = json.loads((ART / "meta.json").read_text())
    d["know"] = json.loads(KNOW.read_text()) if KNOW.exists() else {}
    return d


if not (ART / "meta.json").exists():
    st.error("No artifacts yet. Run `python deployment/refresh.py` first.")
    st.stop()
d = load()
meta, know = d["meta"], d["know"]
panel = d["panel"]
panel["date"] = pd.PeriodIndex(panel["month"], freq="M").to_timestamp()

st.title("Is Canada's grid becoming less combustion-dependent?")
st.caption(f"Monthly data {meta['data_months'][0]} → {meta['data_months'][1]} · refreshed {meta['refreshed_utc']} · "
           "knowledge discovered with the KDD process (CMPE 255, project 3)")

tab0, tab1, tab2, tab3, tab4 = st.tabs(["Validated findings", "Archetypes (K1)", "Structural change (K2)",
                                        "Anomalies (K3)", "Forecast (K4)"])

with tab0:
    st.subheader("What the evaluation step accepted, and what it didn't")
    if know:
        st.dataframe(pd.DataFrame(know["acceptance"]), hide_index=True, width="stretch")
        st.caption(know.get("k2_note", ""))
        st.subheader("Findings ranked by interestingness")
        st.dataframe(pd.DataFrame(know["findings"]), hide_index=True, width="stretch")
    else:
        st.info("knowledge.json not found: the notebook's step 6 writes it.")
    yr = panel.assign(year=panel["month"].str[:4])
    full = yr.groupby("year")["month"].nunique()
    yr = yr[yr["year"].isin(full[full == 12].index)].groupby("year")[["combustion", "gen_total"]].sum()
    st.plotly_chart(px.line(x=yr.index, y=100 * yr["combustion"] / yr["gen_total"], markers=True,
                            labels={"x": "year (complete years)", "y": "combustion share of generation (%)"},
                            title="Canada (sum of 13 geographies): combustion share"), width="stretch")

with tab1:
    cl = d["clusters"]
    win = [col for col in cl.columns if ".." in col]
    w = st.radio("Feature window", win, horizontal=True)
    cl["cluster"] = cl[w].astype(str)
    cl["geo"] = cl["geography"].map(ABBR)
    st.plotly_chart(px.scatter(cl, x="combustion_share", y="hydro_share", color="cluster", text="geo",
                               size=cl["trade_intensity"].clip(lower=0.05), hover_data=cl.columns,
                               title="Archetypes: mix vs trade (bubble size = trade intensity)"), width="stretch")
    st.dataframe(cl[["geography", *win]], hide_index=True)

with tab2:
    cp = d["changepoints"]
    prov = st.selectbox("Province", sorted(cp["geography"].unique()), index=sorted(cp["geography"].unique()).index("Ontario"))
    s = panel[panel["geography"] == prov]
    fig = go.Figure(go.Scatter(x=s["date"], y=100 * s["combustion_share"], name="monthly share", line=dict(color="grey", width=1)))
    for r in cp[cp["geography"] == prov].itertuples():
        x = pd.period_range(r.start, r.end, freq="M").to_timestamp()
        fig.add_trace(go.Scatter(x=x, y=[100 * r.share_mean] * len(x), name=f"{r.start}–{r.end}: {100 * r.share_mean:.1f}%",
                                 line=dict(width=3)))
    fig.update_layout(title=f"{prov}: combustion share and PELT segments", yaxis_title="% of generation")
    st.plotly_chart(fig, width="stretch")
    st.dataframe(cp[cp["geography"] == prov], hide_index=True)

with tab3:
    an = d["anomalies"]
    flagged = an[an["flagged"]].sort_values("iforest", ascending=False)
    st.warning("Unvalidated monitoring: K3 was NOT MET in evaluation (flags matched public-record events no better than "
               "chance). Treat every flag as a candidate to investigate, not as a known event.")
    st.write(f"{len(flagged)} flagged geo-months (top 2% by Isolation Forest on two-sided STL residual z-scores over the "
             f"whole period; Nunavut from {meta['data_breaks'].get('Nunavut', '–')} and NL 2021-01..03 excluded as reporting breaks).")
    st.dataframe(flagged, hide_index=True, width="stretch")
    g = st.selectbox("Geography", list(ABBR), key="an_geo")
    s = panel[panel["geography"] == g]
    f = flagged[flagged["geography"] == g]
    fig = px.line(s, x="date", y="availability", title=f"{g}: availability (MWh) with flagged months")
    fig.add_scatter(x=pd.PeriodIndex(f["month"], freq="M").to_timestamp(),
                    y=s.set_index("month").loc[f["month"], "availability"], mode="markers", marker=dict(size=10, color="red"),
                    name="flagged")
    st.plotly_chart(fig, width="stretch")

with tab4:
    fc = d["forecast"]
    g = st.selectbox("Geography", list(ABBR), key="fc_geo")
    s = panel[panel["geography"] == g].tail(36)
    f = fc[fc["geography"] == g].assign(date=lambda x: pd.PeriodIndex(x["month"], freq="M").to_timestamp())
    fig = go.Figure([go.Scatter(x=s["date"], y=s["availability"], name="actual"),
                     go.Scatter(x=f["date"], y=f["seasonal_naive_mwh"], name="seasonal naive (deployed)"),
                     go.Scatter(x=f["date"], y=f["challenger_mwh"], name=f"{meta['forecast_challenger']} (challenger)",
                                line=dict(dash="dot"))])
    fig.update_layout(title=f"{g}: 12-month availability forecast from {meta['forecast_origin']}", yaxis_title="MWh")
    st.plotly_chart(fig, width="stretch")
    st.caption(know.get("k4_note", ""))

st.divider()
st.caption(ATTR)
