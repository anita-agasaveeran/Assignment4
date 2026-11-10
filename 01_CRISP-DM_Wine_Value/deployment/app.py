"""Wine Value Finder: Streamlit app (CRISP-DM Phase 6, BSC4).

Run from the project folder:
    streamlit run deployment/app.py

Internal pilot tool for a buying team (report §5.3 option F, §6.1). Two views:
- Shortlist (the product, BO1): upload one buying round of candidates, get the ranked ≤ $25 shortlist.
- One wine (BSC4 screen): note + origin + grape + vintage + price -> estimated score band, P(90+), value verdict, flavour
  profile and 5 similar reviewed wines, in under 3 s.
The score band and value verdict are hidden for any note source or country that the pilot stop rule has withdrawn
(deployment/band_status.json, written by deployment/pilot_eval.py).
"""

import json
import sys
import time
from pathlib import Path

import pandas as pd
import streamlit as st

PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR / "src"))

from winevalue import config, monitoring, pilot, production  # noqa: E402
from winevalue.artifacts import load_catalogue, load_value_finder  # noqa: E402

STATUS_PATH = PROJECT_DIR / "deployment" / "band_status.json"

st.set_page_config(page_title="Wine Value Finder", layout="wide")


@st.cache_resource(show_spinner="Loading models…")
def models():
    return load_value_finder()           # refuses an artifact without a passed lockbox reproduction or with a wrong SHA-1


@st.cache_resource(show_spinner="Indexing the reviewed catalogue…")
def similar_index():
    return production.SimilarWines(load_catalogue())


def band_status() -> dict:
    try:
        return json.loads(STATUS_PATH.read_text())
    except (OSError, ValueError):
        return {"withdrawn everywhere": False, "sources": [], "countries": []}


def band_allowed(source: str, country: str, status: dict) -> tuple[bool, str]:
    """The pilot's own rule (``pilot.band_hidden``) on one wine, with the reason."""
    row = pd.DataFrame([{"source": source or None, "country": country or None}])
    if not pilot.band_hidden(row, status).iloc[0]:
        return True, ""
    if status.get("withdrawn everywhere"):
        return False, "withdrawn for the whole pilot by the stop rule"
    if pilot.band_hidden(row.assign(country=None), {**status, "countries": []}).iloc[0]:
        return False, f"withdrawn for note source “{source or 'unknown'}” by the stop rule"
    return False, f"withdrawn for {country} by the stop rule"


try:
    vf = models()
except RuntimeError as e:
    st.error(f"Model artifact refused: {e}")
    st.stop()
status = band_status()

st.title("Wine Value Finder")
st.caption("Internal pilot tool for the buying team. Ranks unscored wines for sampling from their tasting notes. "
           "Estimates are not WineEnthusiast scores and must not be shown to customers. "
           "Data: WineEnthusiast reviews via Kaggle (CC BY-NC-SA 4.0); non-commercial use only.")

tab_one, tab_short, tab_about = st.tabs(["One wine", "Shortlist a buying round", "How to read this"])

