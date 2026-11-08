# Phase 5 · Evaluation: Critic Round 3

- **Date:** 2026-11-08
- **Reviewer:** Claude critic (independent subagent session), persona from `critic_prompt.md`. Read-only.
- **Draft reviewed:** Phase 5 revision 3

## Score: 9 / 10 · Major issues remaining: no

Revision 3 fixes both round-2 MAJOR issues in substance.

The shortlist is now tested under the same retailer-note proxy as the band. `phase5.masked_ranker` refits the frozen price ranker on masked notes, using the same alpha and mask functions as `evaluate.run_split`. It runs on the development folds and the lockbox, and the masked pilot rows now judge both parts of the gate. The result is honest and it is not flattering everywhere. Masking leaves the lockbox shortlist at 0.995, but it costs 0.01–0.14 in development (0.67–0.94). Both facts are reported.

The stop rule now has a unit (note source), a minimum n (50), an uncertainty trigger (80% winery-bootstrap CI wholly outside ±1.0) and a config entry. It is simulated on 12 development writers and 4 lockbox writers. It would have caught O'Keefe: 0.775 of checks at 50 wines unmasked, 0.945 masked. Every number I recomputed matches the CSVs, the row-level predictions or the saved notebook output. All 19 SHA-1s in the run log match the files.

Option F is now disclosed everywhere it matters: the §1.1 dated note, the executive summary, §5.2, §5.3, notebook 5.3 and the `config.py` comment. It leads with a reason that does not depend on the lockbox, and the joint gate is still reported. I found no selective reporting that tilts toward GO.

What remains is minor, and it sits in the pilot protocol rather than the evaluation:
- the gate's interaction with the stop rule is undefined;
- the shortlist's stop rule is unspecified;
- the post-unseal state is still uncommitted;
- some wording residue remains.

None of these would fail a professional review today. The first three must be closed before any pilot data exists.

## Round-2 issues
| # | Fixed? | Note |
|---|---|---|
| 1 | Yes | `masked_ranker` matches the masked score-model construction. Masked BO1: lockbox 0.995 (lift 1.70× vs 1.73×); development 0.670 / 0.795 / 0.940 / 0.745. The wrong sentence about the simple rules is gone. The executive summary, Options B/F and the §5.2 limitation are now like for like. One small point: "development folds first" is only the order of the code inside one cell, not a separate look before the lockbox (issue 7). |
| 2 | Yes | Unit, minimum n, CI trigger, per-country and pilot-wide checks are all defined. ±1.0 is stated as rounded from +0.97 / −1.05. `config.PILOT_STOP_*` exists. The firing rates match `phase5_stop_rule.csv`. Still to do: freeze it in a commit (issue 1). |
| 3 | Yes | §1.1 note, executive-summary clause, the reworded §5.2 sentence, the independent rationale leading Option F, and the band-passes / shortlist-fails case (nothing deploys) are all present. |
| 4 | Yes (writer resampling not done, disclosed) | The masked Sullivan, Krebiehl and Jenssen rows and the masked development rows are added. Jenssen is marked as one evaluation. "1-in-5" is reworded. Phase 1 power is reconciled. The writer-mix limitation is stated. |
| 5 | Yes | `within_group_diff` LBs match: Krebiehl +25.1 (LB +15.5), Sullivan +24.3 (LB +17.8), O'Keefe +5.8 (LB −2.0), Jenssen n = 4. Residue: the pass table still says "holds within critics" (issue 7). |
| 6 | Yes | H5 is +4.1 / −7.6; the fold-3 offset row is +3.5; the reviewer wording is fixed; "every target that was run" is in place. |
| 7 | Yes | Rev-1 stack masked +6.71 pp is verified from the predictions. Text-only P@100 0.721 matches `phase5_ranker_sensitivity.csv`. The 200-word test (+0.159) is now said to exceed the 0.15 bar. |
| 8 | Mostly | The §5 header is precise. The executive summary's "reproduced every table byte for byte" overreaches: the post-hoc pilot table changed between re-executions (0.195 → 0.240). It should say "every first-run table" (issue 7). |
| 9 | Partly | The 5.1c assert covers the 12 tables it saves. The SHA-1s of the 6 post-hoc files are recorded and match. The run log says "all 13" at 03:20 but "12" at 04:38. **The commit and tag are still pending** (issue 1). |

