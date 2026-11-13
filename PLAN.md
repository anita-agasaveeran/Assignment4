# CMPE 255 Assignment 4: Project Plan

Three end-to-end data science projects. Each one uses a different methodology and a different dataset:

| # | Methodology | Dataset | Core problem | Main techniques |
|---|---|---|---|---|
| 1 | **CRISP-DM** | Wine Reviews (≈120k real WineEnthusiast reviews, 2017) | Help a retailer's buying team find unscored wines ≤ $25 likely to score 90+ | Text regression/ranking, flavour-profile clustering, association rules, MinHash LSH, critic-effect model, outlier analysis |
| 2 | **SEMMA** | US flight delays (11.7M flights, Jan 2025 – Aug 2026) | Predict at schedule time whether a flight will arrive 15+ min late | Statistical sampling, logistic regression / decision tree / neural net / gradient boosting, lift and ROC assessment |
| 3 | **KDD** | Canadian electricity generation and trade (StatCan, 2008–2026) | Find and validate knowledge about how provincial power systems differ and change, and forecast availability | Data selection and integration, clustering, change-point detection, anomaly detection, time-series forecasting |

### Why each dataset goes with each methodology
- **CRISP-DM ↔ Wine.** CRISP-DM begins with business understanding and ends with deployment. The wine data supports a concrete buyer decision (which unscored wines to sample), an achievable baseline (simple rules vs text models on held-out critics) and an obvious deployable tool: a *Value Finder* app. Schröer et al. (2021) found that most CRISP-DM papers skip deployment, so this project makes deployment a first-class deliverable. *(Update 2026-11-03: the project first used a bakery dataset. Phase 1 critic reviews showed it was unsuitable: synthetic, with generated production fields and tiny volumes. See `_archive/README.md`.)*
- **SEMMA ↔ Flights.** SEMMA starts with **Sample**. SAS's own best-practices paper (*Data Mining and the Case for Sampling*, in `resources/`) argues for sampling large databases instead of processing everything. At 11.7M rows, this is the only dataset where sampling is actually needed. The plan can follow that paper's structure: access → sample → partition → model → assess.
- **KDD ↔ Canadian electricity.** KDD (Fayyad et al., 1996) is about getting from a *database* to *knowledge*, and its early steps are selection, preprocessing and transformation. This dataset arrives as raw, long-format statistical tables. It has nested subtotals, suppression codes (`..`, `x`), two source tables to integrate, and an accounting identity to verify. That gives the KDD front-end steps real work to do, and the goal is discovering patterns rather than serving a single business KPI.

---

## Shared approach (all three projects)

**Repository layout**
```
Assignment4/
├── README.md                    # overview, links to notebooks/articles/videos
├── PLAN.md                      # this file
├── requirements.txt
├── resources/                   # reference papers
├── 01_CRISP-DM_Wine_Value/
├── _archive/                   # abandoned bakery attempt (documented pivot)
├── 02_SEMMA_Flight_Delays/
└── 03_KDD_Canada_Electricity/
    ├── data/                    # raw (or pointer to Kaggle) + processed
    ├── notebooks/               # Colab-ready .ipynb, one per phase + one end-to-end
    ├── src/                     # reusable pipeline code used by notebooks and the app
    ├── deployment/              # app / scoring service / saved model
    ├── reports/                 # detailed final report (Markdown → PDF) + figures
    ├── critiques/               # critic review log, round by round
    ├── article/                 # Medium article draft (later moved outside the repo)
    └── video/                   # walkthrough script + shot list
```

**Notebooks:** they will be Colab-ready. Each opens with an "Open in Colab" badge, a pip-install cell, and code that loads data from the GitHub raw URL (or from Kaggle for the large flight file). Every phase has its own section, plus a "phase outputs" checklist that maps to the methodology's official tasks. Random seeds will be fixed, and I'll run every notebook top to bottom locally before it's committed.

**Critic review loop (required by the assignment):**
- For each phase of each project, I run a separate Claude critic with this persona: *"You are a world-renowned speaker and authority on [CRISP-DM / SEMMA / KDD] and have written many award-winning books on it."*
- The critic scores the section, lists gaps against the methodology's official tasks, and points out weak reasoning, leakage and missing evidence.
- I revise, then the critic reviews again. That's at least 2 rounds per phase, and more until the critic has no major issues left.
- Every round is saved to `critiques/<phase>_round<N>.md`: prompt, critique, the changes I made, and the score before and after. This file is the audit trail showing multiple revisions.

**Verification:** every number in a report or article comes from a cell that actually ran. Every model is compared against a naive baseline. Leakage is checked explicitly, meaning no features that wouldn't be known at prediction time.

