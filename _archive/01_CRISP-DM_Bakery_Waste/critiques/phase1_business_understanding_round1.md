# Phase 1 · Business Understanding: Critic Round 1

- **Date:** 2026-11-03
- **Reviewer:** Claude critic (independent subagent session), persona from `critic_prompt.md`. Read-only access to the report, notebook, src and raw data. It re-computed the figures itself.
- **Draft reviewed:** `reports/final_report.md` §1 (first draft) and notebook Phase 1 cells

## Score: 5 / 10

The structure is good: every Phase 1 output has a heading, and most figures reproduce exactly. The weakness is rigor. The business case and success criteria rest on a baseline the data shows is an artifact, and the definitions of demand and waste switch between sections.

## Task coverage
| CRISP-DM task / output | Status | Note |
|---|---|---|
| 1.1 Background | Present | Headline figures mix two waste definitions |
| 1.1 Business objectives | Present | BO1 is per item; the DM goals work per category |
| 1.1 Business success criteria | Partial | The baseline is order-conditioned; BSC1 has no size or CI; peak days aren't protected |
| 1.2 Inventory of resources | Partial | Data provenance is TODO; no named stakeholder |
| 1.2 Requirements, assumptions & constraints | Partial | A1/A2 evidence doesn't prove what it claims; R-1 lets in a leaky field |
| 1.2 Risks & contingencies | Partial | Missing: order-conditioned baseline, single-quarter variance, validation period with no festivals |
| 1.2 Terminology | Present | "Waste" doesn't match the field behind the headlines |
| 1.2 Costs & benefits | Partial | Inherits the definition problem; critical ratio mislabelled; costs not quantified |
| 1.3 Data mining goals | Present | Category grain contradicts the R3 contingency |
| 1.3 DM success criteria | Partial | Quantiles not named; DM3 already met by raw data; DM5 measures approximation, not value |
| 1.4 Project plan | Partial | No durations, dates or milestones |
| 1.4 Tools & techniques | Present | No intermittent-demand methods considered |

## Issues raised
| # | Severity | Issue | Suggested fix |
|---|---|---|---|
| 1 | MAJOR | **The recorded baseline is not a real production decision.** `Units_Produced − Quantity ≥ 1` and `Unsold_Units ≥ 1` on 100% of rows, with exactly 1 unsold on 91.8%. Production only exists where an order exists. The baseline is "foresight + 1 unit per order" with a 100% fill rate, which no evening-before forecast can match | Define a realistic ex-ante baseline (e.g. a trailing-mean rule set to the same fill rate). Report the recorded comparison only as secondary |
| 2 | MAJOR | **Headline economics mix definitions.** Margin is on `Quantity`, waste is on `Unsold_Units`. Fresh profit after waste is −₹24k (mixed), −₹305k (waste = produced − ordered) or +₹162k (demand = `Units_Sold`) | One primary definition consistent with A1, plus a sensitivity table |
| 3 | MAJOR | **A2's evidence is circular.** `Produced ≥ Quantity` holds by construction. Baseline fill rate is 100%, so BSC3 allows worse service than today without saying so | Restate A2 as untestable. State the 100% baseline fill rate and the trade-off |
| 4 | MAJOR | **A1 is asserted before R1 is resolved.** The bill/profit identities show what was billed, not what was demanded | Make A1 conditional, with a Phase 2.4 decision gate |
| 5 | MAJOR | **The decision grain doesn't match the decision.** Bakers bake products, not categories. Product level: 21.6% of cells non-zero, mean 2.44 | Make the decision unit store × product × day, or give a disaggregation rule |
| 6 | MAJOR | **The success criteria can't show the model adds value or that results are real.** No comparison of the BSCs with a simple rule; BSC1 has no size; single test quarter, no CI | Add "beats a non-ML rule at equal fill rate", a size, a bootstrap CI and rolling origins incl. Q4 2023 |
| 7 | MAJOR | **Leakage in a requirement.** `Promotion_Applied` varies within store-day on 39.7% of store-days, so it isn't a planned promotion. `Weather` is actual weather, the same across stores per date | Remove promotions from R-1. Make the no-weather model primary |
| 8 | MINOR | The critical ratio 0.41 is revenue-weighted, not quantity-weighted (0.44), and computed on all data including test | Relabel; compute on train only |
| 9 | MINOR | The 95% fill rate has no stakeholder; BO2 and BSC3 conflict; peak days aren't protected | Make it a parameter (90/95/98%); add a peak-day criterion |
| 10 | MINOR | The benefit estimate (₹53k/yr) inherits Issues 1–2, is called "expected" and doesn't price analyst cost | Recompute; call it conditional; give a range |
| 11 | MINOR | "90% of profit" includes ambient products; the ambient list includes refrigerated butter/cheese | Lead with fresh-only figures; add A6 |
| 12 | MINOR | Validation (Jul–Sep 2024) has no Q4 festivals; the test quarter has them | Rolling origins incl. Q4 2023; festival uplift |
| 13 | MINOR | DM1 quantiles not named; DM3 already met by raw data; DM5 weak | Name quantiles; make DM3 about stability and action; justify or drop DM5 |
| 14 | MINOR | The plan has no durations, dates or milestones | Week-by-week schedule |
| 15 | MINOR | Dataset source is TODO | Add URL, author, licence, date |
| 16 | MINOR | Notebook saved without outputs; small mismatches with the report | Save outputs; align text |
| 17 | MINOR | No intermittent-demand methods (Croston/TSB, zero-inflated GLM) | Add as baselines |

