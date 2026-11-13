# Sample, Explore, Modify and Model (Round 3): Critic Verification Review

- **Date:** 2026-11-11
- **Reviewer:** Claude critic (independent subagent session), persona from `critic_prompt.md`. Read-only; no May–Aug 2026 rows loaded, `run_assess.py` not run. 20/20 tests pass. It reproduced the revision-3 network rows exactly (main 2.474 at epoch 2, summer 1.987 at epoch 4).

## Score: 8.5 / 10 (Sample 8 · Explore 8 · Modify 8.5 · Model 8.5) · **No MAJOR issue blocking the one-time Assess run**

## Round-2 issue status
| # | Status | Evidence |
|---|---|---|
| N1 | Resolved (leak) + new caveat R3-1 | Whole-day holdout; preprocessor fit without the held-out days; training window only; sklearn early stopping off |
| N2 | Resolved | "Statistically tied" wording, paired intervals quoted. Assess gives both rows' gaps to the rule, not a paired LR − boosting interval (descriptive) |
| N3 | Partial | The rule lives in `run_model.py`; `run_assess.py` recomputes and asserts the champion and the rate, and writes a SHA-256 freeze before any test row is read. **But** the revision-3 table claimed a git check and hash the code doesn't have, and the project is uncommitted |
| N4, N5, N7, N8 | Resolved | |
| N6 | Resolved (slip) | The network's two settings differed by 0.118, which isn't noise |

## New issues
| # | Severity | Issue | Suggested fix |
|---|---|---|---|
| R3-1 | minor | sklearn `fit()` with `warm_start=True, max_iter=1` rebuilds Adam and re-seeds the batch order every "epoch". Critic rerun with continuous Adam: main 2.480, summer 2.115 (mean 2.298); the champion is unchanged | `partial_fit` over shuffled batches with an advancing `RandomState`; re-run; confirm the champion |
| R3-2 | minor | Audit trail: the claimed git guard doesn't exist; `GIT_HASH` is a SHA-256 fingerprint; "committed to `data/sample/`" is untrue (untracked) | Correct the wording; rename it to `CODE_FINGERPRINT`; commit before and after Assess |
| R3-3 | minor | No crash protocol for the single-run guard | Status "started" → "completed"; allow a restart only with an identical fingerprint, and log it |
| R3-4 | minor | The N6 bullet over-generalises (network tuning gap 0.118, possibly an R3-1 artefact) | Reword after the R3-1 re-run |
| R3-5 | minor (optional) | No test for `day_holdout` | Add one |

## Changes made in response (revision 4)
| # | What changed |
|---|---|
| R3-1 | `_fit_mlp_day_grouped` now runs epochs of `partial_fit` over shuffled 2,048-row batches with `np.random.RandomState(seed)` (continuous Adam). Model re-run: network (128, 64) main **2.468**, summer **2.071**, mean 2.269; (64, 32) main 2.462. **Champion unchanged:** logistic regression 2.334 > boosting 2.304 > network 2.269 > tree 1.950 |
| R3-2 | `GIT_HASH` renamed to `CODE_FINGERPRINT`; the round-2 N3 row corrected below; S.3 wording now says "saved to `data/sample/`". **Git commits are left to the user** (this project's rule is that the user approves every commit and push), so the frozen state is the SHA-256 record in `reports/tables/assess_freeze.json`, written before any test row is read |
| R3-3 | The freeze record has `status` "started" → "completed"; a restart is allowed only if the status is "started" and the code fingerprint is identical, and each restart is logged |
| R3-4 | The tuning bullet now reads "within the noise" with the network included (2.462 vs 2.468 after the fix) |
| R3-5 | `test_day_holdout_holds_out_whole_days_only` added (21 tests pass) |

**Correction to the round-2 "Changes made" table, N3 row:** `run_assess.py` does not check git or record a git hash. It records a SHA-256 fingerprint of `src/`, `scripts/`, `model_chosen.json` and `model_comparison.csv` before reading any test row, and refuses a second completed run.
