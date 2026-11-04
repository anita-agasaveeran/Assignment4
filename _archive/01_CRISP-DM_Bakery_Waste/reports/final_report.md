# Reducing Bakery Over-Production with CRISP-DM: Final Report

*CMPE 255 · Assignment 4 · Project 1 · Author: Anita Agasaveeran*

> Status: **scaffold**. Each section gets filled in as its phase is finished and passes critic review. Every number here must come from a cell in `notebooks/CRISP_DM_Bakery_Waste.ipynb`.

## Executive summary
_TODO: the problem, the approach, headline results against the success criteria, and the recommendation (≤ 200 words)._

---

## 1. Business Understanding

> **Revision 2**, after critic round 1 (5/10; `critiques/phase1_business_understanding_round1.md`). The first draft measured waste against the recorded `Units_Produced` field. The critic showed, and I confirmed, that this field is generated per order line as *ordered quantity + at least 1*, so it isn't a production decision. Phase 1 was reframed around a decision the data can support. Every figure below comes from notebook §1, saved with its outputs. Prices are in Indian rupees (₹).

### 1.1 Determine business objectives

#### Background
The client is a three-store bakery chain (ST01–ST03) selling 35 products:
- **22 fresh products** (median shelf life ≤ 7 days): cakes, pastries, bread, buns, milk, paneer, cold coffee and juice. Unsold units are thrown away.
- **13 long-life products** (median shelf life ≥ 30 days): biscuits, rusk, honey, jam, tea powder, butter, cheese. Assumed to sell later (A6).

The cut-off is clear-cut: the largest fresh median is 5 days and the smallest long-life median is 30.

| 2023–2024 | Fresh (22) | Long-life (13) |
|---|---|---|
| Order lines | 12,124 | 7,197 |
| Units ordered (`Quantity`) | 25,432 | 17,595 |
| Revenue | ₹1,661,467 (62%) | ₹1,029,340 (38%) |
| Reported profit | ₹674,567 | ₹469,171 |

The chain is small: **9.0 orders a day across all three stores**, and 34.8 fresh units a day in total.

Management's question: *"Our fresh range doesn't seem to make money once you count what we throw away. Should we keep baking all of it every day, and if so, how much?"*

**What the recorded fields can and can't tell us (risk R1).**
- **Demand is reliable.** `Total_Bill = Selling_Price × Quantity` and `Profit = (Selling_Price − Cost_Price) × Quantity` hold on 100% of rows. Note that reported profit therefore never includes the cost of waste.
- **The production and unsold fields are not.** `Units_Produced − Quantity ≥ 1` on 100% of rows, and `Unsold_Units = 1` on 91.8%. Production is logged per order line as the order plus at least one unit. There is no production on days without orders, and no stockout is ever recorded.

The answer to management's question then depends on how you read those fields:

| Reading of the recorded fields | Demand | Waste | Fresh profit after waste (2 yrs) |
|---|---|---|---|
| Mixed (the round-1 draft) | `Quantity` | `Unsold_Units` | −₹24,053 |
| Consistent with `Quantity` | `Quantity` | `Units_Produced − Quantity` | −₹304,929 |
| Consistent with `Units_Sold` | `Units_Sold` | `Unsold_Units` | +₹161,826 |

The recorded fields are a byproduct of how the data was generated, not a production log. **This project doesn't use them as a baseline.** It uses only `Quantity` and simulates the bake decision explicitly with `bakery.policy.simulate_plan`.

**Sizing the problem with simple rules.** Assumed current practice (A0) is that every fresh product is baked ahead daily at every store, in quantities set from recent sales. This is proxied by the rule *bake = ⌈k × trailing 28-day mean demand⌉*. That rule, and the alternatives below, are priced on two out-of-sample festive quarters. Each rule's k and the unit economics are fit only on data before the quarter (Q4 2023: fit on Jan–Sep 2023; Q4 2024: fit on Jan 2023–Jun 2024).

