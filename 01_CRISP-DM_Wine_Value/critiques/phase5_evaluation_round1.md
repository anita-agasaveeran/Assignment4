# Phase 5 · Evaluation: Critic Round 1

- **Date:** 2026-11-08
- **Reviewer:** Claude critic (independent subagent session), persona from `critic_prompt.md`. Read-only.
- **Draft reviewed:** Phase 5 revision 1 (report §5, executive summary, notebook §5, run log)

## Score: 6 / 10 · Major issues remaining: yes (7)

The lockbox was handled well. There is a sealed loader, a rehearsal with an equality check, a commit and tag before unsealing, and a single run. Every figure in the §5.1 pass/fail table matches `phase5_summary.csv` and the notebook output, and the calibration failure is disclosed honestly. The weakness is selective reporting and post-unsealing decisions. The draft leaves out a pre-registered sensitivity, the two strongest and weakest candidate rows, and a large drop in BSC2 under masking that bears directly on the pilot gate. It also filters the DM4 rules on lockbox lift inside "Approved models" and bases the GO decision on a "one-house pool" assumption that conflicts with the business setup. As a result the assessment of results and the decision are only Partial.

## Task coverage
| Task | Output | Status |
|---|---|---|
| 5.1 Evaluate results | Assessment of data mining results w.r.t. business success criteria | Partial: every pass/fail is correct, but the pre-registered "without length" sensitivity is computed and not reported, the candidate comparison is incomplete, and the masked-BSC2 result is missing |
| 5.1 Evaluate results | Approved models | Partial: the DM4 approval selects rules on the test set; the DM2 "robust to writer level" reasoning is not supported |
| 5.2 Review process | Review of process | Partial: the exposure inventory and phase audit are good, but the post-hoc inventory is incomplete, some report numbers have no notebook cell, and forking paths are not quantified |
| 5.3 Determine next steps | List of possible actions | Partial: five options are given, but "pilot the shortlist only" is missing and there is no cost or probability-of-success view |
| 5.3 Determine next steps | Decision | Partial: GO to a pilot is defensible, but the gate pass probability is not re-assessed using lockbox evidence and the ±1.5 stop threshold has no stated basis |

## Figures verified
- **§5.1 pass/fail table vs `phase5_summary.csv` and notebook cell 5.1c:** all match.
  - DM1: 31.5% (LB 30.2%); MAE 1.404 vs 2.051.
  - DM1b: frozen list +0.068; strict price mask +0.070.
  - BSC2: 0.736, +7.5 pp (LB +6.4).
  - BSC1: P@100 0.761; 1.95× winery track record (0.390); LB 1.755.
  - BSC3: 8 profiles, smallest 6.4%.
  - DM4: 55 of 88. BSC5: 6 of 6.
- **One mismatch in the masking row:** the round-1 list is +0.063 by my calculation (1.4677 − 1.4044), not +0.064.
- **Lockbox counts:** 17,848 rows; 17,796 after R-3; pool 7,288; 100,530 development rows. Pool shares are 50.4 / 24.0 / 21.0 / 4.6%. All confirmed from the parquet.
- **Italy = O'Keefe:** confirmed. In the lockbox she has 9,667 Italian rows and none outside Italy, and no other lockbox critic has an Italian row. After R-3 that is 9,644 rows, and the "not Italy" and "without O'Keefe" rows in `phase5_subsets.csv` are identical. Italian development rows are 96.4% anonymous.
- **Per critic, ridge → calibrated:** all eight reduction figures and all eight bias figures match `phase5_by_critic.csv`.
- **Shortlist and sensitivity figures:** all match.
  - Shortlist mix and the oracle P@100 of 0.84 (notebook output).
  - Ranker sensitivity: 0.64 / 0.85 / 0.85 / 0.64; simple rules 0.19–0.81; ranker 0.92.
  - Stack variants 0.757 / 0.764.
  - Per-critic top-10% lift from 1.29× (LB 1.19) to 3.07× (LB 2.64).
  - 1,234-ID sensitivity: 30.3% / +6.1 pp (LB +5.0) / 0.758.
  - BSC4: Brier 0.126 vs 0.169; mean P(90+) 0.319 vs value rate 0.216; band ±2.67 with 87% coverage.
