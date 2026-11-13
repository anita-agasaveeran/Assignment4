# CMPE 255 Assignment 4: CRISP-DM, SEMMA and KDD

Three end-to-end data science projects, each following a different methodology on a different dataset. The full plan is in [PLAN.md](PLAN.md).

| # | Methodology | Project | Dataset | Status |
|---|---|---|---|---|
| 1 | CRISP-DM | [Finding Value Wines](01_CRISP-DM_Wine_Value/) | Wine Reviews, WineEnthusiast (Kaggle) | All six phases done: lockbox test passed, pilot decision rule frozen; Streamlit app, model card, monitoring plan, report (tag `wine-phase6-rev7`); article and video script still outlines |
| 2 | SEMMA | [Will My Flight Be Disrupted Tomorrow?](02_SEMMA_Flight_Delays/) | US BTS flights 2025–26 (Kaggle, CC0) | All SEMMA stages + Score done: sealed test summer lift 2.39 vs 1.70 (best rule), targets T1–T3 met; app + report + article/video drafts |
| 3 | KDD | [Is Canada's Grid Becoming Less Combustion-Dependent?](03_KDD_Canada_Electricity/) | StatCan generation & trade (Kaggle, StatCan Open Licence) | All KDD steps done: K1, K2 met; K3, K4 not met (reported); dashboard + report + article/video drafts |

Each project folder has a Colab notebook, a detailed report, deployment artifacts, a critic review log and a video script. The Medium article drafts are kept outside the repo.

## Setup
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

`_archive/` holds the abandoned first CRISP-DM dataset (bakery), documented as a CRISP-DM pivot. Course instructions and reference papers are kept locally and not committed. Citations are in each project's report. `data/` (the original downloads) is git-ignored. Each project keeps the copy of the data it uses.
