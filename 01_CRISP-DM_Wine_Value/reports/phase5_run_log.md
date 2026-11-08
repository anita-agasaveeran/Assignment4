# Phase 5 run log

The order of every Phase 5 step. Times are Pacific, from the Claude Code session record. The models, rules and targets were frozen in commit `8632fba` (tag `wine-phase4`, pushed 2026-11-07) before any Phase 5 code was written.

## Before the lockbox was unsealed (2026-11-07)

| Step | Data used | Lockbox scores read? |
|---|---|---|
| `phase5.py` written: a generic `run_split`, the sealed `lockbox_split` loader, and `evaluate` (every target and sensitivity); tests for the seal | – | No |
| **Dress rehearsal 1** on development fold 3. Stopped on a division by zero: a tiny critic pool where the simple rule's top 10% held no value wine. Fixed by reporting that lift as undefined | Development fold 3 | No (lockbox `points` also blanked in memory) |
| **Dress rehearsal 2** on fold 3: reproduces Phase 4's fold-3 numbers exactly (MAE 1.742, reduction 23.0%, ±2 0.686, P@100 0.678, lift 1.96×, LB 1.77, Brier 0.140, band coverage 0.778). Found two further issues: the sensitivity refit showed DM1b as failed instead of "not run" (fixed), and H6 fails on fold 3 alone (LB −0.02), a risk for BSC5 recorded before unsealing | Development fold 3 | No |
| **BSC3 blind naming:** two reviewer agents on different models (Sonnet, Haiku), no tools, term lists only, blind to each other and to which set is primary. Both named 8 of 8 primary profiles with confidence ≥ 3, and 6 of 8 secondary (`reports/bsc3_naming/`) | Development notes (text only) | No |
| Notebook Phase 5 cells added: rehearsal (with an equality assertion against Phase 4), naming tally, lockbox cell guarded by `config.LOCKBOX_UNSEALED`; full notebook run in sealed mode (no errors; rehearsal assertion holds; lockbox cell printed "sealed") | Development data | No |

## Unsealing

| Time | Step |
|---|---|
| 2026-11-08 | Project owner's go-ahead ("Commit, tag, unseal") |
| 2026-11-08 00:08 PST | Phase 5 code committed as `a140a70`, tagged `wine-phase5-pre-unseal` (lockbox still sealed in that commit) |
| 2026-11-08 00:08 PST | `config.LOCKBOX_UNSEALED = True`; full notebook run started. This is the **only** run that scores the lockbox |
| 01:26 PST | Lockbox run finished with no errors (lockbox evaluation 936 s). Every testable pre-registered criterion passes. Tables saved as `reports/tables/phase5_*.csv` |

## After unsealing (2026-11-08)

