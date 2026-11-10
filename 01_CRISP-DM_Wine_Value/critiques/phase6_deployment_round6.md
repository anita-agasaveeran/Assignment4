# Phase 6 · Deployment: Critic Round 6
- **Date:** 2026-11-09
- **Reviewer:** Claude critic (independent subagent session), persona from `critic_prompt.md`. Read-only.
- **Draft reviewed:** Phase 6 revision 6 (report §6, notebook §6 after re-execution 12, deployment/ files)

## Score: 9 / 10 · Major issues remaining: no

## Summary
Revision 6 fixes round 5's MAJOR issue. I checked it by running the code, not only by reading the text. There is now one definition of a buying round:
- A7 (about 1,000 ≤ $25 candidates) drives the schedule and the model card.
- `monitoring.round_size` sizes every monitoring simulation from A7 (2,067 development candidates, 2,442 lockbox candidates).
- The candidate file is every candidate at any price. The ≤ $25 test comes after the deflator, and this is stated in the same words in §6.1, rollout step 2, README step 1 and `score.py`.
- A file pre-filtered at $25 sets off the alert in 100% of rounds. Normal files do not set it off.

The winery key no longer crosses countries. `gate.json` now reflects the comparator rule. The deflator refusal, the strict yes/no parsing and the serving path from raw rows all work as described. All 61 SHA-1s match. The run log reports the two failed re-executions candidly.

What remains is MINOR, and most of it concerns the new self-referenced rule:
- **Persistent faults:** it goes silent after two rounds of a fault that persists, because faulty rounds enter its own reference. This is not disclosed.
- **Detection claims:** its 100% detection is measured on the two faults it was designed against. A 35-word truncation (a 35% drop) is missed.
- **History:** its history depends on file modification times and on what else sits in the output folder.

Other residuals:
- the interim gate file and console can still say "BO1 PASS" when the comparator is degraded;
- the deflator check accepts a partly blank column;
- the `sampled` flag is parsed two different ways;
- some code comments are stale, the artifact size in the report is stale, and the BSC4 timing still has no notebook assertion.

## What I verified, and how
- **Tests:** `pytest` gives **102 passed** (43.9 s). Nothing was written to the project: no `band_status.json` and no `reports/pilot/`. All my outputs went to the scratchpad.
- **SHA-1s:** all **61** entries in the "Phase 6 files after re-execution 12" block match `shasum`:
  - the artifact `c133a2d…` and the screenshot;
  - 17 `phase6_*` tables;
  - all 25 `src/winevalue/` and 13 `tests/` files;
  - 4 deployment scripts.

  Against the re-execution 9 block, only the alert tables, the timing, `phase6_pilot_dry_run.csv` (one added field) and the screenshot changed. The protocol, pause, tier, verdict, timeline and source-minimum tables are byte-identical. The manifest records five entries, all 0.0.
- **Freeze:** no `wine-phase6-rev6` tag exists. §6.1 "Freeze", the executive summary, rollout step 0 and the model card's version line all say "to be committed and tagged", which is correct. Not hashed: `deployment/requirements.txt`, which pins scikit-learn, and the three deployment `.md` files.
- **One round definition (round-5 issue 1).** A7 reads the same everywhere I looked: §1.2, A9, `config.PILOT_ROUND_CANDIDATES` = `CANDIDATES_PER_CYCLE` = 1,000, the model card, slides 1 and 11, the README and the `score.py` docstring.
  - **`pilot_timeline`:** month 8 at 10% / 3 months; factor 2.77; 145 wines at month 6; about 290 by the cap at 5% / 6 months.
  - **CSV sizes:** `alert_rates` uses 2,067 / 2,442 candidates per round, and `detection_rates` 2,442.
  - **Pre-filter through the real script:** a file pre-filtered at $25 and run through `score.main` gives "≤ $25 share = 1 (outside (0.25, 0.95))". Lockbox and development rounds sit at 41% and 48% and give 0 false alerts.
