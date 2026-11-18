# CMPE 255 Assignment 4: CRISP-DM, SEMMA and KDD

Three end-to-end data science projects, each following a different methodology on a different dataset. The full plan is in [PLAN.md](PLAN.md).

| # | Methodology | Project | Dataset | Status |
|---|---|---|---|---|
| 1 | CRISP-DM | [Finding Value Wines](01_CRISP-DM_Wine_Value/) | Wine Reviews, WineEnthusiast (Kaggle) | All six phases done: lockbox test passed, pilot decision rule frozen; Streamlit app, model card, monitoring plan, report (tag `wine-phase6-rev7`); article and video published |
| 2 | SEMMA | [Will My Flight Be Disrupted Tomorrow?](02_SEMMA_Flight_Delays/) | US BTS flights 2025–26 (Kaggle, CC0) | All SEMMA stages + Score done: sealed test summer lift 2.39 vs 1.70 (best rule), targets T1–T3 met; app + report; article and video published |
| 3 | KDD | [Is Canada's Grid Becoming Less Combustion-Dependent?](03_KDD_Canada_Electricity/) | StatCan generation & trade (Kaggle, StatCan Open Licence) | All KDD steps done: K1, K2 met; K3, K4 not met (reported); dashboard + report; article and video published |

Each project folder has a Colab notebook, a detailed report, deployment artifacts, and a critic review log. The Colab notebooks, Medium articles and walkthrough videos are linked below.

## Colab notebooks
| # | Methodology | Notebook |
|---|---|---|
| 1 | CRISP-DM | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/anita-agasaveeran/Assignment4/blob/main/01_CRISP-DM_Wine_Value/notebooks/CRISP_DM_Wine_Value.ipynb) [`CRISP_DM_Wine_Value.ipynb`](01_CRISP-DM_Wine_Value/notebooks/CRISP_DM_Wine_Value.ipynb) |
| 2 | SEMMA | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/anita-agasaveeran/Assignment4/blob/main/02_SEMMA_Flight_Delays/notebooks/SEMMA_Flight_Disruption.ipynb) [`SEMMA_Flight_Disruption.ipynb`](02_SEMMA_Flight_Delays/notebooks/SEMMA_Flight_Disruption.ipynb) |
| 3 | KDD | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/anita-agasaveeran/Assignment4/blob/main/03_KDD_Canada_Electricity/notebooks/KDD_Canada_Electricity.ipynb) [`KDD_Canada_Electricity.ipynb`](03_KDD_Canada_Electricity/notebooks/KDD_Canada_Electricity.ipynb) |

## Medium articles
| # | Methodology | Article |
|---|---|---|
| 1 | CRISP-DM | [The $20 Bottle That Scores Like a $44 One: Finding Value Wines with CRISP-DM](https://medium.com/@anita.agasaveeran/the-20-bottle-that-scores-like-a-44-one-finding-value-wines-with-crisp-dm-a190430678ab) |
| 2 | SEMMA | [Which 380 Flights Will Go Wrong Tomorrow? A SEMMA Walkthrough on 11.7 Million US Flights](https://medium.com/@anita.agasaveeran/which-380-flights-will-go-wrong-tomorrow-a-semma-walkthrough-on-11-7-million-us-flights-b5c72c315992) |
| 3 | KDD | [Is Canada's Grid Getting Less Dependent on Burning Fuel? What a Decade of StatCan Data Actually Says](https://medium.com/@anita.agasaveeran/is-canadas-grid-getting-less-dependent-on-burning-fuel-81a2680c654d) |

## Videos
| # | Methodology | Video |
|---|---|---|
| 1 | CRISP-DM | [CRISP-DM notebook walkthrough](https://www.loom.com/share/1a678ca245d24bc3875fe6b4f54f29b4) (Loom) |
| 2 | SEMMA | [SEMMA notebook walkthrough](https://www.loom.com/share/dc312f1a15fc444baf1fa86dd301e552) (Loom) |
| 3 | KDD | [KDD notebook walkthrough](https://www.loom.com/share/e78a7b42159d4d64a8f3b5b403ef4822) (Loom) |

## Setup
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

`_archive/` holds the abandoned first CRISP-DM dataset (bakery), documented as a CRISP-DM pivot. Course instructions and reference papers are kept locally and not committed. Citations are in each project's report. `data/` (the original downloads) is git-ignored. Each project keeps the copy of the data it uses.
