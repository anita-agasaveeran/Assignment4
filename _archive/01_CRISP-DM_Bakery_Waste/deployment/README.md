# Deployment: Daily Production Planner

| File | Purpose |
|---|---|
| `app.py` | Streamlit app: pick store + date, see the recommended bake quantity per category |
| `requirements.txt` | Minimal runtime dependencies for the app |
| `monitoring_plan.md` | What gets monitored after go-live, alert thresholds, retraining policy |
| `model_card.md` | Intended use, data, metrics, limitations and ethics of the deployed model |

## Run locally
```bash
pip install -r requirements.txt   # from the repo root
cd 01_CRISP-DM_Bakery_Waste
streamlit run deployment/app.py
```

Status: **scaffold**. The app needs `models/demand_model.joblib`, which Phase 4 creates.
