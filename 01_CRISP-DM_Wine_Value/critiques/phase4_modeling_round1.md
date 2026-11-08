# Phase 4 · Modeling: Critic Round 1

- **Date:** 2026-11-07 (first attempt failed on a network error before reviewing anything; rerun with the same brief)
- **Reviewer:** Claude critic (independent subagent session), persona from `critic_prompt.md`. Read-only. Every analysis script blanked the `points` of lockbox rows on load; lockbox rows were used only for text, counts and fold membership.
- **Draft reviewed:** Phase 4 revision 1

## Score: 6 / 10 · Major issues remaining: yes (5)

The outer evaluation is sound and every figure re-run matched. The interpretation is the weak part: four headline conclusions fail independent checks (the DM1 choice, "8 stable flavour profiles", the DM6 critic effects, "optimism found and fixed"), and the claim that selection rules came before fitting has no evidence.

**Clean checks:** no target leakage in the stack (out-of-fold text scores, winery features, categories and test scores all come from training); code uses outer folds only in the stated selection rules; bootstrap and simulation usage correct; H1–H6 match their pre-registered wording.

## Task coverage
| Task | Output | Status | Note |
|---|---|---|---|
| 4.1 | Modeling technique | Present | Calibrated ridge never listed; transformer rationale wrong |
| 4.1 | Modeling assumptions | Partial | Only the writer offset is tested; reliance on anonymous notes for Italy unstated; DM3 assumption refuted |
| 4.2 | Test design | Partial | Outer design strong; inner flaw (#1); pre-registration unevidenced (#2); R8 residue unmeasured (#4); DM3 single split (#3) |
| 4.3 | Parameter settings | Present | Grid-edge and tree-count weaknesses |
| 4.3 | Models | Partial | `models/` empty; no fold predictions saved |
| 4.3 | Model descriptions | Partial | Selected ranker, NMF, FP-Growth undescribed; "text score" mislabelled |
| 4.4 | Model assessment | Partial | Accurate against targets; mechanism claims unsupported |
| 4.4 | Revised parameter settings | Partial | DM3 only and fragile; DM1 unrevised despite inner evidence |

## Issues raised
| # | Severity | Issue | Suggested fix |
|---|---|---|---|
| 1 | MAJOR | **The DM1 stack is dominated.** A two-parameter recalibration of the OOF ridge score gives MAE 1.755 / 1.506 / 1.719 / 1.609 (mean 1.647) vs the stack's 1.748, and fold-3 reduction 24.0% vs 13.8%. Origin inputs reverse the recalibration (fold 3: −3.1% with origin, +24.2% without). OOF residuals differ between named (+0.64 to +1.73) and anonymous rows (−0.04), so anonymous rows aren't writer-held-out. Inner MAE already prefers text-only in all four folds. Fold-3 trees "316" is an average no inner fold produced ([28, 76, 846]). Mechanism not proven | Add calibrated ridge and stack without origin; compare on inner folds first; apply the attribution filter inside inner folds; replace mean-best-iteration; say fold results are seen and the lockbox stays the unbiased test; update `SELECTED_DM1` |
| 2 | MAJOR | **"Pre-registered before any Phase 4 model was fitted" has no evidence.** The block is uncommitted, `config.py` was saved after `cv.py`, `scoring.py`, `evaluate.py`; outcomes sit in the same file; `PROFILE_STOPWORDS` look data-informed | Reword; add a run log of earlier fits; state stop-list provenance; commit and tag before any Phase 5 run and pin the hash in §5 |
| 3 | MAJOR | **"8 stable flavour profiles" is unsupported.** Other winery seeds give min Jaccard 0.538, 0.538, 0.111, 0.176, 0.176. Profiles are largely writer styles (profile 2 is 76% Voss vs base 23%; V with critic 0.36 vs 0.32 with colour). Critic-disjoint halves collapse (mean Jaccard 0.14). Several labels aren't flavours | ≥ 10 seeds, critic-disjoint splits, profile × critic table; reduce writer vocabulary or balance, rerun the frozen rule; if it fails, say so. Phase 5: blind naming on both vocabularies, primary declared now, term lists only |
| 4 | MAJOR | **"Optimism found and fixed" overclaims.** Fold 3 keeps 4,407 of 8,596 top-guess notes; dropping all takes the stack to 11.8%. No control: about a third of the MAE change is plain data loss. 11.9 → 8.9 is unexplained. Fold 3 isn't a fair lockbox proxy (36% of anonymous notes top-guess fold 3, 5–9% for lockbox critics) | "Reduced", not "fixed"; CV analogue of the Phase 5 sensitivity on all folds; matched control; MAE column; explain the gap; state the asymmetry |
| 5 | MAJOR | **DM6 isn't the §1.3 technique.** §1.3 promises score ~ wine attributes + critic; §4.1 substituted mean residuals, each relative to a different baseline. With fixed effects two signs flip and Kostrzewa, not Peartree, becomes the extreme. H4 itself is unaffected | Fit the §1.3 model on all named development rows with a common baseline; CIs clustered by winery; report overlap identification; keep H4 separately; dated amendment for any change |
| 6 | MINOR | LBs don't bound new-writer risk. Fold-3 reduction by critic: Gregutt 8.7%, Iijima 15.0%, Czerwinski 21.4%; DeSimone −2.2% in fold 4 | Per-critic table; state that LBs condition on the writers present |
| 7 | MINOR | "2–4% smaller" is wrong (19–25%); §3.5 vs §4.2 R8 counts unreconciled; 1,234 vs "1,257" top-guess notes | Correct; reconcile; freeze the Phase 5 sensitivity set as an ID list |
| 8 | MINOR | "Robust to the writer offset" holds only for one-writer pools: critic-level centring raises P@100 in folds 3 and 4 | Rewrite; report shortlist mix by writer and value base rates |
| 9 | MINOR | H5's signs flip by fold (−7.9 / −3.8 / +6.9 / +2.8 pp); within-critic difference −1.1 pp | Keep the verdict, disclose per-fold table, not a buyer insight |
| 10 | MINOR | H6's strong group is 283 of 38,602 wines; H5 provenance text is stale | Report group sizes; correct provenance |
| 11 | MINOR | α at grid edge in 4 of 8 cells; ranker α tuned on all-wine MAE; L2 objective for an MAE target; early stopping tracks both metrics | Extend the grid; show all folds; `first_metric_only` or `objective="l1"`; tune the ranker on inner pool precision |
| 12 | MINOR | "Text score" is the full ridge, so "75% from text" misleads; ranker, NMF, rules undescribed; `models/` empty | Rename; describe them; save fold predictions |
| 13 | MINOR | Fallback scope misapplied to transformers; "no GPU" ignores Colab; "already meets every target" is true only of the stack | Restate as a scope decision |
| 14 | MINOR | Ridge's strongest negatives ("strange", "sour", "watery") aren't on the frozen list, so ≤ 0.10 doesn't show independence from verdict language; masked DM1 not reported | Extended-list sensitivity; report DM1 on the masked model |
| 15 | MINOR | Selected DM2 outputs no P(90+); no band method; BSC4 needs both, and "decided in Phase 6" comes after the lockbox. DM5(b)/(c), retrieval and outlier check missing from §4; no topic coherence | Freeze the mapping before Phase 5; add one line each |
| 16 | MINOR | 35 of 88 DM4 rules have confidence < 0.20; 8 are no better than a parent; some consequents aren't grapes; 52 of 82 keep lift ≥ 2 | Report confidence and a pruned count; "style or grape" rules |
| 17 | MINOR | §1.1 and config header still say every target is met; no test of `fit_stack` OOF integrity; "≈ 20 minutes" comment is wrong | Forward note; leakage unit test; fix the comment |

## Single most important improvement
Fix the DM1 model first: add calibrated ridge and the stack without origin, compare on inner critic-held-out folds, repair the inner design so anonymous rows don't mix writer-held-out and writer-seen regimes, and reselect as a dated revised setting.

## Changes made in response (revision 2)
| # | What I changed | Where |
|---|---|---|
| 1 | Verified first: refit reproduces the critic's numbers. **Revised DM1 rule written to `config` before rerunning**: inner critic-held-out MAE chooses, outer folds only confirm. Inner design repaired (anonymous notes go to their top-guess critic's inner fold; all inner scores on named rows). Candidates added: calibrated ridge (all OOF, named OOF), stack without origin. Trees from a pooled inner curve. **Result: calibrated ridge (all OOF) selected**, inner MAE 1.762, fold-3 reduction 23.0% (LB 21.9%). The repair did not rescue the stack; the mechanism behind origin hurting is reported as unproven. Disclosed as post-hoc; the lockbox stays the unbiased test | config; cv.inner_groups; scoring; evaluate.score_candidates / select_inner; §4.1–4.4 |
| 2 | Claim reworded. New `reports/phase4_run_log.md` built from the session record: design written 22:29, first fit 22:30, **two fold-3 outer looks before the full run**, every later change listed. `PROFILE_STOPWORDS` labelled as judgement. Phase 4 commit to be tagged before Phase 5 | run log; config header; cv docstring; §4.2 |
| 3 | **Multi-split rule written before the scan**: 10 winery splits (≥ 8 passing) plus three critic-disjoint splits; 3 vocabularies × 2 fit sets. Selected: **lexicon vocabulary, NMF, k = 8** (10 of 10 splits; V with critic 0.17, down from 0.37). **No setting reaches 0.5 on critic-disjoint splits (best 0.23)**, so writer independence is reported as not shown. Profile × writer table, UMass coherence, outlier and no-term examples. Phase 5 primary and secondary settings declared; reviewers get term lists only | clustering; config DM3_*; §4.4 DM3 |
| 4 | "Fixed" withdrawn. Ablation on all four folds with baseline MAE, a province-matched control (3 draws), "all top-guess dropped" (Phase 5 analogue) and named-only. Most of the fold-3 ridge change is data loss; the selected model moves ≤ 2 pp under any filter. **The 11.9 → 7.1/8.9% gap rebuilt step by step: data and text cleaning don't explain it; the Phase 4 inputs do, mainly note length** (writer-specific length slopes). Length found on an outer fold, so it becomes a Phase 5 sensitivity, not a change. Fold-3 vs lockbox asymmetry stated (35.7% vs 5.1% of anonymous top guesses) | evaluate.ablation; notebook 4.4c; §4.4 |
| 5 | DM6 now the §1.3 model: within-cell critic fixed effects on all named development rows, winery-clustered CIs, connected-component check, partner counts. Two specifications (SD 1.49 and 0.93, r = 0.56); six critics robust in sign. H4 kept as its own statistic | insights.critic_fixed_effects; §4.1; §4.4 DM6 |
| 6 | Per-critic MAE-reduction table (Gregutt 15.5%, DeSimone −1.0%); stated that LBs condition on the writers present | evaluate.per_critic_table; §4.4 |
| 7 | "19–25% smaller" corrected; §3.5 counts reconciled (different classifier fit); Phase 5 sensitivity set frozen as 1,234 IDs | §4.2; `phase5_sensitivity_anon_ids.csv` |
| 8 | Claim rewritten; writer mix of the top 10% and oracle critic-level P@100 (fold 3 0.68 → 0.74, fold 4 0.64 → 0.67); value base rates in the DM2 table | evaluate.shortlist_mix; §4.4 DM2 |
| 9 | H5 per-fold and within-critic (−1.1 pp) disclosed; called a composition effect, not a buyer insight | notebook 4.4h; §4.4 |
| 10 | H6 group sizes reported (283 of 38,602); H5 provenance text corrected | config.HYPOTHESES; §4.4 |
| 11 | α grid extended to 4 and 8 (DM1 stays at 1–2; ranker moves to 2–8); all folds shown; ranker α tuned on inner pool precision; early stopping replaced by a pooled inner curve | config; scoring.tune_ridge / fit_stack |
| 12 | Renamed to "ridge score" and described as the full ridge; descriptions of the selected ranker (price coefficient), NMF and FP-Growth added; fold predictions saved | scoring; §4.3; `phase4_fold_predictions.csv.gz` |
| 13 | Transformer omission restated as a scope decision with its real reason | §4.1 |
| 14 | Stress-test mask (each fold's 200 strongest ridge words): up to 0.17, fold-3 reduction 18.9%; DM1 targets reported on the masked model | evaluate.MASKS; §4.4 |
| 15 | P(90+) map and 80% score band frozen and checked on held-out folds (Brier below base rate in every fold; coverage 77–87%); DM5(b)/(c), retrieval, outlier check and coherence lines added | evaluate.app_mappings; §4.4 |
| 16 | Pruned count (84), confidence ≥ 0.2 count (53), lift ≥ 2 replication (52 of 82), "style or grape" wording | descriptors.prune_rules; §4.4 |
| 17 | Forward note in §1.1 and the config header; OOF-integrity test (perturbed target leaves its own OOF unchanged); inner-group, calibration, selection, DM6 and DM3 rule tests; run-time comment corrected | tests/test_phase4.py; §1.1 |
