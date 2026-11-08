# Phase 5 · Evaluation: Critic Round 2

- **Date:** 2026-11-08
- **Reviewer:** Claude critic (independent subagent session), persona from `critic_prompt.md`. Read-only.
- **Draft reviewed:** Phase 5 revision 2

## Score: 8 / 10 · Major issues remaining: yes (2)

Revision 2 is a substantial, honest repair. Every round-1 MAJOR issue was addressed in substance, not just claimed. The full candidate table, the without-length sensitivity, the masked ±2 collapse, the withdrawn DM4 filter, the withdrawn "one house" condition and a pilot-gate simulation are all present, and every figure I recomputed matches the CSVs, the row-level predictions or the saved notebook output, to rounding. All 13 first-run tables still match their recorded SHA-1s. Two problems remain, and both sit in the decision (5.3).

**First: the decision rests on asymmetric evidence.** The band is judged on masked notes (BO2 pass rate 0.195), but the shortlist is judged only on unmasked notes (BO1 0.995). The stated reason for not masking BO1 is wrong: the ranker is a ridge on the *note text* plus price, so masking changes its side of the lift ratio.

**Second: the new ±1.0 stop rule is defined per "house", a unit that is never defined, and it has no sample size or uncertainty.** Applied pilot-wide, it would not have caught the very O'Keefe failure that motivated it.

**On Option F:** it is a legitimate pre-pilot amendment in substance. Neither pre-registered bar is lowered, each output is gated by its own pre-registered test on fresh data, and the conjunctive gate is still reported. But it *is* a post-unsealing change to a pre-registered deployment rule, and the stated motive is that the original gate would probably fail. It is disclosed well in §5.2, the run log and notebook 5.3. It is not disclosed in the executive summary or §1.1, and it is not yet timestamped by a commit.

**On the ±1.0 threshold:** it is legitimate, since it tightens a rule that had no pre-registered value.

**Selective reporting:** only minor residue remains, and none of it tilts toward GO.

## Round-1 issues
| # | Fixed? | Note |
|---|---|---|
| 1 | Yes | The point 2 table matches `phase5_score_models.csv`: MAE 1.296 / 1.327 / 1.354 / 1.404 / 1.467, so the frozen model is 4th of 5. Named-OOF gain is +3.99 pp; without length 1.377 / 32.9% / +0.48. The tie-break sentence is added. |
| 2 | Yes | Masked gains match 5.1e for every fold and the lockbox: +2.7 (LB +1.6), +4.5, +2.7, +2.5. Per critic +1.4→−5.8, +13.9→+12.1, +20.1→+16.8, −16.4→−17.3, recomputed from the predictions. The DM1b row is reworded. |
| 3 | Yes | The frozen 88 rules are approved and lockbox lifts are information only. Support counts are added: 44 kept with ≥ 30 notes, and 17 rules below 18 notes. No LB is added, but its absence is stated. |
| 4 | Yes | The mechanism is withdrawn. The per-grape table matches 5.1f, and the Spearman is 0.17. |
| 5 | Yes (small residue) | 5.1d now uses `lb_test` (6,334 rows, pooled +9.65 pp, weighted +0.35 pp). Cells 5.1e–5.1h are executed and saved, and the run log lists every decision. Two per-critic H5 values were carried over from the old 6,337-row version (issue 6). |
| 6 | Yes, but see new issue 2 | The mixed-pool basis is stated and the condition withdrawn. The undefined term "house" returns in §5.3 conditions 4 and 7. |
| 7 | Partly | The simulation, cost, option F and a derived threshold are all added. Still missing: BO1 under masking; resampling across writers or houses (the rates are conditional on the lockbox mix); a stop-rule unit and sample size (new issues 1, 2, 4). |
| 8 | Yes | I verified points = 7.957 + 0.917 × ridge: the shift is +0.90 / +0.66 / +0.33 at 85 / 88 / 92. Per-critic shifts are 0.475 / 0.525 / 0.618 / 0.830. |
| 9 | Yes | Point 1 is reworded correctly. |
| 10 | Yes (wording) | The caveats are added. "Mostly at the lowest passing confidence" overstates it: 8 of 16 ratings were 3 (issue 6). |
| 11 | Yes | DM5(a) is n/a. The weakest-fold column is verified: P@100 0.632 (fold 1); 1.553×, LB 1.470 (fold 0); BSC2 0.648, +10.8 (LB +9.6), fold 4. |
| 12 | Yes | +0.063 (1.4677 − 1.4044); H5 +9.6 pp. |
| 13 | Yes | Present in the H4 row and in §5.2. |
| 14 | Yes, overclaimed | The counts match 5.1g (420 of 7,288; within-critic rates). "Holds within every critic" has no uncertainty attached (issue 5). |
| 15 | Yes | Spec B was run: SD 0.984 (0.924 noise-corrected); Sullivan and Jenssen swap order. Verified against `phase5_dm6_fixed_effects_B.csv`. |
| 16 | Yes | Confidences verified in 5.1b: reviewer 1 gave 3 to A1 and A4–A8, reviewer 2 to A5 and A6. The 7/8 and 6/8 logic is correct. |
| 17 | Partly | The 5.1a content-hash assert has been added, and I matched all 13 SHA-1s. The post-unseal state, revision 2 and the option F amendment are still uncommitted (git status). The 5.1c assert covers only 6 of the 13 tables. |
| 18 | Yes | Forking paths are counted, and the rev-1 vs rev-2 lockbox comparison is stated. It omits that rev-1's stack also survives masking (issue 7). |