- **Report §6.2 tables against the CSVs:**
  - 0% false alerts in 500 A7 rounds;
  - out-of-fold ranker alerts at most 1.4%, and none at 1,000 candidates;
  - fresh seed at most 2.4% (fold 1, size 300), 0.2% at 1,000;
  - leave-one-fold-out 0–0.2%;
  - detection: 30 / 25 / 15 words 100% (25 words: fixed limit 3.5%); 2% unknown words 1.5%; 5% and 20% unknown 100%; prices × 1.1 0%, × 1.3 99%, × 1.5 100%; grapes, countries, promotional sentence and pre-filter 100%; case and alias 0%;
  - every pool value: 30 → 11 → 4.1%, P(90+) 0.32 → 0.19, ≤ $25 share 32 / 23 / 15%.

  All match.
- **Self-referenced rule:**
  - **Minimum round size:** `relative_drop_rates` in `phase6_alert_rates_oof.csv` gives 200: 2.0 / 8.5 / 9.3 / 0.2%; 300: 0.8 / 6.2 / 5.8 / 0%; 600: 0 / 0.8 / 1.2 / 0%; 1,000: 0. The stated rule (smallest size from which every fold is ≤ 2%) gives **600**, the value the notebook asserts.
  - **`score.py --history`, run end to end on seven A7 rounds of lockbox rows:**
    - rounds 1–3 raise no alert;
    - a 25-word truncation from round 4 alerts in **rounds 4 and 5 only**, and is silent in rounds 6–7 (issue 1);
    - with a 396-candidate round 2 in the history, round 4 is silent (only 2 qualifying past rounds) and round 5 alerts. Correct as specified.
  - **Robustness I added:**
    - winery-clustered lockbox rounds at 600 / 1,000: 0% false alerts;
    - rounds whose note-source mix follows Dirichlet(α) across the four lockbox writers: 0% at α = 20 or 8, 0.5% at α = 4.

    So the rule is sound against ordinary mix swings.
  - **Sensitivity beyond the tested faults:** the share above P90 falls from 30% to 20% at 35 words (ratio 0.65) and to 26% at 40 words. Neither crosses the 0.5 line, so neither is caught (issue 2).
- **Winery matching (round-5 issue 2):**
  - Lockbox `lockbox_split(prep)[1]` gives **21 remapped rows (11 in the pool)**, from 7 Italian spellings, with 0 cross-country remaps.
  - "Patria" / Italy stays unmatched. "Patria" / Portugal → "Pátria". "PATRIA" / Italy stays unmatched.
  - "NEUMEISTER" or "neumeister" with country US or Unknown → "Neumeister", with an identical winery-rule score.
  - Upper-cased, lower-cased and swap-cased lockbox wineries give a winery-rule difference of 0.0 and identical coverage (27.3% unseen).
  - **Title case** changes 5 rows (0.66 points): "StoneCap" (10 training reviews) becomes "Stonecap", a separate training spelling with 1 review and its own record. The training data has 24 such case-only pairs (48 spellings), which `_by_case` rightly excludes. The frozen rule treats each pair as two wineries, so a case variant of the minority spelling scores as the majority spelling (issue 6).
  - **Performance:** `prepare` on one row takes about 0.012 s with an unseen, case-variant, exact or accent-variant winery. The saved timing has median 0.030 s and max 0.042 s.
- **Comparator rule (round-5 issue 3), through `evaluate_raw` and `pilot_eval.main`:**
  - **Dry run:** +5.25 pp (LB +1.21), 1.808× (LB 1.434), coverage 70.75%; matched-winery gate 283 wines, 1.59× (LB 1.35).
  - **35% of matched wineries un-matched:** coverage 45.5%, degraded; the matched gate (182 wines) passes and the shortlist deploys.
  - **95% un-matched:** coverage 2.5%; `BO1 passes` True, `BO1 passes (after comparator rule)` **False**, joint False; "deploy nothing". The console prints "fail (fails the comparator rule)" and "too few matched-winery wines (< 100), so the shortlist is not deployed". Correct.
  - **Interim, 300 wines, coverage 0%:** `BO1 passes (after comparator rule)` is **True** and the console prints "BO1 … PASS". It also prints "DEGRADED … so the shortlist is not deployed" (issue 4).