| Plan (fresh products, product × day) | Per store, Q4 2023 | Per store, Q4 2024 | Chain-pooled, Q4 2023 | Chain-pooled, Q4 2024 |
|---|---|---|---|---|
| Rule fit to ~90% fill | fill 93%, 89% of baked wasted, **−₹1,056,582** | fill 90%, 88% wasted, **−₹873,029** | fill 91%, 74% wasted, **−₹290,047** | fill 88%, 72% wasted, **−₹250,485** |
| Profit-maximising rule | k = 0 (bake nothing): ₹0 | k = 0: ₹0 | k = 0: ₹0 | k = 0: ₹0 |
| Make-to-order, 50% / 70% / 90% of demand retained | ₹46,804 / ₹65,525 / ₹84,246 | ₹44,996 / ₹62,995 / ₹80,994 | same as per store | same as per store |
| Perfect-foresight ceiling | ₹93,607 | ₹89,993 | ₹93,607 | ₹89,993 |

**Why:**
- Demand at the level a baker decides is very intermittent. Per store, only **21.6%** of product-days have any demand (mean 0.53 units/day; 2.44 when non-zero). Pooled across the chain it's 49.5% (mean 1.58).
- A unit baked ahead pays off only if the chance it sells is above 1 − critical ratio, which is **0.52–0.73** across categories (see 1.2). An average product-day rarely clears that bar.

**What this means:**
1. Baking ahead everything at high service loses heavily.
2. The best *simple* rule is to bake nothing.
3. Make-to-order earns its retention share of the ceiling, but that share is unknown and depends on the product.
4. **The value at stake is about ₹90k per quarter**: the gap between the best simple plan and the perfect-foresight ceiling.

A forecasting model can add value only by spotting the specific product × day combinations (weekends, festivals, popular items) where baking ahead pays off, and by deciding which products are worth offering for pre-order.

#### Business objectives
- **BO1, fulfilment mode:** decide, for each of the 22 fresh products, whether to **bake ahead**, **make to order / pre-order**, or run a **hybrid** (small display stock + pre-orders).
- **BO2, quantities:** set daily per-store (or central) quantities for bake-ahead and hybrid products that maximise net contribution.
- **BO3, profit:** raise fresh **net contribution** (margin on units sold − cost of discarded units) above the best simple alternative.
- **BO4, service:** keep peak days (weekends, festivals) from turning into frequent sell-outs.
- **BO5, demand shaping:** use cross-selling and customer segments to support pre-ordering and fresh bundles.

**Not in scope:** pricing, staffing, long-life replenishment, opening or closing stores.

#### Business success criteria
- **Evaluation:** two out-of-sample festive quarters (**Q4 2023 and Q4 2024**, rolling origin), all scored with the same simulator (demand = `Quantity`).
- **Reference plan:** for each product, the best simple alternative among bake-nothing, the profit-maximising trailing-mean rule and make-to-order, under the same A7 pre-order assumptions.

| ID | Criterion | Target |
|---|---|---|
| BSC1 | Net contribution of the recommended plan vs the reference plan | Higher by **≥ 5 pp of the perfect-foresight ceiling** (≈ ₹4.5k/quarter) in **both** quarters. The 95% block-bootstrap CI (resampling days) of the difference must exclude 0 |
| BSC2 | Waste on bake-ahead products at a matched fill rate | ≥ 20% fewer wasted units than the trailing-mean rule at the same fill rate |
| BSC3 | Peak-day service | Weekend and festival-day fill rate no more than 5 pp below other days. The contribution-vs-fill trade-off is reported at 50/70/90% fill for management to choose from |
| BSC4 | Usability | A store manager sees tomorrow's mode and quantity for every fresh product on one screen, with the reason (shown in the app) |
| BSC5 | Demand-shaping insight | ≥ 3 recommendations (bundles, pre-order targeting), each backed by statistics that hold in **both** 2023 and 2024 |

**Not a criterion:** comparison with the recorded `Units_Produced`. It would compare against a plan that knew each order in advance. If the recorded figures are mentioned at all, they're reported as context, with the caveat above.

### 1.2 Assess situation