| Step | Lockbox data used | Changes a model, rule or selection? |
|---|---|---|
| Report §5.1–5.3 and the executive summary written from the saved outputs | Saved outputs only | No |
| **Post hoc, descriptive:** H5 value rate by colour within each lockbox critic (notebook 5.1d, run on its own, not as part of a notebook rerun). Pooled +9.7 pp, within critic +0.4 pp | Lockbox `points`, `colour`, `critic` | No |
| Notebook 5.2 / 5.3 cells filled (markdown) | – | No |
| Critic round 1 logged (6/10, 7 MAJOR): selective reporting, masked ±2 gain, DM4 filter chosen on the lockbox, unsupported mechanisms, incomplete post-hoc inventory, the "one-house pool" assumption, pilot gate not re-assessed | – | – |
| **01:43 PST: re-execution 1 of the full notebook** (identical frozen code for every model and target), started to produce the row-level lockbox predictions (`phase5_lockbox_predictions.csv.gz`, needed for the Phase 6 reproduction check and the post-hoc analyses) and saved outputs for the new post-hoc cells 5.1e–5.1h. Cell 5.1c now asserts that the re-run writes byte-identical score, ranker, per-critic, DM4, hypothesis and DM6 tables. SHA-1 of the first run's 13 tables recorded below | Lockbox (same as first run) | No |
| **03:01 PST: re-execution 1 finished** with no errors. Cell 5.1c's assertion held (score, ranker, per-critic, DM4, hypothesis and DM6 tables byte-identical), and all 13 first-run tables match the SHA-1s below. New files: `phase5_lockbox_predictions.csv.gz`, `phase5_pilot_simulation.csv`, `phase5_gain_vs_offset.csv`, `phase5_dm6_fixed_effects_B.csv` | Lockbox (same as first run) | No |
| **Post hoc, descriptive (cells 5.1d–5.1h, saved in re-execution 1):** 5.1d H5 within critic, now on the R-3-filtered lockbox (6,334 rows: pooled +9.6 pp, within critic +0.4 pp); 5.1e every score candidate, the without-length sensitivity, the calibration coefficients, per-critic calibration shift, masked ±2 gains by fold and by critic; 5.1f DM4 by consequent grape; 5.1g H6 within critic, DM6 specification B with the lockbox critics; 5.1h pilot-gate simulation and gain vs offset | Lockbox predictions | No |
| **Report §5 revision 2.** Withdrawn: the DM4 55-rule display filter (selection on the test set; the frozen 88 rules are approved instead) and the "rank within one house's pool" condition (contradicts A1/A7) | Saved outputs only | Withdraws two revision-1 choices; no model changes |
| **Decisions informed by the lockbox** (deployment and display rules, fixed before any pilot data): P(90+) shown as a relative indicator (it over-predicts by 10 pp); score band labelled "may be less accurate for Italian wines and for writers unlike those in training" (Italy = O'Keefe +1.4 pp; Jenssen −26%); pilot stop threshold ±1.0 point of mean residual, replacing revision 1's ±1.5, from the gain-vs-offset table (tightest +5 pp edge between +0.84 and +1.09 in the mixed pool); pilot outputs judged separately, the shortlist on the BO1 part of the gate and the band on the BO2 part, from the pilot simulation (BO1 0.995, BO2 0.805, masked BO2 0.195) | Lockbox outputs | Changes deployment rules only; no model, model-selection rule or Phase 5 threshold |
| Critic round 2 logged (8/10, 2 MAJOR): the shortlist was not tested under masking, and the stop rule's unit, sample size and uncertainty were undefined | – | – |
| **03:20 PST: re-execution 2 of the full notebook** (identical frozen code for every model and target). Adds, post hoc: the selected ranker refit on masked notes (`phase5.masked_ranker`, built exactly like the masked score models), on the development folds and the lockbox in the same cell, so the masked pilot rows judge both parts of the gate; the score-band stop rule's firing rate per note source (`phase5.stop_rule_rate`, `config.PILOT_STOP_*`); H6 within critic with winery-bootstrap LBs. Cell 5.1c's assertion now covers all 12 first-run tables it rewrites (the 13th, the anonymous-ID list, is checked by SHA-1 only) | Lockbox (same as first run) | No |
| **04:38 PST: re-execution 2 finished** with no errors. Cell 5.1c's assertion held for all 12 tables it rewrites, and all 13 first-run tables match the SHA-1s below. New files: `phase5_stop_rule.csv`, `phase5_h6_within_critic.csv`; `phase5_pilot_simulation.csv` gains masked BO1 columns. The masked mixed-pool BO2 rate is 0.240 here against 0.195 in re-execution 1: that run skipped the BO1 part, so the same random stream drew different pilots (simulation SE up to about 0.035). SHA-1s of the post-hoc files are recorded below | Lockbox (same as first run) | No |
| **Report §5 revision 3** and notebook markdown 5.1 / 5.2 / 5.3. The shortlist is now judged on masked notes too (masked BO1 0.995 in the mixed lockbox pool; 0.67–0.94 in development). The stop rule is defined per note source (≥ 50 wines, 80% CI wholly outside ±1.0) with simulated firing rates. H6 is reported with per-critic LBs ("positive in every critic, LB > 0 in two"), replacing "holds within every critic". Option F leads with its lockbox-independent rationale and is labelled an amendment to the pre-registered gate | Saved outputs only | Interpretation and deployment-rule wording; no model changes |
| Critic round 3 logged (9/10, no MAJOR). **Report §5 revision 4** (round-3 minors, text only): gates computed on all pilot wines whatever the stop rule withdraws; within-source qualifier on option F's rationale; shortlist pass rate given as a range; wording fixes. Deferred to Phase 6: shortlist stop-check minimum n and false-pause rate, minimum sources with ≥ 50 wines, saved masked ranker scores and a `masked_ranker` test | Saved outputs only | No |
| **Post-unseal state committed and tagged `wine-phase5-rev4`** (2026-11-08): unsealed config, `PILOT_STOP_*`, the option F amendment, report revisions 2–4, this log, all `phase5_*` tables and the three critic rounds. The stop rule and per-output gate are frozen from this tag; any change before the pilot needs a new dated entry here | – | – |

**Rule for later revisions:** critic feedback may change interpretation and add labelled post-hoc diagnostics. It may not change a model, rule, threshold or selection. If the full notebook has to be re-executed (for example after a code fix), it re-runs the identical frozen code. Each re-execution is logged here, and its numbers must match the first run's tables.

**First lockbox run, SHA-1 of the saved tables** (2026-11-08 01:26 PST):

```
6ecc05c348ec61f7f1da8f627f1f45a1169a3004  phase5_by_critic.csv
a23e3f6787dbe6fa8d7e689477796e8a835ccaa9  phase5_critic_pools.csv
b49a37d05b59efc1ffc5407ef532c604a8304536  phase5_dm4_rules.csv
5fa50b93a0eacdfb0e15bafcddd9bdfe785a9fcb  phase5_dm6_fixed_effects.csv
cf7c4a3c2b75c8d84a60548dfe062b09a9f7dbf0  phase5_hypotheses.csv
b269887ae2e6c3d1aa660b6a1776c3b873f1f18c  phase5_ranker_sensitivity.csv
d70690ae9bab4ba384271fab6ad94e6b1eaa69de  phase5_rankers.csv
d792a874715c5903ec85597886d838e933ed2210  phase5_score_models.csv
e47cbb83723e3c2e9942cd07def1d71a5889df07  phase5_sensitivity_anon_ids.csv
7e42e6a5986d0a9315f39aab1285d05174d42282  phase5_sensitivity_ids.csv
05a381c394c56aaa2e46587cfa09f1cf2fac95c8  phase5_shortlist_mix.csv
cf4636ded4a309e29826f9a24214c06b6aa37d1c  phase5_subsets.csv
8fcb9f95cdea73669acf0251c68f6b335dbc350e  phase5_summary.csv
```

**Post-hoc files after re-execution 2, SHA-1** (2026-11-08 04:38 PST; not part of the first run; any later re-execution must reproduce them):

```
3109c1547b2ddc49ddff7315fdf36450e7593b9a  phase5_lockbox_predictions.csv.gz  (gzip; SHA-1 of the uncompressed CSV 0519b4be7aa170e56ead22e3d70bdd2e88d61ac4)
a8015e54b830cb219edca00f48224d8fec5bfba6  phase5_pilot_simulation.csv
81e3bf742494fc40d29a079bb4b347ed136c1924  phase5_gain_vs_offset.csv
21c834b2e7398d9bf320969268d3896f6491cb04  phase5_dm6_fixed_effects_B.csv
f5c8af01b5bbbcd78419d6b668ed58bfacff47d4  phase5_stop_rule.csv
53a8b68e9be3e42b57bee94c8472710ca811d4b7  phase5_h6_within_critic.csv
```
