# Is Canada's Grid Becoming Less Combustion-Dependent? Knowledge Discovery with the KDD Process

**CMPE 255 · Assignment 4 · Project 3 of 3**
**Methodology:** KDD (Fayyad, Piatetsky-Shapiro & Smyth, 1996).
**Notebook:** [`notebooks/KDD_Canada_Electricity.ipynb`](../notebooks/KDD_Canada_Electricity.ipynb). It runs end to end with saved outputs, and every number below comes from it.
**Critic log:** [`critiques/`](../critiques/).

> Depth note: this project was finished under a deadline at a lighter depth than the CRISP-DM project. Every KDD step is present and every acceptance rule is reported honestly, but some checks (e.g. a line-by-line source check of the event catalogue) are listed as limitations instead of done.

---

## Summary

| Goal | Pre-registered acceptance rule | Result | Verdict |
|---|---|---|---|
| **K1 Archetypes:** which geographies behave alike? | ARI between 2016–24 and 2025–26 clusters ≥ 0.7 | ARI **1.00** at k = 5 (secondary check 1.00; post hoc 0.27–0.84 at other k) | **MET** |
| **K2 Structural change:** when did combustion shares change? | ≥ 3 non-Ontario provinces with a change point that is stable (trimmed-window ≥ 70%) and persistent (margin test on 2025–26) | 5 qualify as written (NL, PE, NS, AB, BC). **In substance: AB and NS** (large, burning-driven) plus a small NL decline; BC and PE qualified because a 12-month blip ended | **MET as written** |
| **K3 Anomalies:** which months were unusual? | Event-level precision ≥ 0.5 vs a catalogue fixed before mining, and permutation p ≤ 0.05 | Precision **0.11** (3/28), p = 0.25 | **NOT MET** |
| **K4 Prediction:** beat seasonal naive? | Sealed pooled WAPE ≤ 0.90 × seasonal naive, and better at both sealed origins | Ratio **1.015** (90% CI 0.92–1.15). Better at 2024-12 (0.969), worse at 2025-12 (1.145) | **NOT MET** |

**Answer to the title question: not nationally.** The 13-geography combustion share was 21.2% in 2016, 19.1% at its 2020 low, 22.1% in 2024 and 22.9% in 2025. Under that flat-to-rising national line the provinces pull in opposite directions:
- **Alberta** (91.5% → 78.2% over 2016–24, then 76.0% in 2025) and **Nova Scotia** (81.4% → 73.6%) are structurally less combustion-dependent;
- **Ontario** rose from 6.7–8.7% (2017–20) to 17.5% (2024) and 21.0% (2025). Since 2019 its nuclear output is down 12 TWh/yr (refurbishments), roughly half of its +22 TWh combustion rise; the rest is demand growth and exports;
- the 2023–24 hydro droughts in Quebec, BC and Manitoba shrank the denominator.

**Decomposition (descriptive):** combustion rose 136.7 → 143.4 TWh from 2016 to 2025 (ON +18.6, AB −6.7, others ≈ −5). Holding total generation at its 2016 level would give 22.2%, so the shrinking denominator explains about 40% of the share rise.

---

## 0. Domain understanding and goals (front pass)
The front pass ([`front_pass.md`](front_pass.md); critic rounds 6/10 → 8/10) set the goals, the acceptance rules and the frozen holdouts, and checked the data:
- **Holdouts:** discovery 2016-01 → 2024-12, confirmation 2025-01 → 2026-08; K4 sealed origins 2024-12 and 2025-12. The loaders enforce this (`allow_sealed=False`), and tests check it.
- **The 2016 break:** StatCan's survey coverage expanded in January 2016 (industrial wind/solar/tidal first reported; Canada total +9%) and thermal output was reclassified. So every cross-year analysis starts in 2016-01 (`CONSISTENT_START`).
- **Scope:** the data records *sources*, not emissions. A coal → gas switch is invisible, so K2 asks about combustion *dependence*, not "cleanliness".

## 1. Selection
- **Geographies:** 10 provinces + 3 territories. The `Canada` aggregate is excluded (it equals the sum of the provinces).
- **Producer class:** all producers.
- **Generation types (non-overlapping):** total, hydro, nuclear, wind, solar, tidal, other, and the combustible-fuels total.
- **Flows:** total, provincial and US receipts and deliveries; availability.
- **Not selected:** firm/non-firm splits and "other receipts from the US", which are `..` for every month since 2016.
- **Target dataset:** 1,404 geo-months (13 × 108) × 16 series.
- The selection is code (`selection.build_panel`), so a refresh rebuilds exactly the same dataset.

