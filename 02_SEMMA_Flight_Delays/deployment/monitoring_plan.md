# Monitoring Plan: Flight Disruption Risk Scorer

The scorer runs every evening at **16:45 US Eastern**, ranks tomorrow's scheduled flights by risk, and flags the top 2% for the care team. This plan says what to watch, how often, and what triggers action.

## Daily (automatic, after each flight day completes)
| Check | How | Alert when |
|---|---|---|
| Inputs present | Every scheduled flight has all 28 inputs (the shrinkage prior means none should be missing) | any input missing for > 0.5% of flights |
| Schedule volume | Flights scored vs the median of the same weekday over the last 4 weeks | outside ±20% (schedule feed problem or a major event) |
| Unseen airports or carriers | Levels not seen in training (pooled as "infrequent") | > 1% of flights, or a new carrier |
| Decision clock | Share of yesterday's flights counted as "known by 16:45 ET" | outside the training range (45–52%), which means a feed delay or a clock bug |

## Weekly (once the outcomes are in)
| Metric | Reference (validation / test) | Alert when |
|---|---|---|
| **Per-day top-2% lift**, 7-day mean | the Assess value (see `reports/tables/assess_results.csv`) | 7-day mean below **1.9**, the better simple rule's level, for 2 weeks running |
| Champion − better simple rule, per day | the Assess gap and its 90% interval | 4-week mean gap ≤ 0 |
| Top-2% precision | Assess test-summer precision | down > 20% relative |
| Calibration (predicted vs observed, by decile) | the Assess calibration table | top decile off by > 5 pp |
| Input drift (PSI) on dep_hour, carrier, origin_d1, flight_w4, nation_w1 | training distribution | PSI > 0.2 on any of them |

## Known reasons performance will move (not alerts on their own)
- **Season:** summer days have a weaker day-to-day carry-over (correlation 0.58 vs 0.66), so lift is naturally lower in summer than in winter–spring.
- **Storm days:** per-day lift can never exceed 1 / that day's disruption rate (1.5 on a day with 65% disrupted). Read weekly lift with the daily rates beside it.
- **Network changes:** carriers entering, leaving or merging (Hawaiian into Alaska, Spirit's exit) change what "carrier" means. Map them in `config.CARRIER_GROUP` when they happen.

## Retraining policy
- **Scheduled:** refit every 4 months on the latest 16 months (the same shape as the Assess refit), re-running `scripts/run_model.py` and the champion rule. Promote a new model only if it beats the current one on the most recent 2 months, scored once.
- **Triggered:** any weekly lift alert or PSI alert for 2 weeks in a row means investigate first (a data feed issue is more likely than model decay), then refit.
- Every refit re-runs the unit tests, including the leakage tests (`tests/test_modify.py`).

## Ownership
The data-science owner reviews the weekly report. The care-team lead confirms each month that the 2% capacity still matches staffing. If capacity changes, the cut-off changes (the app also shows 5%), not the model.
