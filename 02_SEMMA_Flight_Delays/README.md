# Project 2: SEMMA · Will My Flight Be Disrupted Tomorrow?

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/anita-agasaveeran/Assignment4/blob/main/02_SEMMA_Flight_Delays/notebooks/SEMMA_Flight_Disruption.ipynb)

**Problem:** every evening at 16:45 US Eastern, a customer-care team can contact passengers on only ~2% of tomorrow's flights. Which flights are most likely to be disrupted (15+ min late, cancelled or diverted)?

**Methodology:** SAS SEMMA (Sample → Explore → Modify → Model → Assess) + Score, preceded by a short front pass (problem framing, data checks, frozen partition). SEMMA has no business-understanding step of its own.

**Data:** 11.7M real BTS flights, Jan 2025 – Aug 2026 ([Kaggle](https://www.kaggle.com/datasets/samuelpombourcq/us-flight-delays-and-cancellations-2025-2026), CC0). See [`data/README.md`](data/README.md).

**Result (sealed test summer May–Aug 2026, scored once):** the champion (logistic regression on an 800k stratified sample) puts **63%** disrupted flights in the daily top 2%, against 47% for the best simple rule: **per-day lift 2.39 vs 1.70**, gap +0.69 (90% interval +0.53 to +0.86), better on 91% of days. All pre-registered targets are met. See [`reports/final_report.md`](reports/final_report.md).

## Structure
| Path | Contents |
|---|---|
| `notebooks/SEMMA_Flight_Disruption.ipynb` | End-to-end Colab notebook: front pass, Sample, Explore, Modify, Model, Assess, Score (saved with outputs) |
| `src/flightdelay/` | Reusable code: `sampling` (stratified sampler, representativeness), `lcurve` (learning curve), `modify` (16:45 ET clock, trailing-window features), `models` (SAS EM node equivalents), `metrics` |
| `scripts/` | `run_learning_curve.py`, `run_model.py`, `run_assess.py` (the single sealed-test run, with a freeze record) |
| `tests/` | 21 unit tests (`pytest tests`), including leakage-invariance tests |
| `data/sample/` | Exploration sample + training-sample row ids |
| `models/` | `champion.joblib`, `manifest.json` |
| `deployment/` | `score.py` (batch scoring), `app.py` (Streamlit demo), `model_card.md`, `monitoring_plan.md` |
| `reports/` | `final_report.md`, `front_pass.md`, `sas_ondemand_guide.md`, `figures/`, `tables/` |
| `critiques/` | Critic persona prompt and round-by-round reviews |

## Run
```bash
# from the repo root
python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
cd 02_SEMMA_Flight_Delays
pytest tests
streamlit run deployment/app.py
python deployment/score.py --date 2026-07-03
```

## Progress
| Stage | Notebook | Report | Critic rounds |
|---|---|---|---|
| Front pass | ✅ | ✅ | 2 (6 → 8/10) |
| Sample · Explore · Modify | ✅ | ✅ | 3 (6 → 7 → 8.5/10), no major issues in round 3 |
| Model | ✅ | ✅ | 2 (6.5 → 8.5/10), no major issues in round 2 |
| Assess · Score | ✅ (single sealed run) | ✅ | reported; no post-unseal review yet |
| Medium article | ✅ [published on Medium](https://medium.com/@anita.agasaveeran/which-380-flights-will-go-wrong-tomorrow-a-semma-walkthrough-on-11-7-million-us-flights-b5c72c315992) | | |