## Task coverage
| Task | Output | Status |
|---|---|---|
| 5.1 Evaluate results | Assessment of data mining results w.r.t. business success criteria | **Present.** Pass/fail, all candidates, subsets, masking, writer level, BSC3 margin, DM4, H1–H6 and DM6, with post-hoc work labelled. One gap: the shortlist under the retailer-note proxy (issue 1). |
| 5.1 Evaluate results | Approved models | **Present.** Every approval is tied to evidence and scoped to the pilot; DM4 is approved as frozen. |
| 5.2 Review process | Review of process | **Present.** Exposure inventory, a complete list of post-unsealing decisions, counted forking paths and a phase-by-phase audit. The Option F framing is slightly evasive (issue 3). |
| 5.3 Determine next steps | List of possible actions | **Present.** Options A–F, each with for/against, cost and verdict. |
| 5.3 Determine next steps | Decision | **Partial.** GO to a pilot is defensible. But the per-output rule rests on a like-for-unlike comparison (issue 1), and the stop rule cannot be applied unambiguously (issue 2). |

## Figures verified
- **Pass table and summary:** they match `phase5_summary.csv` and cell 5.1c.
  - 31.5% (LB 30.2%); MAE 1.404 vs 2.051.
  - +0.068 / +0.063 / +0.070.
  - 0.736, +7.5 pp (LB +6.4).
  - 0.761, 1.95×, LB 1.755.
  - 8 profiles, shares 6.4–23.4%, 0.8% unassigned.
  - 55 of 88; 6 of 6.
- **From row-level predictions (17,796 rows; pool 7,288):**
  - Within ±2 0.7360 and gain +7.48; masked +2.73; plain ridge masked +9.14.
  - Bias +0.686 overall, +0.766 masked; pool mean residual +0.837.
  - Italy is exactly O'Keefe's 9,644 rows.
  - Mean P(90+) 0.319 vs value rate 0.216; Brier 0.126; band (±2.671) coverage 0.873.
