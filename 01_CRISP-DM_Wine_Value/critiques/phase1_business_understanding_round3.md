# Phase 1 · Business Understanding: Critic Round 3

- **Date:** 2026-11-03
- **Reviewer:** Claude critic (independent subagent session), persona from `critic_prompt.md`. Read-only access. It re-ran the development-fold feasibility check independently (every per-fold figure matched to 2 dp) and confirmed the lockbox seal.
- **Draft reviewed:** revision 3

## Score: 9 / 10 (up from 8) · Major issues remaining: **no**, so Phase 1 passes its exit criterion

Both round-2 major issues are fixed. All targets and lower-bound conditions are consistent across the report, notebook and `config.py`, and every development fold meets them (fold 3 included). Bootstrap and RNG-stream code is correct; 19/19 tests pass; no lockbox leakage.

## Task coverage
All 12 Phase 1 outputs: **Present**.

## Round-2 issues
Resolved: 1–10, 12. Partially resolved: 11 (H4 lower bound undefined; BSC5 bar close to automatic).

## New issues (all minor)
| # | Issue | Suggested fix |
|---|---|---|
| N1 | Pilot gate underpowered at n = 100: a model meeting every development target passes only 39–67% of simulated pilots. The BO1 check compares only with the price rule and has no lower bound | Size the pilot for ~80% power (≈ 400 ≤ $25 wines); compare with the best of the frozen simple-rule set, with a lower bound |
| N2 | BSC5 "≥ 3 of 6" is close to automatic (H1–H4 strong in development) | ≥ 4 of 6, including H5 or H6; label H1–H3 as sanity checks |
| N3 | H4's "LB > 0" is meaningless for an SD; H6's track-record estimator and H5's colour map are unspecified | H4: LB of the SD > 0.5 (4-critic limit stated); H6: shrunk `GroupMeanBaseline` (shrink = 20); H5: freeze the colour map before Phase 5 |
| N4 | Stale config comments (1.55×, +22.5 pp, 0.61–0.71); R9 overstates fold 3 (it's the *strongest* on BSC1) | Update the comments; reword R9 |
| N5 | Tie-break outcomes depend on the rule dict (shared tie stream) | One tie stream per rule; extend the test |
| N6 | Feasibility trains on the 859 anonymous rows that R-3 drops (not a seal breach; negligible) | Apply the filter now, or state it starts in Phase 3 |
| (r1 #14) | Due date unconfirmed | Confirm with the project owner |

## Changes made in response (final Phase 1 polish)
| # | What I changed | Where |
|---|---|---|
| N1 | Pilot = 400 ≤ $25 wines with a later critic score (`PILOT_MIN_WINES = 400`). BO1 check is now top-20% precision ≥ 1.3× the **best of the frozen simple-rule set**, with a winery-clustered LB ≥ 1.0. Power statement added | config; §1.1 pilot gate |
| N2 | BSC5 now requires ≥ 4 of 6 to replicate, including H5 or H6. H1–H3 labelled sanity checks | config; §1.1 |
| N3 | H4: LB of the critic-effect SD > 0.5, expectation fitted on training data, 4-critic limit stated. H6: shrunk `GroupMeanBaseline(keys=("winery",), shrink=20)`. H5: variety → colour map frozen (text only) in Phase 3, before any lockbox use | config `HYPOTHESES`; §1.1 |
| N4 | Config comments updated from the per-fold table. R9 reworded | config; R9 |
| N5 | Separate tie-break stream per rule (`[seed, 1, crc32(name)]`); test extended to a tied rule | value.py; tests |
| N6 | Sentence added: the R-3 filter (859 rows) starts in Phase 3; Phase 1 feasibility trains on all anonymous rows (not lockbox rows) | §1.2 Feasibility |
| (r1 #14) | Asked of the project owner | §1.4 |

**Re-run after N5 (per-rule tie streams):** all targets still met by every development fold. Only tie-sensitive figures moved at the 2nd decimal (fold 0 lift 1.59× → 1.58×; random finds 17.7 → 17.1; best simple finds 37.4 → 37.2; opportunity value $1,874 → $1,900). Report and notebook updated to match.