## 2. Preprocessing
- **Status codes → missing.** Every remaining gap is a *whole series* a geography never publishes (no nuclear outside ON/NB, no trade for the territories, no US tie for PEI). Those are **structural zeros**. After cleaning there are 0 missing cells.
- **Integration:**
  - the two StatCan tables agree exactly on total generation;
  - receipt and delivery parts add up exactly;
  - generation types sum to the total within 300 MWh;
  - the availability identity holds everywhere except **BC, Feb 2019** (+70,931 MWh), which is flagged and not fixed.
- **Data-break register:**
  - **Nunavut, 2024-10:** industrial producers first reported; total doubles. Excluded from K3 from then on.
  - **NL, 2021-02:** industrial hydro first reported (+1.5%). The NL 2021-01 → 03 window is excluded from K3.
  - **NS, 2020:** the industrial collapse (Northern Pulp closure) is a real change and is kept.
- **Event catalogue (K3 ground truth):**
  - 40 discovery-period + 4 confirmation-period public-record events (storms, cold, heat, flood, drought, wildfire, the COVID-19 lockdown);
  - written before mining and hash-frozen;
  - revised once, after critic round 1 and still before mining.

## 3. Transformation
- **Mix shares:** hydro, nuclear, wind + solar, combustion and non-emitting, each as a share of total generation.
- **Trade ratios:** net imports, trade intensity and US net exports, each as a share of availability.
- **Seasonal profile:** winter/summer ratio.
- **K1 feature vectors are calendar-month balanced:** each series is averaged by calendar month first, so the 20-month confirmation window counts like one year. Eight features; the amplitude feature was dropped as redundant (r = 0.97).
- **K2 input:** the combustion share, deseasonalized with the 2016–24 climatology. The same climatology is reused for 2025–26.
- **K3 input:** robust STL (period 12) residual z-scores for log availability, log generation and the net-import ratio. The z scale uses discovery months only.

**What the transformation already showed:**
- three visible system types plus two outliers (PEI imports 61% of its supply; NL exports almost three times its own use);
- electric-heating provinces peak at 1.5–1.7× in winter, while Ontario is flat;
- four provinces have moving combustion shares (AB, NS, ON, NB).

**Pre-registration.** After critic round 1, the operational K1–K4 rules were written into `config.py`. SHA-256 hashes of every rule file (config, catalogue, rule code, tests) went into `PREREGISTRATION.json` (2026-11-11 21:14:59 UTC) before any K1–K3 mining. The notebook calls `prereg.verify()` before mining and again before evaluation. *Disclosure:* the K4 development backtest (development origins only, i.e. legitimate model selection) was run once before the manifest; no K4 rule changed.

## 4. Data mining
| Task | Method (fixed in config) | Pattern found (development data) |
|---|---|---|
| K1 | k-means (100 inits, seed 42) + Ward, standardized features, k = 2–6, k by silhouette | **k = 5** (silhouette 0.382). k-means = Ward (ARI 1.00 for every k ≥ 3). Archetypes: hydro (QC, MB, BC, YT), combustion (AB, SK, NS, NT, NU), nuclear-mixed traders (ON, NB), PEI, NL |
| K2 | PELT (`ruptures`, L2 cost, min segment 12 months, penalty 3·log n on x / σ, σ = 1.4826·MAD(diff)/√2). Primary change point = largest shift ≥ 1 pp | Primary change points in 8 of 10 provinces. Falling: AB 2023-01 (−5.2 pp, burning), NS 2021-12 (−6.0, burning), BC 2020-03 (−2.4, denominator), NL 2018-02 (−1.4, burning), PE 2018-12 (−2.2, burning). Rising: ON 2023-06 (+5.6, burning), SK 2020-10 (+5.2), NB 2024-01 (+16.8, denominator) |
| K3 | Isolation Forest (500 trees) on the 3 STL z-scores; flag budget = top 2% of eligible geo-months (28) | Flags cluster in NU (6), NB (11) and MB (6). Max-\|z\| agrees on 20 of 28 |
| K4 | Three candidates on availability since 2016: growth-adjusted 3-year seasonal mean, damped Holt-Winters on logs, equal-weight combination | Combination chosen: development WAPE 3.59% vs seasonal naive 4.08% (ratio 0.880, 90% CI 0.83–0.93); better on 78% of pairs, but not at every origin |

Change-point stability uses PELT re-run on 25 trimmed sub-series of the *observed* data, so it isn't a model-based bootstrap. A residual block bootstrap and a σ = s.d. sensitivity run are reported as secondary checks: AB, NS, NB, ON, NL and PE survive the conservative σ; BC and SK don't.

## 5. Interpretation / evaluation
The seal was lifted once, after `prereg.verify()`. All four rules were then applied exactly as written (summary table at the top).