- **Per critic:** all reduction and bias figures, ridge → calibrated, match `phase5_by_critic.csv`. Critic-pool lifts 1.29–3.07× (LB 1.19–2.64) are confirmed. Shortlist mix and the oracle 0.84 are confirmed.
- **Ranker sensitivity:** 0.635 / 0.852 / 0.852 / 0.637; rules 0.190–0.805; ranker 0.919.
- **Stack variants and analogue-note run:** stack variants 0.757 / 0.764. The 1,234-ID run gives 30.3% (LB 29.0%) / +6.1 (LB +5.0) / 0.758, 1.93×, LB 1.74.
- **Pilot simulation:** every reported cell matches `phase5_pilot_simulation.csv`.
  - Dev BO2 0.990–1.000 (gain +10.9 to +27.9); BO1 0.775–0.950; both 0.775–0.945.
  - Lockbox mixed 0.805 / 0.995 / 1.73×.
  - Per-writer rows; masked mixed 0.195 (+2.3); masked O'Keefe 0.000 (−5.7).
- **Pilot code:** I read `pilot_pass_rate` and it implements the pre-registered gate correctly.
  - BO2: gain ≥ 5 pp with a 10%-quantile winery-bootstrap LB > 0.
  - BO1: top-20% lift ≥ 1.3× the per-pilot best rule, LB > 1.0. Choosing the best rule per pilot is conservative for BO1.
- **Gain vs offset:** every reported cell matches `phase5_gain_vs_offset.csv`.
  - Mixed: +0.84→+7.5, +1.09→+2.8; best +14.1 at +0.09.
  - O'Keefe: +1.12→+7.2, +1.37→+1.4; best +20.6 at −0.13.
  - Fold 3 values correct, except +1.48 gives +3.5, not +3.6.
  - By linear interpolation, the mixed pool crosses +5 pp at about **+0.97** and **−1.05**.
- **H5 within critic on `lb_test`:** Krebiehl −0.03, O'Keefe **+4.13**, Jenssen +6.19, Sullivan **−7.58**; weighted +0.35; pooled +9.65. Krebiehl writes 32.5% of the whites and 7.5% of the reds.
- **H6, DM4 by grape, DM6 A and B, and BSC3 confidences:** all match the notebook outputs and CSVs.
- **Development comparisons:**
  - Phase 4 P(90+) error: −1 / +2 / −8 / +6 pp.
  - DeSimone −1.0%.
  - Dev H5 +0.9 and H6 +27.6.
- **Integrity:**
  - The SHA-1s of all 13 first-run tables match the run log.
  - `config.py` differs from `a140a70` only in the seal flag.
  - The `phase5.py` diff adds post-hoc functions only.
- **Masked-ranker proxy (my own, not in the draft):** I fitted the ranker score as a linear function of the ridge score and log price on the lockbox pool (R² 0.96), then substituted the masked ridge score.
  - Top-20% precision moves 0.612 → 0.597 for the pool and 0.449 → 0.427 for O'Keefe.
  - So the BO1 conclusion probably survives masking. But this is not evidence the report contains.

