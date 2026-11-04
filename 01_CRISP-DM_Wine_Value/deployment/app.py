"""Value Finder: Streamlit app (CRISP-DM Phase 6).

Run from the project folder:
    streamlit run deployment/app.py

Scaffold: until Phase 4 saves a model to models/, the app only shows a notice.
"""

import sys
from pathlib import Path

import streamlit as st

PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR / "src"))

from winevalue import config  # noqa: E402

MODEL_PATH = config.MODELS_DIR / "score_model.joblib"

st.set_page_config(page_title="Wine Value Finder", layout="wide")
st.title("Wine Value Finder")
st.caption("Estimate a critic-equivalent score from a tasting note and flag value wines. "
           "Data: WineEnthusiast reviews via Kaggle (CC BY-NC-SA 4.0). Non-commercial use only.")

if not MODEL_PATH.exists():
    st.info("No trained model yet. Phase 4 (Modeling) saves one to "
            f"`{MODEL_PATH.relative_to(PROJECT_DIR)}`, and then this page becomes interactive.")
    st.stop()

# TODO (Phase 6): note + origin + grape + vintage + price inputs -> score estimate & band,
# value verdict vs the $25 / 90-point bar, flavour profile, and similar wines (LSH).