## Verification of the critic's key claims (by me)
All confirmed by re-running against the raw data:
- `Units_Produced − Quantity ≥ 1` on 100% of rows; `Unsold_Units == 1` on 91.8%. Of 12,882 fresh unsold units, 12,124 are the one-per-line floor (= the number of fresh lines).
- `Weather` and `Temperature` are constant per date across all stores (100% of dates).
- `Promotion_Applied` varies within a store-day on 39.7% of store-days.

## Follow-up analysis triggered by Issue 1
To check whether the business problem still holds with a realistic baseline, I simulated simple ex-ante rules: bake = ceil(k × trailing 28-day mean demand), with k fit on training data (to Jun 2024), scored on Oct–Dec 2024. Demand = `Quantity`, costs and margins from the training period.

| Grain | Mean demand / cell / day | Cells with demand | Rule at ~90–95% fill: waste % of baked, quarterly net ₹ | Profit-maximising rule (test) | Perfect foresight net ₹ |
|---|---|---|---|---|---|
| Store × product | 0.53 | 22% | 88% waste, −₹872k (90% fill) | **bake nothing** (₹0) | +₹90k |
| Store × category | 1.93 | 53% | 76–82% waste, −₹297k to −₹475k | **bake nothing** (₹0) | +₹89k |
| Chain × category (central bakery) | 5.80 | 86% | – | 47% fill, 22% waste, **+₹26k** | +₹89k |

**Conclusion:** at this dataset's volumes (about 9 orders a day across the whole chain), baking ahead per store at a high service level loses money under any evening-before rule. The original framing (≥20% less waste at ≥95% fill per store) can't be met and isn't the right question. Phase 1 has to be reframed before round 2.

## Decision
The project owner chose to **reframe and keep the bakery dataset** (over switching datasets or moving to a marketing focus). The new business question is fulfilment mode (bake-ahead / make-to-order / hybrid) plus quantities per fresh product.

## Changes made in response (revision 2)
| # | What I changed | Where |
|---|---|---|
| 1 | Dropped recorded production as the baseline. The bake decision is simulated from `Quantity` with `bakery.policy.simulate_plan`. The reference plan is the best simple ex-ante alternative (bake nothing / profit-max trailing-mean rule / make-to-order), sized on Q4 2023 and Q4 2024 | §1.1 Background sizing table; BSCs; `src/bakery/policy.py`, `features.py` |
| 2 | One definition throughout (demand = `Quantity`). Added a 3-row sensitivity table for the recorded fields; "fresh loses money" no longer rests on them | §1.1 Background |
| 3 | A2 restated as untestable, with the reason. Unmet demand is explicit in the simulator. Service trade-off made explicit (BSC3 frontier) | §1.2 Assumptions; BSC3 |
| 4 | A1 made conditional, with a Phase 2.4 decision gate that lists which §1 outputs would be revised | §1.2 Assumptions; §1.4 plan |
| 5 | Decision unit is now product × day (per store and pooled). Category forecast + disaggregation kept as an R3 fallback | §1.1 sizing; DM1; R3 |
| 6 | BSC1 now compares against the best simple plan with a size (≥ 5 pp of ceiling ≈ ₹4.5k/quarter), in both Q4 2023 and Q4 2024, with a block-bootstrap CI | §1.1 BSC1; R6 |
| 7 | `Promotion_Applied` and on-the-day fields excluded (R-1). The no-weather model is primary; with-weather is an upper bound (R-2) | §1.2 Requirements; R4 |
| 8 | Critical ratio relabelled (ratio of quantity-weighted average margin to average price) and computed on training data only | §1.2 Costs & benefits table |
| 9 | 95% removed as an asserted target. Trade-off reported at 50/70/90%, plus a peak-day fill criterion | BSC3 |
| 10 | Benefits restated as conditional, split into "policy change" vs "data mining contribution". Analyst cost priced | §1.2 Costs & benefits |
| 11 | Led with fresh-only figures; "ambient" renamed "long-life"; A6 added | §1.1 Background; A6 |
| 12 | Added R9; evaluation uses rolling origins incl. Q4 2023 | R9; BSC wording |
| 13 | DM1 quantiles named + Brier score; DM3 requires stability in both years; DM4 minimum segment size + a cake-share target; DM5 moved to an appendix with justification | §1.3 |
| 14 | Plan now has dates, inputs → outputs and go/no-go points (due date still to confirm) | §1.4 |
| 15 | Candidate Kaggle source added and flagged unverified (R7) | `data/README.md`; R7 |
| 16 | Notebook executed and saved with outputs; report text taken from the outputs | Notebook; report |
| 17 | Croston/TSB and Poisson / zero-inflated GLM added as candidates | DM1; tools assessment |