## Issues raised
| # | Severity | Issue | Suggested fix |
|---|---|---|---|
| 1 | MAJOR | **The shortlist is never tested under the retailer-note proxy, and the reason given is wrong.**<br>• §5.3 says "masking was not applied to the BO1 part because the simple rules don't read text". But DM2 is `ridge_fit_predict(..., with_price=True)` on the note text, so masking changes the ranker's numerator. Phase 1 mapped DM1b to BO1 as well as BO2.<br>• The executive summary and Option B/F compare unlike things: BO1 "near-certain" on unmasked notes against BO2 "1-in-5" on masked notes.<br>• §5.2 "Limitations" says the band "is the one output [masking] hurts". That is unmeasured.<br>• "Near-certain" (0.995) also omits that in four development pools, which are also mixed-writer, BO1 passes only 0.775–0.950, and only 0.55 in a Krebiehl-like pool. | • Compute BO1 under the frozen mask on the development folds first (no lockbox exposure).<br>• Then add a labelled post-hoc lockbox diagnostic: a masked refit of the price ranker, logged in the run log like the masked score models; or at least the substitution proxy above, labelled as approximate.<br>• Rerun the 5.1h BO1 column for the masked rows and delete the incorrect sentence.<br>• Restate the executive summary like for like: BO1 and BO2 on masked notes, with the development range. |
| 2 | MAJOR | **The stop rule cannot be applied as written.**<br>• "If the house's mean residual leaves ±1.0" never defines a "house", although §5.3 requires notes "from several writers" and revision 2 withdrew the house-pool concept.<br>• Applied pilot-wide, it would have let the lockbox through: mixed +0.84 is inside ±1.0, while the O'Keefe subgroup (+1.37, gain +1.4 pp) fails. That is the exact failure the rule was built for.<br>• There is no minimum n and no uncertainty. The residual SD in the lockbox pool is 1.57, so SE ≈ 0.16 at n = 100 and 0.22 at n = 50.<br>• ±1.0 is also marginally looser than the "tightest edge" it cites (≈ +0.97). | • Define the unit: note source (importer, producer or staff writer), or writer where known.<br>• Apply the rule per unit and per major segment (for example Italy), with a minimum of scored wines (for example ≥ 50).<br>• Use an uncertainty-aware trigger, for example: stop if the 80% CI of the mean residual lies wholly outside ±0.95, or if the point estimate is beyond ±1.0 at n ≥ 100.<br>• State that ±1.0 is rounded from interpolated edges of +0.97 / −1.05.<br>• Freeze the rule in Phase 6 before pilot data, and commit it. |
| 3 | MINOR | **Option F is legitimate but under-disclosed in three places.**<br>• The pre-registered §1.1 text ("Deployment therefore needs a pilot gate … it must beat the note-blind rules:" both bullets) carries no dated amendment note, unlike earlier phases' "Phase 4 note".<br>• The executive summary's "judging the two outputs separately" doesn't say this changes a pre-registered conjunctive gate after unsealing.<br>• §5.2's "None of these changes … a pre-registered Phase 5 threshold" sidesteps the fact that the pilot gate *is* pre-registered (§1.1, `config.PILOT_*`).<br>• Option B's rationale ("a strong shortlist would most likely be held back") reads as goalpost-moving. The lockbox-independent rationale should lead: BO1 and BO2 are separate objectives, and the ranker's order is invariant to a shared level shift.<br>• Undefined case: the band passes but the shortlist fails. | • Add a dated amendment note under §1.1's pilot gate.<br>• Add one clause to the executive summary: "a post-unsealing amendment to the pre-registered gate; the original gate is still reported".<br>• Reword the §5.2 sentence to "changes no model, selection rule or Phase 5 threshold; it amends the pre-registered pilot decision rule".<br>• Lead with the independent rationale.<br>• Specify the band-pass, shortlist-fail case. |
| 4 | MINOR | **Pass rates are conditional on the lockbox writer mix, and some computed rows are omitted.**<br>• The simulation resamples wines and wineries, not writers or houses (round 1 asked for writer resampling). Masked-mixed 0.195 is essentially the effect of a 50% O'Keefe share.<br>• The masked Sullivan and Krebiehl rows (both 1.000) are computed but left out of the report table.<br>• The Jenssen row has 336 < 400 wines, so every "pilot" is the same 336 wines: 0.000 is one evaluation, not a rate, and such a pilot is infeasible.<br>• The Phase 1 "80% power at fold-3-like effects" is not reconciled with the simulated fold-3 0.945. | • Add the two omitted rows and mark the Jenssen row as a single evaluation.<br>• Write "1-in-5" as "if about half the notes behave like O'Keefe's under masking".<br>• Optionally, simulate pilots that draw writers or houses from the 4 lockbox and dev-fold writer profiles.<br>• Add one sentence reconciling the result with the Phase 1 power figure. |
| 5 | MINOR | **"H6 holds within every critic" has no uncertainty**, in §5.1 point 10 and the executive summary.<br>• O'Keefe: +5.8 pp on 101 strong-record wines. A naive binomial 90% LB is ≈ +0.7 pp before winery clustering, which will widen it.<br>• Jenssen rests on 4 wines.<br>• H6 also failed fold 3 alone in the rehearsal. | Reword: "positive in every critic; clearly so for Krebiehl (+25 pp) and Sullivan (+24 pp), marginal for O'Keefe, n = 4 for Jenssen". Add winery-bootstrap LBs per critic to 5.1g. |
| 6 | MINOR | **Small numeric and wording mismatches.**<br>• H5 within critic on the R-3 lockbox: O'Keefe is +4.1 (report +4.2) and Sullivan −7.6 (report −7.5). These were carried over from the 6,337-row version.<br>• Fold 3 offset row: +1.48 gives +3.5, not +3.6.<br>• Executive summary: "mostly at the lowest passing confidence", but only 8 of 16 ratings were 3.<br>• "Every target still passes" for the 1,234-ID sensitivity, but DM1b was "not run" there. | Correct each one. Say "reviewer 1 gave the minimum to 6 of 8 and reviewer 2 to 2 of 8", and "every target that was run". |
| 7 | MINOR | **Computed but unreported (minor, non-tilting).**<br>• The rev-1 stack's masked gain is +6.7 pp (LB +5.5): it would have passed BSC2 under masking where the frozen choice (+2.7) fails. That strengthens the forking-path finding.<br>• The text-only ranker's P@100 is 0.721 vs 0.761, which shows how much of the shortlist is price.<br>• The 200-word stress test's MAE increase (+0.159) exceeds the 0.15 DM1b bar, but it is reported without saying so. | Add one line each: to the §5.2 forking-path bullet, to point 6 and to point 5. |
| 8 | MINOR | The executive summary says the lockbox was "scored … exactly once". It was scored twice by the frozen code: one byte-identical re-execution, plus post-hoc diagnostics on the saved predictions. | Write "scored once by the frozen code; one logged, byte-identical re-execution". |
| 9 | MINOR | **The audit trail is still open** (round-1 #17).<br>• The unsealed config, revision 2, the run log, every `phase5_*.csv` file and the Option F / ±1.0 amendment are uncommitted. So "fixed before any pilot data" has no tamper-evident timestamp.<br>• The 5.1c re-execution assert covers 6 of 13 tables; the other 7 rely on the SHA-1 list. | • Commit and tag the post-unseal state (for example `wine-phase5-rev2`) before any Phase 6 or pilot work.<br>• Add SHA-1s for the four new files (pilot simulation, gain vs offset, DM6 B, lockbox predictions) to the run log.<br>• Extend the 5.1c assert to all 13 tables. |

## Single most important improvement
Make the decision rule rest on like-for-like evidence and a rule that can be measured.

First, measure the shortlist (BO1) under the same retailer-note proxy that was used to condemn the score band. Start with a masked refit of the price ranker on the development folds, then add a labelled post-hoc lockbox diagnostic (or at least the substitution proxy). Rerun the BO1 column of the masked pilot simulation, and restate the executive summary and Options B/F with masked BO1 next to masked BO2 and the development range (0.775–0.950).

Second, define the stop rule's unit (note source or writer), its minimum sample and its uncertainty trigger, so that it would actually catch an O'Keefe-like source inside a mixed pilot.

Then add a dated amendment note to §1.1's pilot gate and commit and tag the result. Option F then stands as a clean, timestamped pre-pilot amendment rather than a lockbox-motivated relaxation.

---

## Changes made (revision 3)

| # | What I changed | Where |
|---|---|---|
| 1 | Added `phase5.masked_ranker`: the selected price ranker refit on masked training notes and scored on masked test notes (frozen verdict list), built exactly like the masked score models. Masked pilot rows now use it, first on development folds 0/1/3/4 and then on the lockbox (mixed and each writer), and include the BO1 part. Result: masked BO1 is 0.995 in the mixed lockbox pool (lift 1.70× vs 1.73×) and 0.67–0.94 in development (0.775–0.95 unmasked). Deleted the wrong sentence about the simple rules. The executive summary, options B/F and the §5.2 limitation now compare masked BO1 with masked BO2 and give the development range | `phase5.py`; notebook 5.1h; report exec summary, §5.2, §5.3; run log (re-execution 2) |
| 2 | Stop rule defined. **Unit:** note source (named writer, else importer or producer). **Trigger:** ≥ 50 scored wines and the 80% winery-bootstrap CI of the mean residual wholly outside ±1.0. Also run per country with ≥ 50 wines (Italy) and pilot-wide. ±1.0 is stated as rounded from +0.97 / −1.05. Settings live in `config.PILOT_STOP_*` and were fixed before the firing rates were computed. `phase5.stop_rule_rate` simulates it: ≤ 2% firing for sources within ±1; 59–95% (50 wines) and 83–100% (100 wines) for the sources where the band fails; it also stops the band for Gregutt and Buzzeo, where it still works. Pilot-wide alone it fires 8% on the masked lockbox, which is why it runs per source | `config.py`; `phase5.py`; notebook 5.1h; `phase5_stop_rule.csv`; report point 7, §5.3, condition 7 |
| 3 | §1.1 dated amendment note under the pilot gate; exec summary clause "a post-unsealing amendment to the pre-registered gate; the original joint gate is still reported"; §5.2 sentence reworded to "amends the pre-registered pilot decision rule"; option F leads with the lockbox-independent reason; band-passes-shortlist-fails case defined (nothing deploys; back to Phase 4) | Report §1.1, exec summary, §5.2, §5.3 condition 3 |
| 4 | Added the masked Sullivan, Krebiehl and Jenssen rows and the masked development rows. Jenssen is marked as one evaluation of all 336 wines. "1-in-5" is replaced by "if about half the notes behave like O'Keefe's under masking". The result is reconciled with Phase 1's 80% power figure (sized for a model just meeting the targets; the frozen models exceed them on fold 3). The writer-mix limitation is stated. Writer-resampling simulation **not done** (optional) | Report §5.3 |
| 5 | `phase5.within_group_diff` gives winery-bootstrap LBs per critic (`phase5_h6_within_critic.csv`): Krebiehl +25.1 pp (LB +15.5), Sullivan +24.3 (LB +17.8), O'Keefe +5.8 (LB −2.0), Jenssen n = 4. The wording is now "positive in every critic, LB > 0 in two", in the exec summary, the pass table and point 10 | `phase5.py`; notebook 5.1g; report |
| 6 | H5 values +4.1 / −7.6; fold-3 offset +3.5; "reviewer 1 gave the minimum to 6 of 8 and reviewer 2 to 2 of 8"; "every target that was run" | Report §5.1 |
| 7 | Rev-1 stack masked +6.7 pp (LB +5.5) added to the forking-paths bullet; text-only ranker P@100 0.721 vs 0.761 added to point 6; the 200-word stress test (+0.159) is now said to exceed the 0.15 bar | Report §5.1, §5.2 |
| 8 | "Scored on the lockbox once; two logged re-executions of the identical frozen code reproduced every table byte for byte" | Report exec summary, §5 header |
| 9 | 5.1c's assert now covers all 12 tables it rewrites, and the 13 first-run SHA-1s still match after re-execution 2. SHA-1s of the 6 post-hoc files are in the run log. **The commit and tag of the post-unseal state are waiting on the project owner's go-ahead** | Notebook 5.1c; run log |
| – | Also: a simulation-noise note (masked mixed BO2 0.195 in re-execution 1 vs 0.240 in re-execution 2, from different random pilots; SE up to about 0.035); critics referred to by name instead of gendered pronouns | Report §5.3; run log |
