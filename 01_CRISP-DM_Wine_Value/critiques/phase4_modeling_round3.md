# Phase 4 · Modeling: Critic Round 3

- **Date:** 2026-11-07
- **Reviewer:** Claude critic (independent subagent session), persona from `critic_prompt.md`. Read-only; lockbox `points` never loaded; fold predictions checked to contain no lockbox rows.
- **Draft reviewed:** Phase 4 revision 3 (interpretation and diagnostics only)

## Score: 8 / 10 · Major issues remaining: no (0)

All three round-2 MAJORs are fixed; each reworded mechanism claim now matches its numbers, and almost every figure in the summary, §4.1, §4.4 and the Phase 5/6 plan was re-derived. No leakage found. **Phase 4 passes the gate.** The most substantive remaining item (N1) should still be fixed before Phase 5 because it changes how the lockbox result is read.

## Task coverage
| Task | Output | Status |
|---|---|---|
| 4.1 | Modeling technique | Present |
| 4.1 | Modeling assumptions | Partial (the selected model's real assumption unstated; (c) listed as tested) |
| 4.2 | Test design | Present |
| 4.3 | Parameter settings | Present |
| 4.3 | Models | Present |
| 4.3 | Model descriptions | Present |
| 4.4 | Model assessment | Present (minor gaps) |
| 4.4 | Revised parameter settings | Present (disclaimer missing from the notebook) |

## Round-2 issues
All 11 resolved; #8's commit and tag remain a gate condition before Phase 5.

## Issues raised
| # | Severity | Issue | Suggested fix |
|---|---|---|---|
| N1 | MINOR (closest to MAJOR) | The pooled calibration hurts writers that ridge already over-predicts (Buzzeo −13.3 pp, Kostrzewa −9.9, Dykes, Adams, Pickard); "recovers most" is backed only by MAE; the model's real assumption is unstated | Per-critic ridge vs calibrated table; cite the bias drop; state the assumption in §4.1; add the risk to Phase 5 |
| N2 | MINOR | Phase 5 risk line names Gregutt (15.5% under the selected model) | Only DeSimone is below 10% |
| N3 | MINOR | "Named-only makes under-prediction larger" holds in folds 0 and 3 only | "Named-only ridge still under-predicts in all four folds" |
| N4 | MINOR | Gap attributed to "inputs" though α alone moves 1.8 pp; dropping length more than closes it on fold 3 | Reword |
| N5 | MINOR | "Origin reverses the calibration" isn't supported (fold 1, fold 4) | "Origin worsens the stack in all four inner folds and three of four outer folds; why is not established" |
| N6 | MINOR | H4 per-critic values have opposite signs to DM6 for Czerwinski and Voss | Say H4's values aren't critic levels |
| N7 | MINOR | Notebook markdown missing the post-hoc disclaimer, §4.2 post-table bullets, §4.3 settings commentary | Sync |
| N8 | MINOR | Per-split critic-disjoint values not displayed; revision-3 diagnostics not saved | Display and save |
| N9 | MINOR | Ranker α wording true for folds 0 and 3 only | Reword |
| N10 | MINOR | "The same loss applies" to the lockbox overclaims | "can apply" |
| N11 | MINOR | Assumption (c) listed as tested; O'Keefe and Italy breakdowns missing from the Phase 5 list | Mark untestable; add breakdowns |
| N12 | MINOR | Revision-3 run log has no "data seen" column | Add it |
| N13 | MINOR | DM3 term lists curated; DM4 top rules out of order; outlier wording; "of the six largest countries" | Quote verbatim; fix order; soften |
| N14 | MINOR | 67 anonymous notes with p > 0.5 for lockbox critics (refit classifier) stay in the Phase 5 training set | Disclose; the 1,234-ID sensitivity covers them |

## Single most important improvement
Tell the calibration story at the writer level: per-critic ridge vs calibrated reduction and bias, the assumption stated in §4.1, the corrected Phase 5 risk line. Then sync the notebook, commit and tag before Phase 5.

## Changes made in response (revision 4)
No model, rule or selection changed (run log, revision 4).

| # | What I changed | Where |
|---|---|---|
| N1 | Per-writer ridge vs calibrated table (13 writers with ≥ 30 test reviews): ridge under-predicts 10 of 13 (96% of reviews); review-weighted writer bias 0.98 → 0.38; calibration hurts Buzzeo (−13.3 pp), Dykes (−12.2), Kostrzewa (−9.9) and slightly overshoots Gordon and Boone. Summary rewritten; the selected model's working assumption stated in §4.1 (a); new Phase 5 risk and a ridge vs calibrated per-lockbox-critic report | notebook 4.4c; §4.1; §4.4; Phase 5 plan |
| N2 | Risk line corrected (only DeSimone below 10%) | §4.4 |
| N3 | Restated: named-only ridge under-predicts in all four folds | §4.4 |
| N4 | "Inputs, TF-IDF set-up and α (about 1.8 pp)"; "dropping length more than closes it on fold 3" | summary; §4.4 |
| N5 | "Adding origin worsens the stack in all four inner folds and three of four outer folds; why is not established" | summary; §4.4 |
| N6 | H4 per-critic values explained as not critic levels; "robust across the two DM6 specifications" | §4.4 DM6 |
| N7 | Notebook markdown synced: revision header with the post-hoc disclaimer, §4.2 design notes after the table, §4.3 tuned-settings commentary and grid-edge disclosure | notebook |
| N8 | Per-split critic-disjoint values displayed; revision 3–4 diagnostics saved (calibration by critic, ablation decomposition, length tables, critic-disjoint splits, nulls, H5 seeds, DM6 decomposition) | notebook 4.4e; `reports/tables` |
| N9 | Ranker α wording per fold | §4.3 |
| N10 | "A similar loss can apply"; Phase 5 reports the writer mix | §4.4 |
| N11 | Assumption (c) marked not testable in development; Italy vs non-Italy and with/without O'Keefe added to the Phase 5 sensitivities | §4.1; Phase 5 plan |
| N12 | "Data seen" column added to the revision 3 and 4 log, including the new outer-fold looks | run log |
| N13 | DM3 terms quoted verbatim (first five); DM4 top rules in confidence order; outlier and country wording softened | §4.4 |
| N14 | The 67 notes disclosed; covered by the 1,234-ID sensitivity | §4.2 |
