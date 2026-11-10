# Project 1: CRISP-DM · Finding Value Wines

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/anita-agasaveeran/Assignment4/blob/main/01_CRISP-DM_Wine_Value/notebooks/CRISP_DM_Wine_Value.ipynb)

**Problem:** most wines a retailer considers have no critic score yet. Can a tasting note tell a buying team which unscored wines under $25 are likely to score 90+, so their limited samples are spent on the right bottles?

**Methodology:** CRISP-DM 1.0, all six phases and every generic task.

**Data:** about 120k real WineEnthusiast reviews ([Kaggle](https://www.kaggle.com/datasets/zynicide/wine-reviews), CC BY-NC-SA 4.0). See [`data/README.md`](data/README.md).

## Structure
| Path | Contents |
|---|---|
| `notebooks/CRISP_DM_Wine_Value.ipynb` | End-to-end Colab notebook, one section per phase and task, saved with outputs |
| `src/winevalue/` | Reusable code (loading, splits, baselines, models, metrics), shared by the notebook and the app |
| `tests/` | Unit tests (`pytest tests`) |
| `data/raw/`, `data/processed/` | Untouched source data (gzip) / derived datasets |
| `models/` | Saved model pipeline(s) |
| `deployment/` | Streamlit Value Finder, monitoring plan, model card |
| `reports/` | Final CRISP-DM report and figures |
| `critiques/` | Critic persona prompt and round-by-round review log |
| `article/` | Medium article draft |
| `video/` | Walkthrough script and shot list |

## Run
```bash
# from the repo root
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cd 01_CRISP-DM_Wine_Value
pytest tests
jupyter notebook notebooks/CRISP_DM_Wine_Value.ipynb   # or open in Colab with the badge
streamlit run deployment/app.py
```

The Colab badge only works once the GitHub repo is **public**, because the notebook clones it.

## Licence
The data is CC BY-NC-SA 4.0 (Zack Thoutt / WineEnthusiast). Derived outputs in this folder (reports, figures, models) are shared under the same licence. Non-commercial use only.

## Progress
| Phase | Notebook | Report | Critic rounds |
|---|---|---|---|
| 1 · Business Understanding | ✅ | ✅ | 3 rounds (7 → 8 → 9/10) |
| 2 · Data Understanding | ✅ | ✅ | 3 rounds (6 → 7.5 → 8.5/10) |
| 3 · Data Preparation | ✅ | ✅ | 2 rounds (7 → 8/10) |
| 4 · Modeling | ✅ | ✅ | 3 rounds (6 → 7 → 8/10) |
| 5 · Evaluation | ✅ | ✅ | 3 rounds (6 → 8 → 9/10) |
| 6 · Deployment | ✅ | ✅ | 6 rounds (7 → 8 → 8 → 8 → 8 → 9/10), no major issues; round-6 minors fixed (revision 7) |
| Medium article · Video script | ☐ | | 0 |

The CRISP-DM project originally used a bakery dataset that turned out to be unsuitable. See [`../_archive/README.md`](../_archive/README.md).
