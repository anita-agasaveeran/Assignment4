# The $20 Bottle That Drinks Like $60: Finding Value Wines with CRISP-DM

*CMPE 255 · Assignment 4 · Project 1 · Author: Anita Agasaveeran*

> Every number in this report comes from a cell in `notebooks/CRISP_DM_Wine_Value.ipynb`, which is saved with its outputs. Data: [Wine Reviews](https://www.kaggle.com/datasets/zynicide/wine-reviews) (Zack Thoutt; scraped from WineEnthusiast, June 2017; CC BY-NC-SA 4.0). This report is shared under the same licence.

## Executive summary
_TODO (after Phase 5): the problem, the approach, headline results against the success criteria, and the recommendation (≤ 200 words)._

---

## 1. Business Understanding

> **Revision 3** (+ round-3 polish), after critic rounds 1 (7/10), 2 (8/10) and 3 (9/10, no major issues); see `critiques/phase1_business_understanding_round*.md`.
> - **Round 2 changes:** targets re-set so **every** development fold passes them, with lower-bound conditions; a pilot gate measured *relative* to note-blind rules; simple rules and RNG streams frozen in `src/`; a broader masking list; pre-registered insight hypotheses.
> - **Round 1 changes:** simulated buying cycles; a fixed simple-rule set; the region confound measured; development-only score statistics.
>
> All figures come from notebook §1, saved with its outputs.

### 1.1 Determine business objectives

#### Background
Critic scores sell wine. A "90 points" tag is one of the strongest quality signals a shopper has. But most wines a retailer considers have **no critic score yet**: new vintages, small producers, new imports. What the retailer usually has is a **tasting note** from the importer, the producer or its own staff, plus basic facts.

This project imagines a **hypothetical stakeholder**: the buying team of an online wine retailer. No company was interviewed, so the parameters are explicit assumptions (§1.2). The team wants a *"Great Value: 90+ points for $25 or less"* collection. Each buying cycle it receives about **1,000 unscored ≤ $25 candidates** (A7) and can sample about **100** (A4).

**The data** (counts only; no scores used here):

| Item | Value |
|---|---|
| Raw rows / exact duplicates / unique reviews | 129,971 / 9,983 / 119,988 |
| Repeat reviews of an already-reviewed title | 1,148 (covering 934 titles) |
| Countries / grape varieties / wineries | 43 / 707 / 16,757 |
| Named critics / reviews with no critic name / reviews with no price | 19 / 24,917 / 8,395 |

**Price vs score (development data only, after the lockbox is sealed):**
- Mean score 88.3 (SD 3.2); correlation with log price **0.63**.
- Median price by score band: 80–84 $15 · 85–87 $18 · 88–90 $26 · 91–93 $44 · 94–100 $74.
- 51.8% of priced wines cost ≤ $25, and 15.0% of those score 90+. In the critic-fold candidate pools used for the simulations the rate is **17.6%**; the 15.0% also includes anonymous reviews.
- So a team sampling 100 of 1,000 candidates at random would find about **18 value wines**.

#### Business objectives
- **BO1, value shortlist:** rank each cycle's ~1,000 unscored ≤ $25 candidates so the ~100 samples contain as many 90+ wines as possible.
- **BO2, internal score estimate:** an *estimated score band* (e.g. "est. 88–91") for buyers' planning until a real review arrives. **Internal only:** never shown to customers as WineEnthusiast points (R10).
- **BO3, shelf navigation:** flavour profiles and descriptor–grape links for collection pages.
- **BO4, catalogue quality:** detect duplicate and near-duplicate listings; "similar wines".
- **BO5, critic calibration and buyer insights:** how much a score depends on who tasted the wine, and which attributes go with value.

**Not in scope:** price setting, demand forecasting, personalised recommendations (no customer data).

#### Evaluation design (fixed in Phase 1)
**What a buyer would face:** notes from writers the model has never seen. So whole critics are held out:
- **Critic folds.** The 19 named critics are dealt into 5 folds with balanced row counts (`winevalue.splits`).
- **Lockbox.** One fold with ≥ 3 critics is drawn (seed 42) as the lockbox. Its scores are examined only in Phase 5.
- **Anonymous reviews** are used for training only.

Critics specialise by region, so the split also holds out regions. The coverage columns use categorical data only, which is allowed for the lockbox.

| Fold | Role | Reviews | Critics | Top countries | Variety × country seen ≥ 20× in training | Winery seen in training |
|---|---|---|---|---|---|---|
| −1 | Training only | 24,917 | (anonymous) | US 64%, Italy 32% | – | – |
| 0 | CV | 23,560 | Roger Voss | France 73%, Portugal 22% | 57% | 11% |
| 1 | CV | 17,812 | Jim Gordon, Michael Schachner | Spain 34%, Chile 23%, US 22% | 29% | 30% |
| **2** | **Lockbox** | **17,884** | **Anne Krebiehl MW, Jeff Jenssen, Kerin O'Keefe, Sean P. Sullivan** | **Italy 54%, US 25%, Austria 11%** | **90%** | **73%** |
| 3 | CV | 17,810 | 6 critics (Gregutt, Czerwinski, Iijima, …) | US 63%, Germany 11%, Australia 11% | 87% | 32% |
| 4 | CV | 18,005 | 6 critics (Boone, Kettmann, Buzzeo, …) | US 84%, South Africa 7% | 85% | 71% |

**What the lockbox tests: new writers in a mix of regions.**
- **Coverage.** Lockbox coverage is better than in development folds 0 and 1, because anonymous training notes include many Italian wines. The closest development fold is **fold 3**, and every target is checked against it.
- **One critic dominates the lockbox's ≤ $25 pool.** Of its 7,334 candidates, Kerin O'Keefe has 3,697 (50%), Sean P. Sullivan 1,757 (24%), Anne Krebiehl MW 1,544 (21%) and Jeff Jenssen 336 (5%).
- **So per-critic results** are reported as precision in the top 10% of each critic's pool, also with and without O'Keefe. Jenssen's are marked low-confidence.

#### Business success criteria (pre-registered; thresholds in `config.py`)
- Measured **once**, in Phase 5, on the lockbox critics. Simple rules are scored on the same data.
- **Pass rule:** the point estimate meets the target **and** the stated lower bound (LB) holds.
- **LBs** are one-sided 90%, from 500 bootstrap resamples of **wineries**.
- Every target is met by **every** development fold, including fold 3.

| ID | Criterion | Target | Lower-bound condition | Weakest development fold |
|---|---|---|---|---|
| BSC1 | **Shortlist.** Expected precision@100 of the DM2 ranker over 200 simulated cycles of 1,000 ≤ $25 candidates | ≥ 0.55 **and** ≥ 1.4× the best rule in the frozen **simple-rule set** (`winevalue.rules`: price, winery track record, province track record, variety × country, winery then price; random ties), measured on the lockbox | Top-10% lift vs that rule, LB ≥ 1.2× | P@100 0.61; lift 1.56×; LB 1.43× |
| BSC2 | **Internal score band.** Share of ≤ $25 candidates whose price-free estimate is within ±2 points | ≥ 0.60 and ≥ +5 pp over variety × country | Gain LB > 0 | 0.63; +7.3 pp (LB +6.0) |
| BSC3 | **Navigation.** Flavour profiles | 6–15 profiles, each ≥ 1% of wines. Two independent reviewer agents (**not** the analyst), each blind to the other, can each name ≥ 80% of profiles from their top terms with confidence ≥ 3/5 | Top-10-term Jaccard ≥ 0.5 between profiles fitted on two halves of the development data | – (Phase 4) |
| BSC4 | **Usability.** One screen. Inputs: note, country, grape, vintage, price. Outputs: est. score band, P(90+), value verdict, flavour profile, 5 similar wines | All shown in the recorded demo, < 3 s per query | – | – |
| BSC5 | **Buyer insights.** Pre-registered hypotheses H1–H6 | **≥ 4 of 6** replicate, **including H5 or H6**: stated direction and condition met in **both** development and lockbox data | As stated per hypothesis | – (Phases 4–5) |

**Pre-registered hypotheses (`config.HYPOTHESES`):**
- *Sanity checks (strong in development data):*
  - **H1:** longer notes go with higher scores (Spearman ρ > 0, LB > 0).
  - **H2:** within a variety × country group, pricier wines score higher (LB > 0).
  - **H3:** a named designation goes with higher scores (same variety × country; LB > 0).
- **H4:** critics differ. The SD of critic effects (vs a training-fitted variety × country expectation) exceeds 0.5 points, **LB > 0.5**. This is a spread statistic, so it compares fairly across datasets with different critics. *Limitation:* the lockbox has only 4 critics, which a winery bootstrap doesn't capture.
- *Actionable:*
  - **H5:** among ≤ $25 wines, whites are more often value wines than reds (LB > 0). The colour map is frozen from variety names in Phase 3, before any lockbox use.
  - **H6:** among ≤ $25 wines, a strong winery track record (shrunk mean ≥ 89, `GroupMeanBaseline(keys=("winery",), shrink=20)` on training) goes with a higher value-wine rate (LB > 0).

**Necessary, not sufficient.** These criteria use *critic* notes, but the real use is on importer, producer or staff notes (A1). Deployment therefore needs a **pilot gate** on **≥ 400 ≤ $25 retailer notes** for wines that later receive a critic score. On those same pilot wines it must beat the note-blind rules:
- ±2 accuracy ≥ +5 pp over variety × country, with LB > 0;
- the ranker's top-20% precision for 90+ wines ≥ 1.3× the **best of the frozen simple-rule set**, with LB > 1.0. In development, top-20% lift vs price is 1.44–1.74×.

**Power:** 400 wines give about 80% power at fold-3-like effects. With 100, a model that meets every development target would pass only 39–67% of the time. (`config.PILOT_*`)

### 1.2 Assess situation

#### Inventory of resources
| Type | Resource |
|---|---|
| Data | Wine Reviews (Kaggle), 129,971 reviews, one table. No sales, inventory or customer data |
| People | One analyst. **Hypothetical stakeholder**: A1–A7 are explicit assumptions with sensitivity checks. No sommelier or domain expert. Reviewers: course instructor, an independent critic, and independent reviewer agents for BSC3 |
| Compute / software | Laptop + Google Colab; Python 3.12, pandas, scikit-learn, LightGBM, mlxtend, datasketch, statsmodels, Streamlit |

#### Requirements
- **R-1, prediction timing:** when a buyer considers a wine, **before any critic review exists**. Available then: note, country/province/region, grape, winery and its *past* scores, vintage, price.
- **R-2, inputs by use:**
  - The **score estimate** (BO2) and **value verdict** exclude `price` (so "quality vs price" isn't circular).
  - The **shortlist ranker** (BO1/DM2) may use price.
  - Neither may use `taster_name` / `taster_twitter_handle`.
- **R-3, honest test:**
  - The lockbox is scored once.
  - Exact duplicates are removed.
  - Test reviews whose title appears in training are dropped (124 of 934 repeat titles span folds).
  - Anonymous notes attributed to a lockbox critic with p > 0.5 are dropped from training (859 rows).
- **R-4, reproducibility:**
  - Fixed seeds.
  - Cycles and tie-breaks use separate RNG streams, so every rule is scored on identical cycles (tested).
  - The simple-rule set and masking list are frozen in `src/`.
  - The notebook runs top to bottom in Colab, saved with outputs.
- **R-5, licence:** outputs shared under CC BY-NC-SA 4.0.

#### Assumptions
| # | Assumption | Testable? | Handling |
|---|---|---|---|
| A1 | Retailer notes carry similar descriptive signal to critic notes | **Not with this data.** Leave-critic-out tests new critics, not new kinds of writer (producers have an incentive to praise) | Masking proxy (DM1b) now; **relative pilot gate** before deployment |
| A2 | 90+ points is a meaningful value bar | No | Also reported at 88+ / 92+ |
| A3 | 2017 prices still rank wines sensibly relative to each other | No | Ranking use only; cap also tested at $20 / $30 |
| A4 | ~100 samples per cycle | No | Also k = 50 / 200 |
| A5 | ~$25 per sample; ~2 analyst-hours per cycle to re-score | No | Illustrative economics |
| A6 | Scores are honest; blind tasting unknown | No | Critic calibration descriptive |
| A7 | **~1,000 unscored ≤ $25 candidates per cycle** (importer/distributor catalogues of a mid-size online retailer) | No | Sensitivity at 500 / 2,000 |

#### Constraints
- One static 2017 snapshot, with no review dates.
- Only wines scoring 80+ are published.
- No stakeholder interviews.
- One analyst and an academic timeline.

#### Anonymous-review check (R-3, R8)
A TF-IDF style classifier uses note *text* and critic names only, no scores. It identifies the critic of held-out named notes with 98.4% accuracy overall.

| Threshold | Accuracy on held-out named notes above threshold | Anonymous notes above threshold | Of which → lockbox critic |
|---|---|---|---|
| **0.5 (used)** | 99.2% | 11,872 | **859** |
| 0.7 | 99.8% | 4,418 | 329 |
| 0.9 | 100.0% | 341 | 29 |

At p > 0.5 the classifier is still 99.2% accurate. Dropping the 859 notes costs only 3.4% of anonymous training data (`config.ATTRIBUTION_THRESHOLD = 0.5`).

#### Risks & contingencies
| # | Risk | Likelihood | Impact | Contingency |
|---|---|---|---|---|
| R1 | **Note-source shift** (A1) | High | High | Masking test (DM1b); relative pilot gate; BSCs "necessary, not sufficient" |
| R2 | **Region confound:** variety × country coverage 29–87% by development fold, so the baseline looks weaker than on a random split | Confirmed | Medium | Both splits reported; targets set on the critic split; per-fold and per-critic results |
| R3 | **Duplicates / repeat titles** (9,983 dups; 1,148 repeat reviews of 934 titles; 124 span folds) | Confirmed | High if ignored | Dups removed; test rows with a training title dropped |
| R4 | **Selection bias:** only 80+ wines are published | Confirmed | Medium | Stated limitation |
| R5 | **Stale prices**, single snapshot | Confirmed | Low–Medium | Ranking use only; cap sensitivity |
| R6 | **Critic differences** for the same variety and country | Observed (descriptive) | Medium | H4 / DM6; the lockbox mixes 4 critics |
| R7 | **Long-tail categories** (707 grapes, 16,757 wineries) | Confirmed | Medium | Rare-category grouping (Phase 3) |
| R8 | **Anonymous notes by lockbox critics** | Small | Low | 859 rows dropped (p > 0.5) |
| R9 | **Weak lockbox result.** Development margins are smallest for fold 3 (the fold most like the lockbox) on DM1/BSC2, and for folds 1 and 4 on BSC1 | Medium | Medium | Every target is met by every development fold; winery-clustered LBs; per-critic reporting |
| R10 | **Misleading or infringing display** of estimated "points" | Medium | Medium | Internal "estimated band" only, labelled |
| R11 | **One critic dominates the lockbox** (O'Keefe 50% of the ≤ $25 pool) | Confirmed | Medium | Per-critic top-10% precision; results with and without O'Keefe |
| R12 | **Licence (NC-SA)** limits commercial use | Confirmed | Low (academic) | Stated in README and app |

#### Terminology
| Term | Meaning |
|---|---|
| Critic score / points | WineEnthusiast's 80–100 rating |
| Value wine | 90+ points at ≤ $25 |
| Tasting note | The `description` |
| Candidate pool / cycle | The unscored ≤ $25 wines considered in one buying round (A7) |
| Shortlist | The top k to sample |
| Precision@k / top-10% precision | Share of the shortlist that are value wines |
| Simple-rule set | The frozen non-ML rankings in `winevalue.rules` |
| Lift | Ranker precision ÷ best simple-rule precision |
| MAE / within ±2 | Mean absolute error / share of estimates within 2 points |
| Critic fold / lockbox | A held-out group of critics / the fold sealed until Phase 5 |
| Lower bound (LB) | One-sided 90% winery-clustered bootstrap bound |
| Evaluative language | Verdict words and drinking windows (`config.EVALUATIVE_TERMS`, `EVALUATIVE_PATTERNS`) |
| TF-IDF | Word weighting for notes |
| Flavour profile | A cluster of similar notes |
| Support / confidence / lift (rules) | Association-rule statistics |
| MinHash LSH | Fast near-duplicate search |

#### Costs & benefits
**Feasibility check.** Development folds only; untuned models; test rows with a training title dropped. Shortlists are scored over 200 simulated cycles (cycles and ties on separate RNG streams, one tie stream per rule); LBs use a winery-clustered bootstrap. Training here uses all anonymous rows: the R-3 attribution filter (859 rows, none of them lockbox rows) starts in Phase 3.

*Score estimate (price-free):*

| Predictor | MAE by fold (0 / 1 / 3 / 4) | MAE mean | Within ±2 on ≤ $25 by fold | Mean |
|---|---|---|---|---|
| Global mean | 2.56 / 2.76 / 2.33 / 2.58 | 2.56 | 0.49 / 0.42 / 0.58 / 0.53 | 0.51 |
| Variety × country | 2.72 / 2.62 / 2.27 / 2.52 | 2.53 | 0.55 / 0.48 / 0.56 / 0.54 | 0.53 |
| **Text model** | 1.83 / 1.75 / 2.00 / 1.72 | **1.82** | 0.71 / 0.70 / 0.63 / 0.72 | **0.69** |
| Text model, round-1 mask | 1.89 / 1.79 / 2.06 / 1.74 | 1.87 | 0.71 / 0.69 / 0.61 / 0.71 | 0.68 |
| Text model, frozen mask | 1.93 / 1.85 / 2.07 / 1.75 | 1.90 | 0.71 / 0.69 / 0.62 / 0.69 | 0.68 |

*Per fold, against the pre-registered targets:*

| Fold | MAE reduction (LB) | Within ±2 gain, pp (LB) | Masked MAE increase | Best simple rule (P@100) | DM2 ranker P@100 | Lift (cycles) | Top-10% lift LB |
|---|---|---|---|---|---|---|---|
| 0 | 32.7% (31.5%) | +16.3 (+15.2) | 0.10 | price (0.42) | 0.66 | 1.58× | 1.50× |
| 1 | 33.2% (32.3%) | +22.4 (+21.4) | 0.11 | price (0.34) | 0.61 | 1.79× | 1.70× |
| 3 | **11.9% (10.5%)** | **+7.3 (+6.0)** | 0.07 | winery then price (0.34) | 0.72 | 2.13× | 1.92× |
| 4 | 31.6% (30.8%) | +17.8 (+16.6) | 0.03 | winery then price (0.40) | 0.62 | **1.56×** | **1.43×** |
| **Target** | ≥ 10% (LB > 5%) | ≥ +5 (LB > 0) | ≤ 0.15 | – | ≥ 0.55 | ≥ 1.4× | ≥ 1.2× |

*Is the weak baseline an artefact of the split?*

| MAE | Random split (title-grouped) | Critic split (mean) |
|---|---|---|
| Global mean | 2.60 | 2.56 |
| Variety × country | 2.39 | 2.53 |
| Text model | 1.30 | 1.82 |

*Shortlist rules* (expected precision@100, random ties):

| Rule | 500 candidates | **1,000 (A7)** | 2,000 |
|---|---|---|---|
| Value base rate | 0.18 | 0.18 | 0.18 |
| Price (pricier first) | 0.34 | 0.36 | 0.37 |
| Winery track record | 0.22 | 0.26 | 0.31 |
| Province track record | 0.18 | 0.17 | 0.14 |
| Variety × country | 0.18 | 0.18 | 0.17 |
| Winery track record, then price | 0.33 | 0.36 | 0.37 |
| Text model (no price) | 0.49 | 0.60 | 0.70 |
| **DM2 ranker (text + price)** | 0.52 | **0.65** | 0.76 |

**Feasibility verdict:**
- **Score estimate.** For unseen critics, the text model cuts MAE by 12–33% vs variety × country; ±2 accuracy rises by +7 to +22 pp.
- **Not just verdict words.** With the frozen evaluative list masked (verdict words + drinking windows), MAE rises by only 0.03–0.11 points, and 87% of the improvement is kept on average (76% in fold 3). The narrower round-1 list kept 91%.
- **The baseline's weakness is partly the split.** On a random title-grouped split, variety × country beats the global mean by about 8%; on the critic split, by about 1%. New writers in partly new regions are genuinely harder, which is the deployment risk.
- **Shortlist.** The DM2 ranker is 1.56–2.13× the best simple rule in each fold, with lower bounds of 1.43–1.92×.
- **Targets.** Every pre-registered target is met by every development fold, including its lower-bound condition.

*Disclosure:* one exploratory check, run before the lockbox existed, used all critics. All figures here use development data only.

*Sampling economics* (1,000-candidate cycles, $25 per sample, 2 analyst-hours ≈ $100 per cycle to re-score):

| Way of choosing samples | Value wines found in 100 samples | Precision@100 | Sampling cost per value wine |
|---|---|---|---|
| Random | 17.1 | 0.17 | $146 |
| Best simple rule (per fold) | 37.2 | 0.37 | $67 |
| **DM2 ranker** | **65.4** | **0.65** | **$38** |

| Benefit framing | Per cycle | Break-even on ~$3,500 analyst time |
|---|---|---|
| **Cash:** the ranker matches the best rule's 37.2 finds with ≈ 50 samples instead of 100 | ≈ $1,250 saved; ≈ $1,150 after running cost | ≈ 3 cycles |
| **Opportunity value:** sampling all 100 anyway | ≈ +28 value wines ≈ $1,900 at the simple rule's cost per find | ≈ 2 cycles |

- **Revenue upside:** probably larger, but not quantifiable without sales data, so it isn't claimed.
- **Other benefits:** BO2–BO4.

**Critic differences (descriptive).** For the *same variety and country*, critics' averages range from −2.30 (Alexander Peartree) to +1.35 (Matt Kettmann) points vs expectation. Critics also differ in which wines they review, so H4 and DM6 test this properly.

**Costs:**
- About 60–80 analyst-hours (≈ $3,500 at an assumed $50/h); open-source software; free hosting.
- About 2 hours per cycle to re-score, plus a quarterly drift check.
- A pilot on about 100 retailer notes.

### 1.3 Determine data mining goals
| ID | Data mining goal | Technique | Success criterion (lockbox, Phase 5; DM5 on the full corpus) | Uncertainty | Supports |
|---|---|---|---|---|---|
| DM1 | **Estimate the critic score** from note + origin + grape + vintage (no price, no critic) | Baselines vs ridge on TF-IDF, gradient boosting, optional transformer embeddings | MAE ≥ 10% below variety × country; plus BSC2 | LB of reduction > 5% | BO2 |
| DM1b | **Signal beyond verdict words** | Same model with the frozen evaluative list masked | Masked MAE ≤ DM1 MAE + 0.15 (absolute, so it's stable even when DM1's reduction is small) | Point estimate | BO1, BO2 (A1 proxy) |
| DM2 | **Rank ≤ $25 candidates** | DM1 model + log price (or a direct P(90+) classifier) | = BSC1; also k = 50/200 and pools of 500/2,000 | = BSC1 | BO1 |
| DM3 | **Flavour profiles** | k-means / NMF on TF-IDF or embeddings; outlier notes checked | = BSC3; silhouette or topic coherence reported | = BSC3 | BO3 |
| DM4 | **Descriptor ↔ grape links** | FP-Growth on descriptor sets + grape | ≥ 10 rules with lift ≥ 2 and support ≥ 0.5% in development data that keep lift ≥ 1.5 in the lockbox | Point estimate | BO3, BO5 |
| DM5 | **Near-duplicates and similar wines** | MinHash LSH on 5-word shingles (128 permutations): loose candidate stage (threshold 0.3), then **exact Jaccard verification ≥ τ = 0.5** (`winevalue.similarity`) | *Re-specified 2026-11-04 (Phase 2 → Phase 1 loop-back); made operational in Phase 3 (revision 2, same day); text only, no scores. *Timeline (Phase 3 critic round 2):* (c) was first run during Phase 3 critic round 1 (0.81 < 0.90); it was demoted to exploratory and the content-word rule amended **after** that run; the result was unchanged (35/43). (a) has not been run. Original, superseded: ~~recall ≥ 0.9 of exact-Jaccard ≥ 0.8 pairs on a 10k sample; precision ≥ 0.9 on 100 hand-checked pairs~~.* **Corpus:** distinct notes after exact de-duplication, barrel-sample and duplicated-note removal (`prepare(..., stop_before="near_duplicates")`; 119,280 notes). **Pass/fail: (a) recall ≥ 0.90** on synthetic positives (a check of the implementation, not of the data: with 37 bands × 3 rows, P(candidate | J = 0.5) = 0.993) (`similarity.synthetic_copies`: 2,000 notes, seed 42; edit rate ~ U(0.02, 0.08); k = round(rate·words) positions replaced by corpus tokens; positives = copies with exact J ≥ 0.5; 1,694 at seed 42). **Reported, not pass/fail:** (b) candidate share (≤ 0.01% target; it can't fail: 1.7e-7 measured, so it's an engineering check); (c) precision under `similarity.is_true_duplicate` (same wine relisted, or recycled/mis-attached note with ≤ 3 differing content words). (c) is **exploratory**, because the 43 real pairs were inspected in Phase 2; it's 35/43 = 0.81 and is reported without re-tuning. Parameters in `config.DM5_*` | Point estimate | BO4 |
| DM6 | **Critic calibration** | Fixed / mixed effects: score ~ wine attributes + critic | Critic effects with 95% CIs; feeds H4 / BSC5 | As BSC5 | BO5 |

**Outlier analysis** from the course template is a supporting step in Phases 2–3: price outliers (up to $3,300), odd vintages, unusually short or long notes.

### 1.4 Produce project plan
Dates assume work started 2026-11-03. `instructions.txt` gives no due date. **The assignment due date still needs confirming with the project owner**, and the dates will be adjusted to fit it.

| Phase | Planned dates | Effort | Inputs → outputs | Milestone / go-no-go |
|---|---|---|---|---|
| 1 Business Understanding | Nov 3–4 | 10% | Raw data → §1; frozen evaluation design, rules, targets, hypotheses | Critic: no major issues |
| 2 Data Understanding | Nov 4–6 | 20% | §1 → description, EDA, quality report (**development data only** for score analysis) | Quality issues logged |
| 3 Data Preparation | Nov 6–9 | 25% | §2 → cleaned table, R-3 filters, features (incl. wine colour for H5), text pipeline | Leakage audit passes |
| 4 Modeling | Nov 9–12 | 20% | §3 → DM1–DM6 on development folds | DM targets met in CV, or loop back |
| *Buffer* | Nov 13 | – | Absorbs one loop-back (Phase 4 → 3) | – |
| 5 Evaluation | Nov 14 | 10% | §4 → single lockbox run, BSC1–BSC5 | Go/no-go |
| 6 Deployment | Nov 15–17 | 15% | §5 → Value Finder app, monitoring, pilot plan, report, article, video | Final critic review |

**Fallback scope:** if time runs short, DM5 (LSH) and DM6 (critic model) shrink to a minimal demonstration. DM1, DM1b, DM2 and DM3 are protected.

**Resources:** one analyst for every phase, plus an independent critic review (≥ 2 rounds) at the end of each.

**Initial assessment of tools & techniques:**
- **scikit-learn:** TF-IDF, ridge, k-means, NMF; pipelines fit inside each fold.
- **LightGBM:** non-linear models.
- **mlxtend:** FP-Growth.
- **datasketch:** MinHash LSH.
- **statsmodels:** critic effects with CIs.
- **Streamlit:** the app.
- **IBM SPSS Modeler** (suggested in the assignment) has a CRISP-DM project view, but needs a licence, handles free text poorly and can't be shared as a runnable notebook, so the CRISP-DM structure is followed in the notebook and this report instead.

## 2. Data Understanding

> **Revision 3**, after critic rounds 1 (6/10), 2 (7.5/10) and 3 (8.5/10, no major issues); see `critiques/phase2_data_understanding_round*.md`. Main changes:
> - a target leak was found in the notes (671 barrel samples);
> - the vintage rule is corrected;
> - the noise floor is redone properly;
> - grape synonyms and a colour map are frozen;
> - near-duplicates are explored (leading to a DM5 loop-back to §1.3);
> - identity and encoding checks are added.
>
> Phase 1's rule applies: anything that looks at **scores** uses development data only (102,104 reviews). Counts, categories and text structure may use all 119,988 unique reviews. All figures come from notebook §2.

### 2.1 Initial data collection report
| Item | Detail |
|---|---|
| Source | Kaggle *Wine Reviews* (Zack Thoutt). Reviews scraped from WineEnthusiast.com, week of 2017-06-15 |
| Licence | CC BY-NC-SA 4.0; derived outputs use the same licence |
| Files received | `winemag-data-130k-v2.csv` (129,971 × 13) · `winemag-data-130k-v2.json` (same reviews, per the dataset page) · `winemag-data_first150k.csv` (older scrape: 150,930 rows, **no critic names**, 53,079 exact duplicates, ~40% of our notes also appear there, matched on note text) |
| Used | **`winemag-data-130k-v2.csv` only.** It's the only file with critic names; SHA-256 verified |
| Not used | JSON (redundant); 150k (no critics; mixing scrapes would double-count) |
| Missing data that would help | Review dates, sales and price history, the retailer's own notes (A1 pilot), blind-tasting status |

### 2.2 Data description report
| Column | Type | Non-null (raw) | Distinct (raw) | Role (Phase 1 R-1/R-2) |
|---|---|---|---|---|
| `points` | int | 100% | 21 (80–100) | **Target** |
| `description` | text | 100% | 119,955 | Input (text) |
| `country`, `province` | cat | 99.95% | 43 / 425 | Input |
| `region_1`, `region_2` | cat | 83.7% / 38.9% | 1,229 / 17 | Input (`region_2` US-only) |
| `variety` | cat | 100% | 707 | Input (raw label; `grape_canonical` added, §2.4c) |
| `winery` | cat | 100% | 16,757 | Input (track record) |
| `designation` | cat | 71.2% | 37,979 | Input |
| `price` | float | 93.1% | 390 | Ranker input / value verdict only (labelled USD; not independently verified) |
| `title` | text | 100% | 118,840 | Source of vintage. **Not a wine key** (§2.4c) |
| `taster_name`, `taster_twitter_handle` | cat | 79.8% / 76.0% | 19 / 15 | **Excluded** as inputs; fold grouping |

- **Notes:** 3–135 words (median 40).
- **Long tails:** top 10 countries cover 96%; 501 of 707 variety labels have fewer than 20 reviews; **15,341 of 16,757 wineries have fewer than 20 reviews (56% of reviews)**.

### 2.3 Data exploration report
**Scores and prices** (development data):
- Mean 88.32, SD 3.16, integer-valued; 37.3% score 90+.
- **Score heaping: critics avoid 89.** 88 has 12,509 reviews, 89 has 8,505 and 90 has 11,450. So the 90+ value label sits where critics round up, which supports Phase 1's A2 sensitivity at 88+ / 92+.
- Price: median $25, 99th percentile $160.

**Value wines** (≤ $25 candidates; 15.0% overall):
- By country: Germany 30%, Portugal 21%, Australia 21%, New Zealand 20%, US 18%, Austria 17%, France 17%, Greece 17%, South Africa 11%, Spain 8%, Argentina 7%, Chile 6%, Italy 5%.
- By variety: Riesling 28%, Gamay 27%, Portuguese Red 27%, Shiraz 27%, Pinot Gris 26%, Syrah 22% … Merlot 8%, Tempranillo 7%, Carmenère 7%, Pinot Grigio 4%. The full ≥ 300-candidate lists are in notebook §2.3g.
- **These mix wine effects with critic effects:** critics specialise by country (O'Keefe Italy only; Schachner Spain and Chile; several US-only). **Pinot Gris (26%) and Pinot Grigio (4%) are the same grape:** the label carries market and style (Grigio 58% Italy, Gris 60% US). Descriptive only; H5, H6 and DM6 test these properly.

**Tasting notes:**
- **Length:** longer notes go with higher scores (ρ = 0.51).
- **High-score words:** drinking-window years ("2022", "2030"), "decade", verdict words ("superb", "gorgeous") and prestige places ("Barolo", "premier").
- **Low-score words:** "everyday", "watery", "bland", "simple", "pizza".
- **⚠ The token "92" in the high-score list was a target leak** (§2.4a).

**Other patterns:**
- **Vintage:** 2004–2014 average about 88–89; 2000–02 and 2016 about 87.4. Median price rises with age, consistent with review timing (older vintages reviewed in 2017 are later, pricier releases).
- **Designation:** a named designation averages 88.6 vs 87.6 without (H3 sanity check).

**Near-duplicates (all reviews, text only):**
- Across 119,955 distinct notes, exact Jaccard (after loose LSH candidates) gives 50 / **43** / 20 / 8 pairs at ≥ 0.4 / **0.5** / 0.7 / 0.8.
- **Only about a third are the same wine relisted** ("Alentejano" vs "Alentejo"). Most are the same critic's note recycled or attached to a *different* wine (different producers, or a producer's red vs white). All pairs are within one fold, so there's no cross-fold leakage. Phase 3 flags these ~80 rows as possible label noise.
- **Phase 1's DM5 can't be measured as written** (a 10k sample would hold fewer than one true pair).
- → **Loop back to §1.3:** DM5 is re-specified there (original kept, struck through and dated). Full corpus; recall on ~1,670 synthetic positives (2–8% word edits, exact J ≥ 0.5, sized by simulation); false-flag rate on random pairs; precision on the 43 real pairs with a labelling rule fixed in advance.

### 2.4 Data quality report
**2.4a The target is written into some notes.**
- **What:** 671 development notes (all fold 0, Roger Voss **barrel samples**; including em-dash and "98-100" forms) open with the score range ("90–92. Barrel sample."). **The recorded score equals the midpoint 99.7% of the time** (MAE 0.008).
- **Other text leaks:** 20 notes state a score ("rated 92 points", "90-point", "90+ rating"), 184 carry WineEnthusiast labels ("Best Buy", "Editors' Choice", "Cellar Selection"), and 333 mention a price ("$15", "10 bucks"). Regexes are limited to 80–100 so "14-15% alcohol" can't match (tested).
- **Who it affects:** barrel samples are almost never priced (1.5%), so they barely touch the ≤ $25 shortlist.
- **Effect on Phase 1:** removing them raises fold 0's MAE reduction from 32.7% to 34.9%, and folds 1/3/4 move by ≤ 0.2 pp. Phase 1 isn't inflated, and the targets stand.
- **Decision:** drop barrel samples (671); strip explicit scores and verdict labels; replace prices with `_price_`.
- **Mask residuals (a DM1b limitation; the frozen list is unchanged):** of 3,923 development 93+ notes with a 20xx year, 920 keep one after masking. 250 contain "decade" and 1,038 contain "N years". So the 87% DM1b retention is an upper bound, and Phase 4 adds a stricter mask as a sensitivity check.

**2.4b The human noise floor**, done properly: pairwise, same **title + variety**, development data. One review = expected score + noise; σ = RMS(diff)/√2; a perfect predictor is within ±2 with P = 2Φ(2/σ) − 1.

| Comparison | Price band | Pairs | Mean \|diff\| | Within ±2 (pairs) | Single-review σ | Ceiling within ±2 |
|---|---|---|---|---|---|---|
| Same critic | all | 728 | 1.53 | 79% | 1.45 | 0.83 |
| Same critic | ≤ $25 | 304 | 1.62 | 77% | 1.49 | **0.82** |
| Different critics | all | 39 | 2.26 | 64% | 2.17 | 0.64 |
| Different critics | ≤ $25 | 20 | 1.70 | 80% | 1.57 | 0.80 (n tiny) |

The Phase 1 model is scored on *unseen* critics, so the relevant ceiling lies between the cross-critic values (0.64 at all prices, n = 39; 0.80 at ≤ $25, n = 20) and the same-critic value (0.82): roughly **0.64–0.83**, on small, selected samples. The model's 0.69 is not "close to critics' own consistency" (the round-1 claim was wrong). There is likely, but uncertain, headroom.

**2.4c Identity and encoding checks:**
- **`title` isn't a wine key.** 250 of 934 repeat titles are different wines (e.g. red and white under one title), and 474 have different prices. Wine key = title + variety.
- **Duplicated notes** (13 groups in development data, 33 overall) sit on different titles. Some are the same wine relisted, some are notes pasted onto another wine, and 2 are barrel samples.
- **Grape synonyms.** `grape_canonical` merges 43 labels / 5,891 reviews (Shiraz → Syrah, Pinot Grigio → Pinot Gris, Garnacha → Grenache, …) from ampelographic synonyms. Raw `variety` stays for the frozen rules; the canonical grape is used for DM4, H5 and the app.
- **Colour map, frozen now for H5:** `wine_colour(variety, title)`. Title style words (rosé, Brut / sparkling, Port) override the grape, and blends take the first-listed grape. Built from grape knowledge and title text only, before any colour × value view: **97.9%** coverage (59.0% red, 30.3% white, 4.3% sparkling, 3.5% rosé, 0.7% fortified).
- **Encoding.** NBSP in 3,290 critic names (Krebiehl only; folds consistent), 22 titles, 15 wineries and 7 designations; mojibake in 5 cells across 3 fields; 29 winery names differ only by case or whitespace.
- **Pseudo-provinces:** 1,921 rows ("France Other", "Other", province = country).
- **Prices > $1,000:** hand-checked. "Château les Ormes Sorbet 2013 Médoc" at $3,300 and Blair 2013 Chardonnay at $2,013 (= vintage) are errors, and Knoll Smaragd at $1,100 is implausible. The first-growth Bordeaux and Burgundy prices are plausible.
- **Vintage parser:** titles took years from winery names ("1912 Winemakers", "Guidi 1929") or brand/solera years after "NV". Corrected rule: strip the winery prefix; NV before the first year → non-vintage; else the **first** year. 17 titles change; pre-1990 vintages fall from 69 to **52, all genuine**. "Nearest the end" would pick planting years.
- **Co-author pair across the lockbox:** Jenssen (lockbox) and DeSimone (fold 4) share @worldwineguys. A style classifier confuses them only 6–7% of the time, and they share no titles. A minor limitation.

**Decisions (applied in Phase 3; none changes the frozen Phase 1 design or targets):**

| Issue | Rows | Decision |
|---|---|---|
| Exact duplicates | 9,983 | Drop |
| **Score in note (barrel samples)** | 671 | **Drop barrel samples** |
| Explicit score / verdict label / price in note | 20 / 184 / 333 | Strip / strip / `_price_` token |
| Duplicated note on different titles | 13 groups (dev) | Keep one row per note |
| Repeat titles | 1,148 / 934 (250 different wines) | Key = title + variety; keep in training; R-3 test filter (evidence: 40 / 30 / 16 / 51 rows by development fold) |
| Missing price (+3 implausible set missing) | 8,398 | Score models keep them; excluded from the ≤ $25 pool and the value verdict |
| Anonymous critic | 24,917 | Training only; 859 dropped (R8) |
| Missing country / province / variety; pseudo-provinces | 60; 1,921 | "Unknown" for models; frozen rules unchanged |
| Missing designation / region | 28% / 16% | Missing indicator |
| Vintage parse | 17 | New rule incl. NV guard (tested) |
| Non-vintage | 4,285 | Flag |
| Grape synonyms | 43 labels | `grape_canonical` (raw label for frozen rules) |
| Encoding / winery case | see above | Normalise; case-fold winery keys for models (frozen winery rule keeps raw names; ≤ 29 groups affected) |
| Notes < 10 words | 39 | Keep; flag |
| No review date; co-author pair | – | Limitations |

**Conclusion:** the data is real and fit for purpose once the barrel-sample leak and the identity issues are handled. None of these changes the frozen Phase 1 targets. The one change to a Phase 1 goal (DM5) is a documented loop-back.

## 3. Data Preparation

> **Revision 3**, after critic round 2 (8/10, **no major issues**: the phase gate is met; `critiques/phase3_data_preparation_round2.md`). Minor fixes:
> - "Blanc de Noir(s)" yields to sparkling cues (40 sparkling wines had been labelled white);
> - the mojibake repair no longer damages correct text;
> - a descriptive "a point" is kept; "bang for the buck", "price point" and `_price_` join the strict DM1b mask;
> - the DM5 timeline and the meaning of (a) are stated;
> - the R8 filter takes a `critics=` argument for per-fold CV.
>
> **Revision 2**, after critic round 1 (7/10; `critiques/phase3_data_preparation_round1.md`). Main changes:
> - the **lockbox mapping is pinned** as a constant;
> - **DM5's corpus is named**, its rule is self-contained, and (c) is reported as exploratory;
> - leak patterns are widened;
> - the **leakage audit has checks that can fail**;
> - `n_words` is counted on the model text;
> - the colour map has a dated amendment;
> - variety is encoded once.
>
> All preparation is one deterministic function, `winevalue.prepare.prepare()` (notebook §3, saved with outputs). Items carried from Phase 2 critic round 3 (N1–N5) are resolved here, before DM5(a) is run and before any H5 use.

**Frozen folds.**
- **Pinned mapping:** the critic → fold mapping derived in Phase 1 on the *de-duplicated* reviews is now a constant (`config.CRITIC_FOLDS`, `LOCKBOX_CRITICS`). Recomputing it on another row set (e.g. the raw file) would give a different lockbox.
- **Enforcement:** `assign_folds()` uses the constant and fails on unknown critics. A test checks that it equals the Phase 1 derivation and that the lockbox is Anne Krebiehl MW, Jeff Jenssen, Kerin O'Keefe and Sean P. Sullivan.

### 3.1 Rationale for inclusion / exclusion
| Column(s) | Role | Rationale |
|---|---|---|
| `points` | Target | Critic score |
| `note` (from `description`) | Input: quality + ranker | Note with scores, score commentary, verdict labels and prices stripped |
| `country`, `province_model`, `grape` (+ `label_differs`), `colour` | Input | Origin; **one** grape encoding (canonical grape + a "label differs" flag) |
| `vintage`, `is_nonvintage`, `n_words`, `has_designation`, `has_region_1` | Input | Constructed (3.3) |
| `price` | Ranker only; value verdict | R-2 |
| `winery` / `winery_key` | Simple-rule set + DM6; not yet a model input | 56% of reviews come from wineries with < 20 reviews; producer names also appear in ~6% of notes (a known channel) |
| `variety` (raw label) | Frozen simple rules + variety × country baseline only | Pre-registered benchmarks unchanged |
| `region_1`, `region_2`, `designation` (text) | Excluded as raw categories | 1,226 / 17 / 37,665 values in the prepared table; represented by flags |
| `taster_name`, `critic`, handle | **Excluded** (R-2) | Folds / DM6 only |
| `title`, raw `description` | Excluded as inputs | Sources for vintage, colour and audits |

**Rows:**
- **Excluded:** exact duplicates; barrel samples (score range in note, or "barrel sample" in title or note); extra copies of duplicated notes and of near-duplicate pairs (exact J ≥ 0.5, the same definition DM5 uses); anonymous notes attributed to lockbox critics (R8).
- **Kept but sealed:** lockbox rows.
- **Kept:** reviews with no price (excluded from the ≤ $25 pool); outliers.

### 3.2 Data cleaning report (incl. outlier analysis)
| Step | Rows before → after | Affected | Of which lockbox |
|---|---|---|---|
| Drop exact duplicates | 129,971 → 119,988 | 9,983 | – |
| Drop barrel samples | 119,988 → 119,311 | 677 | 0 |
| Keep one row per duplicated note (text rule) | 119,311 → 119,280 | 31 | 20 |
| Keep one row per near-duplicate pair (exact J ≥ 0.5; all within one fold) | 119,280 → 119,237 | 43 | 16 |
| Drop anonymous notes attributed to a lockbox critic (R8) | 119,237 → **118,378** | 859 | – |
| Set implausible prices to missing | – | 3 | – |

**Modeling table: 118,378 reviews** (development 100,530; lockbox 17,848). The lockbox lost 36 rows to text-only rules (reported).

**Repairs:**
- mojibake repaired only where the Latin-1 → UTF-8 round trip succeeds ("crÃ¨me" → "crème"; correct text such as "Âme" or "d'Âge" is untouched); whitespace normalised;
- 3 prices set to missing;
- missing categories → "Unknown";
- pseudo-provinces → "Unknown province";
- vintage re-parsed with the corrected rule.

**Model text `note`:** explicit scores, **score commentary** ("too ripe to score higher", "loses a few points"; a descriptive "a point of acidity" is kept), WineEnthusiast labels ("Best Buy(s)", "Editor's Choice") removed; prices, including words like "six bucks", → `_price_` ("bucks the trend" is not a price). **Known R-2 residual:** price-relative wording ("at the price", "value-priced", "bang for the buck", "price point") and the `_price_` placeholder with its context stay in `note`; the stricter mask `text_audit.strict_price_mask` removes both in the Phase 4 sensitivity check.

**Outlier analysis** (inputs only): 1,078 log-price / 1,965 note-length / 1,071 Isolation-Forest outliers. **Kept**, because they're genuine wines; log price and standardisation limit their influence.

### 3.3 Derived attributes & generated records
| Attribute | Definition | Purpose |
|---|---|---|
| `note` | Description minus scores, score commentary, verdict labels; prices → `_price_` | Leak-free model text |
| `grape` / `label_differs` | `grape_canonical(variety)` / grape ≠ raw label | One grape encoding; label style as a flag |
| `colour` | `wine_colour(variety, title, winery)` | H5 (unmapped 1.5% → excluded); navigation |
| `province_model` | Pseudo-provinces → "Unknown province" | Cleaner origin |
| `vintage`, `is_nonvintage` | Revised parser + NV guard | Age signal |
| `age_at_scrape` | 2017 − vintage | Interpretable age |
| `n_words`, `short_note` | Word count of **`note`** (model text) / < 10 words | Length (H1); flag |
| `has_designation` | Designation (named cuvée / bottling) present | H3; specificity |
| `has_region_1` | `region_1` (sub-region / appellation) present | Specificity |
| `winery_key` | Case-folded winery | Producer key |
| `in_value_pool` | Price ≤ $25 | BSC1/BSC2 pool |

**Generated records:** none in the modeling table. DM5's synthetic copies are generated from its **named corpus**: 119,280 distinct notes after exact de-duplication, barrel-sample and duplicated-note removal (`prepare(..., stop_before="near_duplicates")`).
- **Synthetic positives:** 1,694 of 2,000 reach exact J ≥ 0.5 (seed 42).
- **(b) Candidate share:** 1.7e-7, an engineering check that can't fail.
- **(c) Exploratory precision** on the 43 real pairs (seen in Phase 2) under the frozen rule: **35/43 = 0.81**, reported without re-tuning. Eight pairs are different wines sharing recycled phrases; `prepare()` still removes all 43 by Jaccard alone (conservative for training).

### 3.4 Merged data
- **One review table, plus external reference knowledge** (`winevalue.grapes`):
  - a grape-synonym table;
  - a grape-colour table with a title-style override on the winery-stripped title.
- **Frozen before any colour × value view:** Phase 2 rev. 3; re-frozen 2026-11-04; amended the same day in revision 2 (US "Port", still Blanc de Noir, Clairet; negative tests) and again in **revision 3** (critic round 2 N1):
  - "Blanc de Noir(s)" is applied only after the sparkling title cues (now also "Bruto", "bubbles", "Dosage Zero", "Méthode champenoise/traditionnelle") and a sparkling variety label have failed;
  - it then gives sparkling if the note describes bubbles (mousse, bead, tirage, "on the yeast", …; text only), else white;
  - 47 rows changed vs revision 2 (40 → sparkling, 4 "Rosé Blanc de Noir" → rosé; 14 in the ≤ $25 pool, 7 lockbox); 13 rows stay white (German/Austrian still Blanc de Noir, a Malbec, a Grenache, an Oregon still rosé-style wine); 1 is ambiguous (Treveri Cellars, likely sparkling, but its note has no bubble cue) and is left white rather than tuned;
  - tests are built from the affected titles.
- **Colour coverage:** 59.3% red, 30.9% white, 4.3% sparkling, 3.4% rosé, 0.7% fortified, 1.5% unmapped.
- **Not added:** price, exchange-rate or vintage-chart data.

### 3.5 Formatted dataset & dataset description
- **Dataset:** `data/processed/wine_prepared.parquet` (118,378 × 29; lockbox flagged). It's rebuilt by `prepare()` and git-ignored. The dictionary with definitions and provenance is committed (`wine_prepared_dictionary.csv`).
- **Model format** (`features.build_preprocessor`): TF-IDF on `note`; one-hot on origin, grape and colour; standardised vintage and length; flags; log price in the ranker. It's fitted inside each training fold. A demo fit gives 8,675 features.
- **Leakage audit, revision 2, with checks that can fail (all PASS):**
  - an independent give-away term list (0.61% of notes, 723, still match; mostly descriptive, e.g. "to the point of", plus price-relative residue such as "price point", which the strict DM1b mask removes). The 1% bar is a coarse tolerance with no deeper justification: on its own it would not catch one leak family of the barrel-sample size (≈ 0.6%), so it is backed by the per-pattern counts in §3.2 and the probe below;
  - no note text shared across folds;
  - the lockbox is exactly the four frozen critics;
  - a **development-only probe:** the 40 tokens most correlated with the score contain no give-away term ("years", "rich", "simple", "complex", "concentrated", …).
- **R-3** is an evaluation-time filter keyed on **title only**, more conservative than the title + variety wine key.
- **Carried to Phases 4–5:**
  - the R8 attribution filter per development fold in CV (`splits.anon_lockbox_like(..., critics=<fold critics>)`). **Pre-registered:** CV uses the per-fold filter; the final Phase 5 fit uses the lockbox filter. The per-fold filters are larger (critic round 2 measured 2,048 / 1,823 / 4,039 / 3,095 for folds 0/1/3/4 vs 859), and Phase 4 reports this size difference;
  - a Phase 5 sensitivity run excluding all anonymous notes whose top guess is a lockbox critic (1,257 remain below p = 0.5);
  - the stricter DM1b mask (`strict_price_mask`: price-relative wording + `_price_`);
  - DM5(a), reported with recall in the 0.5–0.6 Jaccard band.

## 4. Modeling
### 4.1 Modeling techniques & assumptions
### 4.2 Test design
### 4.3 Parameter settings, models & model descriptions
### 4.4 Model assessment & revised parameters

## 5. Evaluation
### 5.1 Assessment against business success criteria · approved models
### 5.2 Review of process
### 5.3 Possible actions & decision

## 6. Deployment
### 6.1 Deployment plan
### 6.2 Monitoring & maintenance plan
### 6.3 Final presentation
### 6.4 Experience documentation (lessons learned)

---

## References
- Chapman, P. et al. (2000). *CRISP-DM 1.0: Step-by-step data mining guide.* SPSS.
- Schröer, C., Kruse, F., & Marx Gómez, J. (2021). A systematic literature review on applying CRISP-DM process model. *Procedia Computer Science*, 181, 526–534.
- IBM. *CRISP-DM help overview*, IBM SPSS Modeler documentation.
- Thoutt, Z. (2017). *Wine Reviews* [dataset]. Kaggle. https://www.kaggle.com/datasets/zynicide/wine-reviews (data from WineEnthusiast, winemag.com).
