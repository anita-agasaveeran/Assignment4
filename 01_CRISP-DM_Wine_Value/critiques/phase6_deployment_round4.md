# Phase 6 · Deployment: Critic Round 4
- **Date:** 2026-11-09
- **Reviewer:** Claude critic (independent subagent session), persona from `critic_prompt.md`. Read-only.
- **Draft reviewed:** Phase 6 revision 4 (report §6, notebook §6 after re-execution 8, deployment/ files)

## Score: 8 / 10 · Major issues remaining: yes

Revision 4 fixes all ten round-3 issues. I confirmed each one by running the code, not only by reading the text.
- **Model inputs:** country, province and in-training grape spellings now reach the models as the training spelling.
- **Sources and scorers:** a missing source never counts toward the minimum, and only WineEnthusiast scores enter the gate.
- **Price deflator:** applied exactly once and recorded.
- **Alert limits and A11:** both reproduce from their stated rules to the last digit.
- **Run log:** every SHA-1 in the re-execution 8 block matches the file on disk.
- **Freeze:** the pending tag is handled correctly.

Round 3's lesson was "normalise at the single entry point, before anything reads the value", and revision 4 adopts it in the report and on slide 12. But one column is still read raw, and it is the column that matters most for the decision:
- **The winery name feeds the shortlist gate's strongest comparator ("winery track record") as typed.** Upper-casing the wineries in the dry-run file:
  - drops that rule's predictions by up to 1.9 points;
  - switches the gate's best simple rule to price;
  - raises the shortlist lift from 1.81× (LB 1.43) to 1.96× (LB 1.59).
- **Across 150 draws of 400 wines from the lockbox's ≤ $25 pool:**
  - the median lift rises from 1.77 to 1.92;
  - the winery rule stops being the best comparator (57% of draws → 1%).

So the deployment decision gets more lenient when the retailer's spelling differs from WineEnthusiast's, and no flag or indicator shows it. A smaller gap of the same kind affects grape names that only the grape lexicon knows ("Turbiana").

## Summary
- **Deployment plan:** now complete in substance:
  - frozen artifact;
  - one entry point;
  - price basis;
  - outcome data, schedule, cap and fallback;
  - protocol in code, simulated;
  - prerequisites and rollout.
- **Monitoring plan:** now has:
  - limits set by a pre-stated out-of-fold rule;
  - detection rates for broken feeds;
  - an unseen-country indicator;
  - a business KPI.
- **Numbers:** every number I checked in §6, the executive summary, the model card, the monitoring plan, the README and slides 8–12 matches the saved CSVs and notebook outputs, apart from a few stale lines (issue 8).
- **What stops a 9:** issue 1, which affects the primary pre-registered gate.

## What I verified, and how
- **Tests:** `pytest`: **87 passed** in 39 s, including `test_app.py`.
- **SHA-1s:** all 59 entries in the "Phase 6 files after re-execution 8" block match `shasum`:
  - the artifact `ce7f0d1…` and the screenshot;
  - 18 tables;
  - all 25 `src/winevalue/` files and all 13 `tests/` files;
  - the 4 deployment scripts.
  The blocks are now in chronological order (re-executions 2, 4, 5, 6, 8). The manifest records 0.0 for all four outputs.
- **Nothing written to the project:** `models/` and `deployment/` timestamps are unchanged, and there is no `band_status.json` or `reports/pilot/`.
- **Canonicalisation is a no-op on real data (P1):**
  - `vf.prepare` on the raw columns of all **118,378** prepared rows (with and without `vintage`) gives exactly `prepare.prepare`'s model inputs: 0 mismatches in every QUALITY_INPUTS_V2 column, price and pool.
  - `canonical_inputs` remaps 0 values in each of the four columns.
  - **Through the serving path** (raw → `vf.prepare` → score), the lockbox reproduces `phase5_lockbox_predictions.csv.gz` with max difference **0.0** for ridge, estimate, ranker (priced rows) and P(90+).
  - The training spellings have no two spellings sharing a name key (41 countries, 402 provinces, 643 varieties, 1,165 regions). Every alias target is a training country.
  - No lockbox value outside the training spellings gets mapped by key. So I found no case where the mapping sends a distinct name to a wrong training spelling.
- **Variants through `vf.score` (all 7,288 lockbox ≤ $25 rows):**
  - Extra or doubled whitespace, curly apostrophes and "United States of America": **identical** estimates and ranks.
  - Lower or upper case on country, province or region alone: identical.
  - Lower or upper case on **variety**: **87 rows change**, up to 0.37 points in the estimate and 0.24 in the rank, with 12 verdict changes (issue 2).