#### Inventory of resources
| Type | Resource |
|---|---|
| Data | One extract: 19,321 order lines × 40 columns, 2023–2024, 3 stores (`data/README.md`). Kaggle source not yet confirmed (R7). No production log, inventory system, pre-order history or weather feed |
| People | One analyst (the author). **No access to the bakery**, so business parameters (A0, A3, A7) are explicit analyst assumptions and are sensitivity-tested. Reviewers: course instructor and an independent critic |
| Compute / software | Laptop + Google Colab. Python 3.12, pandas, scikit-learn, LightGBM, statsmodels, mlxtend, datasketch, Streamlit (all open source) |

#### Requirements
- **R-1, information available the evening before:** calendar, the public festival calendar, and sales history up to the previous day.
  - **Excluded as model inputs:** `Promotion_Applied`, which varies *within* a store-day on 39.7% of store-days, so it's a per-transaction attribute and not a planned promotion. Also excluded: the on-the-day fields `Units_Sold`, `Unsold_Units`, `Stock_Available` and `Waste_Pct`.
- **R-2, weather:** `Weather` and `Temperature` are the *actual* weather, identical across stores for each date. The primary model excludes them. A with-weather model is reported only as an upper bound.
- **R-3, reproducibility:** fixed seeds, versioned code, and a notebook that runs top to bottom in Colab, saved with outputs.
- **R-4, privacy:** customer data is used only in aggregate (segments).

#### Assumptions
| # | Assumption | Testable? | Handling |
|---|---|---|---|
| A0 | Current practice: every fresh product is baked ahead daily per store, from recent sales | No (no production log) | Proxied by the trailing-mean rule. Recorded fields not used |
| A1 | Demand = `Quantity` | Partly. Bills and profit are computed from it, but `Units_Sold > Quantity` on 26.7% of rows | **Decision gate in Phase 2.4:** if `Units_Sold` proves to be meaningful demand, the §1 figures are recomputed (BSC targets, sizing table, benefits) |
| A2 | Recorded sales are uncensored demand | **No.** Transaction data can't show customers who found an empty shelf | Stated as a limitation. In the simulator, unmet demand is explicit |
| A3 | Unsold fresh units are discarded (salvage = 0) | No | `config.SALVAGE_VALUE`; sensitivity-tested |
| A5 | 2023–2024 represents the near future; festivals recur | Partly | Rolling-origin evaluation over two quarters |
| A6 | Unsold long-life units sell later, so they aren't waste | No | Long-life products out of scope |
| A7 | **Pre-order retention:** the share of a product's demand kept if it's only made to order | No (no pre-order history) | Scenarios: cakes 50/70/90%, other fresh 0/20/40%. Recommendations must hold in every scenario, or be flagged for a pre-order pilot |

#### Constraints
- A single static extract; no new data collection.
- No stakeholder interviews.
- One analyst, the academic timeline in 1.4, and free compute.

#### Risks & contingencies
| # | Risk | Likelihood | Impact | Contingency |
|---|---|---|---|---|
| R1 | Recorded production/unsold fields are generated per order line, not real production | **Confirmed** | High | Not used. Bake decision simulated from `Quantity` only |
| R2 | Dataset looks **synthetic** (34 of 35 products have varying shelf life; segment mean ratings range only 3.82–3.84) | High | Medium | Benchmark every pattern against naive baselines. Report unsupported patterns. Present results as a method demonstration |
| R3 | **Very intermittent demand:** 21.6% of store × product × days have any sales | Confirmed | High | Intermittent-demand methods (Croston/TSB, zero-inflated / Poisson). Pooled vs per-store comparison. Category forecast + product disaggregation as a fallback |
| R4 | **Leakage** from fields recorded on the day | Medium | High | R-1/R-2 exclusions; leakage audit in Phase 3 |
| R5 | Each festival appears only twice | Confirmed | Medium | Festival and days-to-festival features rather than date effects. Evaluate on both Q4s |
| R6 | One test quarter could be luck | Medium | Medium | Two rolling-origin quarters + block-bootstrap CIs (BSC1) |
| R7 | Dataset provenance (source, licence) not confirmed | Open | Low | Confirm the Kaggle URL before publishing |
| R8 | The A7 retention assumptions drive the mode decision | High | High | Recommend only modes that hold across all A7 scenarios; otherwise "pilot pre-orders first" |
| R9 | The Jul–Sep 2024 validation window has no Q4 festivals | Confirmed | Medium | Tune on rolling origins that include Q4 2023 |