- **`pilot_eval.py` deflator check (round-5 issue 6):**

  | Column | Result |
  |---|---|
  | Absent | refused; runs with `--deflator-confirmed` |
  | All blank | refused |
  | Mismatched (0.77) or mixed | refused, even with the flag |
  | String "1.0" | runs |
  | **399 rows of 1.0 and one blank** | **runs** (issue 5) |
- **`business_kpi` (round-5 issue 5):** yes/no/Y/1.0/blank/None/TRUE/0 are read correctly. "maybe", "2", "-1" and "N/A" are refused. `pilot._as_bool`, used for the same `sampled` column in the gate sensitivity, still reads "N/A", "x" or "Sampled" as False silently (issue 5).
- **Serving path (round-5 issue 7):**
  - `reproduces_lockbox(…, raw=load_raw())` gives 0.0 on all five entries in 3.3 s; the raw file has no `vintage` column.
  - Breaking `extract_vintage` gives 0.996 → fails, so title-based vintage parsing is now exercised.
- **Ranker limits (round-5 issue 8):** `ranker_lower` returns None / 0.06 / 0.06 / 0.07 / 0.07 / 0.07 / 0.07 / 0.08 at 199 / 200 / 299 / 300 / 599 / 600 / 999 / 1,000. A 150-candidate round with P(90+) 0.76 and 89% above P90 raises both upper alerts. With low values it raises none, as specified.
- **Other numbers:** these match the CSVs and notebook outputs:
  - executive summary: 0.03 s, every 100 up to 800, 97.5% / 16%, month 8, $1,200–2,400, $10,000, eleven complete of twelve logged re-executions;
  - model card, monitoring plan §1–5, README;
  - slides 8–12: 97.5% / 16%, false pauses ≤ 3%, 44–94% / 0–5%, 0.08 / 3%, 600, 0% / 2.4%, the detection list.

  Exceptions: the artifact size in the report (4.3 MB against 4,644,869 bytes; the notebook prints 4.6 MB) and the stale comments in issue 7.
- **Run log:** rows for re-executions 10–12 are candid and specific:
  - re-execution 10: the assertion that stopped it, the "Neumeister" / Unknown wine, outputs discarded;
  - re-execution 11: the 4.3 s timings, the cause, "no assertion checks the timing", outputs kept only for comparison;
  - the fix before each run and the test added (101, then 102).

  The "eleven complete re-executions" count is consistent with this. §6.4 "Time and cost" takes the right lesson. One gap: the lesson was not turned into an assertion (issue 8).

## Task coverage
| CRISP-DM task / output | Present / Partial / Missing | Note |
|---|---|---|
| 6.1 Plan deployment → Deployment plan | **Present** | **What is in place:**<br>• one definition of the round and the candidate file, used throughout;<br>• an artifact with an exact reproduction, now from raw rows;<br>• one entry point that canonicalises five name columns, with in-country accent matching;<br>• a comparator rule reflected in `gate.json`;<br>• a price basis with refusal paths;<br>• the protocol in code;<br>• schedule, cap, fallback, cost, prerequisites, rollout and freeze.<br>**Residuals:** interim flag (issue 4), partly blank deflator column (issue 5). |
| 6.2 Plan monitoring and maintenance → Monitoring and maintenance plan | **Present** | **What is in place:**<br>• A7-sized simulations;<br>• per-size lower limits from a reproduced rule;<br>• a pre-filter alert;<br>• a self-referenced rule whose minimum round size follows from a stated rule;<br>• honest lists of what is caught and missed;<br>• a KPI with baseline and strict flags;<br>• a retraining policy.<br>**Gaps:**<br>• the rule goes silent on a persistent fault, and this is not disclosed;<br>• its detection is tested only on the faults it was designed for;<br>• its history is fragile (issues 1–3). |
| 6.3 Produce final report → Final report | **Present** | §6 traces to cells and CSVs, and every figure I checked verifies. Stale lines are listed in issue 7. |
| 6.3 Produce final report → Final presentation | **Partial** | A 12-slide outline with speaker notes and a screenshot. Slides 8–12 are accurate and current. Rendering is a declared later deliverable; judged on content, the outline is sound. |
| 6.4 Review project → Experience documentation | **Present** | Specific and self-critical, with a "next time" for each lesson. It now covers the round definition, the self-referenced rule and the cost of the failed runs. |

