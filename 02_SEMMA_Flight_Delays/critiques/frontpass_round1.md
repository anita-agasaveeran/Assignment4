# SEMMA Front Pass: Critic Round 1

- **Date:** 2026-11-03
- **Reviewer:** Claude critic (independent subagent session), persona: world authority on SAS SEMMA / Enterprise Miner. Read-only access; all checks on train + validation (test months: counts only).
- **Draft reviewed:** front pass v1 (`reports/front_pass.md`, notebook front-pass section)

## Score: 6 / 10 · Major issues remaining: yes (6)

| # | Severity | Issue | Suggested fix |
|---|---|---|---|
| 1 | MAJOR | **Target leak via `leg_of_day`.** `tail_number` is missing *only* on cancelled flights (22,511 / 22,511 in train + valid), so NaN ⇒ disrupted. The tail on other rows is the aircraft actually flown (partly flight-day information) | Drop `leg_of_day`; add a missingness-vs-target leak test; treat tail-less (pre-)cancellations as known |
| 2 | MAJOR | **Previous-day rates include flights not landed by the evening decision.** Only 56.9% of d−1 flights are scheduled to arrive by 17:00. With a 17:00 cutoff and no `leg_of_day`: AUC 0.687 / PR-AUC 0.412 / lift 2.10 (vs 0.707 / 0.455 / 2.31) | Fix a decision clock in config; compute d−1 rates only from flights scheduled to arrive before it; unit-test it |
| 3 | MAJOR | **Unfair baseline.** A no-day-before rule compared with a day-before model mixes horizon and model. A trivial day-before rule (mean of yesterday's three rates) gets 0.655 / 0.395 / 2.04. No CIs | Both rules as baselines; day-clustered bootstrap CIs; restate the verdict |
| 4 | MAJOR | **The metric doesn't match the decision.** The team chooses within one evening; pooled lift rewards spotting bad days (daily rate 6.5%–70.7%). Per-day top-decile lift: leak-free model 1.79 vs day-before rule 1.71. 10% ≈ 1,900 flights/day isn't "limited" | Primary = per-day top-k precision/lift with k from a stated capacity; pooled AUC secondary |
| 5 | MAJOR | **Seal slip.** "24.4% of all flights" includes the test months (train + valid is 23.66%); combined with published counts it reveals the test rate | Use the train + valid rate; add a guard refusing target stats on test |
| 6 | MAJOR | **Validation (Jan–Apr) ≠ test season (May–Aug)**; `month` encodes 2025-only weather; no refit policy | Rolling-origin backtest inside non-test data (e.g. Jan–Apr 2025 → May–Aug 2025); state the refit policy; drop `month` or use lagged seasonal rates |
| 7 | MINOR | HA → AS recoding: AS Hawaii flights ~1.3k → ~8k/month in 2026, so AS changes meaning. NK winds down, with 354 test flights on 2026-05-01 | Map HA → AS in train or flag it; report carrier-mix drift |
| 8 | MINOR | Missed anomalies: 8,243 cancelled with `dep_delay`; `sched_elapsed_time` null (4) or ≤ 0 (14); `sched_dep_time = 2400`; the duplicate is two F9 rows; Aug 2026 may be preliminary | Add to checklist with decisions; completeness check |
| 9 | MINOR | `airlines.csv` / `airports.csv` aggregate the whole period, test months included | List as forbidden, or rebuild from train only |
| 10 | MINOR | Tests don't test the real feature matrix or catch #1/#2 | Leak tests on the built features; cutoff and seal tests |
| 11 | MINOR | Lagged features for the first day of a partition only work if built on the full timeline | Always build on the full timeline up to the cutoff, then split; test it |

## Single most important improvement
Drop the tail-derived feature, compute previous-day rates only from flights landed by a fixed cutoff, and rerun feasibility against a day-before rule using a per-day top-k metric. The honest starting point is ~1.79× per-day lift vs ~1.71× for the trivial rule.

## Changes made in response (front pass v2)
| # | What I changed | Where |
|---|---|---|
| 1 | `leg_of_day` and all tail-derived features removed; tail-less flights (100% cancelled) excluded from the scored population; leak tests (missingness vs target; banned features) | features.py; config; tests; F.2/F.4 |
| 2 | 17:00 decision clock (`DECISION_CUTOFF_HHMM`); previous-day rates only from flights scheduled to land the same day by 17:00; unit-tested; `daily_airport_stats` excluded | features.py; tests; F.4 |
| 3 | Two baselines (schedule rule, day-before rule); day-clustered bootstrap for model − rule | F.5 |
| 4 | Primary metric = per-day top-2% lift (capacity ≈ 380 flights/day), top-10% also reported; pooled AUC secondary | F.1; config `TOP_FRACTIONS`; F.5 |
| 5 | All-period rate replaced by train + valid (23.7%); `assert_no_test_targets` guard + test; disclosures | data.py; F.3; report |
| 6 | Summer check inside non-test data (Jan–Apr 2025 → May–Aug 2025); `month` dropped; refit policy stated (train + valid before Assess). Finding: the best simple rule flips by season | config; F.3; F.5 |
| 7 | HA → AS carrier group; carrier-mix counts per period; AS-Hawaii volume shift shown; NK's single test day noted | config; F.2 |
| 8 | Checklist extended (cancelled with dep_delay, sched_elapsed issues, 2400, duplicate F9 rows, per-day completeness, BTS revisions) with a decision for each | F.2 |
| 9 | `airlines.csv` / `airports.csv` aggregates listed as forbidden | config; F.4 |
| 10 | Tests now check the real feature lists, the cutoff, the seal guard and missingness leaks | tests |
| 11 | Lagged features built on the full non-test timeline before splitting (first validation day filled); the rule is written in the docstring | features.py; F.5 |
