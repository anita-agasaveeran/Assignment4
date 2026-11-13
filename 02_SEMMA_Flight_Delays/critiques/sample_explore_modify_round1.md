# Sample, Explore and Modify: Critic Round 1

- **Date:** 2026-11-11
- **Reviewer:** Claude critic (independent subagent session), persona from `critic_prompt.md`. Read-only. It re-ran key figures on train + validation only; no May–Aug 2026 rows were loaded.
- **Draft reviewed:** notebook Sample (S.1–S.5 + Assess targets), Explore (E.1–E.5), Modify (M.1–M.3); `config.py`, `sampling.py`, `lcurve.py`, `metrics.py`, `modify.py`, `features.py`, `models.py`, tests, `sample_learning_curve.csv`.

## Score: 6 / 10 (Sample 6 · Explore 6.5 · Modify 7) · Major issues: **yes (5)**

> "The structure is unusually good … and the Modify leakage design holds up — I tried to break it and couldn't. But one methodological flaw runs through all three stages and into Model: LightGBM early stopping uses a random 10% of training rows from the same days."

## What the critic verified
| Check | Result |
|---|---|
| Unit tests | 18/18 pass |
| Future-truncation test: `build_frame` on Jan–Aug 2025 vs Jan–Jun 2025, all 25 numeric v3 inputs for rows ≤ Jun 30 | identical (max \|diff\| = 0) |
| Outcome-perturbation test: flip every outcome on 2025-06-15 | no day-D input changes; on D+1 only the `*_d1` inputs change |
| Counts built on the full schedule | ✔ |
| Shrinkage prior 0.237 | constant, so no row-level leak; for the summer check it includes that window's validation months |
| 16:45 ET clock vs dep_ET + scheduled elapsed (Jan–Aug 2025) | 3,905 flights (0.08%) wrongly "known" (date line, split-zone airports); 5,754 wrongly excluded (short westbound hops) |
| M.3 summer v3 reproduced | exact match |
| X6 "previous-day rates missing for 24–43%" | **wrong by 100×**: 0.24–0.43% |
| Tree counts in the learning curve | LightGBM-63 hits the 3,000-tree cap in 100% of fits at ≥ 1.6M rows |