## Round-5 issues
| # | Round-5 issue | Status | Evidence |
|---|---|---|---|
| 1 | MAJOR: "buying round" and "candidate file" defined inconsistently | **Resolved** | **One definition everywhere:** A7, A9, the model card, the README, `score.py` and rollout step 2. Every simulation uses `round_size`: 2,067 / 2,442 candidates.<br>**Schedule:** unchanged (month 8).<br>**Monitoring:** an A7 round uses the 1,000+ row; the "400–480" premise is withdrawn in the report.<br>**Pre-filter:** a ≤ $25 share above 95% alerts in 100% of pre-filtered rounds and 0% of normal ones, and I confirmed it through `score.main`.<br>**Residuals:** two stale code comments (issue 7). The 25%–95% band assumes the retailer's price mix resembles the data's (issue 9). |
| 2 | Winery key crosses countries | **Resolved** | 21 rows / 11 in the pool, all Italian, none cross-country. "Patria" / Italy stays unmatched. Case variants keep their record.<br>**Residual:** the 24 training case-only pairs (issue 6). |
| 3 | `gate.json` contradicts the decision when degraded | **Resolved at the decision point** | At 95% un-matched: after-rule False, joint False, "deploy nothing"; the console states the cause.<br>**Residual:** the interim gate file and console (issue 4). |
| 4 | Coverage measure weakly grounded | **Partly resolved (by disclosure)** | The measure is kept. Its coarseness (68% seen against 44% with ≥ 5 reviews) and the 50% judgement call are now stated. The sweep is quoted, and `pilot_eval.py` prints the matched-winery lift. Acceptable as a disclosed judgement call. |
| 5 | `business_kpi` misreads string flags | **Resolved** | `_flag` is strict, and the split is called descriptive.<br>**Residual:** `pilot._as_bool` parses the same `sampled` column leniently (issue 5). |
| 6 | Deflator refusal skipped when the column is missing | **Resolved** | Absent → refused unless `--deflator-confirmed`. Tests run `pilot_eval.main` on match, mismatch, mixed and absent.<br>**Residual:** a partly blank column passes (issue 5). |
| 7 | Serving path not from raw rows | **Resolved** | Starts from `load_raw()` with no `vintage` column; 0.0. Breaking vintage parsing makes it fail. |
| 8 | Lower alerts blind to mild faults; small rounds lose the upper alerts | **Resolved as specified** (new residuals) | The self-referenced rule is implemented, its minimum round size of 600 follows from the stated rule, the notebook asserts it, and `score.py` feeds the history. Upper limits are read at any size, and tests cover 199–1,000.<br>**Residuals:** silent after two rounds of a persistent fault; detection tested only on design faults; history by mtime; not in the app view (issues 1–3). |
| 9 | Stale or inexact text | **Mostly resolved** | Reading 6.1 and 6.2, model card, Freeze list and placeholders are fixed. New stale lines are in issue 7. |
| 10 | Presentation is an outline | **Not resolved (declared deferral)** | Content verified. Acceptable as stated. |