**Deliverables per project:** Colab notebook(s), detailed report, deployment artifact, critique log, Medium article draft, and video script.

---

## 1. CRISP-DM: Finding value wines

**Data:** [Wine Reviews](https://www.kaggle.com/datasets/zynicide/wine-reviews) (Zack Thoutt; WineEnthusiast, scraped June 2017; CC BY-NC-SA 4.0). 129,971 rows; 119,988 unique reviews with tasting note, 80–100 score, price, origin, grape, winery and critic.

**Plan of record:** `01_CRISP-DM_Wine_Value/reports/final_report.md` §1 is the authoritative Phase 1 output (business objectives, success criteria, frozen critic-fold/lockbox evaluation design, data mining goals DM1–DM6 and the dated project plan).

**Earlier attempt:** the bakery dataset plan that used to be here is archived. The reasons are in `_archive/README.md` and the two critic reviews in `_archive/01_CRISP-DM_Bakery_Waste/critiques/`.

---

## 2. SEMMA: Flight arrival-delay prediction

**Data:** `data/flight_delays/`:
- `flights.parquet`: 11,730,351 flights × 40 columns, Jan 2025 – Aug 2026
- `flights_sample.csv`: 500k rows
- `airlines.csv`, `airports.csv`: lookup tables
- `daily_airport_stats.csv`: daily per-airport stats

Base rates: 22.8% of flights arrive 15+ min late, 1.8% are cancelled, 0.3% diverted.

**Business problem:** passengers and airline operations want to know, *when the flight is booked or scheduled*, how likely it is to arrive 15+ minutes late. That lets them choose safer itineraries, set connection buffers and plan staffing. Target: `arr_del15` (binary).

**Leakage rule:** only use information known before departure. That excludes `dep_time`, `dep_delay`, taxi and wheels times, actual elapsed time, the delay-cause columns and *same-day* airport stats. Historical rates for airlines, airports and routes are computed from the training period only, or from lagged days.

### Phase plan

| Phase | What we do | Key outputs |
|---|---|---|
| *(Problem framing)* | SEMMA has no business-understanding step, so a short framing section comes first. The course slides make this same point about SEMMA vs CRISP-DM | Problem statement, success metric (ROC-AUC, PR-AUC, top-decile lift) |
| **Sample** | Follows the SAS sampling paper: (1) access the full parquet; (2) build a **learning curve** (model quality vs sample size: 50k, 100k, 250k, 500k, 1M, 2M) to *justify* the sample size statistically; (3) draw a stratified random sample (by month × airline × delay class) and check it matches the population; (4) partition **by time**: train 2025, validate Jan–Apr 2026, test May–Aug 2026 | Sample-size justification, representativeness checks, train/valid/test sets |
| **Explore** | Delay rates by airline, hour block, day of week, month, airport and route. Delay-cause breakdown, used for insight only. Correlations, and clustering of airports by delay profile | EDA figures, list of findings |
| **Modify** | Departure hour, weekday, month and holiday flags. Distance bands. Scheduled congestion (flights scheduled per airport-hour, which is known in advance). Historical delay rates by airline, origin, destination and route from training data (leakage-safe target encoding). Airport metadata (elevation, size). Missing-value handling, rare-category grouping and outlier treatment | Feature pipeline (`ColumnTransformer`), leakage audit table |
| **Model** | Mirrors SAS Enterprise Miner's standard nodes: **logistic regression**, **decision tree**, **neural network (MLP)**, plus **gradient boosting (LightGBM)**. Class-imbalance handling and hyperparameter tuning on the validation set | Fitted models, tuning logs |
| **Assess** | On the held-out test months: ROC/PR curves, **cumulative lift and gains charts** (the SAS Assess style), calibration, confusion matrix at a business-chosen threshold, and performance broken down by airline and airport. Pick the champion model | Model comparison report, champion model |
| *(Score / deploy)* | SEMMA ends at Assess, but the assignment asks for deployment, so I'll export a **scoring package** (the Python version of SAS EM's Score node): saved pipeline, `score.py` for batch scoring and a small Gradio/Streamlit "delay risk" demo | `deployment/` |

**SAS (optional):** I can't run SAS. If you want the SAS demo the instructions suggest, *SAS OnDemand for Academics* is free for students. I can write step-by-step instructions to rebuild the same flow there (Sample → Data Partition → Regression / Decision Tree / Neural Network → Model Comparison), and you would run and record it.

---

## 3. KDD: Knowledge discovery in Canadian electricity data

