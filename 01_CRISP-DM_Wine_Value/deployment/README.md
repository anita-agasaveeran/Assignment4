# Deployment: Wine Value Finder

| File | Purpose |
|---|---|
| `app.py` | Streamlit app: paste a tasting note + origin/grape/vintage/price and get a score estimate, value verdict and similar wines |
| `requirements.txt` | Minimal runtime dependencies |
| `monitoring_plan.md` | What gets monitored after go-live, alert thresholds, retraining policy |
| `model_card.md` | Intended use, data, metrics, limitations, licence |

Run with `streamlit run deployment/app.py` from the project folder. Status: **scaffold** (needs `models/score_model.joblib` from Phase 4).