## Issues raised
| # | Severity | Issue | Suggested fix |
|---|---|---|---|
| 1 | MINOR | **The self-referenced rule goes silent on a fault that persists, and the plan does not say so.**<br>• `relative_alerts` takes the median of the last 3 qualifying rounds, including rounds that themselves alerted.<br>• Run through `score.py` (3 clean A7 rounds, then 25-word notes from round 4), it fires in rounds 4 and 5. From round 6 the faulty level is the reference and nothing fires.<br>• "Two rounds in a row → new-version review" happens to cover this, but only if the analyst acts. The report and monitoring plan mention only slow drift as a blind spot. | Exclude rounds that raised the self-referenced alert, or any ranker alert, from the reference until the analyst clears them. Or freeze the reference to the last 3 accepted rounds. Store an "accepted" flag in each `.monitoring.json`.<br>Either way, state the behaviour in §6.2 and in monitoring plan §2. Add a test with 3 clean rounds followed by 4 faulty ones. |
| 2 | MINOR | **The rule's detection is measured only on the faults it was designed against, and the text generalises it.**<br>• The 0.5 drop and 3-round history were proposed in round 5 with the 30- and 25-word drops (30 → 11 → 4%) in view. So "100% caught" on those two rows is not an independent test.<br>• The rule needs the share to halve. Notes cut to 35 words (30% → 20%, ratio 0.65) or 40 words (26%) are missed by every alert.<br>• §6.2 says it catches "the mild truncations that the fixed limits miss". The "missed" list does not name drops of 35% or less.<br>• Only the minimum round size was set by a stated rule; 0.5 and 3 are judgement calls, but they are not called that. | • Add 35- and 40-word rows to `PERTURBATIONS`, or report the smallest relative drop the rule detects in ≥ 90% of A7 rounds (about 50%).<br>• Add "drops of less than about half its own level" to the "missed" lists in §6.2, the monitoring plan and slide 11.<br>• Label 0.5 and 3 as judgement calls. |
| 3 | MINOR | **The rule's history is fragile in practice.**<br>• `score.load_history` takes every `*.monitoring.json` in the folder, ordered by file modification time. So:<br>&nbsp;&nbsp;– the rollout step 1 test file counts as a round if it lands there;<br>&nbsp;&nbsp;– re-scoring an old round makes it "latest";<br>&nbsp;&nbsp;– re-scoring a round under a new name counts it twice;<br>&nbsp;&nbsp;– re-scoring round k uses later rounds as its "previous" ones.<br>• The app's shortlist view calls `round_report` with no history, yet §6.2 and monitoring plan say `round_report` "runs inside `score.py` and the app's shortlist view, so every scored round gets" the checks. | • Record a round ID or date (a `--round` argument) in each report, order by it, use only rounds before the current one, and de-duplicate by ID. Tell the analyst to put the step 1 test file elsewhere.<br>• Say in §6.2 and the monitoring plan that the self-referenced rule runs only in `score.py`. |
| 4 | MINOR | **At an interim check, `gate.json` and the console ignore the comparator rule.**<br>• `run_protocol` applies `comparator_check` only at the decision point. At 300 wines with 0% coverage, `BO1 passes (after comparator rule)` is True and the console prints "BO1 … PASS". It also prints "DEGRADED … so the shortlist is not deployed".<br>• README step 3 omits the ≥ 100 matched-wine minimum. | • At interim, apply the rule to the interim flag, or set it to null with "applies at the decision point". Print "interim" in place of PASS/fail.<br>• Add "(at least 100)" to the README.<br>• Add an interim degraded test. |
| 5 | MINOR | **Two input checks are not strict.**<br>• **Deflator:** `pilot_eval.py` drops blanks before comparing, so a file with one blank `price deflator` row passes. That is the case of rows appended from an unscored source.<br>• **`sampled`:** `pilot._as_bool` reads the column for the gate's unsampled-wines sensitivity, and maps "N/A", "x" or "Sampled" to False silently. `monitoring._flag` refuses the same values for the KPI. | • Refuse any blank deflator value; `--deflator-confirmed` covers only an absent column.<br>• Use `monitoring._flag` in `pilot.from_raw`, so one parser serves every yes/no column.<br>• Test both. |
| 6 | MINOR | **"A case variant always scores as its exact spelling" is slightly overstated.**<br>• Training holds 24 case-only pairs (48 spellings, e.g. "StoneCap", 10 reviews, and "Stonecap", 1 review). The frozen rule treats each pair as two wineries with different records.<br>• A variant of the minority spelling ("STONECAP") is mapped by the in-country key to the majority spelling. On the lockbox, title-casing the wineries moves 5 "StoneCap" rows by 0.66 points.<br>• Separately, `_by_case` caches by `id(list)` and length. Two different spelling lists of equal length can reuse an id after garbage collection, for example in tests. | • Reword §6.1 and the model card: "except for the 24 training wineries spelled two ways in case only, which go to the more frequent spelling".<br>• Store the case lookup on the `ValueFinder`, or key the cache on a hash of the spellings. |
| 7 | MINOR | **Stale or inexact text after revision 6.**<br>• `config.py` line 165 and the notebook cell 6.2a comment still say "a real round of 1,000 candidates holds about 400–480".<br>• `config.py` lines 172–173 say the relative rule's rounds need "≥ MONITOR_RANKER_MIN_POOL" (200); the code uses `MONITOR_RELATIVE_MIN_POOL` (600).<br>• The `monitoring.py` docstring says `alert_rates` uses "rounds of 1,000 candidates" and does not list `relative_alerts` or `round_size`.<br>• Report §6.1 gives the artifact as "4.3 MB"; the manifest says 4,644,869 bytes and the notebook prints 4.6 MB.<br>• "1,000 candidates take about 2 s": an A7 file is about 2,400 candidates (my runs: about 2.3 s).<br>• A7 lives in two constants (`CANDIDATES_PER_CYCLE`, `PILOT_ROUND_CANDIDATES`). | Correct each line. Derive one constant from the other. Add `requirements.txt` and the deployment `.md` files to the run log's SHA-1 block and to the Freeze list. |
| 8 | MINOR | **BSC4's timing still has no assertion.**<br>• Re-execution 11 "finished" with 30% of queries over 3 s because nothing checks the timing.<br>• The fix added a unit test (< 0.5 s on a mock), but notebook 6.1c still only displays `bsc4`. | Add `assert bsc4["share under 3 s"] == 1.0` to 6.1c, in line with §6.4's own lesson. |
| 9 | MINOR | **The ≤ $25-share band and the round size assume the retailer's price mix resembles WineEnthusiast's.**<br>• "About 2,400 candidates" and the 25% / 95% limits come from the 41–48% shares in the data. A value-focused retailer's natural share could sit near 95% (constant false pre-filter alerts) or near 25%.<br>• At A7's own low sensitivity (500 ≤ $25 per round), the self-referenced rule is never read and the decision moves to about month 12. This is implied by the A8 rows but not stated. | • At rollout step 1, record the retailer's ≤ $25 share on the pre-tool rounds used for the baseline. Re-centre the limits if it lies outside 35–60%, as a pre-registered step 0 decision.<br>• State in §6.1 that A7 = 500 is equivalent to the 5% yield row and silences the self-referenced rule. |
| 10 | MINOR | **Presentation is an outline** (declared deferral). | Render it with the walkthrough video, as planned. |