## Task coverage
| Task | Output | Status |
|---|---|---|
| 5.1 Evaluate results | Assessment of data mining results w.r.t. business success criteria | **Present.** Pass / fail with development margins, every candidate, subsets, masking for both outputs, writer level, gain vs offset, BSC3 margin, DM4, H1–H6 with per-critic LBs, DM6 A and B. Post-hoc work is labelled throughout. |
| 5.1 Evaluate results | Approved models | **Present.** Each approval is scoped to the pilot and tied to evidence. The band is approved only under the stop rule, and DM4 is approved as frozen. |
| 5.2 Review process | Review of process | **Present.** Exposure inventory, a complete post-unsealing decision table (Option F labelled as an amendment), counted forking paths and a phase-by-phase audit. |
| 5.3 Determine next steps | List of possible actions | **Present.** Options A–F, each with for / against, cost and verdict. |
| 5.3 Determine next steps | Decision | **Present.** GO to a pilot under Option F, with explicit conditions, a defined stop rule and the joint gate still reported. The protocol gaps are minor (issues 2–4). |

## Figures verified
- **Integrity:**
  - `shasum` of all 13 first-run tables matches the run log.
  - The 6 post-hoc files match too, including the gzip (3109c15…) and the uncompressed CSV (0519b4b…).
  - Since `a140a70`, `config.py` adds only the `PILOT_STOP_*` block and the seal flag. The `phase5.py` diff adds post-hoc functions only.
  - Notebook cells 119–126 run in sequence (execution counts 50–57) with no errors.
  - The three new tests pass (`pytest -k "pilot or stop_rule or within_group"`, run without writing caches).
- **Pilot simulation:** every reported cell matches `phase5_pilot_simulation.csv`.
  - Development unmasked: BO2 0.990–1.000, gain +10.9 to +27.9, BO1 0.775–0.950, lift 1.42–1.61×, both 0.775–0.945.
  - Development masked: BO2 0.860–1.000, gain +8.1 to +27.4, BO1 0.670–0.940, lift 1.39–1.59×, both 0.655–0.935.
  - Lockbox mixed: 0.805 / +7.4 / 0.995 / 1.73×. Lockbox masked mixed: **0.240** / +2.5 / **0.995** / 1.70×.
  - O'Keefe 0.125 / 1.000, masked 0.000 / 0.995. Sullivan 1.000 / 0.875, masked 0.995 / 0.900. Krebiehl 1.000 / 0.550, masked 1.000 / 0.535. Jenssen −16.4 / −17.3 pp.
  - The §5.2 claim that masking costs BO1 "0.01–0.14 in development" is correct (0.135, 0.095, 0.010, 0.030).
- **Stop rule:** every band of the §5.3 table matches `phase5_stop_rule.csv`.
  - Within ±1: 7 development writers plus Sullivan and Krebiehl, residual −0.36 to +0.81, fires ≤ 0.010 / ≤ 0.020.
  - Boone and Kostrzewa: 0.155–0.190 / 0.190–0.225.
  - Gregutt and Buzzeo: 0.745–0.895 / 0.915–0.990.
  - Sources where the band fails: 0.585–0.945 / 0.825–1.000.
  - Whole pool: 0.000 / 0.080 / 0.000–0.030.
- **Gain vs offset:** I interpolated the mixed-pool +5 pp crossings myself and got **+0.971** and **−1.046**, which match +0.97 / −1.05. For reference, the edges in other pools are wider: O'Keefe-only +1.22, fold 3 −1.16 / +1.39. So the mixed-pool edge is the tightest, as claimed.
- **From row-level predictions** (pool 7,288):
  - Mixed residual +0.837 and gain +7.48; masked +0.990 and +2.73.
  - Per critic: O'Keefe +1.375 / +1.36 pp, masked +1.602 / −5.77; Sullivan +0.726 / +13.89; Krebiehl +0.162 / +20.09; Jenssen −1.389 / −16.37.
  - Stack masked +6.71 pp; plain ridge masked +9.14 pp.
  - Pool residual SD 1.57, so SE ≈ 0.22 at n = 50.