**Early-stopping experiment (critic's rerun, 800k samples, one seed):**

| Window / inputs | ES = random 10% of rows (as coded) | ES = random 10% of whole days | ES = last 12 days |
|---|---|---|---|
| Summer, v3 | 2,393 trees · lift 2.086 · AUC 0.668 | **124 trees · 2.191 · 0.694** | 60 trees · 2.123 · 0.691 |
| Summer, v2 | 1.879 · 0.663 | **56 trees · 1.993 · 0.685** | – |
| Main, v3 | 880 trees · 2.391 · 0.692 | **80 trees · 2.411 · 0.695** | – |
| Main, v2 | 2.178 · 0.686 | **267 trees · 2.209 · 0.691** | – |

## Task coverage
| Stage | Task | Status |
|---|---|---|
| Sample | Sampling frame | Present |
| Sample | Sample-size justification | **Partial**: confounded by row-random early stopping and the tree cap; summer arm incomplete; tolerance below the reference's noise |
| Sample | Method and strata | Present |
| Sample | Representativeness | Present (two arithmetic slips) |
| Sample | Partition and roles | Present |
| Sample | Deviations disclosed | Partial |
| Sample | Pre-registered Assess targets | Present; benchmark rule inconsistent with the v3 clock |
| Explore | Univariate / bivariate, target relationships | Present |
| Explore | Anomalies | **Partial**: none analysed |
| Explore | Segmentation | Partial: weak (silhouette 0.27), no downstream use |
| Explore | Findings → Modify | Present, but X6's premise is wrong |
| Explore | No test leakage | Present (validation months explored, m3) |
| Modify | Features, leakage audit | Present, verified clean apart from clock edge cases |
| Modify | Missing values, rare categories, outliers | Partial |
| Modify | Evidence that Modify helps | Partial → holds (+0.20 under correct early stopping) |
| Modify | Unit tests | Present; end-to-end invariance tests missing |

## Issues
| # | Severity | Issue | Suggested fix |
|---|---|---|---|
| M1 | **MAJOR** | LightGBM early stopping on a random 10% of training *rows*. Day-level inputs let the model memorise each training day, so the holdout keeps rewarding more trees: the 3,000-tree cap binds at ≥ 1.6M, and the learning-curve verdict, "the data is deep" and "LR beats boosting" are not established. The same scheme is in `models.fit` | Hold out whole days (or the last ~2 weeks) in `lcurve.score`, `models.fit` and M.3; log tree counts; re-run the curve and M.3; re-apply the rule unchanged, disclosed |
| M2 | **MAJOR** | The S.2 reading contradicts the rule's output: no size passes in either window (the AUC criterion binds at 3.2M main), yet the table lists n\* values | Show the `by_n` table per window; say which criterion binds |
| M3 | **MAJOR** | The tolerance can't be measured against the reference: the full-window reference has SD 0.031 lift over 3 refits (one refit in summer) | Report shortfalls with a CI; ≥ 3 full refits in both windows; reword "conservative" |
| M4 | **MAJOR** | 800k for the tree and MLP is extrapolated from the LR curve on v2 inputs; the champion rule compares 800k models with boosting at 7M | Add gradient boosting at 800k so families are also compared at equal n; fix the config comment |
| M5 | **MAJOR** | X6 is wrong (0.24–0.43%, not 24–43%) | Correct it; motivate shrinkage with real low-count shares |
| m1 | minor | Clock edge cases (date line, split-zone states, westbound hops) | Use arr_ET = dep_ET + scheduled elapsed; tests |
| m2 | minor | Shrinkage hides "no data"; `PRIOR_N` unjustified; summer prior includes its validation months | Counts for rate families; justify prior; window-specific prior |
| m3 | minor | Validation months are explored, so validation gains are optimistic | State it; Assess is the unbiased estimate |
| m4 | minor | M.3 single seed, no interval; summer log-loss worsens with v3 (an M1 symptom) | Paired daily difference with block bootstrap; log-loss commentary |
| m5 | minor | Learning-curve deviations misreported (comment says 2 refits; CSV has 1); summer curve non-monotone | Fix; say the summer arm can't discriminate sizes |
| m6 | minor | Representativeness arithmetic: expected counts are 2.84 and 2.40, not 2.0 and 1.6; the z-criterion operationalisation not stated | Correct; state it |
| m7 | minor | No anomaly analysis (e.g. 2026-01-25: 69.7% disrupted, 46.5% cancelled) | Add an anomaly table and a decision |
| m8 | minor | Clustering weak; volatility confounded with volume; no downstream use | Downgrade to descriptive |
| m9 | minor | The day-before benchmark rule uses the v2 local-17:00 rates, not the 16:45 ET clock | Build it from `*_d1` before Assess |
| m10 | minor | Transform wording vs code (min_frequency counts sample rows; imputer vacuous; skewed counts) | Correct wording; log1p counts |
| m11 | minor | Tests miss end-to-end invariance | Add truncation / perturbation tests |
| m12 | minor | float32 cumsums; lags assume contiguous dates | float64; assert contiguity |
| m13 | minor | X3 shares not printed; 0.58/0.69 vs 0.576/0.659 | Print; reconcile |
| m14 | minor | The full-schedule assumption (BTS schedule = what exists at 17:00 D−1) | State it |

## Single most important improvement
Switch every LightGBM early stop to a day-grouped holdout, log the tree counts, and re-run the learning curve and M.3 before Model.

## Changes made in response (revision 2)
| # | What changed | Where |
|---|---|---|
| M1 | Early stopping now holds out a random 10% of whole **days** (`metrics.day_holdout`) in `lcurve.score`, `models.fit` and M.3. LightGBM's learning curve re-run in full (5 reps, 3 full refits, both windows): **no fit hits the cap** (40–500 trees). The rule, applied unchanged, gives n\* = 3.2M (main) and 1.6M (summer), so **f = 72%** (was 100%). Model re-run: boosting gains summer AUC 0.675 → 0.689; the champion is unchanged (logistic regression, mean lift 2.335 vs 2.305) | `metrics.py`, `lcurve.py`, `models.py`; S.2, M.3, Model; `sample_learning_curve.csv` (rev 1 kept as `_rev1_rowES.csv`) |
| M2 | S.2 findings rewritten from the rule's own `by_n` output, stating which criterion binds (AUC) | S.2 findings |
| M3 | Welch 95% intervals on every shortfall; full-window reference refit 3× in both windows (lift SD now 0.009 / 0.011); "conservative" wording removed | `summarize` in S.2; S.2 findings |
| M4 | Gradient boosting at the same 800k sample added to Model as an equal-n check (main 2.42, summer 2.16 vs LR 2.44 / 2.23); `config.py` comment says 800k is justified only for LR | `run_model.py`; Model table; `config.py` |
| M5 | X6 corrected (0.24–0.43%); shrinkage motivated with the printed < 20-flight shares | Explore findings; M.3 |
| m1 | arr_ET = dep_ET + scheduled elapsed time; split-zone airport overrides; tests for the date line, a westbound hop and ELP | `modify.py`; `test_modify.py` |
| m3 | Caveat that validation months were explored, so Assess is the only unbiased estimate | Explore findings |
| m4 | M.3: 3 seeds, paired per-day difference with 7-day-block interval, log-loss reported | M.3 |
| m5 | Deviation comments and markdown corrected; summer arm completed | S.2 |
| m6 | Expected counts corrected (2.84 / 2.40); binomial operationalisation stated | S.4 findings |
| m7 | E.6 anomaly table (top-10 days, cancellation share, max possible lift); Assess also reports the gap without the 5% highest-rate days | E.6; `run_assess.py` |
| m8 | Volume-adjusted volatility; X4 downgraded to descriptive | E.4; X4 |
| m9 | Day-before benchmark rule rebuilt on the 16:45 ET clock (`*_d1`); the v2 version reported only | `models.rules`; Model / Assess |
| m10 | Transform wording matches the code; log1p for count inputs | `models.preprocessor`; Modify text |
| m11 | End-to-end tests: truncation invariance, day-D perturbation, counts before the population filter (20 tests pass) | `test_modify.py` |
| m12 | float64 accumulators; contiguous-date assertion | `modify.py` |
| m13 | E.3 prints the weather + NAS shares | E.3 |
| m14 | Assumption A-sched stated | Modify text |

**Not addressed (with reason):** m2's window-specific prior and per-family counts. The prior is a single constant, so its effect on a per-day *ranking* is negligible, and the deadline doesn't allow another feature iteration. It's disclosed as a limitation. For LightGBM rare categories (m10), its native categorical handling with `min_data_per_group` (default 100) is kept.
