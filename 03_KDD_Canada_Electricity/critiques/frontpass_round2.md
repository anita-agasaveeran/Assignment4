# KDD Front Pass: Critic Round 2

- **Date:** 2026-11-03
- **Reviewer:** Claude critic (independent subagent session), KDD-authority persona. Read-only access; it reproduced every figure on development data and computed no 2025–26 values or sealed-origin errors.
- **Draft reviewed:** front pass v2

## Score: 8 / 10 (up from 6) · Major issues remaining: **no**, so the front pass passes

Round-1 issues: 1, 2, 3, 5, 6, 7, 8 resolved; 4 partial (rules not yet operational for K2/K3).

## New issues (all minor)
| # | Issue | Action |
|---|---|---|
| N1 | Stated drivers of the 2023–24 dip partly wrong: nuclear was flat over 2022–24 (−0.6 TWh); hydro −50.5 TWh was mostly matched by **lower total generation** (−30.6), not combustion; combustion +11.5 TWh, almost all Ontario (+10.2) | **Fixed now** (notebook F.3, report) |
| N2 | Spending national 2025–26 confirmation partly spends Ontario (≈ 90% of the national combustion change) | **Fixed now:** Ontario reported separately; K2 verdict rests on the other provinces |
| N3 | K2 rule not operational (persistence measure, seasonal adjustment, resampling for ±3 months, provinces with no change point, how provinces combine) | **Carried** to KDD Transformation/Mining: specify in config before any K2 mining |
| N4 | K3 precision-only rule can be gamed; no chance baseline, match window or evaluation period | **Carried:** flag budget, lift over catalogue base rate + recall, ±1-month match, scored period, all fixed before mining |
| N5 | K1 ARI ≥ 0.7 at n = 13 means "≤ 1 geography moves"; territories have no trade data; seasonally unbalanced windows | **Carried:** state it explicitly; pre-fix k / algorithm / features / seed; matched calendar months; territory trade = isolated grid, not missing |
| N6 | Coverage wording counted published zeros; it's also a thermal reclassification | **Fixed now** |
| N7 | Title still said "Cleaner" | **Fixed now:** "Is Canada's Grid Becoming Less Combustion-Dependent?" |
| N8 | F.2 displayed two sealed geo-months (2026-08) | **Fixed now:** sealed exceptions only counted |
| N9 | K4 low power (development ratio 0.910 > 0.90; P ≈ 0.35); training windows not covered by the 2016 rule | **Carried:** one model chosen on development origins; report the sealed ratio with an interval; apply `CONSISTENT_START` (or a level shift) to K4 training |
| N10 | iid bootstrap adequate (cluster bootstraps similar) | Info |

## Single most important remaining improvement
Correct the 2023–24 driver story (done) and write K2's rule as an operational test in config before any K2 mining (carried).