- **Variants through `evaluate_raw`:**
  - With every name column upper-cased with padding and "US" written "u.s.a.", the dry-run stand-in gives an identical gate, checks and withdrawn rows.
  - The dry run itself reproduces: +5.25 pp (LB +1.21), 1.81× (LB 1.43), 52.25% hidden, 209 rows.
- **Unseen country:** 30 "Atlantis" rows in the stand-in are flagged 30 times. The indicator reads 0.075 and the alert fires.
- **Unsourced rows:** I replaced the third source with NaN, "", "  ", "unknown", "Unknown" and "UNKNOWN" in turn. Each time there are 2 sources with enough wines, the result is "interim", and 86 unsourced wines are reported. "N/A", "none" and "-" do count as sources (issue 6).
- **Scorer:** a stand-in with 20% "Wine Spectator" rows:
  - gate on 320 wines (interim, as it should be);
  - all-scorers sensitivity on 400;
  - unsampled sensitivity on 200;
  - `per_scorer` produced.
  "Wine Enthusiast", "wine-enthusiast" and "WINE ENTHUSIAST" match. "Wine Enthusiast Magazine" and "winemag" don't. A scorer column with no primary rows crashes `evaluate_raw` (issue 6).
- **Deflator** (monkeypatched to 0.77, then reset):
  - Prepared price ÷ price as given is 0.77, so it is applied once.
  - `score_round` leaves the output's price column as given, and the monitoring report records 0.77.
  - A pilot at nominal prices (2017 ÷ 0.77) with deflator 0.77 gives a gate identical to the dry run, and the gate file records 0.77.
  - No path calls `prepare` twice. Doing so would compound the factor (0.593), so the function is not idempotent; noted, not exploited.
  - `reproduces_lockbox` does not go through `prepare_new` at all (issue 3).
- **Lower alert limits:**
  - `oof_ranker_values` → `ranker_rounds` → `choose_lower_limits` gives **0.08 and 0.03**, equal to `config`.
  - `ranker_alert_rates` plus the quantiles reproduce `phase6_alert_rates_oof.csv` with max difference **0.0**.
  - Revision 3's limits on the same rounds fire in 30.0% of fold-1 rounds and 9.2% of fold-3 rounds, as the report says.
  - 25-word truncation is caught in 9.5% of rounds with the new limits and 86% with revision 3's, as stated.
  - **Extra checks** (issue 5):
    - a fresh seed of rounds: 0% alerts;
    - leaving fold 1 out of the rule: limits 0.09 / 4%, and fold 1 then alerts in 4.6% of its rounds;
    - rounds of 300 candidates: 9% (fold 1) and 3.8% (fold 3).
- **A11:**
  - `source_minimum_probability` reproduces `phase6_source_minimum.csv` with max difference 0.0, and `choose_source_share` gives 0.15.
  - A 200,000-draw Monte Carlo gives 0.107 at 12.5% and 0.803 at 15%.
  - `pilot_timeline()` reproduces its CSV.
- **Numbers checked against CSVs and outputs:**
  - **Protocol:** the protocol table (10 × 10), pause rates at 200 wines (2.9%, 2.0–4.1%; LB trigger 9.4–25.2% / 12.0–30.0%; null ranker 97–100%; Jenssen 10%) and unit truth (France +1.86 / −4.9; South Africa +1.79 / −5.8; DeSimone −1.45 / −2.7; Gregutt −1.43 / +7.8; masked fold 4: Buzzeo +1.73).
  - **Tool:** the verdict and tier tables, BSC4 timing (median 0.028 s), the monitoring reference (all 8 indicators, both columns), and all 12 rows of the detection table.
  - **Elsewhere:** the executive summary (97.5%, 16%, month 8, cost, eight re-executions), the model card, monitoring plan §1–5, the README, and slides 8–12.
- **Freeze wording:** §6.1 says "not yet committed … to be committed and tagged `wine-phase6-rev4` before any pilot data". The deflator commit at step 0 is named as the only later change, and the model card's version line names the tag. That is correct handling of a pending tag.

