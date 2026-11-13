# Sample, Explore, Modify (Round 2) and Model (Round 1): Critic Review

- **Date:** 2026-11-11
- **Reviewer:** Claude critic (independent subagent session), persona from `critic_prompt.md`. Read-only. It re-ran checks on train + validation only (338 s); no May–Aug 2026 rows were loaded. 20/20 tests pass.
- **Draft reviewed:** revision 2: notebook S.1–S.5, E.1–E.6, M.1–M.3, MO.1–MO.3; `config`, `sampling`, `lcurve`, `metrics`, `modify`, `models`, `features`; `run_learning_curve.py`, `run_model.py`, `run_assess.py` (not yet run); learning-curve and model tables in all revisions.

## Score: 7 / 10 (Sample 7.5 · Explore 7.5 · Modify 8 · Model 6.5) · Must fix before unsealing: **yes (N1, with N3)**

> "Round 1 was handled seriously and the LightGBM fix is complete and well evidenced, but the same early-stopping flaw survives in a second model family … The Assess script is sound; I found no leak path."

## Round-1 issue status
| # | Status | Evidence |
|---|---|---|
| M1 | **Partial** | Fixed for LightGBM: day holdout everywhere, no capped fits in 162. **Not fixed for the neural network** (sklearn `validation_fraction` = random rows; summer fit hit `max_iter` = 30) |
| M2 | Resolved (slip) | At main 1.6M the lift criterion also fails, not only AUC |
| M3 | **Partial** | Welch lift intervals and 3 refits are done, but the binding AUC criterion has no interval, and the summer AUC refit SD (0.0024–0.0027) exceeds its 0.002 tolerance |
| M4, M5 | Resolved | |
| m1, m3, m4, m6, m7, m9–m14 | Resolved | |
| m2 | Not resolved (accepted) | Limitation not stated in the notebook |
| m5, m8 | Resolved (slips) | "40–500 trees" is really 25–752; k = 2 chosen while X4 describes three groups |

## Model-stage task coverage
| Task | Status |
|---|---|
| SAS EM families fit | **Partial** (neural network early stopping, N1) |
| Tuning on validation only | Present |
| Summer-check rehearsal | Present |
| Benchmark vs the better rule with block-bootstrap intervals | Present |
| Champion by the pre-declared rule, no post-hoc switching | Present (rule lives in a notebook cell, N3) |
| Equal-n comparison | Present |
| Honest interpretation | **Partial** (the margin is a statistical tie, N2; stale text, N5) |
| `run_assess.py` (T1–T3, refit policy, no leakage) | Present; needs guards (N3) |

## New issues
| # | Severity | Issue | Suggested fix |
|---|---|---|---|
| N1 | **MAJOR** | The neural network keeps the M1 flaw (random-row early stopping). Critic rerun with day-grouped epoch selection: main 2.474 (was 2.328), summer 1.987 (was 1.879); mean ≈ 2.23, so the champion does not change, but Assess would report a mis-fitted network once | Day-holdout epoch selection with warm-start epochs; re-run the network rows; re-apply the rule unchanged |
| N2 | minor | The champion is a tie: paired LR − boosting per-day gap is main −0.028 [−0.089, +0.040], summer +0.088 [+0.024, +0.159]; boosting seed SD ≈ 0.03 | Keep LR (the rule); reword as "statistically tied"; report the LR–boosting test gap as descriptive |
| N3 | minor (fix before unsealing) | Champion and sample rate are written only by a notebook cell; a `RUN_MODEL` re-run would store `sample_rate` 1.0 | Compute the champion in `run_model.py`; assert champion and rate in `run_assess.py`; commit and record the git hash before Assess |
| N4 | minor | f = 72% rests on an AUC difference inside the refit noise | Disclose; no rerun (the champion doesn't depend on f) |
| N5 | minor | Stale text (full window / 7M rows / 10% of rows / ~45 min; S.2 slips; X4 groups) | Edit |
| N6 | minor | Tuning choices are below seed noise | Say so |
| N7 | minor | m2 limitation not in the notebook | One line in Modify |
| N8 | minor | The summer check doesn't rehearse the refit, and Explore saw those months | State it; keep T2 at +0.15, don't raise it |

## Single most important improvement
Give the neural network the same day-grouped early stopping, re-run its rows, re-apply the champion rule unchanged, write the champion and rate from the script with asserts in `run_assess.py`, commit, then unseal once.

## Changes made in response (revision 3)
| # | What changed | Where |
|---|---|---|
| N1 | `models._fit_mlp_day_grouped`: the preprocessor is fit on the non-held-out days; one-epoch warm-start steps keep the epoch with the lowest log-loss on a held-out 10% of **days** (patience 2, max 20). Model re-run: network main **2.474**, summer **1.987** (the critic's numbers exactly), mean 2.230. Champion unchanged (logistic regression 2.334, boosting 2.304) | `models.py`; Model table and text |
| N2 | Model findings now say "statistically tied with boosting; chosen by the pre-declared rule", quoting the paired intervals; Assess reports the LR–boosting test gap as descriptive only | Model findings; Assess |
| N3 | `run_model.py` applies the champion rule and writes `champion` and `sample_rate`; `run_assess.py` asserts the champion follows from `model_comparison.csv` and that the rate is 0.72, *(corrected in round 3: there is no git check; a SHA-256 code fingerprint is recorded in `assess_freeze.json` and `manifest.json`)*; MO.1 passes the S.2 rate; MO.2 only verifies | `run_model.py`, `run_assess.py`, MO.1–MO.2 |
| N4 | S.2: "f = 72% is a call made inside the noise", with the reason it doesn't matter | S.2 findings |
| N5 | Model intro (72% sample, day holdouts, ~5 min), the S.2 binding-criterion row, the tree range 25–752 and the X4 wording corrected | Model intro; S.2; X4 |
| N6 | "Tuning choices are within the noise" bullet | Model findings |
| N7 | Limitation line on the single constant prior | Modify text |
| N8 | Statement that the summer check rehearses fit-then-score, not the refit; T2 kept at +0.15 | Model findings |