**Data:** `data/canada_electricity/` (Kaggle, adapted from Statistics Canada tables 25-10-0015-01 and 25-10-0016-01, Jan 2008 – Aug 2026, MWh):
- `generation_monthly.csv`: 76,776 rows by province × producer class × generation type
- `flows_monthly.csv`: 37,888 rows of receipts/deliveries, interprovincial and US trade
- `availability_panel.csv`: 3,136 province-month balance panels
- Ready-made seasonal-naive backtest: 12-month-ahead WAPE of 3.30% across all geographies. This is a fixed benchmark to beat.

**Problem / knowledge goals:** for energy analysts and policymakers, find out from the data itself:
1. **Which provinces behave alike?** Cluster provinces by generation mix, trade dependence and seasonal shape.
2. **When did each system change structurally?** Change-point detection on fossil share, renewables share and net imports (e.g. coal phase-outs, new hydro and wind capacity).
3. **Which months are anomalous?** Unusual generation or trade months, such as droughts cutting hydro output or extreme weather.
4. **Can availability be forecast better than the seasonal-naive benchmark?** This is the predictive-knowledge check.

### Phase plan (Fayyad et al. KDD process)

| Step | What we do | Key outputs |
|---|---|---|
| **0. Domain understanding & goals** | Background on Canada's grid (hydro-heavy provinces vs fossil-heavy ones, trade with the US). Define the knowledge goals above and how each will be judged as "interesting and valid" | Goal statement, evaluation criteria |
| **1. Selection** | Pick the target data: 10 provinces + 3 territories, kept separate from the `Canada` aggregate. Choose non-overlapping generation types (avoid double-counting nested subtotals) and the right producer class. Choose flow components. Document what's excluded and why | Selection spec, target dataset |
| **2. Preprocessing (cleaning + integration)** | Map status codes (`..` unavailable, `x` suppressed) to missing. Measure missingness by geography and type and decide whether territories stay in. Integrate the two source tables and confirm the cross-table generation match. Verify the accounting identity (generation + receipts − deliveries = availability) and flag the Feb 2019 BC residual instead of "fixing" it | Clean integrated panel, data quality report |
| **3. Transformation** | Pivot to province × month × type. Build mix shares (%), net-import ratio, renewables/fossil share, YoY change, STL seasonal/trend decomposition, normalized seasonal profiles and per-province feature vectors for clustering | Feature tables |
| **4. Data mining** | **(a) Clustering:** k-means + hierarchical (and DTW on seasonal profiles), choosing k with silhouette scores. **(b) Change points:** PELT/binary segmentation (`ruptures`) on share series. **(c) Anomalies:** STL residual z-scores + Isolation Forest. **(d) Forecasting:** ETS/SARIMA and gradient boosting with lag features, using **the same 7 December forecast origins and 12-month horizon** as the provided seasonal-naive backtest so the comparison is fair | Clusters, change-point dates, anomaly list, forecast metrics |
| **5. Interpretation / evaluation** | Check every discovered pattern against public records (e.g. known coal-plant closures, major hydro projects, drought years). Rank patterns by validity, novelty, usefulness and understandability, the KDD "interestingness" criteria. Report the forecast win or loss vs the benchmark honestly | Validated knowledge base: findings with evidence and confidence |
| **6. Using the knowledge (deployment)** | Interactive dashboard (Streamlit) of the clusters, change points, anomalies and forecasts. A reusable `refresh.py` that rebuilds everything from new StatCan releases. A knowledge report | `deployment/`, final report |

**Licensing note:** the dataset is under the Statistics Canada Open Licence, not CC0. The repo will include the required attribution notice (`SOURCE_NOTICES.md`).

---

## Order of work and checkpoints

1. **Repo scaffold:** folder structure, `requirements.txt`, `.gitignore` (excluding the large flight files), README skeleton.
2. **CRISP-DM project:** one phase at a time, each with critic rounds → notebook → report → app → article → video script.
3. **SEMMA project:** same flow.
4. **KDD project:** same flow.
5. **Top-level README** linking everything. Then I push to GitHub, only after you approve.

I'll check in with you after each project is finished, before starting the next one.

## What only you can do
- Publish the three Medium articles. I'll write publish-ready drafts.
- Record the YouTube walkthroughs. I'll write scripts and shot lists.
- Open the notebooks in Colab. The badges will work once the repo is pushed.
- Optional: the SAS OnDemand demo for SEMMA.

## Open questions
1. **Kaggle URLs** for the bakery and flight datasets. They're needed for citations and for downloading the full flight data in Colab. The Canada dataset's source is documented.
2. **Large flight file:** `flights.parquet` (314 MB) is too big for GitHub. My recommendation is to commit the stratified sample produced in the SEMMA *Sample* step (expected to be well under 100 MB) and download the full file from Kaggle inside Colab.
3. **Deployment hosting:** a local Streamlit app is the default. If you want public links, deploying to Streamlit Community Cloud or Hugging Face Spaces needs your account.