## Task coverage
| CRISP-DM task / output | Present / Partial / Missing | Note |
|---|---|---|
| 6.1 Plan deployment → Deployment plan | **Present** | **Present:**<br>• artifact with exact reproduction (verified through the serving path too) and a strict loader;<br>• one entry point with input canonicalisation;<br>• price-basis prerequisite with a named index;<br>• protocol in code with primary-scorer and sampling sensitivities;<br>• A8–A11 with a rule-based A11 floor;<br>• schedule, cap, fallback, cost, prerequisites, rollout, "does not do" list.<br>**Defects:**<br>• winery is not canonicalised and drives the BO1 comparator (issue 1);<br>• lexicon-only grape names are case-sensitive (issue 2);<br>• the integrity check doesn't exercise the serving path (issue 3). |
| 6.2 Plan monitoring and maintenance → Monitoring and maintenance plan | **Present** | **Present:**<br>• leading checks with references, false-alert and detection rates;<br>• lower limits from a stated out-of-fold rule (reproduced);<br>• unseen-country indicator;<br>• lagging checks equal to the frozen protocol;<br>• business KPI; retraining policy; ownership.<br>**Gaps:**<br>• no indicator for winery-match coverage (issue 1);<br>• limits are valid for rounds of about 1,000 candidates only (issue 5);<br>• the KPI baseline data are not required to be collected (issue 7). |
| 6.3 Produce final report → Final report | **Present** | §6 traces to cells and CSVs, and the numbers verify. A few stale lines (issue 8). |
| 6.3 Produce final report → Final presentation | **Partial** | Still a 12-slide outline with speaker notes, honestly labelled; the screenshot exists. Numbers on slides 8–12 verify. No rendered deck (issue 9). |
| 6.4 Review project → Experience documentation | **Present** | Specific, self-critical, with a "next time" for each lesson. The canonicalisation lesson ("before anything reads the value") is stated more strongly than the code delivers, until issue 1 is fixed. |

## Round-3 issues
| # | Round-3 issue | Status | Evidence |
|---|---|---|---|
| 1a | Country variants scored as unseen; no flag | **Resolved** for the four named columns | `canonical_inputs` maps country, province, variety and region by name key plus aliases. It is a no-op on all 118,378 rows, and the serving path reproduces the lockbox at 0.0. Case, whitespace and alias variants give identical scores and an identical gate (verified). The unseen-country flag, indicator and alert work (30/30 flagged; alert fires). **Gaps in neighbouring inputs:** winery (issue 1) and lexicon-only grapes (issue 2). |
| 1b | A missing source counts as a source | **Resolved** | NaN, "", whitespace and any-case "unknown" never count; a two-writer pilot stays interim; `pilot_eval.py` warns with a count; the README makes `source` required. Placeholders like "N/A" still count (issue 6). |
| 2 | Price basis undecided | **Resolved** | `PRICE_DEFLATOR` with a named CPI-U series and base, set at step 0 in a dated commit, checked at step 1. It is applied once in `prepare_new` and recorded in the monitoring report and `gate.json` (verified at 0.77). Not in the manifest; the outputs don't show the 2017-dollar price (issue 4). |
| 3 | Lower limits untested out of fold; wrong stated basis | **Resolved** | The rule is coded and asserted. 0.08 / 3% and `phase6_alert_rates_oof.csv` reproduce exactly. Revision 3's 30% / 9.2% reproduce. The trade-off (86% → 9.5%) is verified and disclosed, and slide 11 and the `config` comment are fixed. Residual: the 0% is measured on the rounds that set the limit, and round size matters (issue 5). |
| 4 | A11 floor doesn't deliver month 8 | **Resolved** | Floor 15% by a stated rule. The exact multinomial reproduces (0.107 / 0.803 / 0.992) and Monte Carlo agrees. The report states the 4-in-5 and month-9 consequence, and the re-check on the first 100 scored wines is in rollout step 2. |
| 5 | Scores from different critics pooled | **Resolved** | Only `PILOT_PRIMARY_SCORER` rows enter the gate. Other scorers get a gate and a per-scorer residual as sensitivities (verified). Edge cases are in issue 6. |
| 6 | Unsampled-wine sensitivity only in prose | **Resolved** | `sampled` column, gate on unsampled wines up to the decision point, `sensitivity.json`, test; verified (200 of 400 unsampled). |
| 7 | Stale text | **Mostly resolved** | Executive summary says "eight"; "0.97–1.9×"; app timing "about 0.05 s"; reading 6.1 aligned. New stale lines are in issue 8. |
| 8 | Screenshot provenance and cropping | **Resolved** | Retaken at 00:44 with artifact `ce7f0d1…`, SHA-1 in the run log; all similar-wines columns visible; band caveat directly under the metrics. |
| 9 | Run-log hashes incomplete and out of order | **Resolved** | All 38 src and test files plus the scripts are hashed, all 59 match, and the blocks are chronological. |
| 10 | No business KPI | **Resolved** (in code and plan) | `monitoring.business_kpi`, test, quarterly owner and trigger. Baseline data collection is not a prerequisite (issue 7). |

