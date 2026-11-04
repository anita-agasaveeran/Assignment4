# SEMMA Front Pass: Critic Round 2

- **Date:** 2026-11-03
- **Reviewer:** Claude critic (independent subagent session), SEMMA-authority persona. Read-only access; it re-ran the whole F.5 pipeline on train + validation (every number matched to 3 decimals) and computed no test-month targets.
- **Draft reviewed:** front pass v2

## Score: 8 / 10 (up from 6) · Major issues remaining: **no**, so the front pass passes

All 6 round-1 majors resolved in substance (the seal guard is weak, cutoff caveat N3).

## New issues (all minor; each moves lift by ≤ 0.02)
| # | Issue | Action |
|---|---|---|
| N1 | The scored population excludes tail-less cancellations using information not shown to be known at 17:00 (1.03% of positives, clustered on storm days; including them: 2.175 → 2.165) | **Fixed now:** stated as an assumption; Assess reports both ways |
| N2 | `origin_*_sched` counted after the population filter, so counts shrink on heavy-cancellation days (dormant leak) | **Fixed now:** counts built on the full schedule before filtering + test. Re-run: model 2.19 (was 2.18) |
| N3 | The 17:00 cutoff uses destination-local time; one national ranking needs one clock; flights landing 16:45–17:00 aren't known by 17:00 (single ET cutoff: 2.175 → 2.167 main, 1.932 → 1.912 summer) | **Carried** to Modify: single reference clock (17:00 ET), time-zone-aware arrivals, 15-min margin, test with a Pacific case |
| N4 | Summer comparison vs the best rule had no interval; single-day bootstrap ignores autocorrelation | **Fixed now:** model − best rule per window with a 7-day-block bootstrap: main +0.30 (+0.18 to +0.40); summer +0.19 (+0.10 to +0.28) |
| N5 | Seal guard only checks dates and wasn't called in F.5 | **Fixed now:** called in F.5; wording softened |
| N6 | Stale "aircraft rotation" mentions | **Fixed now** |
| N7 | Precision named primary but not reported | **Fixed now:** top-2% precision 0.49 vs 0.42 (main), 0.52 vs 0.47 (summer) |
| N8 | "Summer storms don't carry over" stated as fact | **Fixed now:** reported as a measured difference (correlation 0.58 vs 0.69), cause a hypothesis for Explore |

## Single most important remaining improvement
Make features and evaluation match what exists at 17:00 the day before: full-schedule counts (done), one reference clock (carried), and score or justify the tail-less cancellations (stated; both ways in Assess).