- **H1–H6:** the lockbox values match `phase5_hypotheses.csv`.
- **H5 within-critic decomposition (5.1d):** recomputed and confirmed.
  - Krebiehl writes 32.4% of the ≤ $25 whites and 7.5% of the reds, with a 51.1% value rate for both colours.
  - Within-critic differences: Krebiehl 0.0, O'Keefe +4.2, Jenssen +6.2, Sullivan −7.5 pp; weighted +0.4 pp.
  - However, 5.1d uses the lockbox without the R-3 filter (6,337 rows against H5's 6,334). That explains the pooled +9.7 pp (run log) against +9.6 pp (table).
- **DM4:** 55 of 88 rules kept; median lift 3.113 → 2.032. Kept per grape: Cabernet Sauvignon 4/14, Syrah 0/3, Pinot Noir 8/15, Chardonnay 18/24, Riesling 8/9, Sauvignon Blanc 5/5. All confirmed. **The stated mechanism is not confirmed** (issue 4).
- **DM6:** 73,236 rows; SD 1.408 (noise-corrected 1.377); lockbox critic effects +1.16 / +0.66 / +0.61 / −0.81. All match.
- **Development comparison column:** matches the Phase 4 tables (fold 3: 23.0% / LB 21.9%; fold 4 BSC2: +10.8 pp; fold 0 DM1b: +0.07).
- **Did any step after unsealing change a model?**
  - The Phase 4→5 source diff (`features.py`, `scoring.py`, `evaluate.py`, `clustering.py`) only adds default-preserving parameters and refactors.
  - `phase4_fold_predictions.csv.gz` was rewritten during the unsealed run, but its uncompressed content is byte-identical (same md5) to the tagged version.
  - `config.py` differs from `a140a70` only in the `LOCKBOX_UNSEALED` flag.
  - No model, threshold or ranker changed. The DM4 rule set used for display did change (issue 3).
- **Computed but not reported:**
  - The pre-registered "calibrated ridge without length": MAE 1.377, 32.9%, bias +0.48.
  - Stack without origin: 36.8%, ±2 0.790 (best of all candidates).
  - Calibrated ridge (named OOF): 28.4%, ±2 gain **+4.0 pp**, which would fail BSC2.
  - Masked selected model: ±2 0.689, gain **+2.7 pp (LB +1.6)**. In development the masked gain was +12.5 / +27.3 / +12.9 / +8.2 pp.
  - H6 strong-record wines on the lockbox: 420 of 7,288 (5.8%); value rate 41.0% vs 20.4%; positive within every critic (O'Keefe +5.8 pp).

## Issues raised
| # | Severity | Issue | Suggested fix |
|---|---|---|---|
| 1 | MAJOR | **Selective reporting of the score models.** The §4.4 frozen plan lists "the calibrated ridge without note length" as a reported sensitivity. The notebook computes it (MAE 1.377, 32.9%, bias +0.48), but §5 never mentions it. The point 2 table also leaves out two candidates that are in `phase5_score_models.csv`: stack without origin (36.8%, best of all) and calibrated ridge with named OOF (28.4%, ±2 gain +4.0 pp, which **fails BSC2**). So the reader can't see that the selected model ranks 4th of 5. They also can't see that the near-tied alternative calibration (inner MAE 1.785 vs 1.762) would have failed a business criterion. | Show the full lockbox table: all five candidates plus the without-length row, each with MAE, bias, reduction (LB) and ±2 gain (LB), labelled "reported, not selecting". Add one sentence saying BSC2's pass depended on a 0.023-point inner-MAE tie-break between calibration variants. Add the without-length result to the R9/length discussion: dropping length lowers the bias from +0.69 to +0.48. |
| 2 | MAJOR | **BSC2 collapses under masking, and the draft calls DM1b "robust".** With the frozen verdict list masked, the selected model's ±2 accuracy falls from 0.736 to 0.689 and its gain from +7.5 to **+2.7 pp (LB +1.6)**. That is below the +5 pp BSC2 target and below the pilot gate's +5 pp. In development, masking left the gain almost unchanged (+12.5 / +27.3 / +12.9 / +8.2 pp), so this is new behaviour. Masking is the project's only proxy for A1/R1 (retailer notes). DM1b passes only because it measures MAE, not the ±2 gain that the business gate uses. | Report masked ±2 and gain for all mask variants, next to the development values. Replace "DM1b is robust" with an accurate statement: MAE is robust, but the gain that the pilot gate uses is not. Carry this into §5.3 as the main reason the BO2 part of the pilot gate may fail. |
| 3 | MAJOR | **DM4 approval is selection on the test set.** "Approved for display: the 55 rules that kept lift ≥ 1.5 on the lockbox" uses lockbox results to choose which rules ship. That conflicts with the run log's own rule (critique "may not change a model, rule, threshold or selection") and with §5.2's claim that nothing post hoc changed a selection. 17 of the 88 rules have lockbox support below 0.1%; for example, oak + raspberry → Pinot Noir rests on about 6 notes. There is no uncertainty on any lockbox lift. | Approve the frozen rule set (88, or the 84 pruned) as the model, and show each rule's lockbox lift as information. Alternatively, keep the 55-rule filter but label it a post-hoc display choice, list it in the run log, and require pilot confirmation. In either case add a minimum test support or a bootstrap LB before a rule is called "kept". |
| 4 | MAJOR | **Unsupported mechanism for DM4 failures.** "Rules fail in grapes that are rare in an Italy-heavy lockbox" doesn't fit the grape mix. Chardonnay shrinks most (10.3% of development rows → 2.8% of lockbox rows) yet keeps 18 of 24 rules. Syrah barely changes (4.0% → 3.5%) yet keeps 0 of 3. Riesling becomes more common (3.8% → 5.5%) and keeps 8 of 9. | Delete the claim or replace it with a tested one: a per-grape table of development vs lockbox share, support and lift, plus an analysis of which critics write the failing rules' notes. Otherwise state "why is not established". |
| 5 | MAJOR | **The post-hoc inventory is incomplete and some numbers can't be traced.** §5.2 and the run log say "only 5.1d" was post hoc. But several decisions were made after unsealing and are not logged as post hoc: the DM4 55-rule filter, the "less accurate for Italian wines" display label, demoting P(90+) to a "relative indicator", and the ±1.5 stop threshold. Some report numbers have no notebook cell, despite the header saying every number comes from one: the DM4 per-grape kept counts, the median lifts 3.11 → 2.03, and the Krebiehl colour shares (these are in 5.1d). Cell 5.1d also has `execution_count` None and skips the R-3 filter (6,337 vs 6,334 rows), which is why the pooled value is +9.7 in the run log and +9.6 in the table. | Add a labelled post-hoc cell (5.1e) for the DM4 breakdown. Re-run 5.1d on `lb_test`, not the raw lockbox. List every post-unsealing decision in the run log, each with the evidence that drove it. Correct the §5.2 Phase 5 row. |
| 6 | MAJOR | **The DM2 approval claims are not supported.** The draft says the ranker is "robust to the writer level within a pool" and requires that "Shortlists are ranked within one house's pool". But §1.1 and A1/A7 describe each cycle's ~1,000 candidates as notes from many importers, producers and staff. A real pool therefore has many writers, like the lockbox, where writer level clearly distorts the shortlist: Jenssen 0% and Sullivan 7.5% of the top 10% against pool shares of 4.6% and 24%, and an oracle P@100 of 0.84 against 0.76. Ranking within one house would also shrink pools well below 1,000; at 500 candidates P@100 is 0.64. | State that the mixed-pool lockbox figure (0.76) is the relevant estimate and approve DM2 on that basis. Drop the "one house's pool" condition, or define a "house" and estimate pool sizes per house. Report P@100 at those sizes from `phase5_ranker_sensitivity.csv`. |
| 7 | MAJOR | **The decision doesn't use the lockbox evidence about the pilot gate.** The pilot power (80% at 400 wines) was computed for fold-3-like effects. The lockbox shows per-writer ±2 gains of +1.4 (O'Keefe), +13.9, +20.1 and −16.4 pp (Jenssen), plus +2.7 pp under masking. For a pilot with one house's writers, the chance of meeting "+5 pp, LB > 0" is far below 80%. The ±1.5-point stop threshold has no stated basis and is too loose: O'Keefe's +1.19 bias already cut the gain to +1.4 pp. There is also no option to pilot the shortlist alone, nor any pilot cost (A5: ~$25 per sample). | Recompute the pilot pass probability with the lockbox per-writer and masked effects, for example by resampling writers. Derive the stop threshold from the observed bias-to-gain relationship. Add option F, "pilot BO1 as the gate and keep BO2 as secondary", with costs. Then restate the decision and its conditions. |
| 8 | MINOR | Calibration is described as shifting "every prediction up by … about +0.6 points". It is an affine map (a + b·score) that compresses the scale (§4.4): the bias shift is +0.47 for Krebiehl, +0.53 for O'Keefe, +0.62 for Sullivan and +0.83 for Jenssen. | Report the fitted a and b, and describe the map as a compression plus an offset. |
| 9 | MINOR | Point 1 says the "baseline's MAE gap (2.05 vs 2.26)" is larger. A lower baseline MAE means a *stronger* baseline, so the wording is wrong. Also, "easier than fold 3" doesn't hold for O'Keefe, the largest writer (22.7%, vs fold 3's 23.0%). | Rephrase. Say the lockbox was easier on average, but its largest writer did no better than fold 3. |
| 10 | MINOR | The executive summary drops caveats that the body states. "Named by both blind reviewers" omits that writer independence is not shown. "All six replicate" omits that H5 is not a buyer insight. The masked-BSC2 drop and the 10 pp over-prediction of P(90+) are also missing. | Add one clause each to the Profiles, Hypotheses and Caveats bullets. |
| 11 | MINOR | The lockbox pass table marks DM5(a) ✅, but it is a full-corpus synthetic test, not a lockbox result. The BSC1 "weakest development fold" column names fold 0, but fold 1 has the lowest P@100 (0.63). | Mark DM5(a) "n/a (Phase 4, synthetic)". Choose the weakest fold per metric and say how. |
| 12 | MINOR | Small number mismatches: round-1 masking +0.064 vs +0.063; H5 pooled +9.6 vs +9.7 (from issue 5). | Fix both. |
| 13 | MINOR | The H4 lockbox LB (0.76) is an SD of four critic effects with a winery bootstrap, which can't capture sampling of critics. The §5.1 table presents it without that caveat. | Add the pre-registered limitation to the H4 row and to §5.2. |
| 14 | MINOR | H6 is under-reported, though it is the hypothesis that actually satisfies BSC5's "H5 or H6" clause. The draft doesn't report the lockbox strong-record count (420 of 7,288, 5.8%, against 0.73% in development) or the within-critic check (positive for all four critics; O'Keefe only +5.8 pp). | Report both. Say H6 is the only actionable hypothesis that replicates within critics. |
| 15 | MINOR | DM6: "O'Keefe … least well identified" holds by number of partner critics, but Jenssen's SE (0.33) is larger than hers (0.23). DM6 is approved as a range across specifications A and B, but B was not re-run with the lockbox critics. | Word the claim by SE and partners. Run or explicitly omit specification B with lockbox critics. |
| 16 | MINOR | BSC3 passes by a thin margin. Reviewer 1 gave the minimum confidence (3) to 6 of 8 profiles. There is no inter-reviewer agreement measure, and the reviewers disagree on A6 (oak with creamy, tropical terms vs "oak-driven ripe red"). | Report each profile's confidence and a simple agreement check, and note the margin. |
| 17 | MINOR | **Audit trail.** The `LOCKBOX_UNSEALED` flip, all `phase5_*.csv` files and the report are uncommitted. The rehearsal assertion compares against `runs[3]` from the same session, not against the tagged Phase 4 files. | Commit and tag the post-unseal state, with table hashes recorded in the run log. Add a notebook check that the regenerated `phase4_fold_predictions` content hash equals the tagged one; I confirmed it does. |
| 18 | MINOR | **Forking paths are named but not quantified.** §5.2 doesn't say how many candidate and setting comparisons were seen on outer folds. It also doesn't note that the revision-1 choice (stack, 34.0%, ±2 0.750) beat the post-hoc revision-2 choice (31.5%, 0.736) on the lockbox. | Count the outer-fold looks per goal. State plainly that the post-hoc revision did worse on the clean holdout. |

## Single most important improvement
Report everything the lockbox run computed, and let it drive the decision. Five results belong in §5.1, labelled as non-selecting:
- the full candidate table, including the BSC2 failure of the named-OOF calibration;
- the pre-registered without-length sensitivity;
- the masked ±2 gain (+2.7 pp, against +8 to +27 pp in development);
- the per-writer ±2 gains (−16 to +20 pp);
- the mixed-pool shortlist distortion.

Then rebuild §5.3 on that evidence. Re-estimate the pilot gate's pass probability per writer and under masking. Derive the stop threshold from the bias-to-gain relationship. Consider making BO1, the robust result, the deciding gate. Revert the DM4 "55 lockbox-kept rules" filter to the frozen rule set, or log it as post hoc. As written, every individual number is correct, but the selection of numbers and the post-unsealing choices tilt the evaluation toward GO more than the evidence supports.

## Changes made (revision 2)
| # | Change |
|---|---|
| 1 | §5.1 point 2 now shows every candidate on the lockbox with inner MAE, bias, reduction (LB) and ±2 gain (LB), plus the pre-registered without-length sensitivity (32.9%, bias +0.48). It states that the selected model ranks 4th of 5 and that the named-OOF calibration, 0.023 behind on inner MAE, would have failed BSC2 (+4.0 pp) |
| 2 | New point 5 (post hoc, 5.1e): masked ±2 gains for every mask variant next to the development folds (+2.7 pp, LB +1.6 on the lockbox), and by critic (O'Keefe −5.8 pp). The DM1b row now says MAE survives masking but the ±2 gain does not. Carried into §5.3 as the main reason the BO2 part of the gate may fail |
| 3 | DM4 is approved as the frozen 88 rules; lockbox lifts are information only. The 55-rule filter is withdrawn and listed as a withdrawn post-unsealing choice. Support counts added (44 kept with ≥ 30 notes; 17 rules below 0.1%) |
| 4 | The "rare grapes" mechanism is withdrawn. New per-grape table (5.1f); "why is not established" (Spearman 0.17 between share change and rules kept) |
| 5 | 5.1d re-run on the R-3-filtered lockbox (6,334 rows, +9.6 pp). New cells 5.1e–5.1h hold every post-hoc number. §5.2 has a complete table of post-unsealing decisions, each with its evidence; the run log lists them |
| 6 | The mixed-pool lockbox figure (P@100 0.76) is the stated basis for approving DM2; the "one house's pool" condition is withdrawn. Pool-size sensitivity kept (0.64 at 500, 0.85 at 2,000) |
| 7 | §5.3 now opens with a simulation of the pre-registered gate (5.1h) per writer and under masking: BO1 0.995 and BO2 0.805 in the mixed pool, BO2 0.195 masked. The stop threshold is ±1.0 point, from the gain-vs-offset table (point 7). Option F (shortlist judged on BO1, band on BO2) added and chosen; cost ≈ $10,000 (400 × $25, A5) |
| 8 | Calibration reported as points = 7.957 + 0.917 × ridge score, a compression plus an offset; per-critic shifts +0.47 to +0.83 |
| 9 | Point 1 reworded: the lockbox baseline is stronger, the margin still larger, and O'Keefe (22.7%) is no better than fold 3 |
| 10 | Executive summary: profiles (low confidence, writer independence not shown), hypotheses (only H6 within critics; H5 not a buyer insight), masked gain +2.7 pp, P(90+) over-prediction, pilot pass chances and cost |
| 11 | DM5(a) marked n/a. Development column now gives the weakest fold per metric (BSC1: P@100 0.63 fold 1; lift 1.55×, LB 1.47 fold 0) |
| 12 | Round-1 list +0.063; H5 pooled +9.6 pp throughout |
| 13 | H4 row and §5.2 note the four-critic limitation |
| 14 | H6: 420 of 7,288 (5.8%) vs 0.73% in development; 41% vs 20%; positive within every critic. Stated as the only actionable hypothesis that replicates within critics |
| 15 | DM6 identification worded by SE and partners. Specification B run with the lockbox critics (SD 0.98; Sullivan and Jenssen swap order) |
| 16 | BSC3: per-reviewer confidences, the margin (two confidence-2 answers would fail it), agreement on 7 of 8 profiles, A6 disagreement |
| 17 | Row-level lockbox predictions saved; 5.1a checks the Phase 4 predictions' content hash against the tagged file; the re-execution reproduced all 13 tables (SHA-1s in the run log). Commit and tag of the post-unseal state await the project owner's go-ahead |
| 18 | §5.2 counts the forking paths per goal and states that revision 1's stack (34.0%, 0.750) did better on the lockbox than the revision-2 choice (31.5%, 0.736) |