- **H6 within critic:** the notebook 5.1g output and `phase5_h6_within_critic.csv` match the report. Flagged counts are 102 + 213 + 101 + 4 = 420 of 7,288. Rates are 72.5 / 47.5, 35.2 / 10.9, 19.8 / 14.0 and 3 of 4 / 16.9. The bootstrap LB for Jenssen (+53 pp) is correctly called not meaningful.
- **Summary table:** `phase5_summary.csv` matches the pass table. BSC1 LB 1.755 rounds to 1.76.

## Issues raised
| # | Severity | Issue | Suggested fix |
|---|---|---|---|
| 1 | MINOR | **The audit trail is still open.** The unsealed config, `PILOT_STOP_*`, the Option F amendment, revisions 2–3, the run log and every `phase5_*.csv` file are uncommitted. So "fixed before any pilot data exists" has no tamper-evident timestamp. "The 50-wine minimum and the 80% CI were fixed before the firing rates were computed" also rests only on the session record, because no commit separates the two. | Commit and tag the post-unseal state (for example `wine-phase5-rev3`) before any Phase 6 work. Put the hash in the run log and in the §1.1 note. Say in §5.3 that the ordering of the settings and the firing rates is attested by the session record, not by a commit. |
| 2 | MINOR | **The stop rule's interaction with the BO2 gate is undefined.** If the band is withdrawn for a source or a country at an interim check, condition 3 does not say whether the final BO2 gate is computed on all pilot wines or only on the sources still shown. Recomputing on the remainder would select on the outcome and tilt the band toward passing. | Add to condition 3: "The BO2 and BO1 gates are computed on all pilot wines. A stop-rule withdrawal never removes wines from the gate." Report the stop-rule firings next to the gate. |
| 3 | MINOR | **The shortlist's stop rule is unspecified and untested.** "If the shortlist's lift LB falls below 1.0, pause the pilot" has no minimum n, no bootstrap specification and no simulated false-pause rate. At small interim n the LB will often be below 1.0: even at 400 wines the median LB is 1.18 in fold 4 and in a Krebiehl-like pool. Separately, the band rule's "≤ 2% of checks" is for a single look. Repeated interim checks across several sources, countries and the pilot-wide check raise the family-wise firing rate. That rate is not simulated. Both effects err toward stopping, not toward GO. | Freeze a minimum n for the shortlist check (for example ≥ 200 scored wines) in `config.PILOT_*`, then simulate its false-pause rate with `pilot_pass_rate` at the interim sizes. In Phase 6.2, simulate cumulative firing over the planned check schedule. |
| 4 | MINOR | **The stop rule may rarely apply per source in a realistic pilot.** With 400 wines from many importers, most sources may have fewer than 50 scored wines. They are then covered only by the per-country check and the pilot-wide check, and the pilot-wide check fires only 8% of the time in the masked lockbox case. The gap is disclosed, but the pilot design does not address it. | In condition 2, require at least a minimum number of sources with ≥ 50 scored wines (for example 3). Alternatively, pre-specify how small sources are pooled (by importer, then by country) before the rule runs. |
| 5 | MINOR | **Option F's rationale is true only within a source.** "A level error shared by one source's wines … leaves its shortlist order unchanged." Across sources, level errors do distort the shortlist: P@100 is 0.76 against the 0.84 oracle, Sullivan's share drops from 24% to 7.5%, and Jenssen's to 0% (point 6). | Add one clause in §1.1 and Option F: "within a source; across sources, level differences still cost the shortlist about 0.08 of P@100 on the lockbox (point 6)". |
| 6 | MINOR | **The executive summary's shortlist pass rate leads with the most favourable pool.** The 99.5% comes from an Italy-heavy pool where the ranker is at its strongest (O'Keefe alone: 1.000, 1.95×). Development pools give 0.67–0.94 masked, and a Krebiehl-like pool gives 0.54. The range is given in parentheses, but "So the shortlist is the product" rests on the high end. The rates are also conditional on writer mix; writer resampling was not done (disclosed). | State the planning figure as a range: "0.67–0.995 on masked notes, depending on writer mix; 0.54 in a Krebiehl-like pool". Keep 99.5% as the lockbox point. |
| 7 | MINOR | **Wording residue.** <br>• Executive summary: "reproduced every table byte for byte", but the post-hoc pilot table changed between re-executions. <br>• Run log 03:20: "covers all 13 first-run tables" vs "12" at 04:38. <br>• Pass-table BSC5 row and point 10: H6 "holds within critics", although O'Keefe's LB is −2.0 and O'Keefe is half the pool. <br>• Notebook 5.3: the stop-rule bullet omits the per-country check. <br>• "House" survives in the `gain_vs_offset` docstring and the 5.1h comment. <br>• §5.2 decision table: the evidence for the masked ranker is listed as "Lockbox predictions", but it is a new lockbox scoring of a refit, non-frozen variant. <br>• "Development folds first" describes code order inside one cell, not a separate look before the lockbox. | <br>• Write "every first-run table". <br>• Make the run log say 12 tables in both places. <br>• Write "is positive within every critic". <br>• Add the country check to notebook 5.3. <br>• Replace "house" with "note source". <br>• Relabel the evidence as "new lockbox scoring of a masked refit (descriptive)". <br>• Drop "first" or say "in the same cell". |
| 8 | MINOR | **The masked ranker scores are not saved.** `phase5_lockbox_predictions.csv.gz` predates `masked_ranker`, so the masked BO1 rows (0.995, 0.67–0.94), which the decision cites, cannot be recomputed from saved outputs. `masked_ranker` also has no unit test. | Save the masked ranker scores for the lockbox and the development folds as a post-hoc file, with its SHA-1 in the run log. Add a small test that `masked_ranker` equals `ridge_fit_predict(..., with_price=True)` on masked inputs. |

