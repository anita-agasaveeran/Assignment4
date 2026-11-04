# Phase 1 · Business Understanding: Critic Round 2

- **Date:** 2026-11-03
- **Reviewer:** Claude critic (independent subagent session), persona from `critic_prompt.md`. Read-only access, and it re-computed figures itself.
- **Draft reviewed:** Revision 2 (reframed: bake-ahead / make-to-order / hybrid)

## Score: 7 / 10 (up from 5)

All Phase 1 outputs present. The invalid recorded baseline is gone, definitions are consistent, leaky inputs are excluded, every figure reproduces, and the sizing code has no look-ahead. **Not passed:** major issues remained.

## Round-1 issues
Resolved: 1, 2, 3, 4, 5, 7, 8, 11, 14, 17. Partially resolved: 6, 9, 10, 12, 13, 15, 16.

## New major issues
| # | Issue |
|---|---|
| 1 | The realised-demand ceiling (₹90k/quarter) isn't reachable by any forecast. A test-quarter "distribution oracle" (true P(D ≥ j) per location × product × weekend × festival) earns only **≈ ₹3.4k per store / ₹13.2k pooled** with no pre-orders. The data mining headroom is about an order of magnitude below ₹90k, so the BSC1 floor may be infeasible |
| 2 | The make-to-order sizing applied 50/70/90% retention to all products, contradicting A7 (cakes 50/70/90, others 0/20/40) |
| 3 | A0 is a straw man: the 90%-fill rule bakes 8.7× demand, so the "₹0.25M–1.06M avoided loss" benefit is not credible |
| 4 | Q4 2023 is used both for tuning and as an out-of-sample test; Q4 festivals have zero training history at that origin |
| 5 | The rule for choosing the reference plan per product is unspecified (look-ahead risk) |
| 6 | The critical ratio ignores pre-order retention: CR(r) = (1 − r)m / ((1 − r)m + c) |
| 7 | DM1 forecasts quantiles 0.5–0.9, but the decision quantiles are 0.27–0.48 |

Minor: BSC3 met trivially by bake-nothing; text/config inconsistencies; R7 vs data README; decision cut-off time; DM3 met by raw counts; robustness row for "bake nothing".

## Outcome
Not revised further. Round 2 confirmed that the data mining value this dataset can support is very small (synthetic data, ~9 orders/day). The project owner decided to **replace the CRISP-DM dataset** (2026-11-03). This folder stays as a record of the pivot: CRISP-DM's Business Understanding ↔ Data Understanding loop showed early that the data couldn't support the business goal.