**K1 (met).** All 13 geographies keep their archetype in 2025–26 under both the primary (re-clustered) and the secondary (development scaler + nearest centroid) checks. At k = 5, the rule tolerates one geography moving (one-move ARI 0.70–0.96). Two singletons (PEI, NL) make agreement easier.
- **The persistence is specific to k = 5** (post hoc: ARI 0.03 / 0.27 / 0.60 / 0.84 at k = 2 / 3 / 4 / 6).
- **Within-archetype drift is large** (ON combustion 0.11 → 0.22, YT 0.14 → 0.31, AB 0.88 → 0.75).
- This is valid but not novel knowledge: the archetypes match the Canada Energy Regulator's provincial profiles.

**K2 (met as written).**
- **The rule fired for 5 provinces:** NL, PE, NS, AB, BC.
- **Critic round 2 showed that "largest adjacent shift" picked up the end of a 12-month episode in two of them:**
  - **BC:** +0.6 pp first-to-last segment, so no net decline;
  - **PE:** −0.5 pp vs 2016–17, below the 1 pp floor.
- **NL** is a staircase (5.3% → 2.3%), and the primary step is 1.4 pp.
- **Disclosed post-hoc sensitivity:** (a) net first-to-last change ≥ 1 pp and (c) burning-driven leaves **NL, NS and AB**, exactly 3. Also requiring (b) segments ≥ 18 months would remove AB, because its ramp is split into short segments.
- **The substantive knowledge:** two large, burning-driven, persistent declines (**AB** −5.2 pp at 2023-01 and **NS** −6.0 pp at 2021-12) plus a small NL decline.
- **Ontario** rose (+5.6 pp) but missed the stability bar (67% vs 70%), and its confirmation was partly spent. Across the step itself, combustion rose 912 GWh/month, availability about 375 and net exports about 413.
- **Saskatchewan's** rise had already reversed by 2024.
- **New Brunswick's** 2024 jump is unstable and denominator-driven.
- **Next cycle:** pre-register a minimum segment length and a materiality threshold.

**K3 (not met).**
- **Result:** event-level precision 0.11 (3 of 28 flags credited), against a permutation null mean of 0.07 (95th percentile 0.14), so p = 0.25. Flag-level precision 0.25; recall 3/40.
- **The max-|z| comparator (not pre-registered) did beat the null:** precision 0.21, p = 0.012, still below 0.5.
- **What the IF flags show:**
  - MB's drought months match E18/E33;
  - only 4 of NB's 11 flags coincide with a nuclear outage. The 2023 NB flags are a **combustion and export surge** (combustion 490 GWh/month in summer 2023 vs ≈ 270–310, nuclear normal), consistent with exports to drought-hit Quebec, which same-geography matching can't credit;
  - the longest NB outage (Jun–Sep 2024) isn't flagged;
  - Nunavut shows one-month drops with no public event.
- **Reading, as a hypothesis for the next cycle:** monthly anomalies are mostly generation–trade substitution. Changing the catalogue now would be HARKing, so the verdict stands.
- **Next cycle:** pre-register plant outages and allow trade-partner matching.
- **Confirmation (secondary):** frozen detector and threshold, one-sided STL; 4 flags in 240 geo-months; 1 of 4 events matched (coincidentally). The one-sided STL is conservative (|z| > 3 in 1.7–4.6% of geo-months vs 10–15% in development).

**K4 (not met).**
- The combination was better at the 2024-12 origin (4.17% vs 4.31%) but worse over Jan–Aug 2026 (2.66% vs 2.32%), for a pooled ratio of 1.015 (90% CI 0.92–1.15).
- The development advantage (0.88) didn't carry over. Even ETS alone (0.986) would have failed.
- Quebec accounts for 32% of the combination's 2025-12 error (25% for seasonal naive). Why 2026 favoured seasonal naive is a conjecture (2026 resembled 2025), not a tested explanation.
- The seasonal naive matches the dataset's own file on all 156 forecasts it contains. The file has no 2025-12 origin, which is scored with the same formula.

**Public-record validation** (consistency, not line-by-line source checks):

| Finding | Consistent with |
|---|---|
| AB share falls from 2023 | Alberta's wind and solar build-out in 2023–24 (combustion −268 GWh/month, wind + solar +365); coal ended in 2024 (coal → gas leaves the share unchanged) |
| NS share falls from 2021-12, with net imports up | Muskrat Falls hydro over the Maritime Link ramping up; coal-unit reductions |
| ON share rises from 2023 | Since 2019, nuclear refurbishments (Darlington, Bruce) and Pickering's wind-down (−12 TWh/yr) cover about half; demand and exports the rest |
| NB 2022 flags | NB nuclear output 0 in May–June 2022 (Point Lepreau outage), visible in the data |
| NB 2023 flags | Combustion and export surge while Quebec's hydro was low (hypothesis) |
| MB flags in 2021 and 2023–24 | Manitoba Hydro drought years (catalogue E18, E33) |

