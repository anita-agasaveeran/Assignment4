# Project 3: KDD · Is Canada's Grid Becoming Less Combustion-Dependent?

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/anita-agasaveeran/Assignment4/blob/main/03_KDD_Canada_Electricity/notebooks/KDD_Canada_Electricity.ipynb)

**Problem:** use monthly Statistics Canada electricity data (2008–2026; analysed from 2016, after a survey-coverage break) to find which provinces behave alike, when their power systems changed, which months were anomalous, and whether availability can be forecast better than a seasonal-naive benchmark.

**Methodology:** the KDD process (Fayyad et al., 1996): goals → selection → preprocessing → transformation → data mining → interpretation/evaluation → using the knowledge. A front pass (data checks, frozen holdouts) comes first. The acceptance rules were pre-registered and hash-frozen (`PREREGISTRATION.json`) before mining.

**Answer:** *not nationally.* The combustion share was 21.2% in 2016 and 22.9% in 2025. Alberta and Nova Scotia are structurally less combustion-dependent; Ontario is more (gas covering nuclear refurbishments); and 2023–24 hydro droughts shrank the total.

| Goal | Verdict |
|---|---|
| K1 Archetypes (5 stable groups) | ✅ met (ARI 1.00) |
| K2 Structural change | ✅ met as written (5 qualify); in substance AB and NS (+ a small NL decline) |
| K3 Anomalies vs public-record events | ❌ not met (event-level precision 0.11, p = 0.25) |
| K4 Forecast vs seasonal naive | ❌ not met (sealed ratio 1.015) |

**Data:** StatCan tables 25-10-0015-01 and 25-10-0016-01 via [Kaggle](https://www.kaggle.com/datasets/hgultekin/canada-monthly-electricity-benchmark) (Statistics Canada Open Licence). See [`data/README.md`](data/README.md) and [`deployment/SOURCE_NOTICES.md`](deployment/SOURCE_NOTICES.md).

## Status
| Step | Status |
|---|---|
| Front pass (goals, data checks, frozen holdouts, feasibility) | ✅ ([report](reports/front_pass.md); critic 6 → 8/10) |
| 1 Selection · 2 Preprocessing · 3 Transformation | ✅ (critic round 1: 7/10, 3 MAJOR issues fixed; [log](critiques/kdd_steps1-3_round1.md)) |
| 4 Data mining (k-means/Ward, PELT, STL + Isolation Forest, forecasting) | ✅ |
| 5 Interpretation / evaluation (seal lifted once; all four rules reported) | ✅ (critic round 2: 7.5/10, 2 MAJOR issues fixed; [log](critiques/kdd_steps4-6_round2.md)) |
| 6 Using the knowledge (Streamlit dashboard, `refresh.py`, knowledge base) | ✅ ([deployment](deployment/)) |
| Final report · Medium article · video script | ✅ drafts ([report](reports/final_report.md), [article](article/medium_article.md), [video](video/script.md)) |

## Layout
| Path | What |
|---|---|
| `notebooks/KDD_Canada_Electricity.ipynb` | The whole project, executed with outputs (Colab-ready) |
| `src/kddenergy/` | `data` (sealed loaders) · `selection` · `preprocess` · `transform` · `mining` (K1–K3) · `forecast` (K4) · `prereg` · `config` (all rules) |
| `tests/` | 30 unit tests (seal, integration, transformations, rule edge cases, permutation null, dashboard) |
| `data/raw/` · `data/external/` · `data/processed/` | Kaggle/StatCan files · K3 event catalogue (frozen) · derived tables |
| `critiques/` | Critic prompt and every round's log |
| `deployment/` | `app.py`, `refresh.py`, `knowledge.json`, `artifacts/`, `SOURCE_NOTICES.md` |
| `reports/` | `front_pass.md`, `final_report.md`, `figures/` |

## Run locally
```bash
.venv/bin/python -m pytest -q 03_KDD_Canada_Electricity/tests
.venv/bin/python 03_KDD_Canada_Electricity/deployment/refresh.py
.venv/bin/streamlit run 03_KDD_Canada_Electricity/deployment/app.py
```

---
*Adapted from Statistics Canada, Tables 25-10-0015-01 and 25-10-0016-01, Statistics Canada Open Licence. This does not constitute an endorsement by Statistics Canada.*
