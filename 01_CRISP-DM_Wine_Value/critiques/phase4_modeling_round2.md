# Phase 4 · Modeling: Critic Round 2

- **Date:** 2026-11-07
- **Reviewer:** Claude critic (independent subagent session), persona from `critic_prompt.md`. Read-only; lockbox `points` blanked on load in every script; saved fold predictions checked to contain no fold-2 rows.
- **Draft reviewed:** Phase 4 revision 2

## Score: 7 / 10 · Major issues remaining: yes (3)

The DM1 re-selection is sound: the rule is inner-only, and it chose calibrated ridge (all OOF) over the named-OOF variant that did better on fold 3, so it wasn't steered by fold 3. DM3 is reported honestly, DM6 is the §1.3 model, and every headline number re-ran. The weak part is three new mechanism claims in 4.4.

## Task coverage
| Task | Output | Status |
|---|---|---|
| 4.1 | Modeling technique | Present (transformer rationale contradicted by 4.4) |
| 4.1 | Modeling assumptions | Partial (assumption (a) not what the evidence shows; (b) leans on an untested mechanism) |
| 4.2 | Test design | Present |
| 4.3 | Parameter settings | Present |
| 4.3 | Models | Present |
| 4.3 | Model descriptions | Present |
| 4.4 | Model assessment | Partial (three mechanism claims wrong or unsupported) |
| 4.4 | Revised parameter settings | Present |

## Round-1 issues
Resolved: 1, 3, 5, 6, 7, 8, 9, 10, 12, 14, 15, 16. Partly resolved: 2 (revision-2 log thin, stale superseded text in config), 4 (matched-control conclusion inverted, gap mechanism overclaimed), 11 (new grid edges), 13 (new rationale contradicted), 17 (run-time comment still wrong).

## Issues raised
| # | Severity | Issue | Suggested fix |
|---|---|---|---|
| 1 | MAJOR | **Matched-control conclusion is inverted.** Fold-3 ridge: no filter 7.1%, control 5.1%, design 1.4%. Data loss costs 2.0 pp (35%); removing the attributed notes costs 3.7 pp more (65%). Selected model: 0.3 pp loss vs 1.8 pp attribution | Rewrite; show the decomposition and the spread of the 3 control draws |
| 2 | MAJOR | **"Writer level is the main error source" is contradicted.** Knowing each critic's level cuts MAE 1.662 → 1.565 (6%); segment errors vary about as much. The anonymous-residual contrast is confounded (anonymous rows aren't reliably writer-held-out); the named-only ablation makes under-prediction larger | State what is shown; remove "dominated by" / "main error source" from §4.1, the summary and Phase 6; re-label assumption (a) as partly supported |
| 3 | MAJOR | **The note-length mechanism goes beyond its evidence.** On the design training sets dropping `n_words` gives 32.5 → 34.2%, 37.3 → 34.0%, 1.4 → 9.3%, 35.4 → 32.5%: helps 2 folds, hurts 2. Per-critic gains don't track slopes (Kostrzewa and DeSimone don't gain); the fold-3 gain is mostly Gregutt. Length works partly through level (fold-0 bias −0.65 → −0.16) | All-fold table; "fold-3-specific (mainly Gregutt), hurts folds 1 and 4, mechanism not established, overlaps with level"; keep the Phase 5 sensitivity as exploratory |
| 4 | MINOR | DM6: the mover list is wrong (Voss moves 0.44; the largest are Peartree, Dykes, Kostrzewa, Adams, Boone). Iijima, Peartree, Dykes have CIs excluding zero with opposite signs in A and B. Use "0.9–1.5". The sensitivity comes from both log price and province cells | Correct; name the sign-flippers; say the CIs exclude specification uncertainty; add the decomposition |
| 5 | MINOR | The DM3 chance baseline (0.04) ignores matching and term frequency: matched nulls are 0.098 (uniform) and 0.174 (frequency-weighted, 95th pct 0.209) | Report the frequency-weighted null; say profiles barely reproduce across writers |
| 6 | MINOR | The Phase 5 BSC3 decision rule is implicit; the secondary setting is strongly writer-led | State BSC3 is decided on the primary only; the secondary can't rescue it |
| 7 | MINOR | Lockbox exposure omits Southern Italy (567) and Lombardy (356): total 8,557 | Correct |
| 8 | MINOR | Revision-2 log has no times and omits analyses; superseded rule text in `config.py`; "about 10 minutes" (≈ 26 min) | Add times and all analyses; mark superseded text; fix comment; commit and tag before Phase 5 |
| 9 | MINOR | Inner scoring reuses OOF scores whose ridge models saw the inner fold's labels; mildly favours calibrated and stacked candidates | State it (it can't change ridge vs calibrated; could matter at the 0.012 margin vs the no-origin stack) |
| 10 | MINOR | Grid edges: ranker α = 8 in fold 3; stack trees = 25 in fold 1; L2 objective | Extend, or note |
| 11 | MINOR | H5 "not Monte Carlo noise" cites the critic's check, not a notebook cell | Add the seed check to the notebook |

