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
| **13:45 PST: re-execution 3 of the full notebook** (Phase 6). Phases 1–5 run the identical frozen code from tag `wine-phase5-rev4` (cell 5.1c asserts byte-identical tables again). New Phase 6 cells after them: the pilot protocol simulations (parameters set on development folds only), the deployed artifact refit on development rows with a row-by-row reproduction check against `phase5_lockbox_predictions.csv.gz`, BSC4 timing, a dry run of the pilot tooling on 400 lockbox wines, and monitoring reference values. Also saves the masked ranker scores (round-3 issue 8) | Lockbox (same as first run) | No |
| **15:15 PST: re-execution 3 finished** with no errors. Cell 5.1c's assertion held, and all 13 first-run tables and all 6 post-hoc files match the SHA-1s below (`phase4_fold_predictions.csv.gz` differs only in its gzip header; the uncompressed CSV is identical). The artifact reproduces every saved lockbox prediction (largest difference 0.0; `value_finder.joblib` SHA-1 `0e610b47…`). Cell 6.1a's assertion held: the pause minimum chosen on development folds is 200 = `config.PILOT_PAUSE_MIN_WINES` | Lockbox (same as first run) | No |
| **Pilot protocol code changes before re-execution 4** (no pilot data exists; no model, threshold or Phase 5 number changes). (1) A futility pause now ends the pilot with no deployment (`pilot.PAUSED`); before, the simulated decision ignored the pause. (2) `pilot_eval.py` reports a final decision only once ≥ 400 wines come from ≥ 3 sources with ≥ 50 wines each (or a pause fired); otherwise "interim, keep collecting". (3) Protocol simulations use 200 pilots per pool (was 100) and the withdrawn-unit table 100 (was 50): the 100-pilot BO1 rates sat 0.07–0.13 below Phase 5's 200-pilot rates for folds 0 and 1, within the seed-to-seed spread of a scratch check (fold 1: 0.83–0.92 over three seeds). (4) New simulation columns: share of wines whose band is hidden, split by whether their note source or country is off by more than ±1.0 in the whole pool. Two new tests | – | No |
| **15:25 PST: re-execution 4 of the full notebook** (Phase 6), for changes (1)–(4). Phases 1–5 identical frozen code | Lockbox (same as first run) | No |
| **16:47 PST: re-execution 4 finished** with no errors. Cell 5.1c's assertion held; all 13 first-run tables and all 6 post-hoc files match the SHA-1s below. The artifact again reproduces every lockbox prediction (0.0). Its file SHA-1 changed (`0e610b47…` → `6b27d124…`): the only difference is scikit-learn's `_stop_words_id` (a memory address stored in the TF-IDF step); every fitted parameter is identical. Deterministic Phase 6 tables (pause rates, unit truth, verdict tiers, dry run, monitoring reference, masked ranker scores) are byte-identical to re-execution 3; the protocol simulation and withdrawn-unit tables changed as intended (200 / 100 pilots); timing differs by run. SHA-1s below | Lockbox (same as first run) | No |
| Phase 6 critic round 1 logged (7/10, 5 MAJOR): the tool did not enforce the simulated stop rule (pooled unit, name matching), the integrity check could be bypassed, per-round monitoring existed only on paper, shortlist tier labels were wrong for new writers, no outcome feed or schedule | – | – |
| **Changes before re-execution 5** (no pilot data exists; no model, threshold or Phase 5 number changes): (1) one `pilot.band_hidden` rule, with name normalisation and the pooled unit's member sources recorded at each firing, used by the protocol, `pilot_eval.py`, `score.py` and the app. (2) `artifacts.load_value_finder` refuses a missing manifest, one without a passed lockbox reproduction, or a wrong SHA-1, and never rebuilds; rebuilds only via `deployment/build_artifact.py`, which saves only after the reproduction check. (3) `winevalue.monitoring`: schema check, per-row flags, per-round drift report against `config.MONITOR_ALERTS`; `score.py` writes it; alert rates simulated in 6.2a. (4) Checks every 100 wines; decision point = first check with ≥ 400 wines and the source minimum; cap `PILOT_MAX_WINES = 800`; `PILOT_N_BOOT = 200` for every gate and check. (5) Pause table with 1,000 pilots per size, Wilson CIs, and detection pools (null ranker, Jenssen only); the pause-size rule is unchanged and asserted again. (6) Shortlist tiers by rank within the round; the one-wine label reads as a development percentile; new tier table. (7) Verdict tier "Possible" renamed "Long shot", base rate shown. (8) Seed-spread table. (9) Tests: 77 + the app smoke test | – | No |
| **17:12 PST: re-execution 5 of the full notebook** (Phase 6), for changes (1)–(8). Phases 1–5 identical frozen code | Lockbox (same as first run) | No |
| **18:49 PST: re-execution 5 finished**, no errors, every assertion held: the 13 first-run Phase 5 tables and the 6 post-hoc files match their recorded SHA-1s; the artifact reproduces the lockbox predictions (largest difference 0.0); the pause-size rule gives 200 again (fold 4 masked 2.9% at 200 wines with 1,000 simulations, 5.0% with 200 in re-execution 4); the tool's `band_hidden` hides exactly the protocol's 209 dry-run wines. Artifact build 202 s. Afterwards, with no re-run: `phase4_fold_predictions.csv.gz` restored from git (the run rewrote only its gzip header; the uncompressed content is identical), and notebook markdown cells 131, 139, 142, 144 and 146 updated to the run's numbers (code cells and outputs untouched) | Lockbox (same as first run) | No |
| **Phase 6 critic round 2** (8/10, 1 MAJOR, 10 MINOR; `critiques/phase6_deployment_round2.md`) | – | No |
| **Changes before re-execution 6** (no pilot data exists; no model, selection or Phase 5 number changes): (1) `pilot.canonical_names` at intake (`from_raw`, `as_pilot_table`, `run_protocol`): one spelling per note source and country, so units and the source count can't be split by a typing variant; `pilot_eval.py` writes `sources.csv`. On the development and lockbox pools it is a no-op (19 critics and 44 countries, each one name key). (2) `artifacts.reproduction_passed`: all four outputs, finite, ≤ 1e-8; `production.reproduces_lockbox` returns infinity on a length or missing-value mismatch. That stricter check found that the deployed ranker returns no score for the 1,097 lockbox wines without a price, where Phase 5's file holds an imputed-price score; none is a ≤ $25 candidate. The ranker is now compared on the 16,699 priced rows (difference 0.0; the old check skipped the NaNs silently). (3) Two-sided alerts for mean P(90+) (0.10–0.40) and the share above the development P90 (5–40%), lower limits set below the lowest development-fold value; detection simulation `monitoring.detection_rates` on 12 broken-feed variants, fixed before it ran (a smoke run timed it without printing rates). (4) Notebook 6.1e: pilot timeline under A8 (yield), A10 (review lag, new) and the 12-month calendar cap (`config.PILOT_ROUND_CANDIDATES`, `PILOT_REVIEW_YIELD`, `PILOT_LAG_*`, `PILOT_CAP_MONTHS`, `PILOT_FALLBACK_MONTH`). (5) Unit truth and withdrawn units also for the masked development pools; whole-pool mean residuals printed. (6) `score.py` no longer writes the development-percentile label; the one-wine view shows the percentile as a number; the app's shortlist view says pilot rounds must go through `score.py` and offers the monitoring report. Tests: 80 | – | No |
| **19:14 PST: re-execution 6 of the full notebook** (Phase 6), for changes (1)–(6). Phases 1–5 identical frozen code | Lockbox (same as first run) | No |
| **20:53 PST: re-execution 6 finished** (about 99 min), no errors, every assertion held: the 13 first-run Phase 5 tables and the 6 post-hoc files match their recorded SHA-1s (`phase4_fold_predictions.csv.gz` again differs only in its gzip header and was restored from git); the stricter `artifacts.reproduction_passed` accepts the rebuilt artifact (all four outputs 0.0, the ranker on the 16,699 priced rows; build 210 s); the pause-size rule gives 200 again; the tool's `band_hidden` hides exactly the protocol's 209 dry-run wines. `phase6_pause_rates`, `phase6_protocol_simulation`, `phase6_seed_spread`, `phase6_shortlist_tiers`, `phase6_verdict_tiers`, `phase6_pilot_dry_run`, `phase6_alert_rates` and `phase6_monitoring_reference` are byte-identical to re-execution 5, so name canonicalisation changed nothing on these pools and the two-sided alert limits add no false alerts. `phase6_unit_truth` and `phase6_withdrawn_units` differ only by the added masked development pools (fold 4 masked: whole-pool residual +1.09). New: `phase6_alert_detection.csv` (12 broken-feed kinds; mild truncation and a 10% price rise are missed) and `phase6_pilot_timeline.csv` (400 scored wines by month 8 under A8/A10) | Lockbox (same as first run) | No |
| **Phase 6 critic round 3** (8/10, 2 MAJOR, 8 MINOR; `critiques/phase6_deployment_round3.md`) | – | No |
| **Changes before re-execution 7** (no pilot data exists; no model, selection or Phase 5 number changes): (1) `production.canonical_inputs`: country, province, variety and region_1 values that are not an exact training spelling are mapped to one by name key (plus a short country alias table) before scoring; the artifact stores the training spellings (`ValueFinder.categories`); a no-op on lockbox inputs (no lockbox value is remapped). New indicator and alert "share of countries unseen in training" (above 2%; lockbox 0.4%) and a per-row flag. (2) Rows without a note source no longer count toward the 3-source minimum (`pilot.counted_sources`); no development or lockbox pool has such rows. (3) `config.PRICE_DEFLATOR` (1.0 = 2017 dollars) applied in `prepare_new`, recorded in every monitoring report and gate file; set from CPI-U before rollout step 0. (4) Lower limits of the two ranker alerts set by a pre-stated rule on out-of-fold, winery-clustered development rounds (`monitoring.choose_lower_limits`: 1st percentile in the lowest fold, rounded down): 0.10 → 0.08 and 5% → 3%; revision 3's limits would alert in 30% of normal fold-1 rounds. (5) A11 floor 12.5% → 15% by a pre-stated rule (`phase6.choose_source_share`: smallest share with P ≥ 0.80 that 3 sources reach 50 by 400 scored wines; exact multinomial: 0.11 at 12.5%, 0.80 at 15%). (6) Only `config.PILOT_PRIMARY_SCORER` (WineEnthusiast) scores enter the gate; other scorers, and the gate on unsampled wines (`sampled` column), are reported sensitivities (`pilot_eval.py` writes `sensitivity.json`, `per_scorer.csv`). (7) `monitoring.business_kpi`. (8) App: band caveat next to the band, unseen-country warning. Tests: 86 pass | – | No |
| **21:19 PST: re-execution 7 of the full notebook** (Phase 6), for changes (1)–(8). Phases 1–5 identical frozen code | Lockbox (same as first run) | No |
| **23:00 PST: re-execution 7 finished** (about 101 min), no errors, every assertion held: the 13 first-run Phase 5 tables and the 6 post-hoc files match their recorded SHA-1s (`phase4_fold_predictions.csv.gz` again differs only in its gzip header and was restored from git); the artifact (now with the training spellings) passes its reproduction check (all four outputs 0.0); the dry run on a case- and alias-variant copy of the lockbox gives the same gate, withdrawn rows and checks; the A11 share rule gives 15% and the out-of-fold lower-limit rule gives 0.08 and 3%, both asserted against `config`. `phase6_masked_ranker_scores`, `pause_rates`, `pilot_timeline`, `protocol_simulation`, `seed_spread`, `shortlist_tiers`, `unit_truth`, `verdict_tiers` and `withdrawn_units` are byte-identical to re-execution 6, so input canonicalisation changed nothing on these pools. `pilot_dry_run` has the same values plus four new rows (primary scorer, other scorers 0, unsourced 0, deflator 1.0); `monitoring_reference` and `alert_rates` add the unseen-country column (lockbox 0.43%; no false alerts); `alert_detection` uses the new limits and two new rows. New: `phase6_alert_rates_oof.csv` (no false ranker alert in any out-of-fold fold) and `phase6_source_minimum.csv`. **One gap found in the outputs:** the "countries upper-case, US as USA (should change nothing)" row moved the pool's unknown-province share (1.58% → 1.23%) and mean estimate (by 0.0008), because a country unseen in training is not mapped, so ENGLAND no longer matched its province England in the province = country rule (76 lockbox wines) | Lockbox (same as first run) | No |
| **Changes before re-execution 8** (no pilot data exists; no model, selection or Phase 5 number changes): `production.prepare_new` compares province with country by name key and matches the "Other" pseudo-province pattern ignoring case. On all 118,378 prepared rows both give exactly the same rows as `prepare.py`'s exact rules (checked before the change), and on the lockbox the variant copy now gives identical row values (max difference 0.0; checked with the run-7 artifact before re-execution). New test `test_unseen_country_in_another_case_still_matches_its_province`. Tests: 87 pass | – | No |
| **23:03 PST: re-execution 8 of the full notebook** (Phase 6), for that change, so every table comes from the final code. Phases 1–5 identical frozen code | Lockbox (same as first run) | No |
| **00:43 PST (2026-11-09): re-execution 8 finished** (about 100 min), no errors, every assertion held: the 13 first-run Phase 5 tables and the 6 post-hoc files match their recorded SHA-1s (`phase4_fold_predictions.csv.gz` again differs only in its gzip header and was restored from git); the artifact passes its reproduction check (all four outputs 0.0); the variant dry run, the A11 share rule and the lower-limit rule hold as in re-execution 7. Every `src/winevalue/` and `tests/` file was unchanged from the run's start to its end (SHA-1s taken at 23:03 and re-checked). Every Phase 6 table is byte-identical to re-execution 7 except `phase6_bsc4_timing.csv` (wall clock) and `phase6_alert_detection.csv`, whose case-and-alias row now equals the unaltered pool in every indicator (largest difference 0.0). Afterwards, with no re-run: notebook markdown cells 140, 143 and 147 updated to the run's numbers (code cells and outputs untouched); `deployment/app.py` moved the P(90+) caption from under the flavour profile to under the metrics (display only; the app test passes); the screenshot was retaken at 00:44 with artifact `ce7f0d1…` at a 1,900-px viewport (all similar-wines columns visible; computed in 0.05 s). Tests: 87 pass | Lockbox (same as first run) | No |
| **Phase 6 critic round 4** (about 00:47–01:00 PST): 8/10, 1 MAJOR (`critiques/phase6_deployment_round4.md`). All ten round-3 issues resolved; new MAJOR: the winery name, which feeds the BO1 gate's strongest comparator, was read as typed | – | No |
| **Changes before re-execution 9** (no pilot data exists; no model, selection or Phase 5 number changes): (1) `winery` added to `production.CANONICAL_COLUMNS`; a stronger match key (`production.match_key`: accents and punctuation too) for values that are not an exact training spelling; grape-lexicon names and blend parts matched for `variety`. No development row changes (all 118,378 prepared rows give the same model inputs); 24 lockbox rows (13 in the ≤ $25 pool) have a winery that WineEnthusiast's own data spells two ways and are now matched, which gives the comparator those wineries' records; the dry run is unchanged (checked with the notebook's lockbox split before re-execution). (2) Comparator coverage rule (`pilot.comparator_check`, `config.PILOT_MIN_WINERY_COVERAGE = 0.50`) and a matched-winery sensitivity; per-round "share of wineries unseen in training" indicator (no alert). (3) `production.reproduces_lockbox` adds the serving path (raw columns → `vf.prepare` → score, deflator 1.0) as a fifth record that `artifacts.reproduction_passed` requires; the artifact was rebuilt with `deployment/build_artifact.py` at 01:05 (all five 0.0) so the tests could run, and is rebuilt again by the notebook. (4) `ValueFinder.score` outputs `price (2017 $)`; `score.py` writes it and a `price deflator` column; `pilot_eval.py` refuses a file scored with another deflator; `prepare_new` never deflates twice. (5) Ranker lower limits per round size (`config.MONITOR_RANKER_LOWER`, `monitoring.choose_lower_limit_table`, same rule at 200 / 300 / 600 / 1,000 ≤ $25 candidates; not read below 200): revision 4 calibrated on 1,000 ≤ $25 candidates, while a real round of 1,000 candidates holds about 400–480. Notebook 6.2a adds a fresh-seed and a leave-one-fold-out check. (6) Intake: placeholder sources merged into one unsourced unit; scorer aliases; no primary-scorer rows → "nothing to judge"; the all-scorers sensitivity uses the same arrival window. (7) `monitoring.business_kpi` split by `shortlist used`. (8) Notebook 6.1d: wineries in the variant dry run; a pool-wide case assertion over all five name columns. Tests: 92 pass | – | No |
| **01:17 PST: re-execution 9 of the full notebook** (Phase 6), for changes (1)–(8). Phases 1–5 identical frozen code | Lockbox (same as first run) | No |
| **02:55 PST: re-execution 9 finished** (about 98 min), no errors, every assertion held: the 13 first-run Phase 5 tables and the 6 post-hoc files match their recorded SHA-1s (`phase4_fold_predictions.csv.gz` again differs only in its gzip header and was restored from git); the artifact passes its reproduction check, now five entries, all 0.0, including the serving path; the lower-limit table from the per-size rule equals `config.MONITOR_RANKER_LOWER`; the variant dry run (wineries included) and the pool-wide case check over all five name columns (7,288 wines) hold. Every `src/winevalue/` and `tests/` file was unchanged from the run's start to its end (SHA-1s taken at 01:17 and re-checked). `phase6_masked_ranker_scores`, `pause_rates`, `pilot_timeline`, `protocol_simulation`, `seed_spread`, `shortlist_tiers`, `source_minimum`, `unit_truth`, `verdict_tiers`, `withdrawn_units` and `alert_rates` are byte-identical to re-execution 8. `pilot_dry_run` has the same gate and decision plus the comparator coverage (70.8%, not degraded; matched-winery lift 1.59×, LB 1.35); `monitoring_reference` adds the unseen-winery share (lockbox 27.4%) and the ≤ $25 count; `alert_rates_oof` is now per round size, with a fresh-seed column; new `phase6_alert_limits_lofo.csv`; `alert_detection` uses the per-size limits (notes cut to 25 words: 0.5% of rounds). Afterwards, with no re-run: notebook markdown cells 140, 143 and 147 updated (code cells and outputs untouched); the screenshot retaken at 02:57 with artifact `6fc69ab…` (it now shows the 2017-dollar price; computed in 0.06 s). Tests: 92 pass | Lockbox (same as first run) | No |
| **Phase 6 critic round 5** (about 03:00–03:16 PST): 8/10, 1 MAJOR (`critiques/phase6_deployment_round5.md`): revision 5's premise that a round of 1,000 candidates holds 400–480 ≤ $25 wines contradicts A7 (about 1,000 ≤ $25 per round), and "score every ≤ $25 candidate" would let a file pre-filtered at a nominal $25 defeat the deflator | – | No |
| **Changes before re-execution 10** (no pilot data exists; no model, selection or Phase 5 number changes): (1) A7 kept; every monitoring simulation draws rounds that hold about `PILOT_ROUND_CANDIDATES` ≤ $25 candidates (`monitoring.round_size`; about 2,067 development or 2,442 lockbox candidates); the candidate file is defined as every candidate at any price; the ≤ $25-share alert is two-sided (above 95%: pre-filtered file), with a new broken-feed row. (2) Winery matched within its country (`production._winery_key`): 21 lockbox rows (11 in the pool) instead of 24, the two cross-country producers no longer matched; the dry run is unchanged (checked before re-execution). (3) `gate.json`: `BO1 passes (after comparator rule)`, used by the joint gate; `pilot_eval.py` prints the matched-winery lift and the too-few case. (4) `monitoring._flag` reads yes/no flags strictly in `business_kpi`. (5) `pilot_eval.py` refuses a file without `price deflator` unless `--deflator-confirmed`. (6) The serving-path reproduction starts from `data.load_raw()` rows (no vintage column); 0.0. (7) Upper ranker limits read at any round size; self-referenced rule (`config.MONITOR_RELATIVE_*`, `monitoring.relative_alerts`, `relative_drop_rates`, `choose_relative_min_pool`), read from 600 ≤ $25 candidates; `score.py` passes the earlier rounds' reports. (8) Placeholders and scorer aliases extended. The artifact was rebuilt with `deployment/build_artifact.py` at about 06:20 (five entries, all 0.0) so the tests could run; the notebook rebuilds it again. Tests: 100 pass | – | No |
| **06:32 PST: re-execution 10 of the full notebook** (Phase 6), for changes (1)–(8). Phases 1–5 identical frozen code | Lockbox (same as first run) | No |
| **08:10 PST: re-execution 10 stopped** at cell 6.1d (about 98 min), on the assertion that the dry run is unchanged when the stand-in's wineries are upper-cased. One stand-in wine, "Neumeister" with country Unknown, is a training winery (Austria): its exact spelling is seen and gets the winery track record (the frozen rule reads wineries by name alone), but "NEUMEISTER" no longer matched once change (4) matched wineries only within their country. Winery coverage moved 70.75% → 70.5% and the BO1 lift LB 1.434 → 1.419; estimates and ranks were identical. Its outputs are discarded (the notebook file was not written) | Lockbox (same as first run) | No |
| **Fix before re-execution 11** (no model, selection or Phase 5 number change): `production.canonical_inputs` first matches a winery that differs from a training spelling in letter case only, and only if exactly one training spelling equals it case-insensitively, in any country, so a case variant always scores as its exact spelling; accent and punctuation variants are still matched only within the country ("Patria", Italy, stays unmatched). Checked before the run against the saved artifact: cell 6.1d's assertions all hold (the dry run, the variant copy and the whole lockbox ≤ $25 pool lower- and upper-cased), the same 21 lockbox winery remaps (all Italy, 11 in the pool), all five reproduction entries 0.0, no development row changed. Test `test_a_winery_case_variant_scores_as_its_exact_spelling` added (101 pass) | — | No |
| **08:29 PST: re-execution 11 of the full notebook** (Phase 6), for changes (1)–(8) and the fix. Phases 1–5 identical frozen code | Lockbox (same as first run) | No |
| **10:10 PST: re-execution 11 finished** (about 101 min), no errors, every assertion held; the 13 first-run Phase 5 tables and the 6 post-hoc files match their recorded SHA-1s (`phase4_fold_predictions.csv.gz` again differed only in its gzip header and was restored from git). **But BSC4's timing failed:** 30% of the 50 one-wine queries took about 4.3 s (limit 3 s; re-execution 9: all under 0.04 s). The cause was the case lookup added before this run: it rebuilt the duplicate set inside a loop over the ~15,000 training winery spellings for every query whose winery is not an exact spelling. No assertion checks the timing, so the run finished. Its outputs are kept for comparison only | Lockbox (same as first run) | No |
| **Fix before re-execution 12** (no result changes): the case lookup is built once per spelling list and cached (`production._by_case`); median 0.028 s, maximum 0.065 s on the same 50 queries; cell 6.1d's assertions hold again on the saved artifact. Test `test_an_unknown_winery_keeps_a_query_fast` added (102 pass) | — | No |
| **10:14 PST: re-execution 12 of the full notebook** (Phase 6), for changes (1)–(8) and both fixes. Phases 1–5 identical frozen code | Lockbox (same as first run) | No |
| **11:52 PST: re-execution 12 finished** (about 98 min), no errors, every assertion held: the 13 first-run Phase 5 tables and the 6 post-hoc files match their recorded SHA-1s (`phase4_fold_predictions.csv.gz` again differed only in its gzip header and was restored from git); the artifact passes its reproduction check, five entries, all 0.0, the serving path now from raw review rows; the lower-limit table and the self-referenced rule's minimum round size (600) equal `config` (assertions in 6.2a); every Phase 6 table equals re-execution 11's except the wall-clock timing, now all 50 queries under 0.05 s (median 0.030 s). Monitoring at A7 round size: no false alert in 500 development or lockbox rounds; notes cut to 30 or 25 words caught in 100% of rounds (self-referenced rule; fixed limits 0% and 3.5%); a file pre-filtered at $25 caught in 100%; 2% unknown words 1.5%, prices × 1.1 0%. Dry run unchanged (+5.25 pp, lift 1.81× LB 1.43, coverage 70.75%). Screenshot retaken with this artifact | Lockbox (same as first run) | No |
| **Phase 6 critic round 6** (2026-11-09): 9/10, no MAJOR issues; 9 MINOR (`critiques/phase6_deployment_round6.md`). The author chose to fix the minors (revision 7) before committing | — | No |
| **Changes before re-execution 13** (revision 7; no pilot data exists; no model, selection or Phase 5 number changes): (1) the self-referenced rule leaves a round that raised its own alert out of the reference until the analyst accepts it (`monitoring.in_reference`), in `score.py` and in the simulation (`relative_drop_rates`); (2) notes cut to 40 and 35 words added to `monitoring.PERTURBATIONS`; (3) `score.py --round N` (required): history by round number, earlier rounds only, one per round, round 0 for test files; (4) before the decision point `gate.json`'s after-rule flag and joint gate are blank and `pilot_eval.py` prints "interim reading"; (5) `pilot_eval.py` refuses a partly blank deflator column; `sampled` read with the strict `monitoring._flag`; (6) the case lookup's cache checks list identity; (7) `PILOT_ROUND_CANDIDATES` = `CANDIDATES_PER_CYCLE`; stale comments fixed; (8) notebook 6.1c asserts BSC4's timing; (9) `monitoring.share_band`: the ≤ $25-share band re-centred at rollout step 1 if the retailer's share lies outside 35–60%. Tests: 107 pass. Smoke run of cells 6.1c and 6.2a against the saved artifact before the full run: every assertion holds (lower-limit table, minimum round size 600, BSC4 timing) | — | No |
| **17:30 PST: re-execution 13 of the full notebook** (Phase 6), for revision 7. Phases 1–5 identical frozen code | Lockbox (same as first run) | No |
| **19:09 PST: re-execution 13 finished** (about 99 min), no errors, every assertion held: the 13 first-run Phase 5 tables and the 6 post-hoc files match their recorded SHA-1s (`phase4_fold_predictions.csv.gz` again differed only in its gzip header and was restored from git); the artifact passes its reproduction check, five entries, all 0.0; the lower-limit table and the self-referenced rule's minimum round size (600) equal `config`, and BSC4's timing assertion holds (all 50 queries under 0.05 s, median 0.032 s). The five monitoring tables equal the smoke run's; every other Phase 6 table equals re-execution 12's except the wall-clock timing. Monitoring at A7 round size: no false alert in 500 development or lockbox rounds; notes cut to 40 or 35 words missed (0%); cut to 30 or 25 words caught in 100% of rounds (self-referenced rule; fixed limits 0% and 1.5%); a file pre-filtered at $25 caught in 100%; 2% unknown words 1.5%, prices × 1.1 0%. Dry run unchanged (+5.25 pp, lift 1.81× LB 1.43, coverage 70.75%). Screenshot retaken with this artifact (0.08 s) | Lockbox (same as first run) | No |

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

**Phase 6 files after re-execution 4, SHA-1** (2026-11-08 16:47 PST; `phase6_bsc4_timing.csv` is a wall-clock measurement and differs on every run):

```
6b27d124fd099d4bf20f3c05f101d6b98477bc16  models/value_finder.joblib  (bytes vary per build; see the 16:47 row)
dc5d0ef44f01322e8a06887a70efafabe2457223  phase6_masked_ranker_scores.csv.gz
74faa17fc8df43aa137eed92a46ea9abca5d9bfd  phase6_monitoring_reference.csv
cbb8f0e924c987c0515b35d71e2b8d991a470d34  phase6_pause_rates.csv
4cd5b51c36474c958aad8b05d450cc3a6781f0ca  phase6_pilot_dry_run.csv
ff2d405e39283466b56f73cd760524cda9657977  phase6_protocol_simulation.csv
71feb96698518c99e645978e104a24f038b81786  phase6_unit_truth.csv
6aece32a44f02459a7c36b105fef8d1210657c4c  phase6_verdict_tiers.csv
0dcaa8f15aec7db2b8a711bc03b484901b630aca  phase6_withdrawn_units.csv
```


**Phase 6 files after re-execution 5, SHA-1** (2026-11-08 18:49 PST; supersede the re-execution 4 block; `phase6_bsc4_timing.csv` is a wall-clock measurement and differs on every run):

```
d176a32cd21ba46f4d9149c8d14bb262452fa967  models/value_finder.joblib  (bytes vary per build; accepted by its reproduction check)
ceb95015c55000ec705899f7f45b982808d66c02  phase6_alert_rates.csv
dc5d0ef44f01322e8a06887a70efafabe2457223  phase6_masked_ranker_scores.csv.gz
744e8614e57e8473daea236531668799c3ccbc84  phase6_monitoring_reference.csv
59b16cb81ca1bff660d1dd796191129faf646325  phase6_pause_rates.csv
56126e5cf35973e047e62fae439197ccd007defc  phase6_pilot_dry_run.csv
7e14c22562a46ebb9169b5bc56f04007afdd8d00  phase6_protocol_simulation.csv
7faba8577b1f17a8d22012f5a7555d452db6bf86  phase6_seed_spread.csv
f81b1982d6e4f052a88e22dd1226ccf0de5fc7af  phase6_shortlist_tiers.csv
71feb96698518c99e645978e104a24f038b81786  phase6_unit_truth.csv
776d1ef5dec4359f807f1e895d103123c7ad1e03  phase6_verdict_tiers.csv
7add91425c5773f85fc02720a3f2938552b88e24  phase6_withdrawn_units.csv
```

**Phase 6 files after re-execution 6, SHA-1** (2026-11-08 20:53 PST; supersede the re-execution 5 block; `phase6_bsc4_timing.csv` is a wall-clock measurement and differs on every run). The code that produced them is listed too, so a later state can be matched to this run:

```
1f0b69668f8db8de9554561b6f2fa21162a49c30  models/value_finder.joblib  (bytes vary per build; accepted by its reproduction check)
4c48eda0d67fd1b267cd295368cf1b0cf78ab4ac  phase6_alert_detection.csv
ceb95015c55000ec705899f7f45b982808d66c02  phase6_alert_rates.csv
dc5d0ef44f01322e8a06887a70efafabe2457223  phase6_masked_ranker_scores.csv.gz
744e8614e57e8473daea236531668799c3ccbc84  phase6_monitoring_reference.csv
59b16cb81ca1bff660d1dd796191129faf646325  phase6_pause_rates.csv
56126e5cf35973e047e62fae439197ccd007defc  phase6_pilot_dry_run.csv
93cf71e4a08b0cd1d5872e5359418b8fa7ef842a  phase6_pilot_timeline.csv
7e14c22562a46ebb9169b5bc56f04007afdd8d00  phase6_protocol_simulation.csv
7faba8577b1f17a8d22012f5a7555d452db6bf86  phase6_seed_spread.csv
f81b1982d6e4f052a88e22dd1226ccf0de5fc7af  phase6_shortlist_tiers.csv
9c123d8254b8b2adb6d27666510f6d482526f185  phase6_unit_truth.csv
776d1ef5dec4359f807f1e895d103123c7ad1e03  phase6_verdict_tiers.csv
4867f0121d0caa4edd251b3e33b6c8bf7360ed97  phase6_withdrawn_units.csv

code:
3e33cac7885aed4be12094ff98b7ff7f9fe7d0d6  src/winevalue/pilot.py
df0995b528a73ac39c736d0dfdfec14ec6219630  src/winevalue/monitoring.py
a7f229ecb2aba3e16a56b15ec380beee59c2ea45  src/winevalue/artifacts.py
69c129777bb047fbde6d85927c650d2699fb362f  src/winevalue/production.py
ed67676f03a27ebb42a1e62b13d5dd7f5293b33b  src/winevalue/config.py
b649bc0fc3d9e2d139100825200d2db5379a7dc4  src/winevalue/phase6.py
bf954f47d84e686ce033789f69bc89bf27975cce  deployment/app.py
dd1e23481d20969653f8a45822a9d1fbfd239a2e  deployment/score.py
2fd051d29d81b424337ca67ef374f3a8c9bb29d8  deployment/pilot_eval.py
f8497885049f93562cfc2b583000073e592440a5  deployment/build_artifact.py
```

**Phase 6 files after re-execution 8, SHA-1** (2026-11-09 00:45 PST; supersede the re-execution 6 block; `phase6_bsc4_timing.csv` is a wall-clock measurement and differs on every run). Every file in `src/winevalue/` and `tests/` is listed, plus the deployment scripts (`deployment/app.py` as edited after the run), so a later state, or the tag `wine-phase6-rev4` once it exists, can be matched to this run:

```
ce7f0d1d9f6c7ecad92fe2f1709f399c7229544d  models/value_finder.joblib  (bytes vary per build; accepted by its reproduction check)
cc6cab3f4bb0120637a58936508b1fed5a281c48  reports/figures/phase6_app_one_wine.png  (taken with this artifact)
ab06d3098500046355a54e75f2d856c31209dbc9  phase6_alert_detection.csv
cb25d4737a00c20c364482b82bcf287219a927ac  phase6_alert_rates.csv
e266aeec8a3fca3483d2056839968ff0691b0024  phase6_alert_rates_oof.csv
2d5352ddf13c45aa095c4d65078776d621f8d50f  phase6_bsc4_timing.csv
dc5d0ef44f01322e8a06887a70efafabe2457223  phase6_masked_ranker_scores.csv.gz
1abf2a8ee7fdd4445e4fd6ab265558a59604289d  phase6_monitoring_reference.csv
59b16cb81ca1bff660d1dd796191129faf646325  phase6_pause_rates.csv
511a860c6b0f8b8c25d204cc0ea5dd01d1466402  phase6_pilot_dry_run.csv
93cf71e4a08b0cd1d5872e5359418b8fa7ef842a  phase6_pilot_timeline.csv
7e14c22562a46ebb9169b5bc56f04007afdd8d00  phase6_protocol_simulation.csv
7faba8577b1f17a8d22012f5a7555d452db6bf86  phase6_seed_spread.csv
f81b1982d6e4f052a88e22dd1226ccf0de5fc7af  phase6_shortlist_tiers.csv
2c52413ba045361f00145515551b6b233977c2ee  phase6_source_minimum.csv
9c123d8254b8b2adb6d27666510f6d482526f185  phase6_unit_truth.csv
776d1ef5dec4359f807f1e895d103123c7ad1e03  phase6_verdict_tiers.csv
4867f0121d0caa4edd251b3e33b6c8bf7360ed97  phase6_withdrawn_units.csv

code:
29b51f2f5dfd0b19170eb0e2be8bd29677df7dad  src/winevalue/__init__.py
a7f229ecb2aba3e16a56b15ec380beee59c2ea45  src/winevalue/artifacts.py
1b86cf93979c07af3e2b037a69b2777630f139a4  src/winevalue/clustering.py
457a9594cf7664f00df264a2ca47d9a60580c915  src/winevalue/config.py
80a470059d3ced597455fd715395925c8355788a  src/winevalue/cv.py
aedd68c2ddc71fa98b909384b082738e48c8d26c  src/winevalue/data.py
310dc214febe77ee45bff3fef594cb9f7ce71b1c  src/winevalue/descriptors.py
0b565823877fe24f36ee22f977d7739d1e9cef66  src/winevalue/evaluate.py
c8a98958ac3aa49b206b5fa773bae3321a129219  src/winevalue/features.py
b00659e585816e211be200dafd826c12ab0ebaa1  src/winevalue/grapes.py
0a4069ae925a79cf8090b6c374bf27d4533cdb6b  src/winevalue/insights.py
e92151268cb050971d22c95ce825fd62dfb88edc  src/winevalue/metrics.py
bd3276fd2d256d62da8b5facb53f1e1aa7698c92  src/winevalue/models.py
6d7e603686168a4cbc9c83462e8123c1ae14a4fe  src/winevalue/monitoring.py
93fe32c1b657dfef272225ee23d686b33de47b04  src/winevalue/phase5.py
9e14945fe8b3cf026e9559c593c10b9c0be1dbd2  src/winevalue/phase6.py
fa80b8a3814d7171a527df1cfd8b7675f319d7cf  src/winevalue/pilot.py
3a4e0672a21e4fd6a9f50c994369ad012dcaaa52  src/winevalue/prepare.py
8f39575994cafd15eb19b26cf75cfbe141738e42  src/winevalue/production.py
f373f94a99fbae05e93cd58575f7738e7760a645  src/winevalue/rules.py
3413f10f85477f6047f05226dc9f3b9a857c3ee0  src/winevalue/scoring.py
02f658b0984f6e97da2cd1a5ffdf0b7363cf2984  src/winevalue/similarity.py
a4899c595204d8107d89bd9a7d0d496363fbafdf  src/winevalue/splits.py
528dc73f41e4f51aff8d27a94e7ef50ed1b8f6d9  src/winevalue/text_audit.py
2fb0fca05d5338075b20c00e5ead12e77b157740  src/winevalue/value.py
703cee57e4961e23120ecabcd02622b1c10c290c  tests/conftest.py
64d14910d0553e7740fba6037f3925928ef9ccd2  tests/test_app.py
8c477dfaf767645342e8cec609c9297666d4b215  tests/test_data.py
1c2e8631557fbf6d85aa8717a55350fe06335543  tests/test_metrics.py
b41d15e2ceeb43d77442ea41019c40e7e22c9a89  tests/test_models.py
f0e7012c4b2f57571f7101db267358d34a9a9c21  tests/test_phase4.py
f527ac9038fe25bc2da2f6a9d296a353fd38bef7  tests/test_phase6.py
85a4c6e0ca0589f5da2b96645f8a91069c5768aa  tests/test_prepare.py
8ff502e6a0c97437937c932e176b8e01d63b8543  tests/test_rules_value.py
46b77177d38f4f542cf57fa11a3a4fdf7c412238  tests/test_similarity.py
494fba4d5dec72de5b9ef5e386c48d94e1d1d88c  tests/test_splits.py
61411e2c272bd5ea8833f7e18701119f00a02193  tests/test_text_grapes.py
763fd9dec59c5b2cb92a990b5f3f123d96773654  tests/test_value.py
f83ab50079974d27b7b3b81b07b76904341780e8  deployment/app.py
f8497885049f93562cfc2b583000073e592440a5  deployment/build_artifact.py
2cff8207e61dfec5975b4a33fd64cfe598400195  deployment/pilot_eval.py
dc7c18da8cf357e99b9ffa9fdbe6722f001a374f  deployment/score.py
```

**Phase 6 files after re-execution 9, SHA-1** (2026-11-09 02:58 PST; supersede the re-execution 8 block; `phase6_bsc4_timing.csv` is a wall-clock measurement and differs on every run). Every file in `src/winevalue/` and `tests/` is listed, plus the deployment scripts, so a later state, or the tag `wine-phase6-rev5` once it exists, can be matched to this run:

```
6fc69aba600f83ce9565a61a40a1086de1c64c61  models/value_finder.joblib  (bytes vary per build; accepted by its reproduction check, five entries)
71b1d00cbc3a3cd2b3c263895d4ba772b345c995  reports/figures/phase6_app_one_wine.png  (taken with this artifact)
de109a1ca374b05e072abdf8a80d9952b970626c  phase6_alert_detection.csv
f950a072645a6f7a87bb23f873a44df0f76e043b  phase6_alert_limits_lofo.csv
cb25d4737a00c20c364482b82bcf287219a927ac  phase6_alert_rates.csv
a684a0e442f5a2d17cffb6b9ec601895b9d5c72a  phase6_alert_rates_oof.csv
83c4b82c9fc4118a2aa64543ff1781188acd81ed  phase6_bsc4_timing.csv
dc5d0ef44f01322e8a06887a70efafabe2457223  phase6_masked_ranker_scores.csv.gz
c5767eb6720d08346fd65fed6a11e310446e02a0  phase6_monitoring_reference.csv
59b16cb81ca1bff660d1dd796191129faf646325  phase6_pause_rates.csv
cc653594d21d1a2d4c953a3fb63a23af14611190  phase6_pilot_dry_run.csv
93cf71e4a08b0cd1d5872e5359418b8fa7ef842a  phase6_pilot_timeline.csv
7e14c22562a46ebb9169b5bc56f04007afdd8d00  phase6_protocol_simulation.csv
7faba8577b1f17a8d22012f5a7555d452db6bf86  phase6_seed_spread.csv
f81b1982d6e4f052a88e22dd1226ccf0de5fc7af  phase6_shortlist_tiers.csv
2c52413ba045361f00145515551b6b233977c2ee  phase6_source_minimum.csv
9c123d8254b8b2adb6d27666510f6d482526f185  phase6_unit_truth.csv
776d1ef5dec4359f807f1e895d103123c7ad1e03  phase6_verdict_tiers.csv
4867f0121d0caa4edd251b3e33b6c8bf7360ed97  phase6_withdrawn_units.csv

code:
29b51f2f5dfd0b19170eb0e2be8bd29677df7dad  src/winevalue/__init__.py
6337312b3b3028d81fcf6b53d94e3398b5b1242a  src/winevalue/artifacts.py
1b86cf93979c07af3e2b037a69b2777630f139a4  src/winevalue/clustering.py
030633e51afd4923f25f20541ded0e5131b83c2b  src/winevalue/config.py
80a470059d3ced597455fd715395925c8355788a  src/winevalue/cv.py
aedd68c2ddc71fa98b909384b082738e48c8d26c  src/winevalue/data.py
310dc214febe77ee45bff3fef594cb9f7ce71b1c  src/winevalue/descriptors.py
0b565823877fe24f36ee22f977d7739d1e9cef66  src/winevalue/evaluate.py
c8a98958ac3aa49b206b5fa773bae3321a129219  src/winevalue/features.py
b00659e585816e211be200dafd826c12ab0ebaa1  src/winevalue/grapes.py
0a4069ae925a79cf8090b6c374bf27d4533cdb6b  src/winevalue/insights.py
e92151268cb050971d22c95ce825fd62dfb88edc  src/winevalue/metrics.py
bd3276fd2d256d62da8b5facb53f1e1aa7698c92  src/winevalue/models.py
e4312c7a1bda07d0f86745a9fc1a7e198ac8b0ce  src/winevalue/monitoring.py
93fe32c1b657dfef272225ee23d686b33de47b04  src/winevalue/phase5.py
9e14945fe8b3cf026e9559c593c10b9c0be1dbd2  src/winevalue/phase6.py
d92f98a2844be439996d2efddf95b283578ffd89  src/winevalue/pilot.py
3a4e0672a21e4fd6a9f50c994369ad012dcaaa52  src/winevalue/prepare.py
8e7d4d5b78533098664b246a36e4417fa013e9e1  src/winevalue/production.py
f373f94a99fbae05e93cd58575f7738e7760a645  src/winevalue/rules.py
3413f10f85477f6047f05226dc9f3b9a857c3ee0  src/winevalue/scoring.py
02f658b0984f6e97da2cd1a5ffdf0b7363cf2984  src/winevalue/similarity.py
a4899c595204d8107d89bd9a7d0d496363fbafdf  src/winevalue/splits.py
528dc73f41e4f51aff8d27a94e7ef50ed1b8f6d9  src/winevalue/text_audit.py
2fb0fca05d5338075b20c00e5ead12e77b157740  src/winevalue/value.py
703cee57e4961e23120ecabcd02622b1c10c290c  tests/conftest.py
64d14910d0553e7740fba6037f3925928ef9ccd2  tests/test_app.py
8c477dfaf767645342e8cec609c9297666d4b215  tests/test_data.py
1c2e8631557fbf6d85aa8717a55350fe06335543  tests/test_metrics.py
b41d15e2ceeb43d77442ea41019c40e7e22c9a89  tests/test_models.py
f0e7012c4b2f57571f7101db267358d34a9a9c21  tests/test_phase4.py
0fb35171343c8aa4dc118f159b24433ea0f3b3d0  tests/test_phase6.py
85a4c6e0ca0589f5da2b96645f8a91069c5768aa  tests/test_prepare.py
8ff502e6a0c97437937c932e176b8e01d63b8543  tests/test_rules_value.py
46b77177d38f4f542cf57fa11a3a4fdf7c412238  tests/test_similarity.py
494fba4d5dec72de5b9ef5e386c48d94e1d1d88c  tests/test_splits.py
61411e2c272bd5ea8833f7e18701119f00a02193  tests/test_text_grapes.py
763fd9dec59c5b2cb92a990b5f3f123d96773654  tests/test_value.py
7754862d233ca85bae973988dfbb51c2db1a5d87  deployment/app.py
f8497885049f93562cfc2b583000073e592440a5  deployment/build_artifact.py
ff2f821caf6b3e755d4a07ed3344f513c3fb120d  deployment/pilot_eval.py
bd0513d73e38be0f79aaa29d6ed46cd674339e47  deployment/score.py
```

**Phase 6 files after re-execution 12, SHA-1** (2026-11-09 11:55 PST; supersede the re-execution 9 block; `phase6_bsc4_timing.csv` is a wall-clock measurement and differs on every run). Every file in `src/winevalue/` and `tests/` is listed, plus the deployment scripts, so a later state, or the tag `wine-phase6-rev6` once it exists, can be matched to this run:

```
c133a2d586de07f16d7ac09f28544653ca600bd0  models/value_finder.joblib  (bytes vary per build; accepted by its reproduction check, five entries)
9e8a94be33a314fb90abe39d1a88466f4dfe608c  reports/figures/phase6_app_one_wine.png  (taken with this artifact)
c3ea73a83f172a76cf28f48eb04e2d9506abbf98  phase6_alert_detection.csv
f950a072645a6f7a87bb23f873a44df0f76e043b  phase6_alert_limits_lofo.csv
c7eb2ae844991f41145089593c9a2beb2e97fffa  phase6_alert_rates.csv
ec58a6a2e3a45f81ad13b465f3afa886d6f59d13  phase6_alert_rates_oof.csv
eb7cb7186d21ff86d66bfdc9787c3d65ade3cb55  phase6_bsc4_timing.csv
dc5d0ef44f01322e8a06887a70efafabe2457223  phase6_masked_ranker_scores.csv.gz
c5767eb6720d08346fd65fed6a11e310446e02a0  phase6_monitoring_reference.csv
59b16cb81ca1bff660d1dd796191129faf646325  phase6_pause_rates.csv
9cf78234e057ca7872c2ebb4ca3bb4ceaf3b2d84  phase6_pilot_dry_run.csv
93cf71e4a08b0cd1d5872e5359418b8fa7ef842a  phase6_pilot_timeline.csv
7e14c22562a46ebb9169b5bc56f04007afdd8d00  phase6_protocol_simulation.csv
7faba8577b1f17a8d22012f5a7555d452db6bf86  phase6_seed_spread.csv
f81b1982d6e4f052a88e22dd1226ccf0de5fc7af  phase6_shortlist_tiers.csv
2c52413ba045361f00145515551b6b233977c2ee  phase6_source_minimum.csv
9c123d8254b8b2adb6d27666510f6d482526f185  phase6_unit_truth.csv
776d1ef5dec4359f807f1e895d103123c7ad1e03  phase6_verdict_tiers.csv
4867f0121d0caa4edd251b3e33b6c8bf7360ed97  phase6_withdrawn_units.csv

code:
29b51f2f5dfd0b19170eb0e2be8bd29677df7dad  src/winevalue/__init__.py
6337312b3b3028d81fcf6b53d94e3398b5b1242a  src/winevalue/artifacts.py
1b86cf93979c07af3e2b037a69b2777630f139a4  src/winevalue/clustering.py
cba3775f557dbf146ac2fde21cd0f21a816f99fa  src/winevalue/config.py
80a470059d3ced597455fd715395925c8355788a  src/winevalue/cv.py
aedd68c2ddc71fa98b909384b082738e48c8d26c  src/winevalue/data.py
310dc214febe77ee45bff3fef594cb9f7ce71b1c  src/winevalue/descriptors.py
0b565823877fe24f36ee22f977d7739d1e9cef66  src/winevalue/evaluate.py
c8a98958ac3aa49b206b5fa773bae3321a129219  src/winevalue/features.py
b00659e585816e211be200dafd826c12ab0ebaa1  src/winevalue/grapes.py
0a4069ae925a79cf8090b6c374bf27d4533cdb6b  src/winevalue/insights.py
e92151268cb050971d22c95ce825fd62dfb88edc  src/winevalue/metrics.py
bd3276fd2d256d62da8b5facb53f1e1aa7698c92  src/winevalue/models.py
2a0bad05798626bc2dcaeac654bf6eeffb2ecf8c  src/winevalue/monitoring.py
93fe32c1b657dfef272225ee23d686b33de47b04  src/winevalue/phase5.py
9e14945fe8b3cf026e9559c593c10b9c0be1dbd2  src/winevalue/phase6.py
4ae2bee0a3370ecf07e80cba9b55a8725eccbf94  src/winevalue/pilot.py
3a4e0672a21e4fd6a9f50c994369ad012dcaaa52  src/winevalue/prepare.py
9bee01224918e5545cc250f7364374b863c888ea  src/winevalue/production.py
f373f94a99fbae05e93cd58575f7738e7760a645  src/winevalue/rules.py
3413f10f85477f6047f05226dc9f3b9a857c3ee0  src/winevalue/scoring.py
02f658b0984f6e97da2cd1a5ffdf0b7363cf2984  src/winevalue/similarity.py
a4899c595204d8107d89bd9a7d0d496363fbafdf  src/winevalue/splits.py
528dc73f41e4f51aff8d27a94e7ef50ed1b8f6d9  src/winevalue/text_audit.py
2fb0fca05d5338075b20c00e5ead12e77b157740  src/winevalue/value.py
703cee57e4961e23120ecabcd02622b1c10c290c  tests/conftest.py
64d14910d0553e7740fba6037f3925928ef9ccd2  tests/test_app.py
8c477dfaf767645342e8cec609c9297666d4b215  tests/test_data.py
1c2e8631557fbf6d85aa8717a55350fe06335543  tests/test_metrics.py
b41d15e2ceeb43d77442ea41019c40e7e22c9a89  tests/test_models.py
f0e7012c4b2f57571f7101db267358d34a9a9c21  tests/test_phase4.py
f1aa63a2a1e2ca1ec72f590b746d0482462afbe6  tests/test_phase6.py
85a4c6e0ca0589f5da2b96645f8a91069c5768aa  tests/test_prepare.py
8ff502e6a0c97437937c932e176b8e01d63b8543  tests/test_rules_value.py
46b77177d38f4f542cf57fa11a3a4fdf7c412238  tests/test_similarity.py
494fba4d5dec72de5b9ef5e386c48d94e1d1d88c  tests/test_splits.py
61411e2c272bd5ea8833f7e18701119f00a02193  tests/test_text_grapes.py
763fd9dec59c5b2cb92a990b5f3f123d96773654  tests/test_value.py
7754862d233ca85bae973988dfbb51c2db1a5d87  deployment/app.py
f8497885049f93562cfc2b583000073e592440a5  deployment/build_artifact.py
4c5fb23b06007fe938587d6093d43aa00813609a  deployment/pilot_eval.py
1e430258d25d043ef7989f4d6f1713559822b2c0  deployment/score.py
```

**Phase 6 files after re-execution 13, SHA-1** (2026-11-09 19:15 PST; supersede the re-execution 12 block; `phase6_bsc4_timing.csv` is a wall-clock measurement and differs on every run). Every file in `src/winevalue/` and `tests/` is listed, plus the deployment scripts, `deployment/requirements.txt` and the deployment documents, so a later state, or the tag `wine-phase6-rev7` once it exists, can be matched to this run:

```
38fe5c8a2559f87a9b1a547b906b43af71b59308  models/value_finder.joblib  (bytes vary per build; accepted by its reproduction check, five entries)
ad3d71c5832403c0667929798278e8d8628d4f4c  reports/figures/phase6_app_one_wine.png  (taken with this artifact)
ab19aec7304881c7990c9776cda66a9619182e00  phase6_alert_detection.csv
f950a072645a6f7a87bb23f873a44df0f76e043b  phase6_alert_limits_lofo.csv
c7eb2ae844991f41145089593c9a2beb2e97fffa  phase6_alert_rates.csv
4269eea99541d898f09fd927fb4a9bdee391d800  phase6_alert_rates_oof.csv
2fea6f809a1cf399db58555052e50c3d76050ea4  phase6_bsc4_timing.csv
dc5d0ef44f01322e8a06887a70efafabe2457223  phase6_masked_ranker_scores.csv.gz
c5767eb6720d08346fd65fed6a11e310446e02a0  phase6_monitoring_reference.csv
59b16cb81ca1bff660d1dd796191129faf646325  phase6_pause_rates.csv
9cf78234e057ca7872c2ebb4ca3bb4ceaf3b2d84  phase6_pilot_dry_run.csv
93cf71e4a08b0cd1d5872e5359418b8fa7ef842a  phase6_pilot_timeline.csv
7e14c22562a46ebb9169b5bc56f04007afdd8d00  phase6_protocol_simulation.csv
7faba8577b1f17a8d22012f5a7555d452db6bf86  phase6_seed_spread.csv
f81b1982d6e4f052a88e22dd1226ccf0de5fc7af  phase6_shortlist_tiers.csv
2c52413ba045361f00145515551b6b233977c2ee  phase6_source_minimum.csv
9c123d8254b8b2adb6d27666510f6d482526f185  phase6_unit_truth.csv
776d1ef5dec4359f807f1e895d103123c7ad1e03  phase6_verdict_tiers.csv
4867f0121d0caa4edd251b3e33b6c8bf7360ed97  phase6_withdrawn_units.csv

code:
29b51f2f5dfd0b19170eb0e2be8bd29677df7dad  src/winevalue/__init__.py
6337312b3b3028d81fcf6b53d94e3398b5b1242a  src/winevalue/artifacts.py
1b86cf93979c07af3e2b037a69b2777630f139a4  src/winevalue/clustering.py
5e1b0308471ec2b74e54f93d7eb16172f952562b  src/winevalue/config.py
80a470059d3ced597455fd715395925c8355788a  src/winevalue/cv.py
aedd68c2ddc71fa98b909384b082738e48c8d26c  src/winevalue/data.py
310dc214febe77ee45bff3fef594cb9f7ce71b1c  src/winevalue/descriptors.py
0b565823877fe24f36ee22f977d7739d1e9cef66  src/winevalue/evaluate.py
c8a98958ac3aa49b206b5fa773bae3321a129219  src/winevalue/features.py
b00659e585816e211be200dafd826c12ab0ebaa1  src/winevalue/grapes.py
0a4069ae925a79cf8090b6c374bf27d4533cdb6b  src/winevalue/insights.py
e92151268cb050971d22c95ce825fd62dfb88edc  src/winevalue/metrics.py
bd3276fd2d256d62da8b5facb53f1e1aa7698c92  src/winevalue/models.py
387b85b21cc5e8b4978906ca95d2596e1cb0d427  src/winevalue/monitoring.py
93fe32c1b657dfef272225ee23d686b33de47b04  src/winevalue/phase5.py
9e14945fe8b3cf026e9559c593c10b9c0be1dbd2  src/winevalue/phase6.py
cd809095590c4d1ecc5e29e42b94c378dd98a2aa  src/winevalue/pilot.py
3a4e0672a21e4fd6a9f50c994369ad012dcaaa52  src/winevalue/prepare.py
f5afa4be7e252bc23df377cd47012701a4d9a522  src/winevalue/production.py
f373f94a99fbae05e93cd58575f7738e7760a645  src/winevalue/rules.py
3413f10f85477f6047f05226dc9f3b9a857c3ee0  src/winevalue/scoring.py
02f658b0984f6e97da2cd1a5ffdf0b7363cf2984  src/winevalue/similarity.py
a4899c595204d8107d89bd9a7d0d496363fbafdf  src/winevalue/splits.py
528dc73f41e4f51aff8d27a94e7ef50ed1b8f6d9  src/winevalue/text_audit.py
2fb0fca05d5338075b20c00e5ead12e77b157740  src/winevalue/value.py
703cee57e4961e23120ecabcd02622b1c10c290c  tests/conftest.py
64d14910d0553e7740fba6037f3925928ef9ccd2  tests/test_app.py
8c477dfaf767645342e8cec609c9297666d4b215  tests/test_data.py
1c2e8631557fbf6d85aa8717a55350fe06335543  tests/test_metrics.py
b41d15e2ceeb43d77442ea41019c40e7e22c9a89  tests/test_models.py
f0e7012c4b2f57571f7101db267358d34a9a9c21  tests/test_phase4.py
8d3e7e69e9f7350b11cb00dc4367d5328df62453  tests/test_phase6.py
85a4c6e0ca0589f5da2b96645f8a91069c5768aa  tests/test_prepare.py
8ff502e6a0c97437937c932e176b8e01d63b8543  tests/test_rules_value.py
46b77177d38f4f542cf57fa11a3a4fdf7c412238  tests/test_similarity.py
494fba4d5dec72de5b9ef5e386c48d94e1d1d88c  tests/test_splits.py
61411e2c272bd5ea8833f7e18701119f00a02193  tests/test_text_grapes.py
763fd9dec59c5b2cb92a990b5f3f123d96773654  tests/test_value.py
7754862d233ca85bae973988dfbb51c2db1a5d87  deployment/app.py
f8497885049f93562cfc2b583000073e592440a5  deployment/build_artifact.py
afff37d244750f2ba945cef390c5b7cb4a1b18be  deployment/pilot_eval.py
6bfae8a0f5265747f78516016e60fbcd2e2d70c9  deployment/score.py
5cb502197372414338f4421a6dc70500fc79337d  deployment/requirements.txt

deployment documents:
c896c8ca4c3ebd2c26158e6c057f852d286c592c  deployment/README.md
429bb983987259e96946477d97afdda9fe239df3  deployment/model_card.md
b4203fd559a1eab2a9576ef29cead576019d5a20  deployment/monitoring_plan.md
```