## Most important improvement
Make the self-referenced rule hold on a fault that persists, and report its reach honestly (issues 1 and 2):
- **Reference:** keep alerted rounds out of the rule's reference until the analyst clears them, or freeze the reference to accepted rounds. Order the history by round ID, not file time (issue 3).
- **Detection claims:** add a truncation milder than the design faults (35–40 words). State that the rule sees only drops of about half the feed's own level or more.

Today a truncation that starts in round 4 and is never fixed raises two alerts and then disappears from monitoring. The text says the rule "catches mild truncation", but it was tested only on the two faults it was built for. With that fixed, and with the small consistency fixes in issues 4, 5 and 7, the phase is ready to commit and tag as `wine-phase6-rev6`.

## Changes made (revision 7, 2026-11-09; re-execution 13)
| # | Change | Where |
|---|---|---|
| 1 | A round that raised the self-referenced alert stays out of the rule's reference until the analyst sets `"accepted": true` in its report (`monitoring.in_reference`), in `score.py` and in the simulation (`relative_drop_rates`). Test: 3 clean rounds then 4 faulty ones alert in all 4; accepting them moves the reference. The out-of-fold false-alert rates at 200–300 ≤ $25 candidates rise (up to 13%; an alerted round no longer resets the reference); from 600 they are unchanged (≤ 1.2%), so the minimum stays 600 by the same stated rule | `src/winevalue/monitoring.py`, `deployment/score.py`, tests, report §6.2, monitoring plan §2, slide 11 |
| 2 | Notes cut to 40 and 35 words added to the detection table: missed (0%; the share above the P90 falls to 26% and 20% of a 30% level). The "caught" text now says the rule sees drops to about half the feed's own level, the "missed" lists name the milder truncations, and the 0.5 drop and 3-round history are called judgement calls | `monitoring.PERTURBATIONS`, report §6.2, monitoring plan, slide 11, notebook reading 6.2, `config.py` |
| 3 | `score.py --round N` (required): history from reports of rounds 1 to N−1, ordered by round number, one per round (the latest write of a re-scored round), never round 0 (rollout step 1's test file). The text says the rule runs only in `score.py`, not in the app view. Test | `deployment/score.py`, README, report §6.1–6.2, monitoring plan |
| 4 | Before the decision point `BO1 passes (after comparator rule)` and `joint gate passes` are blank, and `pilot_eval.py` prints "interim reading"; README states the 100-wine minimum. Test at 300 wines with 0% coverage | `src/winevalue/pilot.py`, `deployment/pilot_eval.py`, README, report §6.1, reading 6.1 |
| 5 | `pilot_eval.py` refuses a deflator column with any blank value (`--deflator-confirmed` covers only a missing column); `sampled` is read with the strict `monitoring._flag`, and the lenient `_as_bool` is removed. Tests | `deployment/pilot_eval.py`, `src/winevalue/pilot.py`, tests, report §6.1 |
| 6 | §6.1, reading 6.1 and the model card name the exception: the 24 training wineries spelled two ways in case only go to the more frequent spelling. The case lookup's cache holds the spelling list and checks identity, so a reused id never serves an old lookup | `src/winevalue/production.py`, report, notebook, model card |
| 7 | Stale lines fixed: `config.py` comments (400–480; the relative rule's minimum), the 6.2a cell comment, the `monitoring.py` docstring, the artifact size (4.6 MB), `score.py`'s time for an A7 file (about 2–3 s); `PILOT_ROUND_CANDIDATES` = `CANDIDATES_PER_CYCLE`; the Freeze list and the run log's SHA-1 block now include `requirements.txt` and the deployment documents | `config.py`, notebook, `monitoring.py`, report §6.1, run log |
| 8 | Notebook 6.1c asserts `bsc4["share under 3 s"] == 1.0` | notebook |
| 9 | Rollout step 1 records the retailer's ≤ $25 share on the pre-tool rounds; outside 35–60% the band is re-centred (`monitoring.share_band`: share − 0.20 to share + 0.45, within 0.05–0.98; a pre-filtered file stays outside). §6.1 states that A7 = 500 behaves like the 5% yield row and silences the self-referenced rule. Tests | `src/winevalue/monitoring.py`, `config.py`, report §6.1, monitoring plan |
| 10 | Not done: the presentation stays an outline (declared deferral) | – |
