# Phase 6 · Deployment: Critic Round 5
- **Date:** 2026-11-09
- **Reviewer:** Claude critic (independent subagent session), persona from `critic_prompt.md`. Read-only.
- **Draft reviewed:** Phase 6 revision 5 (report §6, notebook §6 after re-execution 9, deployment/ files)

## Score: 8 / 10 · Major issues remaining: yes

## Summary
Revision 5 closes round 4's MAJOR issue properly. I confirmed it by running the code:
- The winery now reaches the "winery track record" rule as the training spelling. That holds for upper case, lower case, stripped accents, padding and punctuation.
- The coverage rule behaves as the report describes.
- The serving-path entry in the reproduction check catches real regressions.
- The per-size lower limits reproduce exactly from their stated rule.

Most of the other round-4 issues are resolved too, and every SHA-1 in the re-execution 9 block matches the file on disk.

Revision 5's own rationale, though, opens a new contradiction at the centre of the plan. **The report now defines a "buying round" in two ways that cannot both be true:**
- **A7 and A9 (schedule):** a round has about 1,000 ≤ $25 candidates. This gives 100 scored wines a month and the decision at month 8.
- **§6.2 and the monitoring plan (revision 5's reason for per-size limits):** "a real round of 1,000 candidates holds about 400–480 ≤ $25 wines." Under that premise the base case reaches only about 382 scored wines by month 12, so there is no decision within the cap.
- **Rollout (step 2, README step 1):** analysts are told to "score every ≤ $25 candidate". If the retailer filters at a nominal $25 before scoring:
  - the deflator can never bring back wines priced $25–32.47 nominal (≤ $25 in 2017 dollars at 0.77);
  - the ≤ $25-share alert, the only alert said to catch a wrong or missing deflator, reads about 100% and can never fire.

The price-basis prerequisite (a round-3 MAJOR fix) therefore only works if whole, all-price candidate files are scored, and the plan doesn't say so.

The rest are MINOR: two cross-producer winery mappings that contradict the report's wording, a crude coverage measure, `gate.json` contradicting the decision when the comparator is degraded, a type bug in `business_kpi`, a deflator refusal that is skipped silently, and some stale text.

## What I verified, and how
- **Tests:** `pytest` gives **92 passed** in 40.9 s.
- **SHA-1s:** all **61** entries in the "Phase 6 files after re-execution 9" block match `shasum`:
  - artifact `6fc69ab…` and the screenshot;
  - all 17 `phase6_*` tables;
  - 25 `src/winevalue/` files, 13 `tests/` files and 4 deployment scripts.

  `manifest.json` records five entries, all 0.0.
- **Nothing written to the project:** there is no `band_status.json` and no `reports/pilot/`. All my outputs went to the scratchpad.
- **Freeze:** no `wine-phase6-rev5` tag exists, as stated. §6.1 "Freeze", the executive summary and the model card's version line describe the pending tag correctly.
- **Winery variants (round-4 issue 1)** on the dry-run stand-in (`phase6.lockbox_pilot_standin`, from `lockbox_split(prep)[1]`, 17,796 rows):
  - Wineries upper-cased, lower-cased, accent-stripped then upper-cased, or padded with extra spaces and punctuation all give an **identical** `evaluate_raw` gate, checks and withdrawn rows.
  - The winery-rule difference is 0.0 and coverage stays 0.7075.
  - All five name columns lower-cased also give an identical result.
- **Dry run reproduces:**
  - +5.25 pp (LB +1.21);
  - lift 1.808× (LB 1.434), with winery track record as the best rule;
  - coverage 70.75% (reported as 70.8%);
  - matched-winery gate on 283 wines: 1.59× (LB 1.35).
- **Name-key collisions (`match_key`):**
  - Among the 15,261 training wineries, 71 keys have two spellings. Every pair has the same country and province and is clearly one producer spelled two ways (Château Bel-Air / Bel Air, Daou / DAOU). The record spread within a key has median 0.19 and max 1.94 (DAOU). So no two distinct training wineries collide.
  - On the lockbox, 24 rows (13 in the ≤ $25 pool) are remapped, from 9 distinct given spellings. Two of them are **different producers in different countries**:
    - "Patria" (Italy, Sicily) → "Pátria" (Portugal, Vinho Verde);
    - "Ménage à Trois" (Italy, Veneto) → "Ménage a Trois" (US, California).

    See issue 2.
- **Comparator rule (`pilot.comparator_check`):**
  - **35% of matched wineries un-matched:** coverage 45.8%, so degraded. The matched gate runs on 183 wines (1.75×, passes) and the shortlist deploys.
  - **95% un-matched:** coverage 4.3%, fewer than 100 matched, so the matched gate is `None` and the decision is "deploy nothing". **But `gate.json` still says `BO1 passes: true` and `joint gate passes: true`, and the console prints "PASS".** (issue 3)
  - **Unit cases:** 150 matched → the matched gate runs; 90 matched → `BO1 holds` is False.
- **Lift against coverage** (60 draws of 400 from the lockbox ≤ $25 pool, matched wineries un-matched at random):

  | Coverage | Median lift | Matched-only lift | BO1 still deploys |
  |---|---|---|---|
  | 68% | 1.67 | 1.57 | 100% |
  | 58% | 1.72 | 1.53 | 100% |
  | 48% | 1.78 | 1.56 | 88% |
  | 38% | 1.82 | 1.57 | 83% |
  | 0% | 1.90 | – | 0% |

  The rule stops the gross case. Between 50% and 68% the lift is inflated by up to about 0.05 and nothing reacts. Even at natural coverage, the full-strength comparator gives about 0.1 less lift.
- **Coverage measure:** 68.1% of pool wines have a training winery, but only 44.4% have 5 or more training reviews. The mean shrinkage weight n/(n+20) among "seen" wineries is 0.30 (issue 4).
- **Serving path (round-4 issue 3):** `reproduces_lockbox` gives 0.0 on all five entries. It fails when it should:
  - `strip_leaks` disabled: 0.189 → not passed;
  - variety lower-cased after canonicalisation: 1.71 → not passed;
  - prices × 1.05 inside `prepare_new`: inf → not passed;
  - `config.PRICE_DEFLATOR = 0.77`: still 0.0, because the check forces 1.0 and restores the old value.

  **Truly raw** lockbox rows from `load_raw()` (no `vintage` column) through `vf.score` give estimate difference 0.0 and ranker 0.0, except one row: a hand-fixed $1,100 price that `prepare` sets to missing (not a ≤ $25 wine). The coded check starts from prepared columns that already include `vintage` (issue 7).
- **Price basis (round-4 issue 4):**
  - `score_round` at a deflator of 0.77 gives `price (2017 $)` / `price` = 0.77, a `price deflator` column of 0.77, and a report that records 0.77.
  - A $30 wine shows $23.10 and "Long shot".
  - Preparing twice still gives 23.1, so `prepare_new` is idempotent.
  - `pilot_eval.main`: matching 1.0 runs; 0.77 is refused; mixed 1.0/0.77 is refused; **no column at all runs silently** (issue 6).
- **Lower limits (round-4 issue 5):**
  - `choose_lower_limit_table` on `oof_ranker_values` reproduces `config.MONITOR_RANKER_LOWER` exactly. The unrounded minima are 0.0665/0.0146, 0.0701/0.0233, 0.0793/0.0333 and 0.0871/0.0388.
  - `ranker_alert_rates` reproduces `phase6_alert_rates_oof.csv` with max difference **0.0**.
  - `ranker_lower` picks the right row at 199/200/299/300/599/600/999/1,000. Below 200, neither the low nor the **high** side is read (issue 8).
  - CSVs match the report:
    - out-of-fold alerts at most 1.4%;
    - fresh seed at most 2.4% (fold 1, size 300);
    - leave-one-fold-out 0–0.2%;
    - detection: 25 words 0.5%, 30 words 0%, 2% unknown words 9.5%, prices × 1.1 0%, × 1.3 94.5%;
    - pool values: share above P90 30 → 11 → 4.1%, P(90+) 0.32 → 0.19.

    All four leave-one-fold-out limit pairs equal the full-rule pair (0.07, 0.02).
  - **At A7's round size** (rounds of 2,440 candidates, about 1,000 ≤ $25): 25 words caught 1.5%, 2% unknown words 0.5%, 30 words 0%, × 1.1 0%. The conclusions hold, but the round size differs from what the report simulates (issue 1).
- **Intake (round-4 issue 6):**
  - "N/A", "none", "-", "?", "", NaN, "UNKNOWN", " n/a " and "Not known" merge into one "unknown" unit (65 wines), and the pilot stays interim. "n.a", "TBD" and "various" still count as named sources (7 wines each, all listed in `sources.csv`).
  - "WINE ENTHUSIAST", "Wine-Enthusiast", "Wine Enthusiast Magazine", "winemag" and "winemag.com" count as primary. "wine enthusiast mag." does not, but it is printed.
  - A file with no primary rows, or a blank scorer column, returns "nothing to judge".
  - Arrival window: in 800 wines with 20% from other scorers, the decision falls at 400 primary wines (max order 500), and the all-scorers sensitivity uses those 500. Correct.
- **`business_kpi` (round-4 issue 7):** correct with boolean columns. With CSV "yes"/"no" strings (or blanks), `.astype(bool)` treats every row as sampled and as "shortlist used" (issue 5).
- **Numbers:** these match the saved CSVs and notebook outputs, except the stale lines in issue 9:
  - report §6 (protocol, pause, dry-run, verdict, tier, timeline, A11, monitoring-reference, alert and detection tables);
  - the executive summary's deployment paragraph (0.03 s, every 100 scores up to 800, 97.5% / 16%, month 8, cost, nine re-executions);
  - the model card, monitoring plan §1–5, the README and slides 8–12.

## Task coverage
| CRISP-DM task / output | Present / Partial / Missing | Note |
|---|---|---|
| 6.1 Plan deployment → Deployment plan | **Present** | **Present:**<br>• artifact with exact reproduction, now including the serving path;<br>• one entry point canonicalising five name columns;<br>• comparator coverage rule;<br>• price basis with a 2017-dollar display and a refusal;<br>• protocol in code with intake guards;<br>• schedule, cap, fallback, cost, prerequisites, rollout and freeze.<br>**Defect:** what a "round" and its candidate file are is inconsistent (issue 1), which undermines the schedule or the price-basis safeguard. |
| 6.2 Plan monitoring and maintenance → Monitoring and maintenance plan | **Present** | **Present:**<br>• per-size lower limits from a reproduced rule, with fresh-seed and leave-one-fold-out checks;<br>• honest disclosure of what is missed;<br>• unseen-winery indicator;<br>• KPI with a baseline and a with/without split;<br>• retraining policy.<br>**Gaps:**<br>• premise about round size (issue 1);<br>• no self-referenced rule for mild faults (issue 8);<br>• KPI type bug (issue 5). |
| 6.3 Produce final report → Final report | **Present** | §6 traces to cells and CSVs, and the numbers verify. A few stale or overstated lines (issues 2 and 9). |
| 6.3 Produce final report → Final presentation | **Partial** | A 12-slide outline with speaker notes and a screenshot. Slides 8–12 are accurate and current. The rendered deck is a declared later deliverable; judged on content, the outline is sound. |
| 6.4 Review project → Experience documentation | **Present** | Specific and self-critical, with a "next time" for each lesson. The name-normalisation lesson now matches the code. |

## Round-4 issues
| # | Round-4 issue | Status | Evidence |
|---|---|---|---|
| 1 | MAJOR: the BO1 comparator reads the winery as typed | **Resolved** (residuals in issues 2–4) | Upper case, lower case, accent and punctuation variants give an identical gate, checks, withdrawn rows and coverage on the dry run. The pool-wide assertion holds. The coverage rule, `gate.json` coverage and the matched-winery sensitivity work as described; the dry run reproduces 70.8% and 1.59× (LB 1.35). Residuals: two cross-country mappings, a crude coverage measure, and `gate.json` flags that ignore the rule. |
| 2 | Lexicon-only grapes case-sensitive | **Resolved** | Lexicon names and blend parts are matched. The notebook asserts identical estimates, ranks, rule scores and colours on all 7,288 pool wines for lower and upper case, and a test covers it. |
| 3 | Integrity check skips the serving path | **Resolved** | A fifth entry is required by `reproduction_passed`. It is 0.0, and it fails under three injected regressions I tried. It starts from prepared columns that include `vintage`, so title-based vintage parsing is not exercised (issue 7); a truly raw run gives 0.0 apart from one hand-fixed $1,100 price. |
| 4 | Deflated price invisible; refusal not enforced | **Resolved** | `price (2017 $)` appears in the app, in `score.py` and in the screenshot. `pilot_eval.py` refuses a mismatched or mixed deflator. Residual: a missing column is accepted silently (issue 6). |
| 5 | Out-of-fold 0% in-sample; round-size dependence | **Resolved** as specified | Per-size table reproduced; "low by construction" is stated; fresh-seed and leave-one-fold-out rates reproduce; the loss of sensitivity is disclosed (25 words: 0.5%). The premise that a round of 1,000 candidates holds 400–480 ≤ $25 wines contradicts A7 (issue 1). |
| 6 | Intake edge cases | **Resolved** | Placeholders merge into one unit; scorer aliases match; empty primary is guarded; arrival window matches. Residual: "n.a", "TBD", "various" and "wine enthusiast mag." (printed for the analyst). |
| 7 | KPI baseline has no data source | **Mostly resolved** | Step 0 now extracts the baseline, and `shortlist used` is recorded and split. Residuals: `astype(bool)` on string flags (issue 5), and the with/without split is confounded by buyer choice. |
| 8 | Stale or overstated text | **Resolved** | §5.3 now says 9–30%; reading 6.1 points to 6.1d; slide 11 qualifies unknown words; model card updated; §6.4 and slide 12 match the code. New stale lines are in issue 9. |
| 9 | Presentation still an outline | **Not resolved (deferred, declared)** | Still an outline; the deck is to come with the video. Acceptable as stated; content verified. |

## Issues raised
| # | Severity | Issue | Suggested fix |
|---|---|---|---|
| 1 | MAJOR | **"Buying round" and "candidate file" are defined inconsistently, and each reading breaks something.**<br>• **A7 and A9 (§1.2, §6.1, `config.PILOT_ROUND_CANDIDATES`):** about 1,000 **≤ $25** candidates per round. This drives the timeline (100 scored wines a month, decision at month 8).<br>• **Revision 5's reason for per-size limits (§6.2 note, monitoring plan):** "a real round of 1,000 candidates holds about 400–480 ≤ $25 wines … so it uses the 300–599 row". The false-alert and detection simulations use rounds of 1,000 candidates of any price (about 410 ≤ $25).<br>• **If rounds really hold about 450 ≤ $25 wines:** `pilot_timeline(per_round=450)` reaches 138 by month 6 and **382 by month 12**, so there is no decision within the cap in the base case, and "month 8" is wrong.<br>• **If A7 holds:** the revision-5 rationale and the simulated round size are wrong. The 1,000+ row (0.08 / 3%) applies; at that size 2% unknown words is caught in 0.5% of rounds, not 9.5%.<br>• **Rollout step 2 and README step 1 say "score every ≤ $25 candidate".** If the file is pre-filtered at a nominal $25:<br>&nbsp;&nbsp;– the deflator cannot restore wines priced $25–32.47 nominal (≤ $25 in 2017 dollars at 0.77);<br>&nbsp;&nbsp;– the pilot population is then ≤ $19.25 in 2017 dollars, not the pre-registered one;<br>&nbsp;&nbsp;– the ≤ $25-share alert, which §6.1 cites as catching inflation ("prices × 1.3 already sets off the ≤ $25-share alert"), reads about 100% and can never fire. | • State one definition: the candidate file is **every** candidate in the round, all prices; the ≤ $25 test is applied only after the deflator. Change the rollout and README wording to match.<br>• Restate A7 consistently: either about 1,000 ≤ $25 per round (then drop the "400–480" premise, re-run detection and false alerts at about 2,400 candidates, and quote the 1,000+ row), or about 1,000 candidates of any price (then recompute `pilot_timeline` and the fallback factor, and admit the cap problem).<br>• Add a per-round check that the file contains wines above the nominal $25 × (1/deflator) line; if none, the file was pre-filtered, so flag it. |
| 2 | MINOR | **The winery key can map a retailer's winery onto a different producer, and the report says it cannot.**<br>• `match_key` ignores country. Of the 9 lockbox spellings it remaps, 2 cross countries: "Patria" (Italy) → "Pátria" (Portugal, Vinho Verde), and "Ménage à Trois" (Italy) → "Ménage a Trois" (US).<br>• §6.1 says these are wineries "WineEnthusiast's own data spells two ways", and that matching "can only make the gate stricter". Neither holds: a wrong record can weaken or strengthen the comparator, and a cross-country match counts as "seen" for coverage.<br>• Within training the key is safe (71 collisions, all the same producer). | • Map a non-exact spelling only to a training spelling **in the same country** (build `by key` on (key, country)), else leave it unmatched.<br>• Reword §6.1 and reading 6.1 ("24 rows, of which 2 producers in another country are no longer matched").<br>• Add a test with "Patria"/Italy. |
| 3 | MINOR | **`gate.json` and the console contradict the decision when the comparator is degraded.**<br>• `evaluate_raw` copies `run_protocol`'s raw `BO1 passes` and `joint gate passes`, which ignore `comparator_check`.<br>• With coverage at 4.3% the file says BO1 PASS and joint PASS, while the decision is "deploy nothing".<br>• When there are fewer than 100 matched wines, the console says "must also pass on matched wines" but not that it could not be checked. | • Add `BO1 passes (after comparator rule)` and use it for `joint gate passes`, or rename the raw flag.<br>• Print "too few matched-winery wines (n < 100): shortlist not deployed".<br>• Test the degraded path end to end through `evaluate_raw`. |
| 4 | MINOR | **The coverage measure and its 50% threshold are weakly grounded.**<br>• "Seen" counts a winery with one training review. Its record is shrunk about 95% toward the global mean (shrink = 20), so it adds almost nothing to the comparator. On the lockbox pool, 68% are seen but 44% have ≥ 5 reviews; the mean weight among seen wineries is 0.30.<br>• The 50% threshold is a judgement call. My sweep shows the lift inflating by about 0.05 between 68% and 58% coverage with no reaction.<br>• The matched-only lift is about 0.1 below the pooled lift even at natural coverage. | • Define coverage as the share with ≥ 5 training reviews, or as the mean n/(n+20). Set the threshold from a stated rule (e.g. the coverage at which simulated lift inflation exceeds 0.1).<br>• Report the coverage-vs-lift sweep in §6.1.<br>• Show the matched-winery lift next to the primary lift in the decision memo, not only in `sensitivity.json`. |
| 5 | MINOR | **`business_kpi` misreads string flags.**<br>• `sampled` and `shortlist used` are cast with `.astype(bool)`. In a CSV with "yes"/"no" (which `pilot._as_bool` accepts for `sampled`) or blanks, every row counts as sampled and as shortlist-used. The "without" group comes out empty and the KPI is wrong, with no warning.<br>• The with/without split compares rounds where buyers chose whether to use the tool, so it is confounded. | • Use `pilot._as_bool` in `business_kpi`, reject unparseable values, and add a test with string flags.<br>• Call the split descriptive in the monitoring plan, not evidence of effect. |
| 6 | MINOR | **The deflator refusal is skipped when the column is missing, and the script path is untested.**<br>• A pilot file without `price deflator` is evaluated with no warning, even though rollout step 2 relies on the column being kept.<br>• No test calls `pilot_eval.main` for the refusal. | • Require the column (refuse, or force a `--deflator-confirmed` flag).<br>• Add a test that runs `pilot_eval.main` on match, mismatch, mixed and absent. |
| 7 | MINOR | **The serving-path entry does not start from raw rows.**<br>• It feeds `prepare` output columns, which are already normalised, missing values filled with "Unknown", and with `vintage` supplied. So vintage parsing from the title (with winery stripping) and `_norm` on raw strings are never checked.<br>• On true `load_raw()` rows the path is exact, apart from the one hand-fixed $1,100 price (`IMPLAUSIBLE_PRICE_TITLES`). | • Run the fifth entry on `load_raw().loc[saved.index]` without `vintage`, and compare the ranker on rows `prepare` priced.<br>• Note the hand-fixed-price exception. |
| 8 | MINOR | **The lower ranker alerts are honest but blind to mild faults, and small rounds lose the upper alerts too.**<br>• Limits set at fold 1's level (about 6% above P90) cannot see a lockbox-level feed (30%) dropping to 4–11% (25- or 30-word truncation: 0–1.5% caught). Disclosed, but not mitigated.<br>• `alerts` skips both sides when there are fewer than 200 ≤ $25 candidates, so a small round with boilerplate (P(90+) 0.76) raises no ranker alert.<br>• No unit test covers `ranker_lower`'s row choice or the under-200 skip. | • Pre-register a self-referenced rule now: from round 4 on, alert if the share above the P90 falls below half its trailing 3-round median. That catches the 30 → 4–11% drops.<br>• Keep reading the upper limit below 200.<br>• Add tests for 199/200/300/600/1,000 and the skip. |
| 9 | MINOR | **Stale or inexact text after revision 5.**<br>• Reading 6.1: "refuse … unless the manifest records that reproduction for all **four** outputs" (now five); "13 lockbox ≤ $25 **wineries**" (13 rows).<br>• Reading 6.2 (cell 143), first bullet: "their lower limits (0.08, 3%)" (the 1,000+ row, not the typical one).<br>• Model card: "a country or winery … is flagged and counted" (wineries are counted, not flagged per row); "winery (only for the winery track record rule … and clustering)" omits that winery also strips the title for colour and vintage.<br>• §6.1 "Freeze" lists `src/winevalue/`, `config` and the artifact, but not `deployment/*.py`, which now holds protocol logic (the deflator refusal).<br>• Intake leftovers: "n.a", "TBD", "various", "wine enthusiast mag.". | Correct each line. Add `deployment/` to the freeze list. Extend `UNSOURCED` and the aliases, or keep relying on the printed lists and say so. |
| 10 | MINOR | **Presentation is an outline** (declared deferral). | Render it with the walkthrough video, as planned. Use the screenshot, the protocol table and the detection table as visuals. |

## Most important improvement
Fix issue 1. Define the buying round and the candidate file once, and make every part of the plan use that definition.
- **The candidate file:** every candidate of the round at all prices, scored before the ≤ $25 test, which is applied after the deflator.
- **A7:** restate it in one unit.
- **Then re-derive** the timeline and fallback factor, or the monitoring round size, detection and false-alert rates, whichever the definition requires.
- **Add a per-round check** that flags a nominally pre-filtered file.

Today the schedule ("decision by month 8") and the monitoring premise ("a round of 1,000 holds 400–480 ≤ $25") cannot both be true. As written, the rollout instruction would also quietly disable both the deflator and the alert meant to catch a wrong one.

Fold in the same-country restriction on the winery key (issue 2) and a `gate.json` that reflects the comparator rule (issue 3). The phase is then ready to commit and tag as `wine-phase6-rev5`.

## Changes made (revision 6, 2026-11-09; re-execution 12)
| # | Change | Where |
|---|---|---|
| 1 | **One definition of a buying round.** A7 is kept: about 1,000 **≤ $25** candidates per round, so the schedule ("decision by month 8") stands. The candidate file is every candidate of the round at any price; the ≤ $25 test comes after the 2017-dollar deflator (report §6.1, README, rollout step 2, `score.py` docstring). Every monitoring simulation now draws rounds of that size (`monitoring.round_size`: about 2,067 development or 2,442 lockbox candidates), so an A7 round uses the 1,000+ row of the lower-limit table (0.08 / 3%). The revision-5 "400–480" premise is withdrawn. A ≤ $25 share above 95% raises an alert (a file pre-filtered at $25: caught in 100% of rounds). False alerts in 500 A7 rounds: none, on development or lockbox rows | `src/winevalue/monitoring.py`, `config.py`, notebook 6.2a, report §6.1–6.2, `deployment/monitoring_plan.md`, README, slide 11 |
| 2 | Accent and punctuation variants of a winery are matched only within its country (`production._winery_key`; "Patria", Italy, stays unmatched). A variant in letter case only is matched first, in any country, to the one training spelling it equals case-insensitively, so it scores as its exact spelling would: the frozen winery rule reads names alone (found when re-execution 10 stopped on the variant assertion). 21 lockbox rows (11 in the pool) remain matched, all Italian wineries spelled two ways; §6.1 reworded. Tests with "Patria"/Italy and "NEUMEISTER"/Unknown | `src/winevalue/production.py`, tests, report §6.1, reading 6.1, README, model card |
| 3 | `gate.json` gains `BO1 passes (after comparator rule)`, and `joint gate passes` uses it; `pilot_eval.py` prints it and says when too few matched-winery wines exist to check. Test of the degraded path through `evaluate_raw` | `src/winevalue/pilot.py`, `deployment/pilot_eval.py`, tests |
| 4 | Coverage measure kept, with its coarseness disclosed in §6.1 (68% seen but 44% with ≥ 5 reviews; the critic's sweep quoted); the 50% threshold is called a judgement call; `pilot_eval.py` prints the matched-winery lift next to the primary lift | report §6.1, `deployment/pilot_eval.py` |
| 5 | `business_kpi` parses yes/no flags strictly (`monitoring._flag`) and refuses anything else; the with/without-shortlist split is called descriptive. Test | `src/winevalue/monitoring.py`, monitoring plan §3, tests |
| 6 | `pilot_eval.py` refuses a pilot file without a `price deflator` column unless `--deflator-confirmed` is passed; tests run `pilot_eval.main` on match, mismatch, mixed and absent | `deployment/pilot_eval.py`, README, tests |
| 7 | The serving-path entry starts from `data.load_raw()` rows (no `vintage` supplied, deflator 1.0); 0.0 on all four outputs | `src/winevalue/production.py`, notebook 6.1b, tests |
| 8 | Self-referenced rule pre-registered: alert when the share above the development P90 falls below half its median over the previous 3 rounds, read from 600 ≤ $25 candidates (the smallest size at which it fires in at most 2% of consecutive out-of-fold rounds in every fold; `monitoring.choose_relative_min_pool`, asserted in 6.2a). It catches notes cut to 30 or 25 words in 100% of A7 rounds (fixed limits: 0% and 3.5%). Upper ranker limits are read at every round size. Tests for 199/200/300/600/1,000 and the skip; `score.py --history` reads earlier rounds | `src/winevalue/monitoring.py`, `config.py`, `deployment/score.py`, report §6.2, monitoring plan, tests |
| 9 | Reading 6.1 (five reproduction entries; 21 rows / 11 in the pool), reading 6.2 (A7 row), model card (wineries counted, not flagged; winery also strips the title), §6.1 Freeze now lists `deployment/*.py`; `UNSOURCED` and the scorer aliases extended ("n.a", "TBD", "various", "Wine Enthusiast Mag") | notebook, model card, report §6.1, `src/winevalue/pilot.py`, `config.py` |
| 10 | Not done: the presentation stays a 12-slide outline (declared deferral; rendered with the walkthrough video) | – |
| – | Found while re-running: re-execution 11 failed BSC4's timing (30% of queries ≈ 4.3 s) because the new case lookup was rebuilt per query. Cached once per artifact; median 0.028 s, maximum 0.065 s; test added. Re-execution 12 carries the fix | `src/winevalue/production.py`, tests, run log |