## Issues raised
| # | Severity | Issue | Suggested fix |
|---|---|---|---|
| 1 | MAJOR | **The shortlist gate's strongest comparator reads the winery as typed, so the deployment decision depends on spelling.**<br>• The BO1 gate compares the ranker with the best frozen simple rule. "Winery track record" (`GroupMeanBaseline(keys=("winery",))`) looks up the exact WineEnthusiast spelling; an unmatched winery gets the global mean. `canonical_inputs` does not cover `winery`, only `winery_key` is case-folded, and that is used only for bootstrap clusters.<br>• **Dry run, wineries upper-cased:** the winery rule moves by up to 1.9 points, the best rule switches to price, and the lift goes from 1.81× (LB 1.43) to **1.96× (LB 1.59)**.<br>• **150 draws of 400 from the lockbox ≤ $25 pool:** median lift 1.77 → **1.92**; the winery rule is the best comparator in 57% of draws → 1%; BO1 pass 98.7% → 100%.<br>• A retailer's winery strings will often differ from WineEnthusiast's in case, accents and suffixes. Even with exact spellings, only 68% of lockbox ≤ $25 wines have a winery seen in training. So the pilot's comparator is weaker than the simulated and pre-registered one, the gate is more lenient, and nothing shows it.<br>• This contradicts "One way into the models", the §6.4 lesson and slide 12. | • Add `winery` to `CANONICAL_COLUMNS`: an exact spelling is untouched, so Phase 5 is unchanged. Consider a stronger winery key (accents folded; "Winery", "Estate", "Château"/"Ch." normalised) that maps only to a unique training spelling.<br>• Report the comparator's coverage in `gate.json` (share of pilot wines whose winery is in the training table) and as a per-round indicator. Pre-register a minimum (e.g. ≥ 50%, near the lockbox's 68%) below which the BO1 result is reported as "comparator degraded".<br>• Add a sensitivity: the gate on matched-winery wines only.<br>• Add a test: a case-variant winery file gives an identical gate. |
| 2 | MINOR | **Grape names known only to the grape lexicon are still case-sensitive.**<br>• `canonical_inputs` maps only to training spellings. A variety that is not in training but is known to `grape_canonical`/`wine_colour` (lockbox: "Turbiana" → Verdicchio, 86 rows; "Pinot Gris-Gewürztraminer") loses its mapping when typed in another case: the grape becomes unseen and the colour "unmapped".<br>• Lower-casing the variety on the lockbox ≤ $25 pool changes 87 estimates (up to 0.37 points), ranks by up to 0.24, and 12 verdicts.<br>• §6.1's "a round with lower-case … names gives identical scores" therefore holds only for training spellings. The notebook's 400-row variant check happened not to include such a grape. | • Make `grape_canonical` and `wine_colour` match case-insensitively, or have `canonical_inputs` fall back to the lexicon's spellings by name key.<br>• Add a pool-wide variant assertion: all four columns lower- and upper-cased on the full lockbox ≤ $25 pool, max difference 0.<br>• Qualify the claim until then. |
| 3 | MINOR | **The integrity check never exercises the serving path.**<br>• `reproduces_lockbox` scores `prepare.prepare` rows directly. `prepare_new`, `canonical_inputs` and the deflator are not part of the check that gates serving.<br>• I confirmed the serving path reproduces the lockbox at 0.0, but no code asserts it. After step 0 (deflator ≠ 1) nothing would catch a regression in `prepare_new`. | • Add a second reproduction through `vf.score(raw lockbox columns)` with the deflator forced to 1.0, and require it in `reproduction_passed`.<br>• Record the deflator in the manifest. |
| 4 | MINOR | **The deflated price is invisible to users and to the pilot file.**<br>• The ≤ $25 pool and the verdict ("Above $25: not a value candidate") use the 2017-dollar price. The app's one-wine view and `score.py`'s output show only the price as given, so a buyer who entered $30 can see "Probable value".<br>• `pilot_eval.py` re-scores with whatever `config.PRICE_DEFLATOR` holds when it runs. The monitoring plan's "a report with a different deflator is not used" is not enforced. | • Show and write "price (2017 $)".<br>• Have `pilot_eval.py` refuse to run if the deflator differs from the one recorded in the round monitoring reports (or in the tag's commit). |
| 5 | MINOR | **The out-of-fold "0 false alerts" is in-sample to the rule that set the limits, and it depends on round size.**<br>• The limits are the 1st percentile of the same 500 rounds per fold, rounded down, so near-zero alerts there are guaranteed by construction.<br>• Independent checks: a fresh seed gives 0% (good). Leaving fold 1 out of the rule gives 0.09 / 4%, and fold 1 then alerts in 4.6% of rounds. Rounds of 300 candidates alert in 9% (fold 1) and 3.8% (fold 3) of rounds. | • Say the 0% is by construction, and report the fresh-seed and leave-one-fold-out rates.<br>• State that the limits hold for rounds of about 1,000 ≤ $25 candidates, and either scale them by round size (binomial or clustered SE) or skip the two ranker alerts below about 500 candidates. |
| 6 | MINOR | **Intake edge cases.**<br>• "N/A", "none" and "-" count as named sources.<br>• NaN and "" sources become two separate stop-rule units ("unknown" and "").<br>• A `scorer` column with no primary rows crashes `evaluate_raw` (`ValueError` in `_codes`) instead of reporting "no primary-scorer wines".<br>• "Wine Enthusiast Magazine" and "winemag" are treated as other scorers (visible only in `per_scorer.csv`).<br>• The all-scorers sensitivity uses every wine received, not the same arrival window as the primary gate. | • Extend `UNSOURCED` with common placeholders, or have `pilot_eval.py` list sources for the analyst to confirm.<br>• Merge NaN and "" into one unit.<br>• Guard an empty primary set.<br>• Add publisher aliases or print the distinct scorer spellings with a warning.<br>• Compute the all-scorers gate up to the same arrival point. |
| 7 | MINOR | **The business KPI's baseline has no data source.** The KPI compares sampled-and-reviewed wines with "the rounds before the tool, from the same review feed". Nothing in the prerequisites or step 2 requires the pre-tool sampling records to be collected and matched. Buyers may also use the shortlist during the pilot, so the KPI mixes tool and no-tool rounds. | • Add to step 0: extract the last N rounds' sampled wines and match them to reviews with the same rule (that is the baseline).<br>• Record per round whether the shortlist was used. |
| 8 | MINOR | **Stale or overstated text.**<br>• §5.3 condition 7's note says the LB trigger "would stop working shortlists in 9–33% of pilots"; §6.1, reading 6.1 and the CSV give 9–30%.<br>• Reading 6.1 says the variant dry-run "assertion in 6.1c"; it is in 6.1d.<br>• Slide 11 lists "unknown words" as caught without saying that 2% unknown words is caught only 9.5% of the time.<br>• Model card: the "Price and time" limitation still says inflation moves wines across the bar without mentioning the deflator, and the Inputs section doesn't mention canonicalisation.<br>• §6.4 and slide 12's "normalise inputs once … before anything reads them" overstates the code (issue 1). | Correct each line; qualify the lesson until issue 1 is fixed. |
| 9 | MINOR | **The final presentation is still an outline.** CRISP-DM 6.3's output is a presentation. A 12-slide outline with speaker notes and one screenshot is honest, but not a deck. | Render the slides (or a slide artifact) from the outline before the video, with the screenshot, the protocol table and the detection table as visuals. |

