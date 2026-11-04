"""Daily Production Planner: Streamlit app (CRISP-DM Phase 6).

Run from the project folder:
    streamlit run deployment/app.py

Scaffold: until Phase 4 saves a model to models/, the app only shows a
notice. The forecasting and recommendation logic comes from src/bakery,
so the app and the notebook run the same code.
"""

import sys
from pathlib import Path

import streamlit as st

PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR / "src"))

from bakery import config  # noqa: E402

MODEL_PATH = config.MODELS_DIR / "demand_model.joblib"

st.set_page_config(page_title="Bakery Production Planner", layout="wide")
st.title("Daily Production Planner")
st.caption("Recommended bake quantity per category, from the CRISP-DM bakery project.")

if not MODEL_PATH.exists():
    st.info(
        "No trained model yet. Phase 4 (Modeling) saves one to "
        f"`{MODEL_PATH.relative_to(PROJECT_DIR)}`, and then this page shows recommendations."
    )
    st.stop()

# TODO (Phase 6): store + date inputs -> features -> forecast quantiles ->
# recommended bake quantity per category, expected waste/fill rate,
# and suggested combos from the basket rules.
