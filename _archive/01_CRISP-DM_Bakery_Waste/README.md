# Project 1: CRISP-DM · Reducing Bakery Over-Production

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/anita-agasaveeran/Assignment4/blob/main/01_CRISP-DM_Bakery_Waste/notebooks/CRISP_DM_Bakery_Waste.ipynb)

**Problem:** a 3-store bakery chain doesn't sell about 28% of the units it bakes. The goal is to bake closer to demand, cutting waste and protecting profit, without running out on busy days.

**Methodology:** CRISP-DM 1.0, all six phases and every generic task.

**Data:** bakery sales, 19,321 order lines, 2023–2024 (see [`data/README.md`](data/README.md)).

## Structure
| Path | Contents |
|---|---|
| `notebooks/CRISP_DM_Bakery_Waste.ipynb` | End-to-end Colab notebook, one section per phase and task |
| `src/bakery/` | Reusable code (loading, features, models, metrics, bake policy), shared by the notebook and the app |
| `tests/` | Unit tests (`pytest tests`) |
| `data/raw/`, `data/processed/` | Untouched source data / derived datasets |
| `models/` | Saved model pipeline(s) |
| `deployment/` | Streamlit Production Planner, monitoring plan, model card |
| `reports/` | Final CRISP-DM report and figures |
| `critiques/` | Critic persona prompt and round-by-round review log |
| `article/` | Medium article draft |
| `video/` | Walkthrough script and shot list |

## Run
```bash
# from the repo root
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cd 01_CRISP-DM_Bakery_Waste
pytest tests
jupyter notebook notebooks/CRISP_DM_Bakery_Waste.ipynb   # or open in Colab with the badge
streamlit run deployment/app.py
```

The Colab badge only works once the GitHub repo is **public**, because the notebook clones it.

## Progress
| Phase | Notebook | Report | Critic rounds |
|---|---|---|---|
| 1 · Business Understanding | ☐ | ☐ | 0 |
| 2 · Data Understanding | ☐ | ☐ | 0 |
| 3 · Data Preparation | ☐ | ☐ | 0 |
| 4 · Modeling | ☐ | ☐ | 0 |
| 5 · Evaluation | ☐ | ☐ | 0 |
| 6 · Deployment | ☐ | ☐ | 0 |
| Medium article · Video script | ☐ | | 0 |
