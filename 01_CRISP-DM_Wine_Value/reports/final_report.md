# The $20 Bottle That Drinks Like $60: Finding Value Wines with CRISP-DM

*CMPE 255 · Assignment 4 · Project 1 · Author: Anita Agasaveeran*

> Every number in this report comes from a cell in `notebooks/CRISP_DM_Wine_Value.ipynb`, which is saved with its outputs. Data: [Wine Reviews](https://www.kaggle.com/datasets/zynicide/wine-reviews) (Zack Thoutt; scraped from WineEnthusiast, June 2017; CC BY-NC-SA 4.0). This report is shared under the same licence.

## Executive summary
**Problem.** A retailer samples about 100 of roughly 1,000 unscored wines at $25 or less in each buying round. The question: can tasting notes find the ones critics will rate 90+?

**Approach.** CRISP-DM on 118,378 WineEnthusiast reviews. Four critics were sealed away as a lockbox, and every target and hypothesis was registered before modeling. The models were chosen on critic-held-out folds, frozen in a commit, and scored on the lockbox once; all twelve complete re-executions of the identical frozen code (thirteen logged; one was stopped by a Phase 6 assertion, fixed and re-run) reproduced every first-run table byte for byte.

**Results on the four unseen critics:**
- **Shortlist:** 76% of a 100-wine shortlist are value wines, against 39% for the best simple rule (1.95×, LB 1.76). It held without the notes probably written by lockbox critics. Within one writer's wines it is weaker (top-10% lift 1.29× for Krebiehl, LB 1.19).
- **Score estimate:** error is 31.5% below the variety × country baseline, and 74% of estimates fall within ±2 points (+7.5 pp over the baseline). Of the five candidates, the frozen one ranks 4th on the lockbox.
- **Profiles:** the 8 flavour profiles were named by both blind reviewers, but with little margin (one reviewer gave 6 of 8 the lowest passing confidence); that they hold for a new writer is not shown.
- **Hypotheses:** all six replicate as written. H6 (a strong winery record goes with more value wines) is positive within every critic: clearly for Krebiehl and Sullivan (LB +15 and +18 pp), marginally for O'Keefe (+5.8 pp, LB −2.0), and Jenssen has only 4 such wines. H5 (whites) is a writer-mix effect, not a buyer insight.

**Caveats.**
- **The score band depends on the writer's level.** The pooled level correction over-predicted the largest lockbox critic, whose Italian wines gain only +1.4 pp, and one writer is predicted worse than the baseline.
- **The score band's gain doesn't survive masking.** With verdict words removed, the stand-in for retailer notes, the ±2 gain falls to +2.7 pp, below the +5 pp target.
- **P(90+) over-predicts** the value rate by 10 pp.

**Recommendation.** Go to a pilot on 400 retailer notes with the frozen models (Phase 5 costed it at about $10,000 for 400 samples; Phase 6 replaced the purchase with published reviews, about $1,200–2,400 of analyst time plus a data licence, keeping $10,000 as a fallback, §6.1), judging the shortlist and the score band each on its own part of the pilot gate. This is a post-unsealing amendment to the pre-registered gate (§1.1); the original joint gate is still reported. On masked notes, the stand-in for retailer notes, simulated pilots pass the shortlist's part 67–99.5% of the time, depending on the writer mix (99.5% in the lockbox's mixed pool, 67–94% in development pools, 54% in a pool of Krebiehl's notes alone). The band's part passes 24% of the time in the lockbox's mixed pool, because half that pool is one writer whose level the band misjudges. So the shortlist is the product. The band is shown internally only if it clears its own bar, and is withdrawn for any note source whose average error is clearly outside ±1 point.

**Deployment (§6).** The frozen models are saved as one artifact that reproduces every lockbox prediction exactly, behind an internal Streamlit tool (one-wine screen in about 0.03 s per query; buying-round shortlist) and two scripts that score a buying round and judge the pilot. The pilot protocol is fixed in code before any pilot data; it is to be committed and tagged (`wine-phase6-rev7`) before rollout, which is what makes the freeze checkable. It checks every 100 scores, up to 800. The band's stop rule runs per note source, pooled small sources, country and whole pilot, and the same rule hides the band in the tool. A futility pause covers the shortlist from 200 wines. The decision comes only once there are ≥ 400 wines from ≥ 3 named note sources with 50+ each, scored by WineEnthusiast (other critics' scores are a sensitivity). Country, region, grape and winery names are mapped to the training spellings before scoring, and prices are converted to 2017 dollars with a deflator fixed before round 1. On simulated pilots from masked lockbox notes, the shortlist deploys 97.5% of the time and the band is shown 16% of the time. Pilots from one- or two-writer pools stop without a decision, as intended. Outcome scores come from later published reviews, not bought samples: at an assumed 10% review yield and 3-month review lag, 400 scored wines arrive by about month 8, within a 12-month calendar cap. The main route costs about $1,200–2,400 of analyst time plus a data licence; a $10,000 tasting-panel fallback applies if the reviews come too slowly. Every buying round gets data-quality flags and input-drift alerts, outcomes are checked as scores arrive, and nothing retrains itself.

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
- Every target is met by **every** development fold, including fold 3. *(Phase 4 note, 2026-11-07: this holds for the untuned feasibility models. Under Phase 4's per-fold R8 filter, plain ridge fails fold 3; the selected calibrated ridge meets every target in every fold, §4.4.)*

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

> **Amendment, 2026-11-08 (after the lockbox was unsealed; Phase 5 §5.3, option F).** The two bullets above are now applied **per output**, not jointly. The shortlist may be deployed if it passes the second bullet; the score band may be shown only if it also passes the first. The joint result of both bullets is still reported. Neither bar was changed. The reason that doesn't depend on the lockbox: BO1 and BO2 are separate objectives, and a level error shared by a source's wines moves every one of that source's scores in the band but leaves their order on the shortlist unchanged. That holds within a source; across sources, level differences still cost the shortlist about 0.08 of P@100 on the lockbox (§5.1 point 6). The lockbox also showed the band's part is the one likely to fail (§5.3). A stop rule for the band was added at the same time (`config.PILOT_STOP_*`). This amendment was made after the lockbox results were known and before any pilot data exists. It is frozen in git tag `wine-phase5-rev4`.

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

> **Revision 4** (after critic rounds 1–3, 2026-11-07; revisions 3 and 4 changed interpretation and diagnostics only, no model or selection). Development data only; the lockbox (fold 2) stays sealed. Everything is in notebook §4 (saved with outputs) and `winevalue.cv`, `scoring`, `evaluate`, `clustering`, `descriptors`, `insights`. The result tables and fold predictions are in `reports/tables/phase4_*`. The order of every fit is in [`reports/phase4_run_log.md`](phase4_run_log.md).
>
> **What changed in revision 2, and why it matters:** the DM1 model and the DM3 vocabulary were both re-chosen after the outer-fold results of revision 1 had been seen. The new rules were written down before the new runs, and DM1 is now chosen on inner folds only. But these are **post-hoc revised settings** (CRISP-DM 4.4), not fresh tests. The lockbox remains the only unbiased estimate.

**Phase 4 in brief:**
- **DM1 / BSC2:** the selected score model is a **calibrated ridge**: the ridge prediction, rescaled by two numbers (a + b × score) fitted on out-of-fold predictions. It had the lowest inner critic-held-out MAE (1.762) and meets every DM1 and BSC2 target in every fold. On fold 3 it cuts MAE by **23.0%** (LB 21.9%). The revision 1 choice, the stack, came out worse (16.3%); adding origin inputs made it worse in all four inner folds, for reasons not established.
- **Why the calibration helps, and where it doesn't:** every held-out fold is under-predicted by plain ridge, and so are **10 of 13 writers (96% of reviews)**. Two pooled calibration numbers shift scores up by 0.6–0.9 points: review-weighted writer bias falls from 0.98 to 0.38 points, and mean outer MAE from 1.83 to 1.66. The shift **hurts the writers ridge already over-predicts** (Buzzeo −13.3 pp of reduction, Dykes −12.2, Kostrzewa −9.9) and slightly overshoots two others. Knowing each critic's own level would cut MAE by a further **6%**.
- **The per-fold R8 filter** removes notes that matter. On fold 3, about two-thirds of the plain ridge's drop is specific to the attributed notes, and a third is plain data loss. Across the filter variants the selected model moves by about 2 points of reduction at most. The gap to Phase 1's 11.9% comes from the change of inputs and model (α alone is about 1.8 pp), not from data or leakage. Note length is involved on fold 3, but the mechanism is **not established**.
- **DM2 / BSC1:** ridge + log price is still the selection (P@100 0.63–0.68, 1.55–1.96× the best simple rule, top-10% lift LB ≥ 1.47). It now has a frozen **P(90+)** and **score band** for the app.
- **DM3:** the profiles now use only the frozen aroma lexicon. They're stable across producers (10 of 10 winery splits) but **not shown to be independent of writers** (critic-disjoint Jaccard 0.23, bar 0.5).
- **DM6:** the §1.3 model (fixed effects for wine and critic) gives a critic SD of **1.49** points. With a richer wine description it gives **0.93**, and the two rankings correlate at only 0.56. Six critics have a clear, same-sign effect in both.
- **H1–H6** all hold in development data, but H5 changes sign across folds (−7.8 to +6.9 pp) and within critics (−1.1 pp).

### 4.1 Modeling techniques & assumptions
| Goal | Candidates | Why | Key assumptions (and where they're tested) |
|---|---|---|---|
| DM1 score (price-free) | Baselines (global mean, **variety × country**); **ridge** on TF-IDF of `note` + one-hot origin, grape, colour + vintage, length, flags; **calibrated ridge** (a + b × ridge score, fitted by least squares on out-of-fold scores of all training rows, or of named rows only); **stack** (LightGBM on the out-of-fold ridge score + the structured inputs) **with or without origin** | Ridge is the transparent text baseline. Calibration is the smallest model that can carry a new writer's average level, and the stack the most flexible. Calibrated ridge and the no-origin stack were added in revision 2 | (a) A new writer differs from training writers partly by a level offset: **partly supported** (4.4: held-out named groups +0.35 to +2.08; per-writer offsets after calibration explain about 6% of the remaining MAE). **The selected model's working assumption:** a new house's writers sit, on average, above the ridge prediction by about the pooled shift (+0.6–0.9 points). That holds for 10 of 13 development writers, not for all. (b) The vocabulary transfers across writers: **partly** (note length transfers poorly to some writers, 4.4). (c) **For Italy, the training data is 96.4% anonymous notes**, and the lockbox is 54% Italy (4.2): the model relies on anonymous notes resembling a named critic. **Not testable in development**; Phase 5 reports Italy vs non-Italy |
| DM1b | The DM1 candidates refit on masked text: frozen list; round-1 list; frozen + strict price mask; and, as a stress test, the 200 strongest ridge words per fold | The MAE increase isolates how much the model leans on the masked words | Masking removes the verdict, not the description |
| DM2 ranker | **Ridge + log price**; **stack classifier** P(90+) + log price; the same **+ winery track record** | Only order within a pool matters, so α is now tuned on inner pool precision | Price and the winery's record are known at decision time |
| DM3 profiles | **NMF** and **k-means**, k = 6–15, on three vocabularies (pre-registered 5,000-term TF-IDF; revised, minus grape names and verdict words; **lexicon**, the 139 frozen aroma terms), each fitted on all notes or a writer-capped sample | NMF gives additive term weights; the lexicon keeps writers' non-flavour habits out | "Stable across producers" is necessary but not sufficient for meaning; writer independence is tested separately (4.4) |
| DM4 rules | **FP-Growth** on descriptor items + grape | Exhaustive for ~180 items | A fixed lexicon captures descriptors; lift corrects for grape popularity |
| DM5 | MinHash LSH + exact Jaccard (Phase 3) | Fixed in Phase 3 | – |
| DM6 | **§1.3 model:** score = wine cell (fixed effect) + critic (fixed effect), within-cell OLS on all named development rows, winery-clustered SEs; two wine descriptions (A: variety × country; B: variety × province + log price) | One common baseline for every critic, unlike revision 1's per-fold residuals | Critics are compared only inside cells that two or more of them reviewed. Effects still include whatever the cell definition leaves out |

**Not run: transformer embeddings** (optional in §1.3). This is a scope and compute decision. The project runs end to end on a laptop CPU and a free Colab runtime, and the TF-IDF models already meet every development target. Whether embeddings would transfer better to new writers is untested. §1.4's fallback scope is about DM5 and DM6, so it doesn't apply here.

### 4.2 Test design
- **Outer CV:** each development critic fold (0, 1, 3, 4) is held out in turn. **The lockbox never enters Phase 4.**
- **Training set:** the other development folds + anonymous notes, **minus anonymous notes attributed (p > 0.5) to the held-out fold's critics** (per-fold R8).
- **Test set:** the held-out fold minus titles seen in training (R-3).
- **Inner CV (revision 2):**
  - the remaining named folds;
  - each anonymous note goes to the inner fold of its **top-guess critic**, so it's held out with its likely writer (top guess outside the inner folds: random);
  - R-3 applies to inner validation;
  - **all inner scores are on named rows**, so they are critic-held-out;
  - caveat: for inner fold g, the calibration and the stack's inner curve use other folds' out-of-fold scores, whose ridge models saw g's labels. That mildly favours calibrated and stacked candidates over plain ridge. It can't change ridge vs calibrated ridge (1.762 vs 1.917), but the margin over the no-origin stack is only 0.012.
- **Tuning:**
  - ridge α ∈ {0.25, 0.5, 1, 2, 4, 8}: inner MAE (DM1), or inner top-10% pool precision (ranker);
  - LightGBM: leaves {15, 63} × trees {25, 50, 100, 200, 400} on one **pooled inner curve**, which replaces early stopping and the mean best iteration.
- **Metrics:**
  - as pre-registered, with one-sided 90% winery-cluster bootstrap lower bounds (500 resamples);
  - these LBs hold the writers fixed, so they **don't** bound new-writer risk; see the per-critic table.
- **Selection:**
  - DM1 (revision 2, written before the runs): lowest mean inner MAE, within 0.01 the simplest, and the winner must meet the targets in every outer fold;
  - DM2 (unchanged): best mean outer P@100 among rankers meeting BSC1 in every fold, within 0.01 the simplest.
- **Provenance:** the revision 1 design was written at 22:29 on Nov 4, before the first fit at 22:30, per the session record. No commit exists from before fitting, and two fold-3 looks happened before the full run ([run log](phase4_run_log.md)). The Phase 4 commit is tagged before any Phase 5 run.

| Held-out fold | Critics | Anonymous dropped (p > 0.5) | Anonymous with top guess here | Training rows | Test rows (after R-3) | ≤ $25 pool |
|---|---|---|---|---|---|---|
| 0 | Roger Voss | 2,163 | 3,961 | 75,492 | 22,836 | 10,786 |
| 1 | Jim Gordon, Michael Schachner | 1,775 | 3,991 | 80,945 | 17,781 | 12,658 |
| 3 | 6 critics (Gregutt, Czerwinski, Iijima, …) | 4,189 | 8,596 | 78,541 | 17,784 | 9,024 |
| 4 | 6 critics (Boone, Kettmann, Buzzeo, …) | 3,022 | 6,263 | 79,508 | 17,949 | 6,134 |

- **Size:** CV training sets are **19–25% smaller** than the Phase 5 training set (100,530 rows).
- **Why these counts differ from §3.5's (2,048 / 1,823 / 4,039 / 3,095):** §3.5's classifier was fitted on the table before preparation, and this one on the prepared table.
- **Fold 3 isn't a fair lockbox proxy for this filter:** 35.7% of anonymous notes have a fold-3 top guess, against 5.1% for the lockbox critics.
- **Phase 5 sensitivity set, now frozen as an ID list** (`reports/tables/phase5_sensitivity_anon_ids.csv`): 1,234 anonymous development notes whose top guess is a lockbox critic. This replaces the "1,257" from the earlier classifier fit. On this refit, 67 of them have p > 0.5 and are still in the 100,530-row Phase 5 training set, because the pre-registered lockbox filter used the Phase 3 classifier. The sensitivity run covers them.
- **Lockbox exposure (counts only):**
  - Tuscany, Piedmont, Veneto, Sicily & Sardinia, Central Italy, Southern Italy and Lombardy are 95–100% anonymous in development data and make up 8,557 lockbox rows;
  - Washington (4,075 lockbox rows) is 0.2% anonymous.

### 4.3 Parameter settings, models & model descriptions
**Tuned settings** (inner folds only):

| Fold | Ridge α (DM1) | Ridge α (ranker) | Calibration a / b | Shift at score 88 | Stack leaves / trees | Ranker stack |
|---|---|---|---|---|---|---|
| 0 | 1.0 | 4.0 | 6.15 / 0.937 | +0.63 | 15 / 50 | 63 / 50 |
| 1 | 1.0 | 2.0 | 9.42 / 0.902 | +0.81 | 15 / 25 | 15 / 50 |
| 3 | 2.0 | 8.0 | 4.75 / 0.956 | +0.86 | 15 / 50 | 63 / 50 |
| 4 | 1.0 | 2.0 | 10.69 / 0.887 | +0.75 | 15 / 50 | 15 / 50 |

- **Ridge α:** the inner MAE curve is flat between 1 and 2 in every fold, so the extended grid didn't move the DM1 α off the old edge. The ranker's inner precision rises to α = 4–8 in folds 0 and 3 (the old grid cut those short), and peaks at an interior α = 2 in folds 1 and 4.
- **Stack:** the pooled curve picks 25–50 trees everywhere.
- **Grid edges, left as they are:**
  - the ranker's α = 8 in fold 3 is the new top edge (inner precision 0.634 at 4, 0.635 at 8, so the curve is flat);
  - the rejected stack's 25 trees in fold 1 is the bottom edge;
  - LightGBM uses an L2 objective for an MAE target, and `objective="l1"` wasn't tried. Neither model is selected.

**Model descriptions:**
- **Calibrated ridge (selected DM1):**
  - the ridge prediction, raised by about **0.6–0.9 points** around a typical score and slightly compressed (b = 0.89–0.96);
  - the two numbers come from out-of-fold predictions, where every named row's writer was held out;
  - the ridge leans on evaluative words ("beautiful", "gorgeous", "superb" raise it; "lacks", "strange", "sour", "odd", "watery" lower it), drinking windows ("2030", "drink through") and note length.
- **Ridge + log price (selected DM2):**
  - the same inputs plus standardised log price (0.92 points per SD of log price);
  - the score is only used to order wines inside a pool.
  - **P(90+)** is a logistic map of its out-of-fold score fitted on training ≤ $25 rows.
  - **Score band** is the DM1 score ± the 80th percentile of the out-of-fold absolute error on named rows (±2.6–2.8 points).
- **Stack (rejected):** 76% of its gain comes from the ridge score, 11% from province, 9% from length. The "ridge score" is the full ridge (text + structured inputs), so the stack sees the structured inputs twice.
- **NMF profiles (DM3):** each profile is a non-negative weight over the 139 lexicon terms; a note's profile is its largest weight. 6.0% of notes contain no lexicon term and get no profile.
- **FP-Growth rules (DM4):** {descriptors} → {grape}, with support ≥ 0.5% and lift ≥ 2, from the item table.
- **Saved models:** `reports/tables/phase4_fold_predictions.csv.gz` holds every test-row prediction of the baseline, ridge, the selected DM1, the stack and the selected ranker. Phase 5 refits the final models on all development data, and Phase 6 saves the pipeline.

### 4.4 Model assessment & revised parameter settings
**DM1 / BSC2: price-free score models** (MAE · reduction vs variety × country (90% LB) · ±2 accuracy on ≤ $25 wines, gain in pp):

| Model | Fold 0 | Fold 1 | Fold 3 | Fold 4 | Mean inner MAE | Mean outer MAE | Meets in every fold |
|---|---|---|---|---|---|---|---|
| Variety × country | 2.67 | 2.63 | 2.26 | 2.51 | – | 2.52 | – |
| Ridge | 1.80 · 32.5% · 0.71, +16.6 | 1.65 · 37.3% · 0.72, +26.5 | **2.23 · 1.4% (LB −0.2) · 0.55, −0.6** | 1.62 · 35.4% · 0.73, +19.1 | 1.917 | 1.827 | ✗ (3 of 4) |
| **Calibrated ridge, all OOF (selected)** | 1.76 · 34.2% (33.1) · 0.67, +12.3 | 1.51 · 42.8% (42.2) · 0.74, +27.9 | **1.74 · 23.0% (21.9) · 0.69, +12.7** | 1.62 · 35.7% (34.9) · 0.65, +10.8 | **1.762** | 1.655 | ✅ |
| Stack, no origin | 1.74 · 34.7% · 0.71, +16.0 | 1.63 · 38.2% · 0.68, +21.9 | 1.69 · 25.4% · 0.71, +15.4 | 1.60 · 36.2% · 0.67, +13.0 | 1.774 | 1.665 | ✅ |
| Calibrated ridge, named OOF | 1.78 · 33.3% · 0.64, +9.0 | 1.56 · 40.7% · 0.70, +24.4 | 1.65 · 27.3% · 0.71, +14.5 | 1.66 · 34.0% · 0.61, +6.5 | 1.785 | 1.662 | ✅ |
| Stack (revision 1 choice) | 1.81 · 32.2% · 0.72, +17.0 | 1.80 · 31.5% · 0.65, +19.1 | 1.89 · 16.3% · 0.67, +11.4 | 1.57 · 37.7% · 0.72, +17.9 | 1.869 | 1.767 | ✅ |

- **Selection (revision 2 rule):** calibrated ridge (all OOF) has the lowest inner MAE (1.762, next 1.774) and meets every target in every outer fold. Its outer mean is also the lowest, but the outer folds didn't choose it.
- **All LB conditions hold for the selected model:** reduction LBs 21.9–42.2%; ±2 gain LBs +9.6 to +27.1 pp.
- **Trade-off:** calibration lowers MAE but compresses the scale, so ±2 accuracy on ≤ $25 wines drops in folds 0 and 4 (0.71 → 0.67, 0.73 → 0.65). It stays above 0.60.
- **Why the stack lost:** repairing the inner folds didn't rescue it. Adding origin worsens the stack in all four inner folds and in three of four outer folds (fold 3: 16.3% with origin, 25.4% without; fold 4 is the exception). **Why is not established.** Anonymous notes' near-zero out-of-fold residuals can't be read as "no level gap", because anonymous rows aren't reliably writer-held-out.

**DM1b:**
- masking the frozen verdict list raises the selected model's MAE by **0.07 / 0.04 / 0.01 / 0.04** (target ≤ 0.15), and the round-1 list and strict price mask change little;
- with the frozen mask applied, the model still cuts MAE by 31.7 / 41.1 / 22.5 / 34.2% (LB 21.4% on fold 3);
- **stress test** (reported only): masking each fold's 200 strongest ridge words, including non-listed ones like "odd", "weird", "disappointing", costs up to **0.17**. Fold-3 reduction is then 18.9%. The model does lean on evaluative language beyond the frozen list, which matters if a new house's writers phrase verdicts differently.

**Error analysis.**
- **Level gap:**
  - mean out-of-fold residual is **+0.35 to +2.08** for every named fold held out of training (anonymous rows: −0.02 to −0.05, but they aren't reliably writer-held-out, so this isn't evidence about anonymous writers' level);
  - the pooled calibration recovers most of this: mean outer MAE 1.83 (ridge) → 1.66;
  - ridge trained on named folds only still under-predicts in all four folds (bias −1.05 / −0.76 / −2.33 / −0.27), so the gap isn't caused by anonymous notes.
- **Per critic** (MAE reduction, selected model):
  - Gregutt **15.5%** (half of fold 3), Iijima 26.2%, Czerwinski 34.3%;
  - DeSimone **−1.0%** (fold 4, 461 reviews);
  - Kostrzewa 16.8%, Buzzeo 23.4%;
  - all others 34–52%.
  - So the fold-level LBs don't bound what happens with one new writer. O'Keefe writes 50% of the lockbox pool (counts only).
- **What the pooled calibration does to each writer** (ridge → calibrated, MAE reduction and bias; writers with ≥ 30 test reviews):
  - helps the under-predicted: Gregutt −15.2% → 15.5% (bias −2.56 → −1.63), DeSimone −39.7% → −1.0%, Iijima 3.4% → 26.2%, Schachner 36.2% → 43.2%, Czerwinski, Kettmann, Voss, Peartree;
  - hurts those ridge already over-predicts: Buzzeo 36.7% → 23.4% (+0.72 → +1.43), Dykes 50.3% → 38.1%, Kostrzewa 26.7% → 16.8% (+0.18 → +1.07);
  - slightly overshoots two others: Gordon −1.2 pp, Boone −0.8 pp;
  - fold 3's bias only halves (−1.84 → −0.93).
- **Knowing each critic's average level** after calibration would cut the review-weighted MAE from 1.66 to **1.56** (6%). Per-writer offsets range from −1.7 to +1.4, but they're a modest part of the remaining error, and segment differences (fortified 1.99 vs Chile 1.40) are about as large.
- **By segment:** red, white, rosé and sparkling 1.50–1.69; fortified hardest (1.99, n = 748). Of the six largest countries, Chile is easiest (1.40) and France and Portugal hardest (1.74).
- **Note length** (diagnostic, found on an outer fold, so **not acted on**). Ridge MAE reduction with and without `n_words` on each design training set:

| Fold | With length | Without length | Bias with / without |
|---|---|---|---|
| 0 | 32.5% | 34.2% | −0.65 / −0.16 |
| 1 | 37.3% | 34.0% | −0.87 / −0.95 |
| 3 | 1.4% | 9.3% | −1.84 / −1.52 |
| 4 | 35.4% | 32.5% | −0.48 / −0.50 |

  - Dropping length helps folds 0 and 3 and hurts folds 1 and 4.
  - The fold-3 gain is mostly Gregutt (−15.2% → −2.0%).
  - The per-critic gains don't track the per-critic length slopes: Kostrzewa and DeSimone have the flattest slopes (0.59 and 0.77 points per 10 words) and don't gain. Those slopes are marginal, not the model's partial coefficient.
  - Dropping length also changes bias (fold 0: −0.65 → −0.16), so length and level are entangled.
  - **The mechanism is not established.** The Phase 5 sensitivity "calibrated ridge without length" is exploratory.

**What the per-fold R8 filter actually did** (MAE reduction: ridge / selected model; matched control = the same number of non-attributed anonymous notes dropped, matched on province, mean of 3 draws):

| Training set | Fold 0 | Fold 1 | Fold 3 | Fold 4 |
|---|---|---|---|---|
| Per-fold R8 (design) | 32.5 / 34.2% | 37.3 / 42.8% | 1.4 / 23.0% | 35.4 / 35.7% |
| No filter | 32.7 / 34.5% | 38.4 / 42.9% | 7.1 / 25.1% | 35.5 / 36.2% |
| Matched control | 32.6 / 34.2% | 39.1 / 43.1% | 5.1 / 24.8% | 35.1 / 35.6% |
| All top-guess notes dropped (Phase 5 sensitivity analogue) | 32.4 / 34.0% | 37.6 / 42.9% | 0.1 / 22.9% | 35.2 / 35.1% |
| Named folds only | 27.0 / 30.8% | 41.7 / 40.9% | −15.0 / 24.6% | 32.1 / 29.0% |

- **Decomposition** (no filter − matched control = data loss; matched control − design = specific to the attributed notes):
  - fold-3 ridge: **2.0 pp** data loss and **3.7 pp** attribution-specific, so about two-thirds of the drop comes from the attributed notes (control draws 4.6–5.6%);
  - fold-3 selected model: 0.3 pp and 1.8 pp;
  - folds 0 and 4: both parts below 0.6 pp for either model;
  - fold 1 ridge: −0.8 pp data loss and 1.9 pp attribution-specific.
- **What that means:** the attributed notes carry something about their writers that a random sample doesn't. Removing them costs the plain ridge on fold 3, which is what the filter is for. Across the filter variants (design, no filter, matched control, all top-guess dropped) the selected model moves by at most 2.2 pp on fold 3 (22.9–25.1%).
- **Phase 1's 11.9% on fold 3**, rebuilt one change at a time:

| Step | Fold-3 reduction |
|---|---|
| Phase 1 as run | 11.9% |
| + Phase 3 rows | 12.3% |
| + Phase 3 cleaned text | 12.4% |
| + Phase 4 inputs and tuned ridge | 7.1% |

  Neither the Phase 3 rows nor the cleaned text explain the gap; the change of inputs, TF-IDF set-up and α does (α alone moves the no-filter fold 3 from 8.9% at α = 1 to 7.1% at α = 2). On fold 3, dropping length more than closes it (13.9% at α = 2, 15.2% at α = 1), but it hurts folds 1 and 4 (table above). Revision 1's "optimism found and fixed" was wrong.

**DM2 / BSC1: rankers** (expected P@100 in 200 cycles of 1,000 ≤ $25 candidates · lift vs the best frozen simple rule · top-10% lift LB):

| Ranker | Fold 0 | Fold 1 | Fold 3 | Fold 4 | Mean P@100 |
|---|---|---|---|---|---|
| Value base rate in pool | 0.19 | 0.10 | 0.22 | 0.19 | – |
| Best simple rule | price 0.42 | price 0.34 | winery then price 0.35 | winery then price 0.38 | – |
| **Ridge + log price (selected)** | 0.65 · 1.55× · 1.47 | 0.63 · 1.85× · 1.76 | 0.68 · 1.96× · 1.77 | 0.64 · 1.69× · 1.55 | **0.649** |
| Stack P(90+) + log price | 0.64 · 1.54× · 1.46 | 0.61 · 1.80× · 1.72 | 0.69 · 2.00× · 1.82 | 0.67 · 1.77× · 1.62 | 0.655 |
| … + winery track record | 0.64 · 1.53× · 1.45 | 0.62 · 1.81× · 1.74 | 0.69 · 2.00× · 1.83 | 0.67 · 1.76× · 1.62 | 0.654 |

- **Selection:** all three meet BSC1 in every fold and sit within 0.01 (0.649 vs 0.655), so the simplest wins.
- **Sensitivity (mean over folds):**
  - P@50 = 0.76 and P@200 = 0.52 with 1,000 candidates;
  - P@100 = 0.52 with 500 candidates and 0.76 with 2,000;
  - the simple rules stay at 0.27–0.38.
- **Writer mix matters for ranking too.** In a one-writer pool (fold 0), a writer's level can't change the order. In mixed pools it can:
  - fold 3's top 10% is 55% Czerwinski (30% of the pool), but only 26% Gregutt (41% of the pool, highest value rate);
  - if each critic's level were known, P@100 would rise from 0.68 to **0.74** (fold 3) and from 0.64 to **0.67** (fold 4). This is an oracle, not available in use.
  - The lockbox mixes four critics, so a similar loss can apply there; Phase 5 reports the shortlist writer mix.
- **BSC4 outputs, frozen before Phase 5:**

| Fold | Brier (base rate) | Mean P(90+) vs value rate | Band half-width | Band coverage |
|---|---|---|---|---|
| 0 | 0.109 (0.151) | 0.18 vs 0.19 | 2.6 | 0.77 |
| 1 | 0.054 (0.091) | 0.12 vs 0.10 | 2.8 | 0.87 |
| 3 | 0.140 (0.173) | 0.14 vs 0.22 | 2.6 | 0.78 |
| 4 | 0.124 (0.156) | 0.25 vs 0.19 | 2.7 | 0.83 |

  - **P(90+):** pooled reliability is close: predicted 0.04 / 0.14 / 0.29 / 0.49 / 0.69 / 0.87 against actual 0.04 / 0.16 / 0.31 / 0.51 / 0.68 / 0.85 by bin. Per fold it inherits the writer level (fold 3 under, fold 4 over).
  - **The 80% band covers 77–87%.**

**DM3: flavour profiles (revision 2).**
- **Revision 1's rule rested on one split.** On its own winery split, the pre-registered vocabulary passes (min Jaccard 0.538). Across 10 splits the minimum is 0.000 in one, and every vocabulary collapses on **critic-disjoint** splits.
- **Settings at their chosen k** (NMF; k-means fails the seed rule in every setting):

| Vocabulary · fit set | k | Splits passing (of 10) | Mean matched Jaccard | Smallest profile | Critic-disjoint mean Jaccard |
|---|---|---|---|---|---|
| Pre-registered · all | 8 | 9 | 0.85 | 6.2% | 0.15 |
| Pre-registered · writer-capped | 7 | 7 (fails) | 0.75 | 6.3% | 0.18 |
| Revised · all | 8 | 8 | 0.75 | 9.8% | 0.13 |
| Revised · writer-capped | 7 | 10 | 0.82 | 9.9% | 0.13 |
| **Lexicon · all (selected)** | **8** | **10** | **0.80** | **7.6%** | **0.23** |
| Lexicon · writer-capped | 9 | 8 | 0.74 | 6.3% | 0.21 |

- **Selected by the rule** (highest critic-disjoint mean among settings passing the seed rule): **lexicon, all notes, NMF, k = 8**.
- **BSC3 stability condition:** passes across producers (every split's minimum Jaccard ≥ 0.667).
- **Writer independence: not shown.** No setting reaches 0.5 on critic-disjoint splits. The chance level for matched top-10 sets from the lexicon is 0.098 (uniform) and **0.174** (weighted by document frequency; 95th percentile 0.209). So 0.23 is barely above chance, and one critic-disjoint split (0.194) is inside it. **The profiles barely reproduce across writers.** BSC3's blind naming may pass on development profiles and still not describe how a new house's writers group wines.
- **Less writer-led than before:**
  - Cramér's V with critic is **0.17**, against 0.37 for the revised vocabulary, and colour now carries more (0.36 vs 0.30);
  - the largest writer share in any profile is 38% (Voss, base 20%), down from 76%.
- **Profiles** (first five top terms, verbatim; full lists in the notebook):
  1. cherry, black cherry, chocolate, herb, tobacco (7.6%);
  2. apple, lemon, pear, peach, lime (21.4%);
  3. blackberry, chocolate, cassis, pepper, black currant (13.2%);
  4. spice, red fruit, black fruit, pepper, baking spice (12.2%);
  5. plum, herbal, earthy, herb, chocolate (12.3%);
  6. oak, vanilla, smoky, toasty, toast (13.3%);
  7. citrus, mineral, tropical, melon, stone fruit (9.4%);
  8. raspberry, strawberry, jammy, cranberry, pepper (10.7%).
- **Fit quality:**
  - cosine silhouette 0.08;
  - UMass coherence −2.4 to −3.3;
  - 6.0% of notes have no lexicon term (generic notes such as "ripe and fruity … firm tannins") and get no profile;
  - the weakest-fitting 1% include notes that mix many descriptors (five examples in the notebook).
- **Phase 5:** the blind naming test runs on the **primary** (lexicon) and **secondary** (revised vocabulary) settings, declared now. **BSC3 is decided on the primary only;** the secondary is strongly writer-led (V 0.37; one profile 76% Voss) and can't rescue a failure. Reviewers get term lists only. A naming pass does not establish writer independence.

**DM4: descriptor → grape rules.**
- **88 rules** (target ≥ 10). Of these:
  - 84 remain after dropping rules no better than a parent;
  - 53 have confidence ≥ 0.20 (minimum 0.025).
- **Strongest by confidence:** oak + pineapple → Chardonnay (0.85, lift 8.2), oak + pear → Chardonnay (0.78), apple + oak → Chardonnay (0.77), pomegranate → Pinot Noir (0.67, 5.5), apple + vanilla → Chardonnay (0.64), butter → Chardonnay (0.60).
- **Not all consequents are grapes:** five are style or blend labels (Red Blend, Bordeaux- and Rhône-style blends, Rosé, Sparkling Blend), so these are "style or grape" rules.
- **Development replication:** 71 of 82 rules mined on folds −1/0/1 keep lift ≥ 1.5 on folds 3/4, and 52 keep lift ≥ 2.

**DM5.**
- **(a)** Recall **1.000** on 1,694 synthetic positives (537 in the 0.5–0.6 band). It passes, but mostly confirms the implementation.
- **(b)** Engineering check, and **(c)** exploratory 35 of 43: both unchanged from §3.3.
- **"5 similar wines"** (BSC4): built on the same LSH index in Phase 6.

**DM6: critic calibration (§1.3 model).**

| Specification | Rows · cells | Critic SD (noise-corrected) | Lowest | Highest |
|---|---|---|---|---|
| A. Variety × country | 58,715 · 320 | 1.49 (1.46) | Kostrzewa −3.17 | Kettmann +1.90 |
| B. Variety × province + log price | 45,572 · 472 | 0.93 (0.85) | Schachner −1.44 | DeSimone +1.17 |

- **The answer depends on the specification:**
  - the two rankings correlate at 0.56;
  - the largest movers are Peartree (2.73 points), Dykes (2.21), Kostrzewa (1.89), Adams (1.86) and Boone (1.39);
  - **Iijima, Peartree and Dykes have 95% CIs excluding zero with opposite signs in A and B**, so within-specification CIs understate the real uncertainty.
- **Where the sensitivity comes from** (same priced rows):

| Variant | Critic SD | Correlation with A |
|---|---|---|
| A | 1.50 | 1.00 |
| A + log price | 1.25 | 0.94 |
| Variety × province cells | 1.31 | 0.83 |
| Both (B) | 0.93 | 0.56 |

  Both additions matter, together more than either alone. It isn't a sample artefact.
- **Robust conclusion:** six critics have 95% CIs excluding zero with the same sign in both. Schachner, Kostrzewa, Czerwinski and Buzzeo score lower than peers on the same wines; Gordon and Kettmann higher.
- **For BO5** ("how much does a score depend on who tasted it?"): **0.9–1.5 points** of between-critic SD (0.85–1.46 noise-corrected), against a within-cell residual SD of 2.2–2.8.
- **Identification:** all 15 development critics are in one connected component; DeSimone is linked through only 5 partners. Pickard (6 identifying reviews) is not usefully identified.
- **H4 keeps its own pre-registered statistic** (below), which is a different quantity from DM6. H4's per-critic values are relative to each fold's training baseline, which mixes in anonymous and other writers' levels, so they aren't critic levels: Czerwinski is +0.45 there but −1.47 / −1.06 in DM6. "Robust" above means robust across the two DM6 specifications.

**H1–H6, development half of BSC5** (each held-out fold scored with its own training data; one-sided 90% winery LB):

| Hypothesis | Estimate | 90% LB | Bar | Holds |
|---|---|---|---|---|
| H1 longer notes, higher scores (Spearman ρ) | 0.485 | 0.479 | 0 | ✅ |
| H2 within variety × country, pricier → higher (partial r) | 0.590 | 0.584 | 0 | ✅ |
| H3 named designation (points) | +0.71 | +0.67 | 0 | ✅ |
| H4 SD of critic effects (pre-registered statistic) | 1.24 | 1.20 | 0.5 | ✅ |
| H5 ≤ $25: whites more often value than reds | +0.9 pp | +0.1 pp | 0 | ✅ (composition) |
| H6 ≤ $25: strong winery record → more value wines | +27.6 pp | +22.9 pp | 0 | ✅ (0.73% of wines) |

- **H5 holds as pre-registered, but:**
  - it's a composition effect: by fold it's −7.8 / −3.8 / +6.9 / +2.9 pp, and the review-weighted within-critic difference is **−1.1 pp**;
  - it isn't Monte Carlo noise: across 20 bootstrap seeds the LB stays at +0.02 to +0.17 pp and H5 replicates in all 20 (notebook 4.4h);
  - it isn't a buyer insight.
- **H6** applies to the 283 of 38,602 pool wines (0.73%) with a strong record (11 / 87 / 34 / 151 by fold).

**Assessment summary** (development folds vs the Phase 1 targets):

| Criterion | Target | Selected model (folds 0 / 1 / 3 / 4) | Every fold? |
|---|---|---|---|
| DM1 MAE reduction (LB) | ≥ 10% (> 5%) | 34.2 / 42.8 / 23.0 / 35.7% (33.1 / 42.2 / 21.9 / 34.9%) | ✅ |
| BSC2 within ±2 (gain, LB) | ≥ 0.60 (≥ +5 pp, > 0) | 0.67 / 0.74 / 0.69 / 0.65 (+12.3 / +27.9 / +12.7 / +10.8 pp; LB ≥ +9.6) | ✅ |
| DM1b masked MAE increase | ≤ 0.15 | 0.07 / 0.04 / 0.01 / 0.04 | ✅ |
| BSC1 P@100 / lift / LB | ≥ 0.55 / ≥ 1.4× / ≥ 1.2 | 0.63–0.68 / 1.55–1.96× / 1.47–1.77 | ✅ |
| BSC3 stability | 6–15 profiles ≥ 1%, Jaccard ≥ 0.5 | 8 profiles ≥ 7.6%; 10 of 10 splits pass (min 0.667) | ✅ across producers; writer independence not shown (naming: Phase 5) |
| DM4 rules | ≥ 10 | 88 (84 pruned; 53 with confidence ≥ 0.2) | ✅ (lockbox: Phase 5) |
| DM5(a) recall | ≥ 0.90 | 1.000 | ✅ |
| BSC5, development half | ≥ 4 of 6 incl. H5 or H6 | 6 of 6 (H5 a composition effect) | ✅ (lockbox: Phase 5) |

**What Phase 5 runs** (frozen in `config`; the Phase 4 commit is tagged before Phase 5):
- **Models:**
  - DM1 = calibrated ridge (all OOF);
  - DM2 = ridge + log price, with the P(90+) map and the ±80% band;
  - DM3 = lexicon NMF, k = 8 (primary, which decides BSC3), and revised-vocabulary NMF, k = 8 (secondary, reported only).
- **Procedure:** each is refit on all 100,530 development rows with the same procedure (inner folds = the four named folds; anonymous notes by top guess). The lockbox is scored **once**, with R-3 against all development titles.
- **Reported sensitivities** (none of these can change a selection):
  - without the 1,234 frozen IDs;
  - the calibrated ridge without note length (exploratory);
  - per-critic MAE reduction and bias, ridge vs calibrated;
  - shortlist writer mix;
  - Italy vs non-Italy, and with vs without O'Keefe (the §1.2 R11 contingency).
- **Also in Phase 5:** DM4 lockbox lifts; BSC3 blind naming by two reviewer agents; H1–H6 on the lockbox.
- **Risks to read the lockbox result against:**
  - most lockbox Italy rows rest on anonymous training notes;
  - one critic (O'Keefe) writes about half the lockbox pool;
  - a single writer's reduction can sit below 10% even when the fold passes: DeSimone (−1.0%); Gregutt (15.5%) and Kostrzewa (16.8%) are the next lowest;
  - **if ridge over-predicts a lockbox writer, the pooled calibration makes that writer worse** (as for Buzzeo and Kostrzewa). With O'Keefe at half the lockbox pool, that writer's direction decides much of the result. Phase 5 reports ridge vs calibrated per lockbox critic;
- **Phase 6:**
  - writer-level calibration in the pilot (the pooled level correction is part of the model; a new note source's writers may need their own);
  - the "5 similar wines" retrieval;
  - the saved pipeline.

## 5. Evaluation
> **Revision 3** (2026-11-08), after critic rounds 1 (6/10, 7 MAJOR) and 2 (8/10, 2 MAJOR; `critiques/phase5_evaluation_round*.md`). Revision 3 adds the masked shortlist refit to the pilot simulation, defines and simulates the band's stop rule, and adds per-critic LBs for H6 (re-execution 2). **Revision 2**, after critic round 1: Everything below comes from notebook §5 (saved with outputs) and `reports/tables/phase5_*.csv`. The order of events, including every decision made after unsealing, is in `reports/phase5_run_log.md`. **Revision 2 changes no model, rule, threshold or selection.** It reports every result the lockbox run computed, adds labelled post-hoc diagnostics (notebook 5.1d–5.1h), withdraws two post-unsealing choices of revision 1 (the 55-rule DM4 filter and the "one house's pool" condition), and rebuilds the decision on the full evidence.

**How the lockbox was scored:**
- The Phase 5 code was frozen in commit `a140a70` (tag `wine-phase5-pre-unseal`), with the lockbox still sealed: `phase5.lockbox_split` raises an error while `config.LOCKBOX_UNSEALED` is False.
- **Dress rehearsal first.** The same `phase5.evaluate` code ran on development fold 3 and reproduced Phase 4's fold-3 numbers exactly; a notebook assertion checks the match. Cell 5.1a also checks that the regenerated `phase4_fold_predictions` content has the SHA-1 of the tagged Phase 4 file.
- **Unsealed** on 2026-11-08 at 00:08 PST, on the project owner's go-ahead. **One scoring run** (00:08–01:26).
- **Two logged re-executions** of the identical frozen code, to save row-level lockbox predictions and the outputs of the new post-hoc cells: re-execution 1 (01:43–03:01, revision 2) and re-execution 2 (03:20–04:38, revision 3). Each time, cell 5.1c asserted that the first run's tables were rewritten byte for byte (6 tables in re-execution 1, all 12 it saves in re-execution 2), and all 13 first-run tables matched their recorded SHA-1s (run log).
- **Training:** every selected model is refit on all **100,530** development rows, with the Phase 4 procedure.
- **Test:** the lockbox, 17,796 of 17,848 rows after R-3 (52 rows whose title appears in development were dropped). Its ≤ $25 pool has 7,288 wines.

### 5.1 Assessment against business success criteria · approved models
**Pass / fail** (pre-registered targets; LB = one-sided 90% winery-clustered lower bound). The development column gives, per metric, the fold with the smallest margin to the target:

| Criterion | Target | Lockbox result | Weakest development fold (Phase 4) | Pass |
|---|---|---|---|---|
| DM1 MAE reduction vs variety × country | ≥ 10%, LB > 5% | **31.5%** (LB 30.2%); MAE 1.40 vs 2.05 | 23.0% (LB 21.9%), fold 3 | ✅ |
| DM1b masked MAE increase | ≤ 0.15 | **+0.068** (frozen list); round-1 list +0.063; strict price mask +0.070 | +0.07, fold 0 | ✅ (but see point 5: the ±2 gain does not survive masking) |
| BSC2 within ±2 on ≤ $25 wines | ≥ 0.60, gain ≥ +5 pp, gain LB > 0 | **0.736**, +7.5 pp (LB +6.4) | 0.65, +10.8 pp (LB +9.6), fold 4 | ✅ |
| BSC1 shortlist | P@100 ≥ 0.55, ≥ 1.4× best simple rule, top-10% lift LB ≥ 1.2 | **0.761**, 1.95× winery track record (0.39), LB 1.76 | P@100 0.63 (fold 1); 1.55×, LB 1.47 (fold 0) | ✅ |
| BSC3 navigation | 6–15 profiles each ≥ 1%; each of two blind reviewers names ≥ 80% with confidence ≥ 3 | **8 profiles**, smallest 6.4% of lockbox notes; reviewers **8 of 8** and **8 of 8** | 10 of 10 winery splits stable | ✅ **thin margin** (point 8; writer independence not shown, §4.4) |
| DM4 rules | ≥ 10 development rules keep lift ≥ 1.5 | **55 of 88** (44 with ≥ 30 lockbox notes) | 71 of 82 (folds 3/4) | ✅ |
| BSC5 buyer insights | ≥ 4 of H1–H6 in both datasets, including H5 or H6 | **6 of 6**; H6 is the only actionable one that is positive within every critic (LB > 0 in two of four; point 10) | 6 of 6 | ✅ |
| DM5(a) near-duplicate recall | ≥ 0.90 | n/a: a full-corpus synthetic check, not a lockbox result (Phase 4: 1.000) | – | n/a |
| BSC4 usability | One screen, < 3 s per query | **Not yet tested.** The P(90+) and band outputs are computed below; the recorded demo is Phase 6 | – | Phase 6 |

**Every pre-registered criterion that can be tested before deployment passes.** BSC4 needs the Phase 6 demo, and the pilot gate (§1.1) needs retailer notes. As §1.1 says, these criteria are **necessary, not sufficient**, and the points below show where the passes are fragile: the score band's gain depends on the writer's level and does not survive masking (points 2–5), while the shortlist holds up under every check (point 6).

**What the lockbox shows beyond pass / fail** (points 1–4 and 6–7 use the pre-registered outputs of cell 5.1c; every row marked *post hoc* comes from cells 5.1d–5.1h, added after unsealing, and selects nothing):

1. **The lockbox was easier than fold 3 on average, but not for its largest writer.** Risk R9 picked fold 3 as the closest proxy, on coverage. On the lockbox the baseline is stronger than on fold 3 (variety × country MAE 2.05 vs 2.26), and the model's margin over it is still larger (31.5% vs 23.0%). But O'Keefe, who writes 54% of the lockbox, gets a 22.7% reduction, no better than fold 3's 23.0%. Fold 3's difficulty came from one writer, Gregutt, whom ridge under-predicted by over 2.5 points; the lockbox's comes from one writer over-predicted (point 2). Coverage predicted neither.

2. **Every score candidate on the lockbox** (reported, not selecting; `phase5_score_models.csv`):

| Model | Inner MAE (Phase 4) | MAE | Bias | MAE reduction (LB) | Within ±2 on ≤ $25 (gain, LB) |
|---|---|---|---|---|---|
| Variety × country | – | 2.051 | −0.63 | – | 0.661 |
| Ridge | 1.917 | 1.327 | +0.14 | 35.3% (34.2%) | 0.780 (+11.9 pp, +10.7) |
| **Calibrated ridge, all OOF (selected)** | **1.762** | **1.404** | **+0.69** | **31.5% (30.2%)** | **0.736 (+7.5 pp, +6.4)** |
| Stack, no origin | 1.774 | 1.296 | +0.26 | 36.8% (35.8%) | 0.790 (+12.9 pp, +11.8) |
| Calibrated ridge, named OOF | 1.785 | 1.467 | +0.87 | 28.4% (27.1%) | 0.701 (**+4.0 pp**, +2.9) |
| Stack (revision 1 choice) | 1.869 | 1.354 | +0.45 | 34.0% (32.6%) | 0.750 (+8.8 pp, +7.6) |
| *Pre-registered sensitivity:* calibrated ridge without note length | – | 1.377 | +0.48 | 32.9% | not computed |

   - **The selected model ranks 4th of 5 candidates on the lockbox.** The runner-up on inner MAE (stack, no origin, 0.012 behind) is the best of all; the third (calibrated ridge with named-only OOF, 0.023 behind) **would have failed BSC2** (+4.0 pp < +5 pp). So the BSC2 pass rested partly on a narrow inner-fold tie-break between two calibration variants.
   - **What calibration does.** It is an affine map fitted on all development out-of-fold scores: **points = 7.957 + 0.917 × ridge score**. That compresses the scale and lifts it: the shift is about +0.9 points at a ridge score of 85, +0.65 at 88 and +0.3 at 92. On the lockbox's critics the shift was +0.47 (Krebiehl), +0.53 (O'Keefe), +0.62 (Sullivan) and +0.83 (Jenssen). Plain ridge already sits close to the lockbox's level on average (bias +0.14), so the lift over-predicts. §4.4 named this risk, and it happened.
   - **Note length.** Dropping it lowers the bias from +0.69 to +0.48 and raises the reduction from 31.5% to 32.9%. Note length carries some of the writer level, as the Phase 4 diagnostic suggested; the effect is reported, not acted on.
   - Per lockbox critic (MAE reduction, then bias, for ridge → calibrated):
     - **O'Keefe** (9,644 rows, 54%): 34.3% → **22.7%**, bias +0.66 → **+1.19**. Ridge already over-predicts this writer, so the lift makes it worse, the same pattern as Buzzeo and Kostrzewa in development;
     - **Krebiehl** (3,268): 49.5% → **55.0%**, bias −0.45 → +0.02. She's under-predicted, and calibration helps;
     - **Sullivan** (4,448): 32.0% → 33.4%, bias −0.31 → +0.31;
     - **Jenssen** (436, 2.4%): −68.6% → **−26.0%**, bias −2.44 → −1.61. The model is **worse than the baseline** for this writer either way (point 4).
   - **The selection stands.** Switching to plain ridge or the no-origin stack now would choose a model on the test set, and plain ridge failed fold 3 in development (1.4%). What the lockbox shows is that a new writer's level offset can go either way, and nothing available before scoring predicts its sign.

3. **Italy is the weak segment for the score band.** In the lockbox, "Italy" and "O'Keefe" are exactly the same 9,644 rows (O'Keefe reviews only Italy, and nobody else in the lockbox does), so the two can't be separated:

| Subset | Rows | MAE | Bias | MAE reduction (LB) | Within ±2 (gain) | Ranker top-10% precision vs rule (lift, LB) |
|---|---|---|---|---|---|---|
| All | 17,796 | 1.404 | +0.69 | 31.5% (30.2%) | 0.736 (+7.5 pp) | 0.763 vs 0.392 (1.95×, 1.76) |
| Italy = O'Keefe | 9,644 | 1.531 | +1.19 | 22.7% (20.9%) | 0.670 (**+1.4 pp**) | 0.602 vs 0.196 (3.07×, 2.64) |
| Not Italy = without O'Keefe | 8,152 | 1.255 | +0.09 | 41.2% (39.4%) | 0.803 (+13.7 pp) | 0.925 vs 0.482 (1.92×, 1.68) |

   - **Score band:** for Italian wines it barely beats variety × country (+1.4 pp). The BSC2 target applies to the whole lockbox, but **a buyer working mainly on Italy wouldn't see the +5 pp gain**.
   - **Ranker:** strongest in Italy (3.07× the best rule). An over-prediction shared by every wine in a one-writer group doesn't change their order.
   - **Analogue notes:** the sensitivity run without the 1,234 anonymous development notes whose top guess is a lockbox critic gives 30.3% (LB 29.0%), 0.722 within ±2 (+6.1 pp, LB +5.0), and P@100 0.758 (1.93×, LB 1.74). **Every target that was run still passes (DM1b was not run here), so the result doesn't rest on notes probably written by lockbox critics.** It can't rule out other, sub-threshold anonymous Italian notes by O'Keefe; Italian training data is 96% anonymous (§4.1).

4. **Jenssen: the model fails for one writer.** For Jenssen's 436 reviews, the model's estimates sit 1.6–2.4 points below the actual scores, and the MAE is worse than variety × country. In development Jenssen's co-author DeSimone (shared handle @worldwineguys, §2.4) was the only writer below zero (−1.0%). So the two writers the model handles worst are a writing pair. **That is an observation, not an explained mechanism.** It is the strongest evidence here that a single new writer can fall outside what the model learned.

5. ***Post hoc (5.1e):* MAE survives masking; the ±2 gain does not.** Masking is the project's only proxy for retailer notes (A1, R1). DM1b passes because it measures MAE. The business gate measures the ±2 gain, and that falls sharply on the lockbox, unlike in development:

| Selected model, within ±2 gain over variety × country (pp) | Fold 0 | Fold 1 | Fold 3 | Fold 4 | Lockbox (LB) |
|---|---|---|---|---|---|
| Unmasked | +12.3 | +27.9 | +12.7 | +10.8 | **+7.5** (+6.4) |
| Frozen verdict list masked (DM1b) | +12.5 | +27.3 | +12.9 | +8.2 | **+2.7** (+1.6) |
| Round-1 list masked | +12.8 | +28.0 | +12.1 | +9.6 | +4.5 (+3.3) |
| Frozen list + strict price mask | +12.6 | +27.2 | +12.9 | +8.3 | +2.7 (+1.6) |
| Top 200 ridge words masked (stress test) | +9.6 | +23.1 | +11.7 | +8.8 | +2.5 (+1.3) |

   - **Under masking the selected model would fail BSC2's +5 pp target, and the pilot gate's.** The MAE increase stays small for the frozen list (+0.068). The 200-word stress test (reported only, not a target) costs +0.159, above the 0.15 DM1b bar.
   - **By writer** (frozen list masked): O'Keefe +1.4 → **−5.8 pp**, Sullivan +13.9 → +12.1, Krebiehl +20.1 → +16.8, Jenssen −16.4 → −17.3. The collapse is O'Keefe's.
   - **Why, in part:** masking raises the over-prediction (bias +0.69 → +0.77), and ±2 accuracy is a threshold metric that falls steeply once the level is off (point 7, gain vs offset). In development the biases were near zero or negative, and masking moved them little. This is consistent in direction; it isn't a full quantified explanation.
   - **Plain ridge keeps more of its gain under masking** (+9.1 pp) because it starts with almost no bias. That is reported, not acted on (option C).

6. **The shortlist (DM2) holds up in a mixed-writer pool.** A real buying round mixes notes from many importers, producers and staff (§1.1, A1, A7), as the lockbox does, so the **mixed-pool figure, P@100 0.76, is the relevant estimate**. Revision 1's condition "rank within one house's pool" is withdrawn: it contradicts the business setup, and it would shrink pools well below 1,000.
   - **Candidate pools and k:** P@100 is 0.64 with 500 candidates and 0.85 with 2,000; P@50 0.85 and P@200 0.64 with 1,000. Every simple rule stays at 0.19–0.81. The 0.81 is province track record at k = 50 with 2,000 candidates; the ranker scores 0.92 there.
   - **Stack variants:** within 0.004 of the selected ranker (0.757 and 0.764), so the "simplest within 0.01" choice is unchanged.
   - **How much is price:** the same ridge without price (text score only) gets P@100 0.721, against 0.761 with log price, so most of the shortlist's strength comes from the note.
   - **Per critic:** top-10% lift ranges from 1.29× (Krebiehl, LB 1.19) to 3.07× (O'Keefe, LB 2.64).
   - **The writer level distorts the mix** of the shortlist:

| Critic | Pool share | Top-10% share | Value rate |
|---|---|---|---|
| O'Keefe | 50.4% | 50.5% | 14.2% |
| Sullivan | 24.0% | **7.5%** | 13.9% |
| Krebiehl | 21.0% | **42.0%** | 49.1% |
| Jenssen | 4.6% | **0.0%** | 17.6% |

   Krebiehl's high value rate fills the shortlist; Jenssen's wines never reach it. If each critic's level were known, P@100 would be **0.84** instead of 0.76. That's an oracle, not available in use; it measures what the mixed pool costs.

7. **BSC4 outputs on the lockbox, and how the ±2 gain depends on level:**
   - **P(90+):** Brier score 0.126 against 0.169 for the base rate. The mean predicted P(90+) is 0.32 against an actual value rate of 0.22, so **it over-predicts by 10 pp**. In development the per-fold error ran from −8 to +6 pp, so the error inherits the writer level here too.
   - **80% band** (± 2.67 points): covers **87%** of lockbox wines, so it's conservative here.
   - ***Post hoc (5.1h):* gain vs offset.** Adding a constant offset to every ≤ $25 prediction and recomputing the ±2 gain shows how much of the gain is level (`phase5_gain_vs_offset.csv`; mean residual = prediction − actual):

| Pool | Mean residual as frozen | Gain as frozen | Gain at the best offset (oracle) | Gain falls below +5 pp between |
|---|---|---|---|---|
| Lockbox, mixed writers | +0.84 | +7.5 pp | +14.1 pp (residual +0.09) | residual +0.84 (+7.5) and +1.09 (+2.8) |
| Lockbox, O'Keefe only | +1.37 | +1.4 pp | +20.6 pp (residual −0.13) | residual +1.12 (+7.2) and +1.37 (+1.4) |
| Development fold 3 | −0.52 | +12.7 pp | +15.6 pp (residual −0.02 to +0.23) | residual −1.02 (+7.1) and −1.27 (+3.1); on the other side +1.23 (+7.6) and +1.48 (+3.5) |

     The gain falls below +5 pp once the mean residual leaves a band whose edges, in the mixed lockbox pool, interpolate to **+0.97** and **−1.05**. So the pilot's stop threshold is set at **±1.0 point**, rounded from those edges (§5.3 defines the rule). A correct level would roughly double the lockbox gain (+7.5 → +14.1 pp).

8. **DM3 / BSC3:**
   - **Profile shares on lockbox notes:** 6.4–23.4%. Only 0.8% of lockbox notes have no lexicon term, against 6.0% in development.
   - **Naming passes by a thin margin.** Both blind reviewers named all 8 primary profiles, but reviewer 1 gave the minimum passing confidence (3) to 6 of 8 (A1, A4–A8) and reviewer 2 to 2 of 8 (A5, A6). One profile at confidence 2 from reviewer 1 would have dropped the pass to 7 of 8, still ≥ 80%; two would fail it.
   - **Agreement between the reviewers:** they agree on colour and broad style for 7 of 8 profiles. They disagree on **A6**: reviewer 1 reads oak with creamy and tropical terms as a mixed red-and-white oak style, reviewer 2 as an "oak-driven ripe red". The secondary set (reported only) got 6 of 8 from each.
   - **Writer independence:** still not shown (§4.4). The reviewers saw development term lists, not a writer-disjoint fit.

9. **DM4: the frozen rules on the lockbox.**
   - **Overall:** 55 of 88 rules keep lift ≥ 1.5; 44 of those have ≥ 30 lockbox notes, and 17 of the 88 rules have fewer than 18 (support < 0.1%). The median lift falls from 3.11 to 2.03. No lockbox lift has an uncertainty bound.
   - ***Post hoc (5.1f):* by consequent grape** (rules · kept · development share → lockbox share of rows):

| Consequent | Rules | Kept (lift ≥ 1.5) | Median lift, development → lockbox | Grape share, development → lockbox |
|---|---|---|---|---|
| Chardonnay | 24 | 18 | 3.49 → 2.89 | 10.3% → 2.8% |
| Pinot Noir | 15 | 8 | 2.98 → 1.54 | 12.1% → 1.9% |
| Cabernet Sauvignon | 14 | 4 | 3.09 → 1.14 | 8.0% → 4.3% |
| Riesling | 9 | 8 | 4.53 → 2.66 | 3.8% → 5.5% |
| Sauvignon Blanc | 5 | 5 | 3.46 → 2.61 | 4.5% → 2.1% |
| Syrah | 3 | 0 | 2.61 → 1.38 | 4.0% → 3.5% |
| 11 other consequents | 18 | 12 | – | – |

   - **Why some grapes' rules fail is not established.** Revision 1 said the rules fail "in grapes that are rare in an Italy-heavy lockbox"; that claim is withdrawn. Chardonnay shrinks most and keeps 18 of 24; Syrah barely changes and keeps 0 of 3. Across the 17 consequents, the change in grape share and the share of rules kept are barely related (Spearman 0.17).
   - **What is approved** (below) is the frozen rule set, not the 55 that held up here.

10. **H1–H6 on the lockbox:** all six replicate.

| Hypothesis | Rows | Estimate | 90% LB | Development estimate |
|---|---|---|---|---|
| H1 longer notes, higher scores (ρ) | 17,796 | 0.560 | 0.547 | 0.485 |
| H2 pricier → higher, within variety × country (partial r) | 16,699 | 0.508 | 0.493 | 0.590 |
| H3 named designation (points) | 17,796 | +0.62 | +0.54 | +0.71 |
| H4 SD of critic effects | 17,796 | 0.84 | 0.76 (bar 0.5); **4 critics only**, see below | 1.24 |
| H5 ≤ $25 whites more often value than reds | 6,334 | +9.6 pp | +7.8 pp | +0.9 pp |
| H6 ≤ $25 strong winery record → more value | 7,288 | +20.5 pp | +15.2 pp | +27.6 pp |

   - **H4:** the SD is taken over only four critic effects, and the LB resamples wineries, not critics, so it can't capture which four writers happened to be sealed away. This was a pre-registered limitation (§1.1); the row passes as written but is weak evidence.
   - ***Post hoc (5.1d):* H5 is a composition effect again.** On the R-3-filtered lockbox (6,334 rows; revision 1's version skipped R-3 and used 6,337), Krebiehl writes 32.5% of the ≤ $25 whites but only 7.5% of the reds, and Krebiehl's value rate is 51% for both colours. Within each critic, the review-weighted white − red difference is **+0.4 pp**: Krebiehl 0.0, O'Keefe +4.1, Jenssen +6.2, Sullivan −7.6. **H5 passes as written, but it isn't a buyer insight** ("whites are better value") in either dataset.
   - ***Post hoc (5.1g):* H6 is positive within every critic, but clearly so in only two.** On the lockbox, 420 of 7,288 pool wines (5.8%) have a strong winery record, against 0.73% in development. Their value rate is 41% against 20% for the rest. Within critics (difference in value rate, one-sided 90% winery-bootstrap LB, `phase5_h6_within_critic.csv`):

| Critic | Strong-record wines | Value rate, strong vs others | Difference | 90% LB |
|---|---|---|---|---|
| Anne Krebiehl MW | 102 | 72.5% vs 47.5% | +25.1 pp | +15.5 pp |
| Sean P. Sullivan | 213 | 35.2% vs 10.9% | +24.3 pp | +17.8 pp |
| Kerin O'Keefe | 101 | 19.8% vs 14.0% | +5.8 pp | −2.0 pp |
| Jeff Jenssen | 4 | 3 of 4 vs 16.9% | +58.1 pp | not meaningful (n = 4) |

   **H6 is positive within every critic**: clearly so for Krebiehl and Sullivan, marginal for O'Keefe (the LB crosses zero), and untestable for Jenssen. It is still the only actionable hypothesis that is positive within every critic, and it is the one that satisfies BSC5's "H5 or H6" clause in substance. It failed on fold 3 alone in the rehearsal (LB −0.02).

11. **DM6 with the lockbox critics.**
   - **Specification A** (19 critics, 73,236 rows): critic SD 1.41 (noise-corrected 1.38), close to 1.49 / 1.46 in development. Krebiehl +1.16 (SE 0.16, 5 partner critics), Sullivan +0.66 (0.13, 14), Jenssen +0.61 (0.33, 7), O'Keefe −0.81 (0.23, 4).
   - ***Post hoc (5.1g):* specification B** (61,315 rows, 721 cells): SD 0.98 (noise-corrected 0.92). Krebiehl +1.68 (SE 0.18, 10 partners), Jenssen +1.19 (0.26, 10), Sullivan −0.18 (0.19, 9), O'Keefe −1.10 (0.22, 10).
   - **Identification:** in A, O'Keefe is linked through the fewest partner critics (4) but Jenssen has the largest standard error (0.33). **Sullivan and Jenssen swap order between the specifications**, so only the signs of Krebiehl (above peers) and O'Keefe (below peers) are robust. The SD across critics is 0.9–1.4 points depending on the specification.
   - **Caveat:** these are cell-level effects on scores, not ridge residuals, so they don't predict the ridge bias in point 2. O'Keefe scores below peers on the same wines, yet O'Keefe's notes read higher than the scores given.

**Approved models** (for the Phase 6 pilot, not for unattended use):

| Goal | Model (frozen in `a140a70`) | Status |
|---|---|---|
| DM1 / BO2 score band | Calibrated ridge (all OOF), 80% band ± 2.67 | **Approved for the pilot only, internal display.** Its ±2 gain depends on the note source's writer level and falls below +5 pp under masking (points 2, 5, 7). Shown only while the pilot's stop rule allows (§5.3) |
| DM2 / BO1 shortlist | Ridge + log price; P(90+) by logistic map | **Approved.** The mixed-pool lockbox estimate (P@100 0.76, 1.95×, LB 1.76) is the basis; it held without the analogue notes. Within single critics the top-10% lift is 1.29–3.07×, and a simulated pilot of Jenssen's wines alone would fail (§5.3). The writer level skews which writers reach the shortlist (point 6). P(90+) over-predicts by 10 pp on the lockbox |
| DM3 / BO3 profiles | Lexicon NMF, k = 8 | **Approved for navigation**, passing by a thin naming margin; they don't describe how a new writer groups wines |
| DM4 / BO3 rules | FP-Growth descriptor → grape or style rules | **Approved as frozen** (the 88 development rules), shown with their development lift and labelled as associations. The lockbox lift of each rule is recorded in `phase5_dm4_rules.csv` as information; it is not used to choose which rules ship. Revision 1's 55-rule filter is withdrawn |
| DM5 / BO4 | MinHash LSH, τ = 0.5 | **Approved** (catalogue de-duplication; "5 similar wines" built in Phase 6) |
| DM6 / BO5 | Critic fixed effects, specifications A and B | **Approved as analysis**, reported as a range (0.9–1.4 points of SD with the lockbox critics), not as a single ranking |

### 5.2 Review of process
**Lockbox exposure before unsealing** (complete list, attested by the session record and commit order, not cryptographically):
- **Scores:**
  - **Phase 1:** one exploratory check before the lockbox existed used all critics (§1.1 disclosure).
  - **After that:** no lockbox score was read until 00:08 PST on 2026-11-08. Commit `a140a70`, made before then, still has `LOCKBOX_UNSEALED = False`.
- **Categorical counts** (allowed by the design): pool sizes and critic shares (§1.1), coverage of variety × country (§1.1), the anonymous share by region (§4.2).
- **Text only** (no scores):
  - the R8 attribution classifier was trained on named notes, including the lockbox critics' notes;
  - 859 anonymous notes were dropped and the 1,234-ID sensitivity list was built from it;
  - text-level deduplication removed 36 lockbox rows.
- **Fitted steps:** every fitted transform (TF-IDF, one-hot, imputer, scaler, ridge, calibration, P(90+) map, band, NMF, rule mining) is fit on development rows inside `phase5.evaluate`. The Phase 3 steps are row-wise rules or hand-written lists (lexicon, colour map, grape map), frozen before Phase 4.

**Decisions made after unsealing** (each is in the run log with the evidence that drove it):

| Decision | Evidence | Kind |
|---|---|---|
| 5.1d: H5 within critic (re-run on the R-3-filtered lockbox in revision 2) | Lockbox `points`, `colour`, `critic` | Descriptive diagnostic |
| 5.1e–5.1h: every candidate, masked ±2 gains, DM4 by grape, H6 within critic, DM6 spec B, pilot simulation, gain vs offset | Lockbox predictions | Descriptive diagnostics |
| Re-executions 1 and 2 of the full notebook | Identical frozen code; tables byte-identical | Reproduction |
| 5.1h, revision 3: shortlist ranker refit on masked notes; stop-rule firing rates; H6 per-critic LBs | New lockbox scoring of a masked refit of the frozen ranker (not a frozen model); lockbox predictions | Descriptive diagnostics |
| DM4 55-rule display filter (revision 1) | Lockbox rule lifts | **Withdrawn** in revision 2: selection on the test set |
| "Shortlists ranked within one house's pool" (revision 1) | Shortlist writer mix | **Withdrawn** in revision 2: contradicts A1/A7 |
| P(90+) displayed as a relative indicator, not a probability | Lockbox over-prediction of 10 pp | Display choice, lockbox-driven |
| Score band labelled "may be less accurate for Italian wines and for writers unlike those in training" | Points 3–4 | Display choice, lockbox-driven |
| Pilot stop rule for the band: ±1.0 point (revision 1: ±1.5 with no basis), per note source, ≥ 50 wines, 80% CI wholly outside (revision 3) | Gain vs offset (point 7); unit, n and CI set before the firing rates were computed | Deployment rule, lockbox-driven |
| Pilot outputs judged separately: the shortlist on the BO1 part of the gate, the score band on the BO2 part (§5.3) | Pilot simulation (§5.3) | Deployment rule, lockbox-driven |

None of these changes a model, a model-selection rule or a Phase 5 threshold. **The last one amends the pre-registered pilot decision rule (§1.1, dated amendment note there)**: the two bars are unchanged, but they are now applied per output instead of jointly. The last three were fixed before any pilot data exists, but they were informed by the lockbox, so the pilot is the first clean test of them.

**Forking paths, counted** (from `reports/phase4_run_log.md`):
- **DM1:** chosen twice. Revision 1's rule chose the stack after one full outer run and two earlier fold-3 looks. Revision 2 rewrote the rule after those outer results had been seen and chose among five candidates on inner folds. Two further outer-fold diagnostics (note length on fold 3, then on folds 0, 1 and 4) changed nothing.
- **DM2:** one selection rule, unchanged; two full outer runs (revisions 1 and 2) with the same outcome.
- **DM3:** re-chosen once in revision 2, after a scan of 120 settings (3 vocabularies × 2 fit sets × 2 methods × 10 values of k) for stability; no value metric was used.
- **What the lockbox says about it:** **the post-hoc revision did worse on the clean holdout.** Revision 1's stack scores 34.0% and 0.750 within ±2 (+8.8 pp); revision 2's calibrated ridge scores 31.5% and 0.736 (+7.5 pp). Both pass. Under masking the gap widens: the stack keeps +6.7 pp (LB +5.5) and would still pass BSC2, while the frozen choice falls to +2.7 pp. The lockbox stays an unbiased estimate for the frozen choice, which is what it was for.

**Phase-by-phase audit:**

| Phase | What held up | Deviations and weaknesses | Effect on the Phase 5 claims |
|---|---|---|---|
| 1 Business understanding | Critic-grouped lockbox; targets, LBs and hypotheses pre-registered; simple-rule set frozen; pilot gate defined | **R9's proxy was wrong in direction** (point 1). **Targets apply to the whole pool only**: with a single critic covering most of one region, an Italy-only gain of +1.4 pp passes as part of the whole. **H5 was written as a pooled contrast**, which composition can satisfy; it should have been within-critic. **H4 uses four critic effects**, too few for its LB. **DM1b measures MAE**, not the ±2 gain the business gate uses | The lockbox passes are valid as pre-registered; the Italy, H4, H5 and masking caveats are reported above |
| 2 Data understanding | Score analysis on development data only; duplicates and repeat titles found early (R3) | DM5 re-specified after a look at real pairs (logged); (c) is exploratory | None on the lockbox (text only) |
| 3 Data preparation | Row-wise rules; leak stripping; R-3 and R8 filters; leakage probe on development data | Hand-written stop-word list is judgement, not a rule (§4 log) | Text rules removed 36 lockbox rows; reported |
| 4 Modeling | Inner-fold selection; the rule written before each run; run log with times; three critic rounds | **Forking paths** (counted above). **The calibration's sign risk was named but had no pre-registered rule.** The BSC2 pass depended on a 0.023 inner-MAE tie-break between calibration variants | The frozen choice ranks 4th of 5 on the lockbox, reported, not acted on |
| 5 Evaluation | Sealed loader; dress rehearsal with an equality assertion; content-hash check of the Phase 4 predictions; commit and tag before unsealing; one scoring run and two byte-identical re-executions | **Revision 1 reported selectively** (critic round 1): it left out the without-length sensitivity, two candidates and the masked ±2 gain, and filtered the DM4 rules on the lockbox. Revision 2 reports all of them and withdraws the filter. Revision 2 judged the band on masked notes but the shortlist only unmasked, and its stop rule had no unit or minimum n (critic round 2); revision 3 masks both and defines the rule. Every post-unsealing decision is listed above | The decision in §5.3 is rebuilt on the full evidence |

**Limitations that remain** (they apply to every pass above):
- **Note source (A1, R1).** The test uses critic notes; the real input is importer, producer or staff notes. Masking is only a proxy. It hurts the score band's ±2 gain most (point 5); it leaves the shortlist's simulated pilot pass rate at 0.995 on the lockbox but costs it 0.01–0.14 in development (§5.3). The pilot gate exists for this reason.
- **One holdout of four writers.** The LBs resample wineries, not writers. With four writers, the lockbox can't bound what one new writer will see: Jenssen's −26% and O'Keefe's +1.4 pp show the range.
- **AI reviewers.** The critic rounds and the BSC3 naming were done by Claude agents, not wine buyers. They catch analysis errors and test readability, but they don't validate business value.
- **Data age.** One 2017 snapshot; prices are stale (R5); only 80+ wines are published (R4).
- **Pilot and BSC4 are untested.**

### 5.3 Possible actions & decision
***Post hoc (5.1h):* how likely is the pre-registered pilot gate to pass?** Notebook 5.1h estimates it by simulation: draw 400 ≤ $25 wines from a pool (200 pilots), apply the gate exactly as pre-registered (±2 gain ≥ +5 pp with a winery-bootstrap LB > 0; top-20% precision ≥ 1.3× the best frozen simple rule on that pilot, LB > 1.0), and count passes (`phase5_pilot_simulation.csv`). The **masked** rows stand in for retailer notes: both the score model and the shortlist ranker are refit on masked training notes and scored on masked test notes (frozen verdict list), since both read the note.

| Pool the pilot is drawn from | BO2 part passes | Mean ±2 gain | BO1 part passes | Median top-20% lift | Both pass |
|---|---|---|---|---|---|
| Development folds 0 / 1 / 3 / 4 | 0.990–1.000 | +10.9 to +27.9 pp | 0.775–0.950 | 1.42–1.61× | 0.775–0.945 |
| Development folds 0 / 1 / 3 / 4, masked | 0.860–1.000 | +8.1 to +27.4 pp | 0.670–0.940 | 1.39–1.59× | 0.655–0.935 |
| Lockbox, mixed writers | 0.805 | +7.4 pp | **0.995** | 1.73× | 0.805 |
| **Lockbox masked, mixed writers** (retailer-note proxy) | **0.240** | +2.5 pp | **0.995** | 1.70× | 0.240 |
| Lockbox, O'Keefe only | 0.125 | +1.5 pp | 1.000 | 1.95× | 0.125 |
| Lockbox masked, O'Keefe only | 0.000 | −5.5 pp | 0.995 | 1.90× | 0.000 |
| Lockbox, Sullivan only | 1.000 | +13.9 pp | 0.875 | 1.52× | 0.875 |
| Lockbox masked, Sullivan only | 0.995 | +12.2 pp | 0.900 | 1.54× | 0.895 |
| Lockbox, Krebiehl only | 1.000 | +19.8 pp | 0.550 | 1.31× | 0.550 |
| Lockbox masked, Krebiehl only | 1.000 | +16.6 pp | 0.535 | 1.31× | 0.535 |
| Lockbox, Jenssen only (all 336 wines: **one evaluation**, not a rate) | fails | −16.4 pp | fails | 1.23× | fails |
| Lockbox masked, Jenssen only (same 336 wines) | fails | −17.3 pp | fails | 1.14× | fails |

- **Like for like, masking barely touches the shortlist and sinks the band.** On masked lockbox notes the shortlist's part still passes 0.995 (lift 1.70× vs 1.73×). In development masking costs it more (0.67–0.94 against 0.775–0.95 unmasked). The band's part falls from 0.805 to 0.240.
- **The band's part is likely to fail if about half the notes behave like O'Keefe's under masking.** O'Keefe writes 50% of the lockbox pool, and the masked mixed rate (0.240) is mostly that writer's effect: masked pools of Sullivan or Krebiehl alone pass 0.995–1.000. Jenssen's pool fails both parts.
- **The shortlist is weak inside some single-writer pools:** Krebiehl 0.535–0.550, and Jenssen fails. A pilot from "several writers" (condition 2) matters for it too.
- **Reconciling with Phase 1's power figure** ("about 80% at fold-3-like effects"): that figure was sized for a model that just meets the development targets (Phase 1 critic round 3, issue N1). The frozen models exceed them on fold 3 (+12.7 pp against the +5 pp bar), so fold 3's simulated both-pass rate is higher (0.945). What the lockbox changes is the size of the effect, not the sample size needed.
- **Limits:**
  - the pass rates are conditional on the lockbox's four-writer mix: the simulation resamples wines and wineries, not writers;
  - the pools are critic notes, masked or not, not retailer notes;
  - 200 pilots per row, so a rate has a simulation SE of up to about 0.035. The masked mixed BO2 rate was 0.195 in revision 2's run, which skipped the BO1 part and so drew different random pilots; this run gives 0.240.
- **Cost** (A5, illustrative): 400 pilot wines × ~$25 per sample ≈ **$10,000**, plus analyst time, whichever option below runs the pilot. *(Superseded in §6.1, "Outcome data and schedule": the pilot uses published reviews of logged candidates, about $1,200–2,400 of analyst time plus a data licence; the $10,000 panel is the fallback.)*

***Post hoc (5.1h):* the stop rule for the band, defined and simulated.**
- **Unit: the note source**, meaning the named writer where known, otherwise the importer or producer that supplied the note.
- **Rule:** once a source has ≥ 50 scored pilot wines, and at every interim check after that, compute its mean residual (prediction − actual) and an 80% winery-bootstrap CI. **If the CI lies wholly outside ±1.0, stop showing the band for that source's wines.** The same check runs on each country with ≥ 50 scored wines (Italy is the known weak segment, point 3) and on the whole pilot. On the lockbox, Italy's wines are all O'Keefe's, so Italy's firing rate is O'Keefe's row below.
- **Settings** (`config.PILOT_STOP_*`): the ±1.0 is rounded from the gain-vs-offset edges (+0.97 / −1.05, point 7). The 50-wine minimum and the 80% CI were fixed in `config.py` before the firing rates below were computed; that order is attested by the session record and run log, not by a commit. All three were informed by the lockbox.
- **Simulation:** draw 50 or 100 wines from one source (200 checks), apply the rule, count how often it fires (`phase5_stop_rule.csv`). Sources are every development-fold writer with ≥ 200 pool wines, plus the lockbox writers, masked and unmasked.

| Sources | Mean residual | Source's ±2 gain | Rule fires at 50 / 100 wines |
|---|---|---|---|
| Within ±1: 7 development writers; Sullivan and Krebiehl, masked or not | −0.36 to +0.81 | +12.1 to +38.4 pp | ≤ 0.010 / ≤ 0.020 |
| Just outside: Boone, Kostrzewa | +1.08, +1.10 | +10.2, +5.9 pp | 0.155–0.190 / 0.190–0.225 |
| Well outside, band still passes: Gregutt, Buzzeo | −1.43, +1.51 | +7.8, +9.9 pp | 0.745–0.895 / 0.915–0.990 |
| Well outside, **band fails**: O'Keefe, O'Keefe masked, Jenssen, Jenssen masked, DeSimone | +1.37, +1.60, −1.39, −1.40, −1.45 | +1.4, −5.8, −16.4, −17.3, −2.7 pp | **0.585–0.945 / 0.825–1.000** |
| Whole pool, 400 wines: lockbox / lockbox masked / development folds | +0.84 / +0.99 / −0.52 to +0.96 | +7.5 / +2.7 / +10.8 to +27.9 pp | 0.000 / 0.080 / 0.000–0.030 |

- **What it does:**
  - it rarely fires for a source within ±1 (at most 2% of checks);
  - it catches the sources where the band fails 59–95% of the time at 50 wines and 83–100% at 100;
  - it errs on the safe side: it also withdraws the band from some sources where it still works (Gregutt, Buzzeo).
- **Why per source:** run only on the whole pilot, it would have missed the masked lockbox case (fires 8% of the time, mean residual +0.99).
- **Gap:** a source with fewer than 50 scored wines is covered only by the whole-pilot check.

| Option | For | Against | Verdict |
|---|---|---|---|
| A. Stop the project | – | Every pre-registered criterion that can be tested passes; the shortlist is strong under every check | Rejected |
| B. Go to the pilot with the pre-registered gate unchanged (both parts must pass to deploy anything) | Exactly as pre-registered | On masked lockbox notes the joint gate passes 0.24 of simulated pilots, almost entirely because of the band's part; the shortlist's part passes 0.995 | Rejected as the deployment rule; the joint gate is still computed and reported |
| C. Switch DM1 to plain ridge or the no-origin stack, which did better on the lockbox | 35.3–36.8% vs 31.5%; ±2 0.78–0.79 vs 0.74; plain ridge keeps +9.1 pp under masking | Selecting on the test set; the lockbox would no longer be an unbiased estimate. Plain ridge failed fold 3 in development (1.4%) | Rejected; reported as a sensitivity only |
| D. Go back to Phase 4 and add writer-level calibration | Points 2, 4 and 7: a correct level roughly doubles the ±2 gain | No fresh holdout left to test a new model on | Moved into the pilot as a **secondary** analysis (condition 4) |
| E. Collect a new holdout (post-2017 reviews, new critics) | A second clean test | Out of scope; needs new data | Recommended for monitoring (Phase 6.2) |
| F. **Pilot both outputs, each judged on its own part of the gate** | **Independent of the lockbox:** BO1 and BO2 are separate objectives (§1.1). A level error shared by one source's wines shifts every one of its band estimates but leaves its shortlist order unchanged (within a source; across sources, level differences still cost the shortlist about 0.08 of P@100 on the lockbox, point 6). Each output must still clear its own pre-registered bar; neither bar changes | **A post-unsealing amendment to the pre-registered gate** (§1.1 dated note; §5.2), informed by the simulation above, so the pilot is its first clean test. Same cost as B | **Chosen** |

**Decision: GO to Phase 6 for a pilot (option F).** No unattended or customer-facing use. The conditions are fixed now, before any pilot data exists:
1. **Models:** exactly as frozen in `a140a70` (the Phase 5 code commit; the model selections themselves were frozen earlier, in the Phase 4 commit `8632fba`). The Phase 6 pipeline must reproduce the lockbox predictions in `phase5_lockbox_predictions.csv.gz`.
2. **Pilot data:** ≥ 400 ≤ $25 retailer notes for wines that later receive a critic score, from several note sources. *Made precise in §6.1: at least 3 sources with ≥ 50 scored wines each; the outcome data, schedule and cap are in §6.1.*
3. **Gate, per output** (the bars are the pre-registered ones from §1.1):
   - **Shortlist (BO1):** top-20% precision ≥ 1.3× the best frozen simple rule, LB > 1.0. Pass → the shortlist may be deployed for internal buying.
   - **Score band (BO2):** ±2 accuracy ≥ +5 pp over variety × country, LB > 0. It is shown only next to a deployed shortlist. Shortlist and band pass → the band may be shown internally. Band fails → it is not shown.
   - **Band passes, shortlist fails:** nothing is deployed; both results are reported and the project returns to Phase 4.
   - Both gates are computed on **all** pilot wines. A stop-rule withdrawal never removes wines from either gate, and every firing is reported next to the gate.
   - The joint pre-registered gate (both parts) is reported either way.
4. **Writer level, secondary and reported only:** the pilot also reports each note source's mean residual, and the gate metrics after a source-specific intercept fitted on the first scored wines from that source. Phase 6 freezes the exact rule before any pilot data. If it helps, it becomes a candidate for a later model version, tested on new data, not on the same pilot.
5. **Display:** the band is labelled "estimated" (R10) and "may be less accurate for Italian wines and for writers unlike those in training". P(90+) is shown as a relative indicator, since it over-predicted by 10 pp on the lockbox.
6. **BSC4:** the Phase 6 demo must show all outputs on one screen in under 3 s per query.
7. **Stop rules at each interim check** (schedule set in Phase 6.2):
   - **Band:** stop showing it for a note source once that source has ≥ 50 scored wines and the 80% winery-bootstrap CI of its mean residual lies wholly outside ±1.0. The same check runs per country (≥ 50 scored wines; the band is withdrawn for that country) and on the whole pilot (the band is withdrawn everywhere).
   - **Shortlist:** if the shortlist's lift LB falls below 1.0, pause the pilot and report. *Superseded in Phase 6 (§6.1, before any pilot data): pause if the lift point estimate falls below 1.0 from 200 wines on; the LB version would stop working shortlists in 9–30% of pilots.*

## 6. Deployment
> **Revision 7** (2026-11-09), after critic round 6 (9/10, no MAJOR issues, 9 MINOR; `critiques/phase6_deployment_round6.md`). Revision 7 fixes the minors before the phase is committed. The self-referenced drift rule keeps a round that raised its own alert out of its reference until the analyst accepts it, so a fault that persists keeps alerting; its history is read by round number; and its reach is now measured on two milder truncations (35 and 40 words, both missed) and stated as such. Before the decision point the gate file no longer reports a pass the comparator rule could still block. A partly blank deflator column is refused, one strict parser reads every yes/no column, BSC4's timing is asserted, and the ≤ $25-share band is re-centred at rollout if the retailer's price mix differs from the data's. Numbers from re-execution 13.
>
> **Revision 6** (2026-11-09), after critic round 5 (8/10, 1 MAJOR; `critiques/phase6_deployment_round5.md`). Revision 5 had said that a round of 1,000 candidates holds about 400–480 ≤ $25 wines, which contradicts A7 (about 1,000 ≤ $25 candidates per round) and the schedule built on it. Revision 6 keeps A7, defines the candidate file once (every candidate of the round, at any price; the ≤ $25 test after the deflator), sizes every monitoring simulation to A7's round, and flags a file that looks pre-filtered at $25. It also matches accent and punctuation variants of a winery only within its country (case-only variants as their exact spelling); makes `gate.json` show the comparator rule's result; reads yes/no flags strictly; refuses a pilot file without the deflator column; runs the serving-path reproduction from the raw review file; keeps the upper ranker alerts at any round size; and adds a self-referenced drift rule that catches mild truncation. Everything below comes from notebook §6 (re-execution 13, saved with outputs).
>
> **Revision 5** (2026-11-09), after critic round 4 (8/10, 1 MAJOR; `critiques/phase6_deployment_round4.md`). Revision 5 maps the winery name to its training spelling too, since it feeds the BO1 gate's strongest comparator, and adds a pre-registered rule for when too few pilot wines have a known winery; matches grape names known only to the grape lexicon in any case; adds the serving path to the integrity check; shows the 2017-dollar price and refuses a pilot file scored on another price basis; sets the lower drift-alert limits per round size, since a round of 1,000 candidates holds only about 400–480 ≤ $25 wines; tightens intake edge cases (placeholder sources, scorer aliases, no primary-scorer rows); and gives the business KPI a baseline and a per-round "shortlist used" record. Its numbers came from re-execution 9.
>
> **Revision 4** (2026-11-08), after critic round 3 (8/10, 2 MAJOR; `critiques/phase6_deployment_round3.md`). Revision 4 maps the scoring inputs (country, province, grape, region) to the training spellings, not only the grouping labels, and flags a country the models never saw; stops a missing note source from counting toward the source minimum; makes the price basis a rollout prerequisite (2017 dollars via a CPI deflator); sets the lower alert limits on out-of-fold development rounds by a stated rule; raises the A11 floor to 15% by a stated rule; restricts the gate to WineEnthusiast scores, with other critics and unsampled wines as coded sensitivities; and adds a business KPI. Its numbers came from re-execution 8.
>
> **Revision 3** (2026-11-08), after critic round 2 (8/10, 1 MAJOR; `critiques/phase6_deployment_round2.md`). Revision 3 canonicalises note-source and country names once, at intake, so a typing variant can't split a unit or meet the source minimum; tightens the reproduction record (all four outputs, finite); makes the ranker-level alerts two-sided and measures how often the alerts catch a broken feed; reconciles the schedule with a review-lag assumption (A10) and a source-mix check (A11); and gives one cost line.
>
> **Revision 2** (2026-11-08), after critic round 1 (7/10, 5 MAJOR; `critiques/phase6_deployment_round1.md`). Revision 2 makes the tool enforce exactly the stop rule that was simulated (one shared rule, with the pooled unit and name matching), hardens the integrity check, builds the per-round monitoring checks into `score.py` and the app, replaces the shortlist tiers that were wrong for new writers, adds the outcome-data plan and schedule, and checks every 100 wines up to a cap. Its numbers came from re-execution 5; revision 3's from re-execution 6, `reports/tables/phase6_*.csv` and the files in `deployment/` and `models/`. **Phase 6 changes no model, selection or Phase 5 number.** It builds the tool, fixes the pilot protocol in code before any pilot data exists (to be frozen by a tag, §6.1 prerequisites), and fills in the parts of the §5.3 conditions that Phase 5 left to Phase 6. Where it departs from an earlier plan, the change is listed in §6.1 under "Departures from earlier plans".

### 6.1 Deployment plan
**What is deployed: an internal pilot tool, not a product.** The buying team uses it during the pilot. Customers never see its output (R10), it runs only when an analyst runs it, and it never retrains itself.

**The artifact** (`models/value_finder.joblib`, 4.6 MB; SHA-1 and build settings in `models/manifest.json`):
- **What it holds:** the frozen Phase 4 selections, refit on all 100,530 development rows with the same procedure as the Phase 5 lockbox run (`winevalue.production.build`, notebook 6.1b, about 3–4 minutes). It is **not** refit on the lockbox critics; that would be a model nobody has tested (§5.3 condition 1).
- **Reproduction check (§5.3 condition 1):** scored on the lockbox, the artifact reproduces `phase5_lockbox_predictions.csv.gz` row by row. The largest absolute difference is **0.0** for the ridge score, the calibrated estimate, the shortlist ranker and P(90+). The ranker is compared on the 16,699 priced lockbox rows: the deployed tool gives no ranker score to a wine without a price (it can't be a ≤ $25 candidate), whereas Phase 5's file holds an imputed-price score for the other 1,097. Revision 2's check skipped those rows silently; revision 3's check fails on any missing-value or length mismatch, so the comparison is now stated. **Since revision 5 the same reproduction also runs through the path the tool serves** (raw lockbox columns → `ValueFinder.prepare` → score, with the deflator at 1.0): largest difference **0.0** over all four outputs (critic round 4 found the check had skipped `prepare_new`). The manifest must record all five entries as finite differences ≤ 1e-8, or the tool refuses it. The simple rules, the variety × country baseline and the flavour-profile assignments are identical to the Phase 5 objects (notebook assertions).
- **Integrity:** the app and the scripts refuse to serve the artifact unless `manifest.json` exists, records a passed lockbox reproduction (every difference ≤ 1e-8), and holds the file's SHA-1 (`artifacts.load_value_finder`). They never rebuild it. A rebuild goes through `deployment/build_artifact.py` (or notebook 6.1b), which writes the artifact and manifest only after the reproduction check passes (tested). The SHA-1 identifies one saved file, not the model: two builds differ in their bytes only because scikit-learn stores a memory address (`_stop_words_id`) in the TF-IDF step, with every fitted parameter identical. That is why a rebuild is accepted by the reproduction check, not by its SHA-1. scikit-learn is pinned to the version that saved it (1.9.1, `deployment/requirements.txt`).

| Output | Model in the artifact | How it is shown |
|---|---|---|
| Shortlist (BO1) | Ridge on the note's TF-IDF, origin, grape, vintage and log price (DM2) | Rank within the buying round; tier "Sample first" (top 10% **of this round**) or "Worth sampling" (top 20%). The one-wine view has no round, so it shows the wine's percentile among development candidates, with a caveat (tier table below) |
| Score band (BO2) | Calibrated ridge, price-free (DM1): points = 7.957 + 0.917 × ridge score, 80% band ± 2.67 | "Estimated 85–90", with the condition-5 caveat; hidden wherever the stop rule fired |
| Value verdict | The price-free estimate against the 90-point / $25 bar | Likely / Probable / Long shot / Unlikely, next to the base rate; hidden with the band |
| P(90+) | Logistic map of the ranker's out-of-fold score | "Relative indicator, not a probability" (condition 5) |
| Flavour profile | Lexicon NMF, k = 8 (DM3) | Both blind reviewers' names for the profile |
| 5 similar wines | TF-IDF cosine over the 118,378 reviewed notes, same colour; DM5 near-duplicate flag (Jaccard ≥ 0.5) | Title, critic score, price, similarity, near-duplicate flag |

**The tool** (`deployment/`; how to run it is in `deployment/README.md`):
- **`app.py`** (Streamlit) has two views:
  - **One wine** is the BSC4 screen. A buyer pastes a note and enters country, grape, vintage and price (province, designation and title are optional). The screen shows every BSC4 output: the estimated band, P(90+), the value verdict, the flavour profile and 5 similar reviewed wines.
  - **Shortlist a buying round** takes a CSV of candidates and returns the ranked ≤ $25 shortlist with round tiers and data-quality flags, plus the round's drift alerts, ready to download.
- **`score.py`** scores a buying round from the command line. An A7 round's file (about 2,400 candidates) takes about 2–3 s. It refuses a file without the required columns, adds per-row flags, and writes the round's monitoring report next to the scores (§6.2).
- **`pilot_eval.py`** runs the pilot protocol below on the scores received so far. It writes the gate, every check, the withdrawn units and the secondary intercept table. With `--update-status` it writes `band_status.json`: the withdrawn sources, the member sources of a withdrawn pooled unit, the withdrawn countries, and whether the whole pilot lost the band.
- **One way into the models.** Every tool path prepares raw inputs with `ValueFinder.prepare`. Country, province, grape, region **and winery** values that are not an exact training spelling are mapped to one by a match key (case, spaces, apostrophes, accents and punctuation), plus a short country alias table (USA → US, Czechia → Czech Republic, …). A grape that does not match as a whole is matched part by part at blend separators, and grape names the grape lexicon knows but training does not (Turbiana → Verdicchio) are matched too, so they keep their canonical grape and colour in any case. Prices are converted to 2017 dollars with `config.PRICE_DEFLATOR`.
  - **Why each was added.** Revision 3 matched names only for grouping; critic round 3 showed a lower-case "italy" was still scored as an unseen country (about 1 point off). Critic round 4 showed the same for wineries, where it mattered more: the "winery track record" rule, the BO1 gate's strongest comparator, looked wineries up as typed, so upper-casing them weakened the comparator and raised the dry run's lift from 1.81× to 1.96× with no flag.
  - **What it changes on real data.** Exact training spellings are never touched, so no development row changes (all 118,378 prepared rows give the same model inputs) and the reproduction above is exact. **Accent and punctuation variants of a winery are matched only within its country** (revision 6): in revision 5 the key also matched "Patria" (Italy) to "Pátria" (Portugal) and an Italian "Ménage à Trois" to the US one, two different producers (critic round 5). **A variant in letter case only** is matched first, in any country, to the one training spelling it equals case-insensitively (if exactly one does). The frozen "winery track record" rule reads a winery by name alone, so an exact spelling already gets that winery's record whatever the country; matching the case variant the same way keeps "NEUMEISTER" scoring as "Neumeister". The exception: the training data holds 24 wineries spelled two ways in case only ("StoneCap", 10 reviews; "Stonecap", 1), which the frozen rule treats as two wineries; a case variant of one of them goes to the more frequent spelling (5 lockbox rows move by 0.66 points when title-cased). Re-execution 10 stopped on exactly this: one dry-run wine, "Neumeister" with country Unknown, lost its record when upper-cased (coverage 70.75% → 70.5%), and the variant assertion caught it. Now the key matches 21 lockbox rows (11 in the ≤ $25 pool), all Italian wineries that WineEnthusiast's own data spells two ways ("Monte del Frà" / "Monte del Frá", "Fattoria del Cerro" / "Fattoria Del Cerro"). Within the training data, the 71 keys with two spellings are each one producer. A matched record can move the comparator either way; the dry run below is unchanged.
  - **Checks.** A country still unseen after mapping is flagged per row and counted by a drift alert, and the share of wineries unseen in training is reported each round (§6.2). Tests and notebook 6.1d check that a round with lower-case, upper-case or alias names gives identical scores, rule scores, gate, checks and withdrawn wines, on the dry run and on the whole lockbox ≤ $25 pool (7,288 wines).
- **One rule hides the band everywhere.** `pilot.band_hidden` is used by the protocol simulation, `pilot_eval.py`, `score.py` and the app. It matches source and country names after normalising spaces, case and apostrophes (a straight "O'Keefe" matches the curly one). A test feeds a status file through `score.py` and checks that it hides exactly the wines the rule hides, and notebook 6.1d asserts the same on the dry run.
- **BSC4 (§5.3 condition 6): passes on screen and timing; the recorded demo is pending.** Notebook 6.1c timed 50 lockbox notes end to end (prepare, score, 5 similar wines): about **0.03 s** per query (median; wall-clock, so it varies slightly per run), all under 3 s. In the app the same query takes about 0.05–0.08 s once the similarity index is built (about 2 s, once at start). Every BSC4 output is on one screen: see `reports/figures/phase6_app_one_wine.png` (the app's one-wine view, captured headless with the example note via `?demo=1`; band, P(90+), verdict with base rate, ranker percentile, profile, 5 similar wines and the 2017-dollar price used, computed in 0.08 s), and the automated app test (`tests/test_app.py`, Streamlit `AppTest`) asserts all five outputs and a time under 3 s. **The recorded demo BSC4 names is still to come** with the walkthrough video.

**Departures from earlier plans** (each made before any pilot data; none changes a model or a Phase 5 number):

| Earlier plan | Phase 6 | Why |
|---|---|---|
| "5 similar wines" built on the DM5 LSH index (§4.4) | TF-IDF cosine within the same colour; LSH kept for the near-duplicate flag | The LSH stage returns a candidate only when 5-word shingles overlap heavily (Jaccard ≥ about 0.3), i.e. for near-copies. A typical new note has no such neighbour, so the index can't supply five. An early cosine version also returned a white for a Tempranillo; the colour filter fixes that |
| Value verdict named in BSC4 but never defined | Tiers from the price-free estimate and its 80% band: **Likely** (whole band 90+), **Probable** (estimate 90+), **Long shot** (only the top of the band reaches 90), **Unlikely** (otherwise); only for priced wines at ≤ $25. The screen shows the base rate next to it, and says why it can disagree with the shortlist | R-2: the verdict must not use price as a quality input. The tiers are read off the frozen band, not tuned. Their value rates are checked below. The third tier was called "Possible" in revision 1; on the lockbox its value rate is below the base rate, so the label now says so |
| Shortlist tiers against fixed development cut-offs (revision 1) | Tiers by rank **within the buying round**; the one-wine view shows a development percentile with a caveat | Fixed cut-offs put 30% of the lockbox's candidates in "top 10%" (tier table below) |
| §5.3: "interim checks" at 100–400 wines | A check every **100** wines; decision at the first check with ≥ 400 wines **and** the source minimum; at most **800** wines | Critic round 1, issue 8: a pilot that keeps collecting must keep being checked, and it needs an end |
| §5.3 condition 2: "several note sources" | **At least 3 note sources with ≥ 50 scored wines each.** Smaller sources are pooled into one unit for the stop rule | Phase 5 critic round 3, deferred issue. Below 3 sources, one writer's level decides the result (the lockbox lesson) |
| §5.3 condition 7: pause if the shortlist's lift **LB** falls below 1.0 | Pause if the lift **point estimate** falls below 1.0, from **200** scored wines on | The LB trigger would pause 9–25% of simulated pilots at 200 wines from development pools where the shortlist works (up to 30% masked), so a working shortlist would often be stopped. The point-estimate trigger asks only "is it doing no better than a simple rule?". Rule and selection below |
| §5.3 condition 4: "an intercept fitted on the first scored wines" | Each source's intercept is its mean residual over its first **50** scored wines, applied to its later wines; reported for sources with ≥ **100** wines | Freezes the rule, as condition 4 required |

**The value verdict on held-out critics** (notebook 6.1c, `phase6_verdict_tiers.csv`; ≤ $25 wines; development folds use each fold's out-of-fold estimates, so every row is a new writer):

| Verdict | Development folds 0 / 1 / 3 / 4: wines · value rate | Lockbox: wines · value rate |
|---|---|---|
| Likely value | 22–40 per fold · **0.85–1.00** | 207 · **0.88** |
| Probable value | 539–1,326 · 0.55–0.74 | 1,586 · 0.52 |
| Long shot | 3,351–5,342 · 0.19–0.36 | 3,791 · 0.14 |
| Unlikely value | 1,796–8,224 · 0.01–0.07 | 1,704 · 0.02 |

- **The tiers sort wines in the right order in every fold and on the lockbox.** "Likely" is rare (under 1% of development wines, 3% of the lockbox's), so most of the verdict's use is in telling "Probable" from "Unlikely".
- **On the lockbox, "Probable" and "Long shot" are at the low end of the development range** (0.52 and 0.14). This is the same over-prediction as the band's (+0.84 points, §5.1 point 7): more lockbox wines reach the upper tiers than deserve to. It is why the verdict is hidden with the band.
- **"Long shot" is near or above the base rate in development (0.97–1.9×: 0.19–0.36 against 0.10–0.22; fold 4 is 0.97×) and below it on the lockbox (0.65×: 0.14 against 0.22).** It means "not ruled out", not "likely". That is why revision 2 renamed it from "Possible" and puts the base rate next to every verdict.

**The shortlist's percentile label on new writers** (notebook 6.1c, `phase6_shortlist_tiers.csv`; ≤ $25 wines; development folds use out-of-fold ranks). The cut-offs are the 80th and 90th percentiles of all development out-of-fold ranks, the "top 20%" and "top 10%" of revision 1's tiers:

| Pool | Wines | Value rate | Share above the development P90 / P80 | Value rate above P90 / P80–P90 / below P80 |
|---|---|---|---|---|
| Development fold 0 | 10,786 | 0.19 | 12.7% / 26.0% | 0.61 / 0.38 / 0.08 |
| Development fold 1 | 12,658 | 0.10 | 6.1% / 12.1% | 0.76 / 0.39 / 0.04 |
| Development fold 3 | 9,024 | 0.22 | 6.5% / 13.9% | 0.73 / 0.53 / 0.16 |
| Development fold 4 | 6,134 | 0.19 | 19.5% / 35.6% | 0.52 / 0.27 / 0.07 |
| Lockbox | 7,288 | 0.22 | **30.1% / 46.4%** | 0.53 / 0.20 / 0.05 |
| Lockbox, masked | 7,288 | 0.22 | 31.1% / 47.8% | 0.51 / 0.18 / 0.05 |

- **A fixed cut-off is a level, and the level moves with the writer.** Pooled over development the shares are 10% and 20% by construction, but per fold they range from 6% to 20% above P90, and on the lockbox's writers 30%. A label "top 10%" would have been wrong by a factor of 3 for them.
- **The ordering still holds.** Wines above the cut are 2.4–7.5× as likely to be value wines as the pool, in every fold and on the lockbox. So the shortlist view ranks within the round, which is unaffected by the level. The one-wine view, which has no round, shows the development percentile with the caveat that new writers can sit above it.

**The pilot protocol, fixed before any pilot data** (to be frozen by the tag under "Prerequisites") (`config.PILOT_*`; `winevalue.pilot`, used both by `pilot_eval.py` and by the simulations; tested in `tests/test_phase6.py`):

| Step | Rule | Set how |
|---|---|---|
| Pilot wines | ≥ 400 ≤ $25 retailer notes for wines that later receive a critic score, from ≥ 3 note sources with ≥ 50 scored wines each. **The pilot wines are chosen without the model**: all eligible candidates, or a random sample of them, whatever the shortlist says. Buyers may use the shortlist for their own sampling meanwhile | §1.1; condition 2. If the pilot wines were the shortlisted ones, the top-20% lift could not be measured |
| Checks | After every 100 scores, in order of arrival (`PILOT_CHECK_EVERY`), up to 800 (`PILOT_MAX_WINES`). Every gate and check uses 200 winery-bootstrap resamples (`PILOT_N_BOOT`) | Schedule; critic round 1, issues 6 and 8 |
| Band stop rule | Per unit with ≥ 50 scored wines: stop the band if the 80% winery-bootstrap CI of the mean residual (estimate − score) lies wholly outside ±1.0. Units: each note source, the pooled small sources, each country, the whole pilot. A withdrawal is permanent; the whole-pilot unit withdraws it everywhere | §5.3 (unchanged), plus the pooled unit |
| Shortlist futility pause | From 200 scored wines: if the top-20% lift against the best simple rule is below 1.0, pause the pilot. **Nothing is deployed**; the result goes to the buying lead and the project returns to Phase 4 | Development folds (below) |
| Final gate | At the **decision point**, the first check with ≥ 400 wines **and** ≥ 3 sources with ≥ 50 wines, on **all** pilot wines up to it: shortlist lift ≥ 1.3×, LB > 1.0; band ±2 gain ≥ +5 pp, LB > 0; joint gate reported. Wines scored later are not used. Before the decision point, `pilot_eval.py` reports "interim, keep collecting"; without one by 800 wines, the pilot stops with no deployment | §1.1 bars, option F |
| BO1 comparator coverage | At the decision point, the share of wines used whose winery is in the training data (the "winery track record" rule knows only those). If it is below **50%** (`PILOT_MIN_WINERY_COVERAGE`; dry run 71%), the shortlist part must **also** pass on the matched-winery wines alone (at least 100 of them), else the shortlist is not deployed. The matched-winery gate is always reported (`sensitivity.json`), and `gate.json` records `BO1 passes (after comparator rule)`, which the joint gate uses. Before the decision point both are blank and `pilot_eval.py` prints "interim reading" (revision 7) | Critic round 4 issue 1: an unknown winery gets the overall mean, which weakens the comparator and makes the lift easier to reach. Set before any pilot data; simulated pools come from reviewed wines and are not affected |
| Decision | Shortlist and band pass → deploy the shortlist and show the band internally where it was not withdrawn. Shortlist only → deploy the shortlist, no band. Shortlist fails → deploy nothing; report both; back to Phase 4 | Option F (§5.3 condition 3) |
| Secondary (reported only) | Per source: intercept from its first 50 wines; ±2 gain on its later wines with and without it | Condition 4 |

**How the pause threshold was chosen** (notebook 6.1a, `phase6_pause_rates.csv`; 1,000 simulated pilots per pool and size, with 95% Wilson intervals):
- **Rule, stated before the simulation ran:** choose the smallest interim size at which the futility trigger pauses at most 5% of simulated pilots in **every development pool**, masked and unmasked. Development pools are the ones where the shortlist is known to work, so a pause there is a false one. The lockbox is reported for information only.
- **Result:**
  - at 100 wines the trigger pauses up to 10.5% of development pilots (fold 4, masked);
  - at **200**, at most **2.9%** (fold 4, masked; 95% CI 2.0–4.1%), and 0.3–2.4% elsewhere;
  - at 300, at most 1.5%.

  So the minimum is 200, as `config.PILOT_PAUSE_MIN_WINES` says (a notebook assertion checks the match). Every development pool's upper interval at 200 wines is below 5%. Revision 1's run, with 200 simulations, put fold 4 masked at 5.0%, exactly on the line; with 1,000 it is 2.9%.
- **For comparison, the LB trigger of §5.3 condition 7** pauses 9.4–25.2% of unmasked development pilots at 200 wines, and 12.0–30.0% of masked ones.
- **Lockbox, for information:** the futility trigger pauses 0.0% of lockbox pilots at 200 wines, masked or not (95% CI up to 0.4%).
- **What the pause catches** (the "check:" pools, never used to choose the size):
  - **A shortlist that does no better than chance.** With the ranker replaced by random noise, the trigger pauses 97–100% of pilots at 200 wines in every development pool, and 90–98% at 100.
  - **Not a shortlist that is weak but better than the simple rules.** On the lockbox's Jenssen pool (336 wines, lift 1.23×, below the 1.3× bar, §5.3), it pauses 10% of pilots at 200 wines and none at 300. That case is left to the final gate, which Jenssen's pool fails. The pause is a futility stop, not a second gate.
- **Caveat:** the threshold was chosen on development folds, but after the lockbox results were known. The pilot is its first clean test.

**The whole protocol on simulated pilots** (notebook 6.1a, `phase6_protocol_simulation.csv`). Each simulated pilot draws up to 800 ≤ $25 wines from a pool in random arrival order. It runs the check every 100 wines until the decision point, a pause or the cap, exactly as `pilot_eval.py` would. 200 pilots per pool, so a rate has a simulation SE of up to about 0.035. The pools are critic notes (masked rows stand in for retailer notes), with the critic as the note source. The "first 400" columns give each part of the gate on the first 400 wines, whether or not the pilot reached a decision there.

| Pool the pilot is drawn from | Shortlist part passes (first 400) | Decision point reached | Paused | Stopped at 800 (source minimum) | **Shortlist deployed** | Band part passes (first 400) | Band withdrawn everywhere | **Band shown** | Band hidden: wines in an offset unit / other wines | Sources with ≥ 50 wines (median) |
|---|---|---|---|---|---|---|---|---|---|---|
| Development fold 0 | 0.800 | 0.000 | 0.020 | 0.980 | **0.000** | 0.995 | 0.000 | **0.000** | 0.935 / 0.005 | 1 |
| Development fold 1 | 0.900 | 0.000 | 0.005 | 0.995 | **0.000** | 1.000 | 0.000 | **0.000** | 0.000 (1% of wines) / 0.051 | 2 |
| Development fold 3 | 0.950 | 0.985 | 0.015 | 0.000 | **0.940** | 0.995 | 0.000 | **0.935** | 0.671 / 0.000 | 3 |
| Development fold 4 | 0.755 | 0.970 | 0.030 | 0.000 | **0.750** | 0.985 | 0.115 | **0.665** | 0.438 / – (all wines) | 4 |
| Lockbox, mixed writers | 0.990 | 1.000 | 0.000 | 0.000 | **0.990** | 0.780 | 0.025 | **0.765** | 0.914 / 0.028 | 3 |
| Development fold 0, masked | 0.670 | 0.000 | 0.025 | 0.975 | **0.000** | 0.995 | 0.000 | **0.000** | 0.781 / 0.000 | 1 |
| Development fold 1, masked | 0.810 | 0.000 | 0.015 | 0.985 | **0.000** | 1.000 | 0.000 | **0.000** | 0.000 (1% of wines) / 0.050 | 2 |
| Development fold 3, masked | 0.940 | 0.975 | 0.025 | 0.000 | **0.935** | 0.990 | 0.000 | **0.930** | 0.683 / 0.013 | 3 |
| Development fold 4, masked | 0.720 | 0.980 | 0.020 | 0.000 | **0.720** | 0.890 | 0.465 | **0.345** | 0.728 / – (all wines) | 4 |
| **Lockbox masked, mixed writers** (retailer-note proxy) | 0.975 | 1.000 | 0.000 | 0.000 | **0.975** | 0.190 | 0.240 | **0.160** | 0.935 / 0.243 | 3 |

*"Offset unit": a wine whose note source or country has a mean residual beyond ±1.0 in the whole pool, which is what the stop rule is meant to catch. "Band shown" means the decision shows the band at all; within a pilot it is still hidden for withdrawn units. Band-hidden shares are measured over all wines the pilot collected, up to 800 for pilots that stopped. Unit-level detail: `phase6_withdrawn_units.csv` (100 pilots per pool) and `phase6_unit_truth.csv`. Where the decision point is reached, it is at 400 wines in the median pilot.*

- **The source minimum decides folds 0 and 1, as intended.** Fold 0 is one writer (Voss), and fold 1 has only two with 50+ pool wines in most draws (Schachner, Gordon). No pilot from them reaches 3 sources with ≥ 50 wines. So 97.5–99.5% stop at 800 wines with nothing deployed, and the rest pause. A pilot like that can't show that the result holds across writers, which is what condition 2 asks. The "first 400" columns show what the gate alone would have said: the shortlist's part passes 0.80–0.90 (0.67–0.81 masked), the band's 0.995–1.000.
- **Where the decision point is reached** (folds 3 and 4, and the lockbox), the shortlist deploys in 72–94% of development pilots and 97.5–99% of lockbox pilots. The futility pause fires in at most 3% of pilots. All of them come from pools where the shortlist works, so every pause here is a false one. The deployed share is at most 0.01 below the first-400 pass share.
- **The band is shown in 67–94% of unmasked pilots from folds 3 and 4 (69–95% of those that reach a decision), and in 77% of unmasked lockbox pilots, but in only 16% of masked lockbox pilots.**
  - **Masked lockbox:** the band's part passes 19% of the time, and the whole-pilot check withdraws the band everywhere in 24%. The pool's mean residual is +0.99, right on the ±1.0 line.
  - **Development fold 4, masked**, shows the other way the band can be lost. Its part of the gate passes 89% of the time, but the whole-pilot check withdraws the band in 46.5% of pilots. Fold 4's whole pool sits near the line: its mean residual is +0.96 unmasked (11.5% whole-pilot withdrawals), and its largest units are beyond it (Buzzeo +1.51, Boone +1.08, the US +1.01). Masking pushes it over: the masked pool's mean residual is +1.09, and Buzzeo goes to +1.73, Boone to +1.18 and the US to +1.14 (`phase6_unit_truth.csv`, which since re-execution 6 also covers the masked development pools).

  Where the gate and the stop rule disagree, the band is hidden: the stop rule is conservative on purpose.
- **The stop rule mostly hits the right wines.** Wines in a unit that is really off by more than a point lose the band in 44–94% of pilots. Other wines lose it in 0–5%, except on masked lockbox notes (24%, the whole-pilot firings above).
- **What it misses: units too small to reach 50 wines.**
  - **France in development fold 3** is over-predicted by +1.86 points, and the band does worse than the baseline there (−4.9 pp). But a 400-wine pilot holds only about 25 French wines, so the rule never checks it.
  - **South Africa in fold 4** (+1.79, −5.8 pp; about 50 wines per pilot) is withdrawn in only 51% of pilots.
  - **DeSimone** (−1.45, −2.7 pp; about 17 wines per pilot) is only ever checked inside the pooled small-source unit, which fires in 13% of fold-4 pilots.

  A note source that supplies fewer than 50 pilot wines is protected only by the pooled and whole-pilot checks.
- **What it over-withdraws: a level error with a working band.** Gregutt's wines are under-predicted by 1.43 points, yet the band still beats the baseline for them (+7.8 pp). The rule withdraws it in 99% of pilots. It targets the level, not the gain, because a buyer reads the band's centre.
- **How much of this is simulation noise** (`phase6_seed_spread.csv`: Phase 5's 400-wine pass-rate simulation, `phase5.pilot_pass_rate`, 200 pilots, seeds 1–3). The pass rates move between seeds by up to 0.10:

  | Pool | Shortlist part, seeds 1–3 | Band part, seeds 1–3 |
  |---|---|---|
  | Development folds 0 / 1 / 3 / 4 | 0.755–0.790 / 0.850–0.900 / 0.930–0.955 / 0.730–0.830 | 0.990–1.000 / 1.000 / 0.995–1.000 / 0.955–0.980 |
  | Development folds 0 / 1 / 3 / 4, masked | 0.630–0.670 / 0.810–0.860 / 0.905–0.925 / 0.720–0.795 | 0.990–1.000 / 1.000 / 0.990–1.000 / 0.820–0.865 |
  | Lockbox / lockbox masked | 0.985–1.000 / 0.980–0.995 | 0.780–0.865 / **0.185–0.255** |

  Phase 5's figures (§5.3: shortlist 67–99.5% masked, band 24% in the masked lockbox pool) and this table's "first 400" columns fall inside these ranges or within 0.03 of them. They differ by random draws, not by method. The conclusions do not depend on which seed is quoted.
- **Limits:** critic notes, masked or not, are not retailer notes; the simulation resamples wines, not writers; and the pass and withdrawal rates are conditional on each pool's writer mix.

**Dry run of the tooling** (notebook 6.1d, `phase6_pilot_dry_run.csv`). A stand-in pilot file of 400 ≤ $25 lockbox wines, in the real pilot format with the critic as the note source and a random arrival order, went through `pilot_eval.py`'s code path. It tests the tooling, not the model: these wines were already scored in Phase 5.
- **Gate:** band +5.25 pp (LB +1.21), shortlist 1.81× the best simple rule (winery track record; LB 1.43). Decision: deploy the shortlist and show the band internally.
- **Comparator coverage:** 70.8% of the dry-run wines have a winery from the training data, above the 50% minimum. On those 283 wines alone the shortlist's lift is 1.59× (LB 1.35), so it would pass even with the comparator at full strength.
  - **How coarse the measure is** (critic round 5). "Seen" counts a winery with a single training review, whose record is shrunk almost entirely to the overall mean. On the lockbox ≤ $25 pool 68% of wines have a seen winery but only 44% have five or more training reviews. The 50% threshold is a judgement call, not a tested rule: the critic's sweep (60 draws of 400 lockbox wines with matched wineries un-matched at random) found the pooled lift about 0.05 higher at 58% coverage than at 68%, with no rule reacting, and the matched-only lift about 0.1 below the pooled lift even at natural coverage. So `pilot_eval.py` prints the matched-winery lift next to the primary one, and the decision memo reports both.
- **Typing variants:** the same file with lower-case or alias countries, lower-case grapes, upper-case provinces and upper-case wineries gives the identical gate, checks and withdrawn wines (notebook assertion).
- **Stop rule:** the band was withdrawn for O'Keefe and for Italy at the 200-wine check (O'Keefe writes all the lockbox's Italian wines), so 52% of the pilot's wines would have lost the band. The shortlist was never paused. 3 sources had ≥ 50 wines from the 300-wine check on, so the decision point came at 400 wines, on all 400. **The tool hides the same wines:** `pilot.band_hidden`, applied to the stand-in file through `production.prepare_new` with the status file `pilot_eval.py` wrote, hides the band for 209 of the 400 wines, exactly the protocol's set (notebook assertion).
- **Secondary intercept:** O'Keefe's first 50 wines give an intercept of +1.02. Applied to the 159 later O'Keefe wines it turns the ±2 gain from −7.6 pp into +15.1 pp. This is one draw, on wines already used in Phase 5. It shows the analysis works, not that the intercept helps.

**Outcome data and schedule** (Phase 6 critic round 1, issue 5). Every gate and every lagging check needs a critic score for wines the model has already ranked. Where those scores come from sets the pilot's length and cost.
- **What a round's candidate file is** (revision 6, critic round 5 issue 1). A buying round has about 1,000 unscored ≤ $25 candidates (A7, A9). The file scored each round is **every candidate of the round, at any price**: the ≤ $25 test is applied after the price deflator, so a file filtered at a nominal $25 beforehand would lose wines that are ≤ $25 in 2017 dollars, and the deflator could not restore them. The ≤ $25-share alert fires above 95% (a file that looks pre-filtered) as well as below 25% (§6.2). In the lockbox, 41% of candidates are ≤ $25, so an A7 round is about 2,400 candidates in all.
- **Which wines are pilot wines.** Every ≤ $25 candidate in every buying round is logged and scored by `score.py` before anyone tastes it, and its note source is recorded. A candidate becomes a pilot wine when a critic score for it appears. Pilot wines are therefore chosen by critics, not by the model. Buyers may use the shortlist meanwhile. Because a listing could make a wine more likely to be submitted for review, the pilot file has a `sampled` column (the team sampled or listed the wine), and `pilot_eval.py` reports the gate on the unsampled wines up to the decision point as a sensitivity (`sensitivity.json`; tested).
- **Where the scores come from: published WineEnthusiast reviews,** the scorer the models were trained on (`config.PILOT_PRIMARY_SCORER`). Only these enter the gate, the stop rule and the decision. A scorer's level is this project's largest error source, and the stop rule's units are note sources, not scorers, so pooling critics would move every residual. "Wine Enthusiast Magazine" and "winemag" count as the same publisher, and `pilot_eval.py` prints every distinct scorer spelling for the analyst. A file with no primary-scorer rows is reported as "nothing to judge". Scores from other critics on the 100-point scale are logged with the critic (`scorer` column) and reported as a sensitivity: the gate on all scorers over the same arrival window as the primary gate, and each scorer's mean residual (`pilot_eval.py` writes `sensitivity.json` and `per_scorer.csv`). A8's yield counts WineEnthusiast reviews only. Using newly published scores for a retailer's internal evaluation needs the publisher's permission or a data licence (see prerequisites below).
- **Matching.** A review is matched to a candidate on normalised winery, vintage and grape, then title-word Jaccard ≥ 0.8. Only unique matches count, and every match is logged with the round's file. Two checks run before the first interim check and then each quarter:
  - **Precision:** the analyst hand-checks 50 random matches. If fewer than 48 are right, the rule is fixed first. 48 of 50 still allows a true precision as low as about 86% (95% lower bound), so a wrong-match rate of a few percent is part of the pilot's noise.
  - **Recall:** the analyst takes 50 published reviews of ≤ $25 wines and searches the logged candidates by hand. Of those found in the log, the rule must find at least 40 (80%). A lower recall is fixed, or it lowers the effective yield (A8), and the timeline below is recomputed.
- **Censoring.** Only 80+ scores are published (R4), and many ≤ $25 wines are never reviewed. The pilot measures the gate on reviewed wines, like the training data and the lockbox, not on every candidate.
- **Assumptions** (no data in this project to test them; `config.PILOT_*`):
  - **A8, review yield:** about 10% of ≤ $25 candidates eventually receive a published score (sensitivity 5–20%);
  - **A9:** one buying round a month, with about 1,000 ≤ $25 candidates (A7);
  - **A10, review lag:** a candidate's review appears a median of 3 months after its round (sensitivity 2–6), log-normal, with 90% within 3× the median;
  - **A11, note-source mix:** at least 3 named note sources each supply **15%** or more of the ≤ $25 candidates (`config.PILOT_MIN_SOURCE_SHARE`). Revision 3's 12.5% gave 50 per source of 400 only on average: three sources at exactly 12.5% all reach 50 by 400 scored wines with probability 0.11 (exact multinomial, notebook 6.1e, `phase6_source_minimum.csv`). The floor is now the smallest share at which that probability is at least 0.80 (`phase6.choose_source_share`): 0.80 at 15%, 0.999 by 500 wines. So at the floor the decision comes at 400 wines in about 4 pilots of 5, and otherwise at 500 (about month 9). It is re-checked on the first 100 scored wines, since yield may differ by source. Rows without a note source (blank, "unknown", "N/A", "none", "-" and similar) never count as a source, and form one stop-rule unit. This one is checked at once: if round 1's logged candidates don't meet it, the note sourcing is fixed before round 2. Simulated pilots from one- or two-writer pools never reach the decision point (above), so a pilot that fails A11 would run to the cap for nothing.

**When 400 scored wines arrive** (notebook 6.1e, `phase6_pilot_timeline.csv`; month counted from round 1; the decision follows at the next 100-wine check):

| Review yield (A8) | Median lag 2 months | **3 months (A10)** | 6 months |
|---|---|---|---|
| 20% | month 4 | month 5 | month 7 |
| **10% (A8)** | month 7 | **month 8** | month 10 |
| 5% | month 11 | month 12 | **not within the cap** (about 290 by month 12) |

- **Under the assumptions, the decision comes at about month 8.** At 5% yield it is at the cap or beyond. That is the case the fallback is for. Halving A7 (about 500 ≤ $25 candidates a round) has the same effect as the 5% yield row, and it also silences the self-referenced drift rule, which is read only from 600 ≤ $25 candidates (§6.2).
- **Cap:** the pilot ends **12 calendar months after round 1** (12 monthly rounds), or at **800 scored wines** (`config.PILOT_MAX_WINES`), whichever comes first. Scores published after month 12 are not used. Without a decision point by then, the pilot stops with no deployment.
- **Fallback rule, written down.** At **month 6** the analyst multiplies the scored pilot wines so far by the projection factor S(12)/S(6): **2.77** under A10, or 2.46 / 3.66 for a 2- or 6-month median lag. If the matched reviews' own lags (publication date minus round date) give a different median, the factor for that median is used. If the projection is below 400 (under A10, fewer than about 145 scored wines at month 6), the retailer may buy a random sample of 400 logged candidates and have them scored blind on the 100-point scale by one external panel. That costs $10,000 (400 × $25, A5), and the panel's scores take about 2 months, so a decision comes at about month 9. The panel is a new scorer. Its scores still test the shortlist's ranking, but they test the band against the panel's level, not the training critics'.
- **Cost of the main route:** no sample purchases. Logging, scoring, matching, the two matching checks and a check every 100 scores take about 2–4 analyst-hours per round (A5, restated for this larger task). At about $50 an hour, that is **$1,200–2,400 for 12 rounds**, plus a data licence (to be quoted, see prerequisites). **Fallback: +$10,000.** This replaces §5.3's "$10,000 for 400 samples", which assumed the pilot bought its wines.

**Prerequisites before rollout step 0** (critic round 1, issue 15):
- **Licence.** The training data is CC BY-NC-SA 4.0, and a retailer's buying tool is commercial use. A real deployment needs a licence from the data owner, or a retrain on licensed data, which would be a new model that has to pass the same tests. As built, this tool is an academic demonstration.
- **Business baseline.** The quarterly business KPI (§6.2) compares the sampled wines' outcomes with the rounds before the tool. So at step 0 the analyst extracts the sampling records of the last 12 pre-tool rounds, matches them to published WineEnthusiast reviews with the same matching rule, and computes `monitoring.business_kpi` on them. That figure is the baseline, frozen with the deflator.
- **Hosting.** It runs locally or on a private, authenticated host. The public Streamlit Community Cloud route in `deployment/README.md` is for the course demonstration only; the app has no login (R10).
- **Price basis.** The models, the ≤ $25 pool, the value bar and the ranker's log price are all in 2017 dollars (the data's prices). A pilot run years later sees nominal prices, and inflation alone would push wines over the bar: the detection table in §6.2 shows that prices × 1.3 already sets off the ≤ $25-share alert in most rounds. So before rollout step 0 the analyst sets `config.PRICE_DEFLATOR` = CPI-U (BLS series CUUR0000SA0, all items, US city average) for 2017 as an annual average, divided by CPI-U for the month before round 1, in a dated commit. It is fixed for the whole pilot, applied in `production.prepare_new` (the price as given is kept), and recorded in every monitoring report and gate file. This keeps the bar at $25 in 2017 dollars. The 2017-dollar price is shown in the app and written by `score.py` (`price (2017 $)`, with a `price deflator` column), and `pilot_eval.py` refuses a pilot file whose rounds were scored with a different deflator, or that has no `price deflator` column (unless the analyst confirms the basis with `--deflator-confirmed`), or in which any row lacks a deflator value (rows not scored by `score.py`; the flag does not cover these). The deflator only works if the whole candidate file is scored (above); a file pre-filtered at a nominal $25 sets off the ≤ $25-share alert. If the buying lead wants a nominal $25 bar instead, `VALUE_MAX_PRICE` changes, and with it the pool and the gate population; that would be decided at step 0 too, before any pilot data. The shipped value is 1.0 (prices taken as 2017 dollars), which is correct only for the course demonstration.
- **Freeze.** As of revision 7 the Phase 6 state is **not yet committed**. The protocol code (all of `src/winevalue/` and the scripts in `deployment/`, which now hold protocol logic such as the deflator refusal), `deployment/requirements.txt` (it pins scikit-learn), the deployment documents (`README.md`, `model_card.md`, `monitoring_plan.md`), `config.PILOT_*` and `config.MONITOR_*`, the artifact and its manifest are to be committed and tagged **`wine-phase6-rev7`** before any pilot data. Setting `PRICE_DEFLATOR` at step 0 is the only later change, in its own dated commit. Rollout step 0 cites the tag and its commit hash, and the model card's version line names it. Until then, "fixed before any pilot data" rests on the run log's timestamps and SHA-1s (`reports/phase5_run_log.md`, which hashes every source and test file).

**Rollout steps:**

| Step | Who | What | Duration | Done when |
|---|---|---|---|---|
| 0. Approve | Buying lead, analyst | The prerequisites above, including the price deflator (set and committed) and the business baseline; approves the pilot (main route about $1,200–2,400 of analyst time plus a data licence; $10,000 more if the fallback is used) and the protocol, frozen at the cited tag | 2 weeks | Signed off |
| 1. Install | Analyst | Installs `deployment/requirements.txt` and runs the app and `score.py --round 0` on one test file (round 0 is never used as drift history). The loader refuses the artifact unless its manifest records a passed lockbox reproduction and its SHA-1 matches; no `band_status.json`; the test file's monitoring report shows the committed `price deflator`. The analyst also records the retailer's ≤ $25 share on the pre-tool rounds used for the business baseline: if it lies outside 35–60%, the ≤ $25-share band is re-centred on it (`monitoring.share_band`: share − 0.20 to share + 0.45, within 0.05–0.98), a pre-registered change logged with the deflator (revision 7, critic round 6 issue 9) | 1 day | The integrity check passes |
| 2. Collect | Buying team, analyst | Each round: score the whole candidate file (every candidate, at any price; the ≤ $25 test comes after the deflator) with `score.py --round N`, in one folder so the self-referenced drift rule sees the earlier rounds (by round number; a re-scored round replaces its earlier report), keep the scored file and its monitoring report, and record note sources, plus what the team sampled or listed and whether that round's samples were picked with the shortlist (`shortlist used`). Record each score's publisher (`scorer`). After round 1, check A11 (≥ 3 named sources with ≥ 15% of candidates each), and again on the first 100 scored wines; at month 6, apply the fallback rule | About 8 months under A8–A10; at most 12 (cap) | A decision point, or the cap |
| 3. Check | Analyst | Match new reviews; run `pilot_eval.py --update-status` after every 100 scored wines; review each round's drift alerts (§6.2) | Each round | Each check logged with its file |
| 4. Decide | Analyst, buying lead | Final gate and Option F decision at the decision point (≥ 400 wines and the source minimum); joint gate reported | 1 week | Decision recorded |
| 5. Run | Buying team | If the shortlist deploys: use it each round, with the monitoring of §6.2 | Ongoing | Quarterly review |

**What this deployment does not do:** show estimates to customers; score wines above $25 for the shortlist or verdict; replace tasting; compare critics or writers; retrain itself. The model card (`deployment/model_card.md`) states these limits for users.

### 6.2 Monitoring & maintenance plan
The full plan, with every threshold and action, is `deployment/monitoring_plan.md`. Its thresholds are fixed now, before any pilot data. The main problem it has to solve: a critic score, the outcome, arrives weeks or months after a wine is shortlisted. So monitoring has two layers.

**Leading checks, every buying round, no outcomes needed.** `winevalue.monitoring.round_report` runs inside `score.py` and the app's shortlist view, so every scored round gets them; the self-referenced rule below needs the earlier rounds, so it runs only in `score.py`. The alert levels live in `config.MONITOR_ALERTS`. References: notebook 6.2a, `phase6_monitoring_reference.csv`. The development column is computed on the training rows themselves, so it is in-sample for the vocabulary, P(90+) and the percentile share. The lockbox is the only out-of-sample reference.

| Input-drift indicator | Development rows | Lockbox (4 new writers) | Alert if a round is |
|---|---|---|---|
| Note words outside the model vocabulary | 0.7% | 0.9% | above 3% |
| Median note length (words) | 40 | 38 | below 20 or above 80 |
| Unmapped colour | 1.3% | 2.6% | above 5% |
| Grapes rare or unseen in training | 2.0% | 4.0% | above 8% |
| Countries unseen in training | 0% (by definition) | 0.4% | above 2% |
| Wineries unseen in training | 0% (by definition) | 27.4% | reported, no alert (the pilot gate has its own coverage rule, §6.1) |
| ≤ $25 share of candidates | 48% | 41% | below 25%, or above 95% (a file pre-filtered at $25); re-centred at rollout step 1 if the retailer's own share lies outside 35–60% |
| Mean P(90+) on ≤ $25 candidates | 0.21 | 0.32 | above 0.40, or below the limit for the round's size (0.08 in an A7 round of about 1,000 ≤ $25 candidates) |
| ≤ $25 candidates above the development 90th percentile | 17.4% in-sample (6–20% per fold out of fold) | 30.1% | above 40%, or below the limit for the round's size (3% in an A7 round); or below half its median over the previous 3 rounds (from 600 ≤ $25 candidates) |

- **Reading:** four new writers move every indicator, but only a little. Unseen grapes and unmapped colours double and mean P(90+) rises by 0.11, the 10-pp over-prediction of §5.1. Each alert level is set beyond the lockbox value (about 2× for unmapped colour and unseen grapes, over 3× for vocabulary). They are judgement calls. An alert is reviewed by the analyst; it does not stop scoring.
- **The two ranker-level alerts are two-sided since revision 3** (critic round 2 found that notes cut to 25 words lowered both indicators and set off nothing). Revision 3 put the lower limits (0.10; 5%) just below in-sample and out-of-fold *point* values, but a round varies around its pool's value: on out-of-fold development scores those limits would have fired in **30% of normal rounds from fold 1** and 9% from fold 3 (critic round 3). Revision 4 set them by a rule stated before the rates were read (`monitoring.choose_lower_limits`): score each development fold out of fold (`phase4_fold_predictions.csv.gz`), draw 500 winery-clustered rounds per fold, take each indicator's 1st percentile in the lowest fold, and round down to two decimals. Revision 5 applies the same rule at each round size, since smaller rounds vary more (critic round 4). Revision 5 had also said a round of 1,000 candidates holds about 400–480 ≤ $25 wines; that contradicts A7, which counts about 1,000 **≤ $25** candidates per round (critic round 5). Under A7 a round's file holds about 2,067 candidates at the development ≤ $25 share or 2,442 at the lockbox's, and **every monitoring simulation in revision 6 draws rounds of that size** (`monitoring.round_size`). The table (`monitoring.choose_lower_limit_table`, `config.MONITOR_RANKER_LOWER`; a notebook assertion ties the two):

  | ≤ $25 candidates in the round | 200–299 | 300–599 | 600–999 | 1,000+ |
  |---|---|---|---|---|
  | Mean P(90+) below | 0.06 | 0.07 | 0.07 | 0.08 |
  | Share above the development P90 below | 1% | 2% | 3% | 3% |

  A round uses the row for the largest size it reaches, so an A7 round uses the 1,000+ row; the smaller rows serve the first rounds of a slow pilot or a short round. Below 200 ≤ $25 candidates the two lower limits are not read; the upper limits are read at every size (revision 6).
- **A self-referenced drift rule (revision 6).** Fixed lower limits must sit below fold 1's level (6% above the P90), so they cannot see a feed fall from a higher level of its own (critic round 5): notes cut to 25 words take the lockbox from 30% to 4%, still above 3%. So the plan also compares a round with its own past: an alert when the share above the development P90 falls **below half its median over the previous 3 reference rounds** (`monitoring.relative_alerts`; `score.py` reads the earlier rounds' monitoring files by round number, `--round N`). **A round that raised this alert stays out of the reference** until the analyst checks it and sets `"accepted": true` in its report (for example after a real change in the writer mix). Without that, a fault that persists became its own reference after two rounds and the rule went quiet (critic round 6, found by running `score.py` on 3 clean rounds and 4 truncated ones); now it alerts every round until the fault is fixed or accepted (tested). The drop (0.5) and the history (3 rounds) are judgement calls, proposed with the 25- and 30-word truncations in view. It is read only from **600 ≤ $25 candidates** per round, by a rule stated before the rates were read (`monitoring.choose_relative_min_pool`: the smallest size at which it fires in at most 2% of consecutive out-of-fold rounds in every fold). It fires in up to 13% of such rounds at 200–300 ≤ $25 candidates (0–2% in folds 0 and 4, 7–13% in folds 1 and 3; an alerted round now stays out of the reference, so a false alert can repeat), at most 1.2% at 600 and none at 1,000 (`phase6_alert_rates_oof.csv`). A7 rounds qualify. It needs three earlier rounds, so it is silent in rounds 1–3, and a feed that drifts slowly over many rounds moves its own median with it.
- **False-alert rate** (notebook 6.2a): **no alert fired in any round**, the self-referenced rule included, in 500 A7-sized rounds (about 1,000 ≤ $25 candidates: 2,067 candidates drawn from the development rows, 2,442 from the lockbox; `phase6_alert_rates.csv`). On the out-of-fold rounds that set the limits, ranker alerts fire in at most 1.4% of rounds per fold and size, and in none at 1,000 ≤ $25 candidates (`phase6_alert_rates_oof.csv`); that is low by construction, since those rounds set the limits. Two checks the rule did not see: on a **fresh seed**, at most 2.4% (fold 1, rounds of 300–599) and 0.2% at 1,000; and with **each fold left out of the rule** (limits from the other three, rounds of 400), the left-out fold alerts in 0–0.2% of rounds (`phase6_alert_limits_lofo.csv`). So on data like the training data or like these four new writers, an alert costs little.
- **What that also means: the alerts would not have flagged the lockbox.** Its writer shift raised the share above the development P90 from 10% to 30% and mean P(90+) by 0.11, but both stay below their upper limits (40%, 0.40). A writer's level, which is what hurt the band, is caught by the outcome checks below and by the band's stop rule, not by input drift. Tighter limits would have been chosen on the lockbox after seeing it, so they stay as set.
- **Detection of broken feeds** (notebook 6.2a, `phase6_alert_detection.csv`; the lockbox pool altered on purpose, then 200 simulated A7 rounds of 2,442 candidates each, about 1,000 of them ≤ $25; share of rounds in which any alert fires; the self-referenced rule's history is three rounds of the unaltered feed, so the fault starts in round 4):

  | Broken feed | Caught | Of which, self-referenced rule | Alert that fires | Pool value that moves |
  |---|---|---|---|---|
  | Notes cut to 40 words (revision 7) | **0%** | 0% | none | share above P90 30% → 26% (ratio 0.85) |
  | Notes cut to 35 words (revision 7) | **0%** | 0% | none | 30% → 20% (ratio 0.65), P(90+) 0.32 → 0.25 |
  | Notes cut to 30 words | **100%** (revision 5: 0%) | 100% | self-referenced drop | share above P90 30% → 11%, P(90+) 0.32 → 0.19 |
  | Notes cut to 25 words | **100%** (revision 5: 0.5%) | 100% | self-referenced drop; fixed lower limit in 1.5% | 30% → 4.1% (fixed limit 3%) |
  | Notes cut to 15 words | 100% | 100% | note length, both ranker levels, self-referenced drop | median 15 words |
  | 2% of note words unknown | **1.5%** | 0% | vocabulary | 0.9% → 2.9% (limit 3%) |
  | 5% or 20% of note words unknown | 100% | 0% | vocabulary | 5.9%, 21% |
  | Prices × 1.1 | **0%** | 0% | none | ≤ $25 share 41% → 32% |
  | Prices × 1.3 | 99% | 0% | ≤ $25 share | 23% |
  | Prices × 1.5 | 100% | 0% | ≤ $25 share | 15% |
  | 10% of grapes unlisted | 100% | 0% | unmapped colour, rare grapes | 12%, 14% |
  | Countries upper-case, US written USA (a check, not a fault) | 0% | 0% | none | none: every indicator identical to the unaltered pool |
  | 5% of countries unrecognised | 100% | 0% | countries unseen in training | 0.4% → 5.3% |
  | A promotional sentence on every note | 100% | 0% | both ranker levels, high | share above P90 89%, P(90+) 0.76 |
  | File pre-filtered at $25 (only ≤ $25 wines sent; revision 6) | 100% | 0% | ≤ $25 share, high | 41% → 100% |

  - **Caught:** gross failures (heavy truncation, a feed partly in another language, a lost grape list, a large price shift, unrecognised countries, boilerplate added to every note, a pre-filtered file) and, with the self-referenced rule, truncations that halve the feed's own share above the P90 (30 and 25 words), which the fixed limits miss.
  - **Missed:** milder truncation (35 or 40 words cut the share above the P90 by a third or less, and the rule needs about half: these two rows were added in revision 7 because the 25- and 30-word rows had been in view when the rule was proposed, so they were not an independent test); 2% unknown words (the vocabulary share sits just under its 3% limit); and a 10% price rise, which drops nine points of the ≤ $25 share. **The fixed lower limits still trade sensitivity for few false alerts**; the self-referenced rule covers truncation only for a feed that starts healthy, in rounds of 600+ ≤ $25 candidates, from round 4. These faults move the shortlist's inputs, so the outcome checks are still needed. The analyst also sees each round's indicator values in the monitoring JSON, not just the alerts.
  - **The base matters.** The faults are applied to the lockbox, the highest-level reference (30% above the development P90). On a feed at fold 1's level (6%), the fixed lower limit trips sooner; the self-referenced rule is relative, so it reads a halving the same way at any level, provided the round is large enough.
  - The case-and-alias row checks that the input mapping works on a whole pool: country spellings that differ only in case or alias reach the models as the training spelling, so nothing moves. Re-execution 7 found one gap here (an unseen country in another case no longer matched its province); the province = country rule now ignores case, and the row shows no change. Notebook 6.1d checks the same for all five name columns on the whole ≤ $25 pool.
  - These are synthetic faults, chosen before the run; real feed failures may look different.
- **Data-quality checks.** A file without a note, `country`, `variety` or `price` column is refused, with the missing columns named. Per row, `score.py` and the app flag a note under 10 words, a missing price, a duplicate or near-duplicate (DM5, Jaccard ≥ 0.5) of another candidate in the same round, and a note from which a score or price was stripped. They also count the flags per round. Near-duplicates of already-reviewed wines are flagged in the one-wine view's similar-wines list, not in the batch.

**Lagging checks, as scores arrive.** During the pilot these are exactly the pilot protocol of §6.1. After deployment, the same rules run each quarter on the latest 400 scored ≤ $25 wines:
- the shortlist lift below 1.3× triggers a review, and below 1.0 stops the shortlist;
- a band below its bar, or a stop-rule firing, hides the band.

As in the pilot, those wines must be every logged candidate that later received a review, whether or not it was shortlisted. So every round's full scored file is kept; otherwise the lift cannot be measured.

**Business outcome, each quarter** (owner: the buying lead; `monitoring.business_kpi`). The checks above compare the shortlist with simple rules; BO1 is about fewer wasted samples. So each quarter, among the wines the team sampled that later received a WineEnthusiast score, the plan reports the share scoring 90+ and the samples spent per value wine found. It compares them with the same figures for the rounds before the tool, from the same review feed (picking at random finds about 18 value wines per 100 samples, §1.1). A quarter below the baseline is raised at the quarterly review, and two in a row trigger the new-version review. Like every outcome here it counts only reviewed wines, and it is a reported measure, not a gate.

**Maintenance:**
- **No automatic retraining.** The current model's only clean test is the lockbox. A refit on new data is a new model, and it has to earn its place the same way: the frozen procedure (`production.build`), a holdout of post-2017 reviews by critics not in the training data (option E), the same pre-registered gate, and a logged replacement that keeps the old artifact.
- **When to consider a new version:** a lagging check fails; the same drift alert fires in two rounds in a row; after the pilot, CPI-U moves more than 10% from the pilot's deflator base (the deflator is then re-set in a logged change); or the annual review.
- **Candidates already known:** the per-source intercept, if the pilot's secondary analysis supports it; the no-origin stack or plain ridge, which did better on the lockbox but can't be chosen on it (option C).
- **Operations:** response time is shown per query (BSC4 limit 3 s). The artifact's manifest, reproduction record and SHA-1 are checked at every start. A library upgrade requires a rebuild with `deployment/build_artifact.py`, which saves only after the reproduction check.

### 6.3 Final report & final presentation
- **Final report:** this document. Each phase's section carries its revision history and critic rounds; the order of events after unsealing is in `reports/phase5_run_log.md`.
- **Final presentation:** `reports/final_presentation.md` is a **slide outline**: 12 slides for the buying lead and the analytics manager, with content and speaker notes. Every number on it is taken from this report, and each slide names its section. Its order: the question, how the test was kept honest, the data, the shortlist result, the fragile band, other findings, the option F decision, the tool, the guard rails, monitoring, lessons. Slide 9 uses the app screenshot in `reports/figures/phase6_app_one_wine.png`.
- **For a wider audience:** a Medium article and a walkthrough video (both kept outside the repo). Both tell the story of this report.

### 6.4 Experience documentation (lessons learned)
**What worked:**
- **Freezing before looking.** The lockbox was sealed in code, every target was registered first, the models were frozen in a commit and tag before unsealing, and the lockbox was scored once. Twelve complete later re-executions reproduced every first-run table byte for byte, and the deployed artifact reproduces every lockbox prediction exactly. Because of that, the post-hoc analyses can be read for what they are.
- **Splitting by critic.** A random split would have hidden the main risk: on a title-grouped split the baseline beats the global mean by about 8%, on the critic split by about 1% (§1.2). The shortlist's result held for four unseen writers; the band's did not hold for all of them.
- **Note-blind rules as the yardstick.** Comparing the shortlist with the best of a frozen set of simple rules, rather than with chance, made a 1.95× result meaningful, and gave the pilot a bar that new note sources can't game.
- **One code path, once it really was one.** The notebook, the app, the scripts and the simulations call the same `src/` functions, with tests. In revision 1 they did not quite: the tool hid the band with its own matching code, which ignored the pooled unit and missed a straight apostrophe, so the simulated guard rails were not the ones buyers would get (critic round 1). Now one function (`pilot.band_hidden`) does it everywhere, and a test proves the tool and the protocol hide the same wines. Revision 2 still matched names only inside that function, while the source minimum counted names as typed (critic round 2). In revision 3 names get one spelling when pilot rows come in (`pilot.canonical_names`), so every count and lookup sees the same units; a test checks a misspelt pilot against the clean one. Round 3 then found the same gap one layer down: the labels were canonical but the model inputs were not, so "italy" was scored as an unseen country, and a blank source counted as a source. Round 4 found it once more, in the one name column left raw: the winery, which feeds the shortlist gate's strongest comparator, so a retailer's spelling could make the gate more lenient. The lesson took four rounds to learn fully: *normalise every name column at the single entry point, before anything reads it, list which consumers read each column, and test each consumer against ground truth* (now a pool-wide assertion in notebook 6.1d). Each fix needs the same test: revision 6 matched accent variants of a winery within its country only, and the assertion stopped re-execution 10 because a case variant no longer scored as its exact spelling, which the frozen winery rule reads by name alone.
- **A strict integrity check pays for itself.** The first check accepted a reproduction record if the values it had were small; a missing or NaN entry slipped through. Requiring all four outputs, finite and ≤ 1e-8, at once exposed a real gap: the deployed ranker gives no score to the 1,097 lockbox wines without a price, which Phase 5 had scored with an imputed price. None is a ≤ $25 candidate, so no result moves, but the old check had hidden it.

**What went wrong, and what I would do differently:**
- **Forking paths in Phase 4.** DM1 was chosen twice, and the rewritten rule did worse on the lockbox than the first (31.5% against 34.0%; under masking +2.7 pp against +6.7 pp). *Next time:* write the selection rule once, before the first full outer run, and treat every later idea as a sensitivity.
- **The gate was joint when the objectives were separate.** The pre-registered pilot gate made the shortlist wait on the band. Splitting it (option F) was justified on grounds that don't depend on the lockbox, but it was still an amendment made after unsealing. *Next time:* one gate per business objective from Phase 1.
- **Whole-pool targets hid a failing segment.** Italy, all one writer, gained only +1.4 pp inside a passing pool. *Next time:* pre-register a floor per large segment (region, writer), not just a pooled target.
- **The writer's level was the biggest error source, and it was known early.** Phase 4 measured it (an oracle level would lift P@100 from 0.68 to 0.74 on fold 3), but the pooled calibration was frozen anyway. *Next time:* plan writer-level calibration and a way to test it before Phase 5.
- **The proxy for the real input came late.** Masking verdict words was the only stand-in for retailer notes, and it was a sensitivity, not a target, for the band. It turned out to decide the band's fate. *Next time:* make the deployment-input proxy a pre-registered target.
- **Hypotheses written as pooled contrasts.** H5 ("whites are better value") passed twice as written, and twice turned out to be a writer-mix effect. *Next time:* write such hypotheses within writer.
- **Deployment details found only in Phase 6:**
  - the LSH index can't find similar wines for a new note;
  - the value verdict was never defined;
  - the §5.3 pause rule would have stopped working shortlists;
  - the protocol's decision at first ignored its own pause and source minimum;
  - the pilot wines have to be chosen without the model;
  - the shortlist tiers were calibrated on development writers and were 3× too generous for new ones;
  - nothing yet said where the outcome scores would come from, or how long the pilot would take;
  - the drift alerts were one-sided, so a feed that lowered the ranker's level (truncated notes) went unnoticed; their first lower limits were then set against in-sample reference values and would have fired in 30% of normal rounds from one development fold; revision 4 calibrated them on one round size and revision 5 on a round size that contradicted A7's (rounds 4 and 5), and fixed limits set at the lowest fold's level could not see a feed fall from its own level, which needed a self-referenced rule (revision 6);
  - a "buying round" was defined in two ways (≤ $25 candidates in A7, all candidates in the monitoring text), so the schedule, the price check and the alert limits each assumed a different file (round 5);
  - the price basis (2017 dollars) was never connected to a pilot that runs years later.
  
  *Next time:* build a throwaway end-to-end prototype in Phase 1 and simulate the pilot protocol in Phase 5, before its rules are written into the report.
- **Simulation size was not planned.** The first Phase 6 protocol run used 100 pilots per pool, and its shortlist pass rates sat 0.07–0.13 below Phase 5's 200-pilot rates for the same folds. Re-running Phase 5's simulation over three seeds showed pass rates moving by up to 0.10 (§6.1), and the pause threshold sat exactly on its 5% line with 200 simulations but at 2.9% with 1,000. *Next time:* fix the number of simulations from a target SE before reading any rate against a threshold.

**On the review process.** The critic rounds were run by Claude agents with a fixed reviewer persona (`critiques/critic_prompt.md`), at least two per phase, until no MAJOR issues remained. They found real problems: selective reporting and a filter chosen on the lockbox (Phase 5 round 1), a stop rule with no unit or sample size (round 2), three pilot details Phase 6 had to settle (round 3), and, in Phase 6, guard rails that existed in the simulator but not in the tool. They are not domain experts or buyers: they check the analysis, not the business value. The pilot is what checks that.

**Time and cost.** One full notebook run takes about 90–100 minutes on a laptop CPU, mostly the critic-held-out refits. Every logged re-execution paid that cost again, including one stopped by an assertion after 98 minutes and one whose only fault was a slow lookup (BSC4 timing, re-execution 11); caching the fold models would have saved hours, and running all the Phase 6 cells alone against the saved artifact before each full run would have caught both in minutes.

---

## References
- Chapman, P. et al. (2000). *CRISP-DM 1.0: Step-by-step data mining guide.* SPSS.
- Schröer, C., Kruse, F., & Marx Gómez, J. (2021). A systematic literature review on applying CRISP-DM process model. *Procedia Computer Science*, 181, 526–534.
- IBM. *CRISP-DM help overview*, IBM SPSS Modeler documentation.
- Thoutt, Z. (2017). *Wine Reviews* [dataset]. Kaggle. https://www.kaggle.com/datasets/zynicide/wine-reviews (data from WineEnthusiast, winemag.com).