**Interestingness ranking** (validity → novelty vs CER profiles → usefulness → understandability):
1. AB's (and NS's) structural, burning-driven fall.
2. The national share is *not* falling: ON +18.6 TWh vs AB −6.7, with drought about 40% of the rise (descriptive).
3. Five archetypes persist at k = 5 (valid, well known, k-specific).
4. Simple models don't reliably beat seasonal naive 12 months ahead.
5. Ontario's rise (descriptive).
6. *Hypothesis:* monthly anomalies are generation–trade substitution (validity 1).

## 6. Using the knowledge
- **`deployment/knowledge.json`:** the acceptance verdicts and ranked findings, written by the notebook.
- **`deployment/refresh.py`:** rebuilds all artifacts from a new release with frozen rules (k = 5, PELT penalty, 2% flag budget) and **seasonal naive as the deployed forecast**, since K4 failed; the combination is shown only as a challenger.
- **`deployment/app.py`:** Streamlit dashboard with five tabs. The K2 caveat is shown under the acceptance table, and the Anomalies tab is labelled *unvalidated monitoring* because K3 failed. The notebook checks that it renders without exceptions (`AppTest`).
- **`deployment/SOURCE_NOTICES.md`:** Statistics Canada Open Licence attribution.
- **Monitoring rules:** a refreshed change point or flag is a candidate until it's checked against the public record. If AB's or NS's change point moves by more than 3 months, or AB's fall stops, re-evaluate. Replace the forecast only when a challenger wins on new sealed origins.

## Critic process
| Round | Scope | Score | Major issues | What changed |
|---|---|---|---|---|
| Front pass 1–2 | Goals, checks, holdouts | 6 → 8 | 3 → 0 | 2016 coverage break, reframed K2, sealed loaders |
| KDD round 1 | Selection, Preprocessing, Transformation, rules | 7 | 3 | K2 and K3 made falsifiable (trimmed-window stability, margin persistence, attribution, ≥ 3 provinces; event-level precision + stratified permutation null); pre-registration manifest; catalogue revision; NL break; K1 feature fix |
| KDD round 2 | Mining, Interpretation, Using the knowledge | 7.5 | 2 | K2 "met as written" split from the substance (post-hoc sensitivity: NL, NS, AB); NB explanation rewritten from the data; anomaly finding demoted to a hypothesis; ON/national decomposition; K1 adjacent-k; dashboard K3 warning |

## Limitations
- **Data vintage:** the data is StatCan's latest *revised* vintage. Backtests can look better than real-time forecasting would.
- **Generation-side shares only:** consumption-side dependence differs for importers (PEI, NS). Emissions intensity is out of scope.
- **Event catalogue:** compiled from the analyst's knowledge of public reporting and not verified line by line. Plant outages are out of scope.
- **Pre-registration evidence:** a hash manifest plus a copy outside the repo, not a git commit (commits need the user's approval). Recommended: commit `PREREGISTRATION.json` with the rule files.
- **K1 at n = 13:** an ARI threshold is coarse, and singletons inflate agreement.
- **K2:** a mean-shift model is fitted to some ramps (AB). The change-point *date* marks where the ramp steepens, not a single event.

## References
- Fayyad, U., Piatetsky-Shapiro, G., & Smyth, P. (1996). From data mining to knowledge discovery in databases. *AI Magazine*, 17(3), 37–54.
- Killick, R., Fearnhead, P., & Eckley, I. A. (2012). Optimal detection of changepoints with a linear computational cost. *JASA*, 107(500), 1590–1598. (PELT)
- Truong, C., Oudre, L., & Vayatis, N. (2020). Selective review of offline change point detection methods. *Signal Processing*, 167. (`ruptures`)
- Cleveland, R. B., Cleveland, W. S., McRae, J. E., & Terpenning, I. (1990). STL: A seasonal-trend decomposition procedure based on loess. *Journal of Official Statistics*, 6(1), 3–73.
- Liu, F. T., Ting, K. M., & Zhou, Z.-H. (2008). Isolation Forest. *ICDM*.
- Hyndman, R. J., & Athanasopoulos, G. (2021). *Forecasting: Principles and Practice* (3rd ed.). OTexts.
- Statistics Canada. Tables 25-10-0015-01 and 25-10-0016-01. Via Kaggle, *Canada Electricity: Generation and Trade* (H. Gultekin).

---
*Adapted from Statistics Canada, Tables 25-10-0015-01 and 25-10-0016-01 (reference periods 2008-01 to 2026-08), Statistics Canada Open Licence. This does not constitute an endorsement by Statistics Canada.*