with tab_one:
    left, right = st.columns([1, 1.25])
    with left:
        with st.form("wine"):
            note = st.text_area("Tasting note", height=150, placeholder="Paste the importer's, producer's or staff tasting note…",
                                value="Bright and juicy, with ripe red cherry, raspberry and a hint of dried herbs. "
                                      "Smooth tannins and fresh acidity carry a lingering, spicy finish.")
            c1, c2 = st.columns(2)
            country = c1.text_input("Country", "Spain")
            province = c2.text_input("Province / state (optional)", "Northern Spain")
            variety = c1.text_input("Grape or blend on the label", "Tempranillo")
            vintage = c2.number_input("Vintage (0 = non-vintage)", min_value=0, max_value=2100, value=2014, step=1)
            price = c1.number_input("Price (USD)", min_value=0.0, value=18.0, step=1.0,
                                    help=f"Converted to 2017 dollars (the models' basis) × {config.PRICE_DEFLATOR:g} "
                                         f"({config.PRICE_INDEX}); set before the pilot, see the report §6.1.")
            source = c2.text_input("Note source (writer, importer or producer)", "")
            c3, c4 = st.columns(2)
            has_desig = c3.checkbox("Has a designation (e.g. Reserva, vineyard name)")
            has_region = c4.checkbox("Has a sub-region on the label")
            go = st.form_submit_button("Estimate", type="primary")
    go = go or st.query_params.get("demo") == "1"     # ?demo=1 runs the example note on load (for the report screenshot)
    if go and note.strip():
        index = similar_index()
        t0 = time.perf_counter()
        row = pd.DataFrame([{"note": note, "country": country, "province": province or None, "variety": variety,
                             "vintage": vintage or None, "price": price or None, "source": source,
                             "designation": "yes" if has_desig else None, "region_1": "yes" if has_region else None}])
        out = vf.score(row).iloc[0]
        prepared = vf.prepare(row)
        sims = index.query(prepared["note"].iloc[0], colour=prepared["colour"].iloc[0])
        elapsed = time.perf_counter() - t0
        ok, why = band_allowed(source.strip(), prepared["country"].iloc[0], status)
        with right:
            m1, m2, m3 = st.columns(3)
            if ok:
                m1.metric("Estimated score band", f"{out['band low']:.0f}–{out['band high']:.0f}", help=production.APP_BAND_CAVEAT)
            else:
                m1.metric("Estimated score band", "hidden", help=why)
            m2.metric("P(90+), relative", "–" if pd.isna(out["P(90+)"]) else f"{out['P(90+)']:.0%}", help=production.APP_P90_CAVEAT)
            pct_short, pct_text = production.percentile_text(out["share of candidates ranked above"], out["shortlist tier"] != "Not a ≤ $25 candidate")
            m3.metric("Ranker percentile", pct_short, help=production.APP_TIER_CAVEAT)
            if ok:
                st.caption(production.APP_BAND_CAVEAT)
            st.caption("P(90+): " + production.APP_P90_CAVEAT)
            if monitoring.country_unseen(vf, prepared).iloc[0]:
                st.warning(f"“{country}” is not a country in the training data: the estimates treat it as unknown origin.")
            st.markdown(f"**Value verdict:** {out['value verdict'] if ok else 'hidden (' + why + ')'}")
            if ok and not str(out["value verdict"]).startswith(("No price", "Above")):
                st.caption(production.APP_VALUE_BASE)
            if pd.notna(out["price (2017 $)"]):
                st.caption(f"Price used by the verdict and the ranker: ${out['price (2017 $)']:.2f} in 2017 dollars "
                           f"(as given × {config.PRICE_DEFLATOR:g}).")
            st.markdown(f"**Shortlist ranker:** {pct_text}")
            st.caption(production.APP_TIER_CAVEAT)
            st.markdown(f"**Flavour profile:** {out['profile name']}")
            st.markdown("**5 similar reviewed wines**")
            show = sims[["title", "points", "price", "variety", "country", "similarity", "near-duplicate listing"]].rename(columns={"points": "critic score"})
            st.dataframe(show.style.format({"price": "${:.0f}", "similarity": "{:.2f}"}, na_rep="–"), hide_index=True, use_container_width=True)
            st.caption(f"Computed in {elapsed:.2f} s (target < 3 s).")
    elif go:
        right.warning("Paste a tasting note first.")