## Single most important improvement
Rewrite the 4.4 error analysis (and its echoes in the summary, §4.1 and Phase 6) so that each mechanism claim matches its own numbers: reverse the matched-control conclusion, replace "main error source" with the measured 6%, and replace the length-slope story with the all-fold table. Then commit and tag before Phase 5.

## Changes made in response (revision 3)
No model, rule or selection changed in revision 3; every change is interpretation or a diagnostic (run log, revision 3).

| # | What I changed | Where |
|---|---|---|
| 1 | Verified and accepted: conclusion reversed. Decomposition table added (data loss vs attribution-specific, with control-draw range): fold-3 ridge 2.0 vs 3.7 pp, selected model 0.3 vs 1.8 pp | notebook 4.4c; summary; §4.4 |
| 2 | "Dominated by" / "main error source" / "writers, not wines" removed from §4.1, the summary, the error analysis and Phase 6. States what's shown: held-out groups under-predicted 0.35–2.08; calibration 1.83 → 1.66; per-writer level a further 6%; anonymous-residual contrast flagged as not evidence; named-only ablation noted. Assumption (a) marked partly supported; transformer omission restated as scope and compute | §4.1; §4.4; summary |
| 3 | All-fold length table (helps folds 0 and 3, hurts 1 and 4), per-critic table, entanglement with level; slope story and "most of the gap" claim removed; Phase 5 length sensitivity marked exploratory | notebook 4.4c; §4.4 |
| 4 | Mover list corrected; the three opposite-sign critics named; "within-specification CIs understate the uncertainty"; 0.9–1.5; decomposition table | notebook 4.4h; §4.4 DM6 |
| 5 | Matched nulls computed in the notebook (uniform 0.098; frequency-weighted 0.174, 95th pct 0.209); "barely reproduce across writers" and the BSC3 implication stated | clustering.matched_null; §4.4 DM3 |
| 6 | BSC3 decided on the primary setting only; the secondary can't rescue it | config; §4.4 |
| 7 | Exposure list and total corrected (seven regions, 8,557 rows) | §4.2 |
| 8 | Run log rebuilt with times from the session record and every revision 2 and 3 step; superseded config text marked; run-time comment corrected (about 25 minutes). Commit and tag before Phase 5 | run log; config; notebook 4.3 |
| 9 | OOF-reuse caveat stated, with the 0.012 margin | §4.2 |
| 10 | Edges disclosed (ranker α flat between 4 and 8; rejected stack's trees; L2 objective untried); not re-run | §4.3 |
| 11 | H5 seed check moved into the notebook (LB +0.02 to +0.17 pp, 20 of 20) | notebook 4.4h; §4.4 |