#### Terminology
| Term | Meaning |
|---|---|
| Fresh / long-life product | Median shelf life ≤ 7 days / ≥ 30 days |
| Demand | `Quantity`: units ordered and paid for |
| Bake-ahead / make-to-order / hybrid | Stock produced before the day / produced only against a pre-order / small stock + pre-orders for the rest |
| Retention (A7) | Share of a product's demand kept under make-to-order |
| Waste | Units baked ahead and not sold that day |
| Fill rate | Units sold (from stock + pre-order) ÷ demand |
| Net contribution | Margin on units sold − cost of discarded units |
| Perfect-foresight ceiling | Net contribution if exactly the demand were baked |
| Critical ratio | Cu / (Cu + Co) = unit margin ÷ unit price. Baking one more unit pays off if P(demand ≥ that unit) exceeds 1 − critical ratio |
| Pinball loss | Loss function used to score quantile forecasts |
| WAPE | Σ\|actual − forecast\| ÷ Σ actual |
| Croston / TSB | Forecasting methods for intermittent (mostly-zero) demand |
| Support / confidence / lift | Share of orders containing an itemset / P(B \| A) / confidence ÷ P(B) |
| RFM | Recency, frequency, monetary value of a customer |

#### Costs & benefits
Unit economics are fit on training data only (Jan 2023 – Jun 2024):
- **Co** (cost of waste) = average unit cost
- **Cu** (cost of a stockout) = average unit margin

| Fresh category | Avg unit margin | Avg unit cost | Critical ratio Cu/(Cu+Co) | Bake a unit only if P(it sells) > |
|---|---|---|---|---|
| Dairy (Milk, Paneer) | ₹10.22 | ₹28.17 | 0.27 | 0.73 |
| Cakes | ₹124.15 | ₹202.50 | 0.38 | 0.62 |
| Bread & Daily | ₹10.10 | ₹12.65 | 0.44 | 0.56 |
| Beverages (Cold Coffee, Juice) | ₹28.36 | ₹34.07 | 0.45 | 0.55 |
| Savoury Bakery | ₹11.36 | ₹12.48 | 0.48 | 0.52 |
| Pastry & Sweet | ₹19.94 | ₹21.39 | 0.48 | 0.52 |

*(Averages are weighted by quantity. Critical ratio = ratio of the average margin to the average price.)*

**Benefits (conditional estimates, not forecasts; they depend on A0 and A7):**
- **Value at stake:** about ₹90k per quarter between the best simple plan and the perfect-foresight ceiling.
- **Choosing the right mode per product:** compared with the assumed current practice (A0, baking ahead at about 90% fill), this alone is worth ₹0.25M–₹1.06M per quarter in avoided losses. That gain comes from changing policy, not from data mining.
- **The data mining contribution** is whatever the recommended plan earns above the best simple plan. BSC1 measures exactly that, with a floor of about ₹4.5k per quarter.

**Costs:**
- About 60–80 analyst-hours for this project (≈ ₹60–80k at an assumed ₹1,000/hour). Open-source software; free hosting on Streamlit Community Cloud.
- Running costs: a monthly retraining check (Phase 6).
- A pre-order pilot to measure A7 is recommended before full roll-out.

