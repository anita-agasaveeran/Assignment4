# SEMMA Project: Front Pass

*Problem framing, data checks and frozen partition, done before the SEMMA stages. Every figure comes from the front-pass section of `notebooks/SEMMA_Flight_Disruption.ipynb` (saved with outputs).*

> **Revision 2**, after critic round 1 (6/10; `critiques/frontpass_round1.md`). Main changes:
> - a **target leak** is removed (tail-number feature);
> - previous-day rates use a **17:00 decision clock**;
> - **two baselines**, with a per-day top-k metric and day-clustered intervals;
> - a **summer check** inside the non-test data;
> - a seal guard, and the Hawaiian → Alaska recoding.
> - Round 2 (8/10, no major issues): schedule counts built on the full schedule; best-rule block-bootstrap intervals; precision reported; the population assumption stated.

## Why a front pass
SEMMA (SAS Institute) starts at **Sample** and has no business-understanding step. The front pass supplies the minimum needed to avoid modeling the wrong thing, and it freezes the test set before any modeling.

## Problem
| Item | Decision |
|---|---|
| Stakeholder (hypothetical) | Customer-care team of a travel-booking service or airline |
| Decision | At **17:00 local the day before**, pick the **~2% of tomorrow's flights** (~380 of ~19k) whose passengers get proactive help |
| Allowed inputs | Published schedule + outcomes of flights **scheduled to land by 17:00** on previous days |
| Target `disrupted` | Arrived 15+ min late, cancelled or diverted: **23.7%** in train + validation (test sealed) |
| Scored population (assumption) | Flights with a tail number. All 22,511 tail-less flights in train + valid are cancelled. We *assume* they're early cancellations known by 17:00 the day before, but the data can't confirm it, and they cluster on storm days. **Assess reports results both ways** (excluded / scored as disrupted) |
| Primary metric | **Per-day top-2% precision and lift**, averaged over days (top-10% also reported) |
| Secondary metrics | Pooled ROC-AUC / PR-AUC, calibration |
| Benchmark | The **best of two simple rules** in the window: carrier × departure-hour history, or yesterday's disruption rates |

## Data checks (all 11,730,351 flights; structure only for the test months)
- **Coverage:** 2025-01-01 → 2026-08-31; 11,001–21,576 flights per day (median 19,677); 14 carriers; 361 airports.
- **Consistency:**
  - Delay flags match delay minutes (100%).
  - Delay causes sum to `arr_delay` on 99.994% of late flights.
- **Exceptions, each with a decision:**
  - 8,243 cancelled flights have a `dep_delay` (they left the gate, then were cancelled; documented).
  - `sched_elapsed_time` is missing for 4 flights and ≤ 0 for 14: dropped.
  - 1 flight is scheduled at 2400: departure hour 23.
  - 1 duplicate key (two F9 3237 rows on 2026-01-04): one kept.
  - August 2026 looks complete but may be revised by BTS (a limitation).
- **Carrier changes:**
  - Hawaiian (HA) stops after 2025-12-31, and its network appears under Alaska (AS flights touching Hawaii: ~1.4k/month in 2025 → ~8.1k/month in 2026), so `carrier` maps HA → AS.
  - Spirit (NK) shrinks through 2026, with its last flights (354) on 2026-05-01.
- **Leak found and removed:** `tail_number` is missing exactly when a flight is cancelled, so the v1 feature `leg_of_day` leaked the target. No feature is derived from `tail_number`, and those flights are out of the scored population.

## Frozen partition and seal
| Partition | Months | Flights | Disrupted | Use |
|---|---|---|---|---|
| Train | Jan–Dec 2025 | 7,001,619 | 23.7% | Fit |
| Validation | Jan–Apr 2026 | 2,269,061 | 23.6% | Tuning, model choice, targets |
| *Summer check* | *Jan–Apr 2025 → May–Aug 2025* | – | *27.2%* | *Season-matched check inside non-test data* |
| **Test (sealed)** | **May–Aug 2026** | **2,459,671** | – | **Scored once in Assess, after refitting on train + valid** |

- **Seal guard:** `assert_no_test_targets` runs on the data before the target statistics in F.3 and F.5.
- *Disclosure:* v1 printed all-period quarterly rates and quoted an all-period rate (24.4%). Neither informs modeling.

## Leakage audit
| Column / file | Known at 17:00 the day before? | Use |
|---|---|---|
| Schedule (date, weekday, carrier, flight no., route, scheduled times, distance, scheduled elapsed time) | Yes | Features |
| Scheduled departures per origin-hour / day (counted on the **full** schedule, before any population filter) | Yes | Features |
| **`tail_number` and anything derived from it** | **No** (the aircraft actually flown; missing ⇔ cancelled) | **Excluded** |
| `month` | Encodes one year's weather | Excluded |
| Yesterday's disruption rates (origin, destination, carrier), from flights scheduled to land by 17:00 | Yes | Day-before features |
| Flight-day outcomes | No | Target only |
| `daily_airport_stats.csv` | Full-day, so not cut off at 17:00 | Excluded |
| `airlines.csv`, `airports.csv` departures/arrivals | No (whole-period aggregates incl. test) | Excluded |

## Feasibility
Train samples of 400k; full validation windows scored; test untouched.

| Per-day top-2% lift (precision) | Main: 2025 → Jan–Apr 2026 | Summer check: Jan–Apr 2025 → May–Aug 2025 |
|---|---|---|
| Schedule rule (carrier × dep-hour history) | 1.56 (0.36) | **1.74 (0.47)** |
| Day-before rule (yesterday's 3 rates) | **1.89 (0.42)** | 1.39 (0.37) |
| LightGBM, schedule only | 1.98 (0.45) | 1.85 (0.50) |
| **LightGBM, schedule + day-before** | **2.19 (0.49)** | **1.93 (0.52)** |
| *Model − best simple rule (90% 7-day-block interval)* | *+0.30 (+0.18 to +0.40); better on 71% of days* | *+0.19 (+0.10 to +0.28); better on 67% of days* |
| *Pooled ROC-AUC (same model)* | *0.685* | *0.675* |

- **The best simple rule depends on the season:**
  - the day-before rule wins in winter–spring;
  - the schedule rule wins in summer, when the day-before rule ranks flights within a day poorly (AUC 0.58).
  - Daily disruption is somewhat less persistent in summer (day-to-day correlation 0.58 vs 0.69). That's a measured difference; the cause (local thunderstorms?) is a hypothesis for Explore.
- **The model beats the best simple rule in both windows, modestly.** Both 7-day-block intervals exclude 0.
- **The v1 headline (2.3× vs 1.5×) was inflated** by the leak, uncut previous-day rates and an unfair baseline.
- **Next stages:**
  - *Sample* sets targets against the best simple rule.
  - *Modify* targets summer-relevant features.
  - *Assess* (a summer test) has the summer-check window as its preview.