## Single most important improvement
Freeze the complete pilot decision protocol in one commit and tag, before any Phase 6 work. That protocol has four parts:
- the per-output gate, computed on all pilot wines whatever the stop rule withdraws (issue 2);
- the band stop rule as now defined;
- a fully specified shortlist stop rule with a minimum n and a simulated false-pause rate (issue 3);
- the minimum number of sources with ≥ 50 wines (issue 4).

Record the commit hash in §1.1, §5.3 and the run log. The evaluation itself is now sound and honest. What would let a sceptical reviewer accept Option F as a clean pre-pilot amendment, rather than a lockbox-motivated relaxation, is a tamper-evident timestamp on a rule that leaves no room for choices after the pilot data arrives.

---

## Changes made (revision 4, round-3 minors; no new computation)

| # | What I changed | Where |
|---|---|---|
| 1 | §5.3 now says the order "stop-rule settings, then firing rates" is attested by the session record and run log, not by a commit. **The commit and tag of the post-unseal state wait on the project owner's go-ahead**; after that, the hash goes into the run log and the §1.1 note | Report §5.3; pending commit |
| 2 | Condition 3: both gates are computed on all pilot wines; a stop-rule withdrawal never removes wines from either gate, and every firing is reported next to the gate. Same in notebook 5.3 | Report §5.3; notebook 5.3 |
| 3 | **Deferred to Phase 6.2** (pilot protocol): a minimum n and a simulated false-pause rate for the shortlist stop check, and the cumulative firing rate over the interim check schedule. Both are to be frozen in `config.PILOT_*` and committed before any pilot data | Phase 6.2 |
| 4 | **Deferred to Phase 6.2:** the minimum number of sources with ≥ 50 scored wines, or a pre-specified pooling of small sources | Phase 6.2 |
| 5 | §1.1 note and option F: "within a source; across sources, level differences still cost the shortlist about 0.08 of P@100 on the lockbox (point 6)" | Report §1.1, §5.3 |
| 6 | Executive summary gives the shortlist pass rate as a range: 67–99.5% depending on writer mix (99.5% mixed lockbox, 67–94% development, 54% Krebiehl alone) | Report exec summary |
| 7 | "Every first-run table"; run log now says 12 asserted tables + 1 SHA-1-only in both places; H6 "positive within every critic" in the pass table and point 10; country check added to notebook 5.3; "house" → "note source" in the `gain_vs_offset` docstring and the 5.1h comment (comment-only; no re-run); §5.2 evidence relabelled "new lockbox scoring of a masked refit"; "first … then" replaced by "in the same cell" | Report; run log; `phase5.py`; notebook 5.1h / 5.3 |
| 8 | **Deferred to Phase 6:** saving the masked ranker scores (needs a re-execution of 5.1h) and a unit test for `masked_ranker`. Phase 6 must re-run the pipeline anyway for the reproduction check (condition 1), so it will save them then and record their SHA-1 | Phase 6 |