### 1.3 Determine data mining goals
| ID | Data mining goal | Technique | Data mining success criterion | Supports |
|---|---|---|---|---|
| DM1 | **Forecast the next-day demand distribution** per fresh product × store (and pooled): quantiles 0.5/0.6/0.7/0.8/0.9 and P(demand ≥ 1) | Baselines: seasonal-naive, trailing mean, Croston/TSB. Models: Poisson / zero-inflated GLM, LightGBM (Tweedie, quantile) | Mean pinball loss ≥ 10% below the best baseline in both test quarters. Empirical coverage of the 0.7/0.8/0.9 quantiles within ±5 pp. Brier score for P(demand ≥ 1) below the baseline's | BO1–BO4 |
| DM2 | **Choose the mode and bake quantity** per product × day: bake at the critical-ratio quantile, make-to-order for the rest; mode chosen per product from validation contribution across the A7 scenarios | Newsvendor policy + scenario analysis, tuned on rolling origins | Meets BSC1–BSC3 | BO1–BO4 |
| DM3 | **Bundles:** products bought together | FP-Growth association rules | ≥ 5 rules with support ≥ 1% of orders and lift ≥ 1.5 in **both** 2023 and 2024; ≥ 2 with a fresh product as the consequent | BO5, BSC5 |
| DM4 | **Customer segments for pre-order targeting** | k-means / hierarchical clustering on RFM + fresh/cake share + festival buying | 3–6 segments, silhouette ≥ 0.25, ARI ≥ 0.8 across 10 seeds, each ≥ 5% of customers, and ≥ 1 segment with a cake share ≥ 1.5× the average | BO5, BSC5 |
| DM5 (appendix) | **Scalable "customers like you" lookup** (course LSH topic) | MinHash LSH on baskets | Recall@10 ≥ 0.9 vs exact Jaccard. A scalability demo only: with 500 customers exact search is trivial, so there's no business criterion | Course requirement |

**Outlier analysis** from the course template is a supporting step in Phase 3: unusually large orders and festival spikes are checked and handled before modeling.

### 1.4 Produce project plan
Dates assume work started 2026-11-03. **The assignment due date still needs confirming**, and the dates will be adjusted to fit it.

| Phase | Planned dates | Effort | Inputs → outputs | Milestone / go-no-go |
|---|---|---|---|---|
| 1 Business Understanding | Nov 3–4 | 10% | Raw data, course material → §1 | Critic: no major issues |
| 2 Data Understanding | Nov 4–6 | 20% | §1 → data reports; **A1 decision gate** | If A1 fails, revise §1 figures |
| 3 Data Preparation | Nov 6–9 | 25% | §2 → demand grids, features, RFM, baskets; leakage audit | Leakage audit passes |
| 4 Modeling | Nov 9–12 | 20% | §3 → DM1–DM5 | DM criteria met, or loop back to 3 |
| 5 Evaluation | Nov 12–13 | 10% | §4 → BSC1–BSC5 backtest | Go/no-go |
| 6 Deployment | Nov 13–16 | 15% | §5 → app, monitoring, report, article, video script | Final critic review |

**Resources:** one analyst for every phase, plus an independent critic review (≥ 2 rounds) at the end of each.

**Initial assessment of tools & techniques:**
- **pandas / scikit-learn / statsmodels:** baselines, Poisson and zero-inflated GLMs, clustering, metrics.
- **Croston/TSB:** short custom implementations, suited to mostly-zero demand.
- **LightGBM:** Tweedie and quantile objectives for sparse counts.
- **mlxtend:** FP-Growth.
- **datasketch:** MinHash LSH.
- **Streamlit:** a quick way to put a usable tool in front of staff.
- **IBM SPSS Modeler** (suggested in the assignment) was considered. It has a built-in CRISP-DM project view, but it needs a licence and can't be shared as a runnable notebook, so the CRISP-DM structure is followed in the notebook and this report instead.

## 2. Data Understanding
### 2.1 Initial data collection report
### 2.2 Data description report
### 2.3 Data exploration report
### 2.4 Data quality report

## 3. Data Preparation
### 3.1 Rationale for inclusion / exclusion
### 3.2 Data cleaning report (incl. outlier analysis)
### 3.3 Derived attributes & generated records
### 3.4 Merged data
### 3.5 Formatted dataset & dataset description

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
- Dataset: _TODO Kaggle citation_