## Most important improvement
Fix issue 1: canonicalise `winery` at the same entry point as the other names, and make the BO1 comparator's coverage visible:
- **Mapping:** map non-exact winery spellings to the training spelling by key. This is a no-op on training and lockbox rows.
- **Coverage in the gate:** report in `gate.json` the share of pilot wines whose winery matches the comparator's table, and pre-register what happens if it is low.
- **Matched-winery sensitivity:** gate only on wines whose winery is in the training table.
- **Test:** prove on the dry-run file that a case-variant winery gives an identical gate.

The shortlist gate is the decision that deploys the product. Right now, how the retailer types a producer's name can lift it from 1.77× to 1.92× with no flag. Fix that, and fold in the lexicon-grape case gap (issue 2) and a serving-path reproduction check (issue 3), and the phase is ready to commit and tag as `wine-phase6-rev4`.

## Changes made (revision 5, 2026-11-09; re-execution 9)
| # | Change | Where |
|---|---|---|
| 1 | `winery` added to `production.CANONICAL_COLUMNS`, matched by a stronger key (`production.match_key`: case, spaces, apostrophes, accents, punctuation) only when it is not an exact training spelling. No development row changes; 24 lockbox rows (13 in the ≤ $25 pool) have a winery WineEnthusiast's own data spells two ways and are now matched, which can only strengthen the comparator; the dry run is unchanged. **Comparator coverage rule**, set before any pilot data (`pilot.comparator_check`, `config.PILOT_MIN_WINERY_COVERAGE = 0.50`): if fewer than half the wines used at the decision point have a training winery, the shortlist part must also pass on those wines alone (≥ 100), else it is not deployed; `gate.json` reports the coverage and `sensitivity.json` the matched-winery gate. Dry run: coverage 70.8%, matched-winery lift 1.59× (LB 1.35). Per-round indicator "share of wineries unseen in training" (lockbox 27.4%, no alert). Tests and notebook 6.1d: upper-case wineries give an identical rule score, gate, checks and withdrawn wines | `src/winevalue/production.py`, `pilot.py`, `monitoring.py`, `config.py`, `deployment/pilot_eval.py`, tests, notebook 6.1d, report §6.1 and §6.4, monitoring plan §2–3, README, slides 8, 10, 12 |
| 2 | Grape-lexicon names and blend parts are matched for `variety` (training spellings take precedence), so a lexicon-only grape in any case keeps its canonical grape and colour. Notebook 6.1d asserts on the whole lockbox ≤ $25 pool (7,288 wines) that all five name columns lower- or upper-cased give identical estimates, ranks, rule scores and colours. Test | `src/winevalue/production.py`, notebook 6.1d, tests |
| 3 | `production.reproduces_lockbox` adds the serving path (raw columns → `vf.prepare` → score, deflator 1.0) as a fifth entry, required by `artifacts.reproduction_passed`; 0.0 on all four outputs | `src/winevalue/production.py`, `artifacts.py`, `models/manifest.json`, tests, report §6.1 |
| 4 | `ValueFinder.score` outputs `price (2017 $)`; the app shows it under the verdict; `score.py` writes it and a `price deflator` column; `pilot_eval.py` refuses a pilot file scored with a different deflator; `prepare_new` never deflates twice. Tests. (The deflator is not put in the manifest: it is set at step 0, after the artifact is frozen, and recorded in every round report and gate file instead) | `src/winevalue/production.py`, `deployment/app.py`, `score.py`, `pilot_eval.py`, README, model card |
| 5 | Lower limits of the two ranker alerts set by the same rule **per round size** (200 / 300 / 600 / 1,000 ≤ $25 candidates: 0.06 / 0.07 / 0.07 / 0.08 and 1% / 2% / 3% / 3%; `config.MONITOR_RANKER_LOWER`, asserted in notebook 6.2a); not read below 200. The report says the out-of-fold rate is low by construction and adds two checks the rule did not see: a fresh seed (at most 2.4%) and each fold left out of the rule (0–0.2%; `phase6_alert_limits_lofo.csv`). Detection is recomputed: notes cut to 25 words are now caught in 0.5% of rounds, stated | `src/winevalue/monitoring.py`, `config.py`, notebook 6.2a, report §6.2, monitoring plan §2, slide 11 |
| 6 | Placeholder sources ("N/A", "none", "-", "?", …) are merged with blank and "unknown" into one unsourced unit that never counts as a source; scorer aliases ("Wine Enthusiast Magazine", "winemag"); `pilot_eval.py` prints every scorer spelling; a file with no primary-scorer rows reports "nothing to judge"; the all-scorers sensitivity uses the primary gate's arrival window. Tests | `src/winevalue/pilot.py`, `config.py`, `deployment/pilot_eval.py`, README, report §6.1 |
| 7 | Business KPI baseline: at step 0 the analyst computes `monitoring.business_kpi` on the last 12 pre-tool rounds' sampling records, matched with the same rule; each round records `shortlist used`, and the KPI is reported for rounds with and without it. Test | `src/winevalue/monitoring.py`, report §6.1 (prerequisites, steps 0 and 2) and §6.2, monitoring plan §3, README |
| 8 | §5.3 note "9–30%"; reading 6.1 points to 6.1d; slide 11 qualifies unknown words (2% caught in 9.5% of rounds); model card's inputs and "Price and time" limitation mention the name matching and the deflator; the §6.4 lesson and slide 12 now match the code | report, notebook reading 6.1, slides, model card |
| 9 | Not done: the final presentation stays a 12-slide outline with speaker notes and the screenshot. The rendered deck is produced with the walkthrough video, a separate deliverable | – |
