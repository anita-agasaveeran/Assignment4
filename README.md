# CMPE 255 Assignment 4: CRISP-DM, SEMMA and KDD

Three end-to-end data science projects, each following a different methodology on a different dataset. The full plan is in [PLAN.md](PLAN.md).

| # | Methodology | Project | Dataset | Status |
|---|---|---|---|---|
| 1 | CRISP-DM | [Finding Value Wines](01_CRISP-DM_Wine_Value/) | Wine Reviews, WineEnthusiast (Kaggle) | Phase 1 done |
| 2 | SEMMA | [Will My Flight Be Disrupted Tomorrow?](02_SEMMA_Flight_Delays/) | US BTS flights 2025–26 (Kaggle, CC0) | front pass done |
| 3 | KDD | [Is Canada's Grid Becoming Less Combustion-Dependent?](03_KDD_Canada_Electricity/) | StatCan generation & trade (Kaggle, StatCan Open Licence) | front pass done |

Each project folder has a Colab notebook, a detailed report, deployment artifacts, a critic review log, a Medium article draft and a video script.

## Setup
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

`_archive/` holds the abandoned first CRISP-DM dataset (bakery), documented as a CRISP-DM pivot. Course instructions and reference papers are kept locally and not committed. Citations are in each project's report. `data/` (the original downloads) is git-ignored. Each project keeps the copy of the data it uses.