with tab_short:
    st.markdown("Upload one buying round as CSV. Columns: `note` (or `description`), `country`, `variety`, `price`; "
                "optional `province`, `vintage`, `title`, `winery`, `designation`, `region_1`, `source`, `wine_id`.")
    k = st.number_input("Wines the team can sample", 10, 500, config.SHORTLIST_K, step=10)
    up = st.file_uploader("Candidates CSV", type="csv")
    if up is not None:
        cand = pd.read_csv(up)
        try:
            flags, report = monitoring.round_report(vf, cand)
        except ValueError as e:
            st.error(f"File refused: {e}")
            st.stop()
        t0 = time.perf_counter()
        sl = vf.shortlist(cand, k=int(k))
        st.caption(f"{len(cand):,} candidates, {len(sl):,} at ≤ ${config.VALUE_MAX_PRICE:.0f}; ranked in {time.perf_counter() - t0:.1f} s.")
        if report["alerts"]:
            st.warning("Input-drift alerts for this round (review before relying on the ranks): " + "; ".join(report["alerts"]))
        st.caption("Data-quality flags: " + ", ".join(f"{k.removeprefix('flag: ')} {v}" for k, v in report["flag counts"].items()))
        keep = [c for c in ["wine_id", "title", "winery", "variety", "country", "price", "source"] if c in cand.columns]
        view = cand.loc[sl.index, keep].join(sl[["rank", "round tier", "on shortlist", "P(90+)", "profile name"]]).join(flags)
        st.dataframe(view[view["on shortlist"]], hide_index=True, use_container_width=True)
        st.download_button("Download the ranked list", view.to_csv(index=False).encode(), "shortlist.csv", "text/csv")
        st.download_button("Download the round's monitoring report", json.dumps(report, indent=2, default=float).encode(),
                           "shortlist.monitoring.json", "application/json")
        st.caption("This view is for browsing a round. **Pilot rounds must be scored with `deployment/score.py`**, which keeps "
                   "every candidate's scores and the monitoring report as files: the outcome checks need every logged "
                   "candidate, shortlisted or not (report §6.1–6.2).")

with tab_about:
    st.markdown(f"""
**What the outputs mean**
- **Shortlist** (the main output): wines are ordered by a ridge model on the note plus log price. On four held-out critics it put
  76% value wines into a 100-wine shortlist, against 39% for the best simple rule. In a buying round, the tiers are the
  top 10% and 20% of that round's ≤ ${config.VALUE_MAX_PRICE:.0f} candidates. The one-wine view can only compare a wine with
  development candidates, and new writers' notes clear those cut-offs far more often, so use the round rank to pick samples.
- **Estimated score band**: a price-free estimate ± {vf.band_half_width:.2f} points (an 80% band on held-out writers). Its accuracy
  depends on the writer's level: it is hidden for any note source or country the pilot stop rule has withdrawn.
- **Value verdict**: the price-free estimate compared with the 90-point / ${config.VALUE_MAX_PRICE:.0f} bar: Likely (the whole band
  is 90+), Probable (the estimate is 90+), Long shot (only the top of the band reaches 90), Unlikely. Hidden with the band.
  {production.APP_VALUE_BASE} {production.APP_DISAGREE}
- **P(90+)**: a relative indicator from the shortlist ranker; it over-predicted the 90+ rate by 10 points on held-out critics.
- **Flavour profile**: one of 8 profiles from the note's flavour terms, named by two blind reviewers.
- **Similar wines**: the closest reviewed notes by TF-IDF cosine similarity; near-duplicate listings (same note, J ≥ {config.DM5_TAU}) are flagged.

**Band status:** {'withdrawn everywhere' if status.get('withdrawn everywhere') else 'shown'}; withdrawn sources: {', '.join(status.get('sources', [])) or 'none'};
pooled small sources withdrawn: {', '.join(status.get('pooled sources', [])) or 'none'}; withdrawn countries: {', '.join(status.get('countries', [])) or 'none'}.

Models: the Phase 4 selections frozen in commit `{vf.info['frozen code']}` (evaluated with the Phase 5 code of `a140a70`), fitted on {vf.info['training rows']:,} development reviews. Full report:
`reports/final_report.md` §5–6.
""")
