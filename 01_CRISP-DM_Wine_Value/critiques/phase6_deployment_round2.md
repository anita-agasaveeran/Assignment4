# Phase 6 · Deployment: Critic Round 2
- **Date:** 2026-11-08
- **Reviewer:** Claude critic (independent subagent session), persona from `critic_prompt.md`. Read-only.
- **Draft reviewed:** Phase 6 revision 2 (report §6, notebook §6 after re-execution 5, deployment/ files)

## Score: 8 / 10 · Major issues remaining: yes

Revision 2 is a real revision. The five round-1 MAJOR issues were each addressed in code and tested, not just reworded:
- one `pilot.band_hidden` rule that handles the pooled unit and name variants;
- a loader that refuses rather than rebuilds;
- a per-round monitoring report written by `score.py`;
- round-relative shortlist tiers;
- an outcome-data plan with a schedule.

I re-ran the key paths myself, and the tool now hides the same wines the protocol hides. Every number I checked in §6 matches the saved outputs, with one stale exception (BSC4 timing).

What stops a 9:
- **One MAJOR defect, of the same kind as round-1 issue 2.** Names are normalised only where the band is hidden. The protocol builds its units and counts its note sources from raw strings. So one writer typed two ways counts as two sources toward the ≥ 3-source minimum, which is condition 2.
- **The new schedule doesn't add up internally.** The review lag, the 12-month cap and the source mix are not reconciled.
- **Stale text.** The pilot cost ($10,000) and BSC4 timing in the executive summary, model card, monitoring plan and slides are out of date.
- **Untested alerts.** The alerts have a false-alert rate but no detection check.

**What I verified, and how:**
- **Tests:** `pytest`: **78 passed** in 37.5 s, including `test_app.py` (not skipped; the prepared table exists).
- **Integrity of files:**
  - `shasum` of `models/value_finder.joblib` (d176a32…) and of all 12 `phase6_*` files matches the "after re-execution 5" block in the run log. `phase6_bsc4_timing.csv` is wall-clock and correctly excluded.
  - The 13 first-run Phase 5 tables and the 6 post-hoc files match their recorded SHA-1s.
  - `phase4_fold_predictions.csv.gz` is identical to HEAD (`git diff --quiet`).
  - The project's model files still carry their 18:48:34 timestamps from re-execution 5, after all my checks.
- **Loader (temporary copies in my scratch dir, paths monkeypatched).**
  - Refused, as claimed:
    - missing manifest;
    - reproduction `null` or `{}`;
    - one difference of 1e-3;
    - an appended byte (SHA-1 mismatch);
    - missing artifact.
  - **Accepted:**
    - a manifest whose reproduction entry is `NaN`;
    - a manifest that records only one of the four outputs.
  - `save_value_finder` also passes a `NaN` reproduction to `joblib.dump` (issue 5).
- **Band rule, end to end.** I re-ran `evaluate_raw` on the stand-in pilot file:
  - Same gate as saved: +5.25 pp (LB +1.21), 1.81× (LB 1.43), the same status.
  - I fed that status to `score.score_round` on the raw stand-in: **209 hidden, exactly `run_protocol`'s 209**.
  - On 1,000 random lockbox candidates, I retyped O'Keefe as "kerin o'keefe", used a status with pooled members [O'Keefe, Jenssen] and the country "austria". `score_round` hid **707**, `band_hidden` hid 707, my own count gave 707, and 707 verdicts were hidden. It took 0.86 s.
- **Defect found the same way.** In the dry-run table I set half of O'Keefe's wines to the straight-apostrophe spelling. `run_protocol` then reported **4 sources with ≥ 50 wines** (the truth is 3), with the two spellings as separate units.
- **Numbers:**
  - Every cell of the §6.1 protocol table matches notebook cell 135 and `phase6_protocol_simulation.csv`, as do the pause bullets, the seed-spread table, the verdict and tier tables, the unit-truth bullets and the dry-run bullets. The unit-truth bullets include France ≈ 25 wines per pilot (570 / 9,024 × 400), South Africa ≈ 50 and DeSimone ≈ 17.
  - All 20 Phase 5 pass rates lie within 0.03 of the seed ranges (largest gap 0.015). The claim holds.
  - I recomputed from the artifact: lockbox tier shares 30.1% / 46.4%, value rate 0.216, and the verdict tiers 207 / 1,586 / 3,791 / 1,704 with value rates 0.88 / 0.52 / 0.14 / 0.02.
  - Monitoring table, executive-summary deployment paragraph and slide 10 all match.
  - **Mismatch:** BSC4 timing (issue 4).
- **Alerts on perturbed rounds** (1,000 lockbox candidates). These fired:
  - notes truncated to 15 words;
  - 5% of words unknown;
  - prices × 1.3;
  - superlatives appended.

  **Notes truncated to 25 words fired nothing**, though mean P(90+) fell from 0.30 to 0.13 and the share above the development P90 from 26% to 5% (issue 6).

## Task coverage
| CRISP-DM task / output | Present / Partial / Missing | Note |
|---|---|---|
| 6.1 Plan deployment → Deployment plan | **Present** | **Present:**<br>• artifact reproduction (0.0), with a loader that refuses;<br>• tool, scripts, and one band rule;<br>• protocol in code, simulated, with detection pools;<br>• departures table, outcome data, prerequisites, rollout with durations, "does not do" list.<br>**Defects:**<br>• protocol counts sources on raw names (issue 1);<br>• schedule arithmetic (issue 2);<br>• stale cost text (issue 3). |
| 6.2 Plan monitoring and maintenance → Monitoring and maintenance plan | **Present** | Leading checks are in code, with thresholds in `config` and a false-alert rate. Lagging checks are the frozen protocol. The retraining policy and owner are stated. Weak points: no detection evidence for the alerts, alerts one-sided, development reference in-sample (disclosed). |
| 6.3 Produce final report → Final report | **Present** | §6 is traceable to cells and CSVs. Stale numbers remain: BSC4 timing, and the $10,000 in the executive summary. |
| 6.3 Produce final report → Final presentation | **Partial** | Now honestly labelled a slide outline. Slide 9's screenshot still doesn't exist. Slide 8 ("~400 retailer notes, ~$10,000") and slide 9 (0.027 s) are stale. |
| 6.4 Review project → Experience documentation | **Present** | Specific and self-critical. It now records the round-1 lesson that the guard rails lived in the simulator but not in the tool. Each lesson has a "next time". |

## Round-1 issues
| # | Round-1 issue | Status | Evidence |
|---|---|---|---|
| 1 | Monitoring and data-quality checks not in code | **Resolved** | `monitoring.round_report`: schema refusal names the missing column (verified); short-note, no-price, duplicate and leak flags (5 duplicates flagged in my test); `score.py` writes `<out>.monitoring.json`; the app shows the alerts; tested. What remains is detection evidence (issue 6). |
| 2 | Tool doesn't enforce the simulated stop rule | **Partly resolved** | One `band_hidden`, with names normalised and pooled members stored at firing time. 209 = 209 on the dry run; 707 = 707 on 1,000 candidates. But `check_units`, `run_protocol` and `from_raw` use raw `source` and `country` strings, so variants split units and inflate the source count (issue 1). |
| 3 | Integrity control can be bypassed | **Resolved, with an edge case** | Every refusal claimed was confirmed on scratch copies. Never rebuilds. `build_artifact.py` checks before saving. `requirements.txt` fixed. A `NaN` or partial reproduction record still passes (issue 5). |
| 4 | Shortlist tiers wrong for new writers | **Resolved** | Tier table recomputed (30.1% / 46.4%). Round view ranks within the round (tested: 10% / 10%). A development-percentile column still appears in the batch output (issue 8). |
| 5 | No schedule or outcome feed | **Partly resolved** | Now present: source, licence, matching rule, censoring, A8 and A9, timeline table, caps, fallback, durations, full-round logging. The arithmetic and assumptions don't reconcile (issue 2). |
| 6 | Inconsistent pass-rate estimates | **Resolved** | `PILOT_N_BOOT = 200` and `SEED` are the defaults everywhere. The seed-spread table is saved. I checked the reconciliation claim (largest gap 0.015). The model card labels both runs. |
| 7 | Pause size within noise; power unknown | **Resolved** | 1,000 simulations with Wilson CIs. Fold 4 masked is 2.9% (2.0–4.1%). Detection pools are added. Caveat: the Jenssen pool has 336 wines, so draws of 200 or 300 overlap heavily and its 10% / 0% are nearly deterministic. |
| 8 | Protocol gaps past 400 wines | **Resolved** | Checks every 100 wines up to 800. Pooled membership is stored at firing time. Tested (`checks_continue_past_400…`). |
| 9 | No tamper-evident freeze | **Partly resolved (pending by design)** | The `phase4_fold_predictions.csv.gz` restore is verified. The commit and tag are correctly made a prerequisite of rollout step 0. But the text says "frozen" in the present tense, never names the tag, and the model card's version line omits Phase 6 (issue 7). |
| 10 | Misleading middle verdict tier | **Resolved** | Renamed "Long shot". Base rate shown. "How to read this" explains disagreements. Minor wording (issue 11). |
| 11 | Monitoring references and thresholds untested | **Partly resolved** | False-alert rate simulated, in-sample reference labelled. Out-of-fold references not done (disclosed). The false-alert test is close to circular (issue 6). |
| 12 | BSC4 rests on evidence that doesn't exist | **Partly resolved** | `AppTest` exists and passes. Status is "recording pending". No screenshot yet (issue 10). |
| 13 | §6.3 overclaims | **Resolved** | "Slide outline"; article and video "still outlines". |
| 14 | Stale or inconsistent text | **Mostly resolved** | Re-execution count, 202 s, the "superseded" notes in §5.3 and cell 131, the two commits, and the fold-1 qualifier are all fixed. A new stale figure appeared: BSC4 timing (issue 4). |
| 15 | Hosting and licence | **Resolved** | Prerequisites in §6.1. The README marks the public route as demo-only. The app caption states NC use. |
| 16 | No `masked_ranker` test | **Resolved** | `test_masked_ranker_refits_the_ranker_on_masked_notes` passes. |

## Issues raised
| # | Severity | Issue | Suggested fix |
|---|---|---|---|
| 1 | MAJOR | **The protocol counts note sources and builds its units from raw strings. Only the band-hiding step normalises names.**<br>• `pilot.from_raw` keeps `source` as typed. `check_units` and `run_protocol` group by it, and `country` is only `_norm`-ed, not case-folded.<br>• Two spellings of one writer therefore become two units and two sources. In my test on the dry-run table, "Kerin O'Keefe" plus "Kerin O’Keefe" gave **4 sources with ≥ 50 wines instead of 3**.<br>• So condition 2 (≥ 3 sources, the guard that stops a one- or two-writer pilot from reaching a decision) can be met by a typing variant. Splitting a source also halves each half's chance of reaching the 50-wine stop-rule minimum.<br>• Revision 2 fixed exactly this class of defect, but only in `band_hidden`.<br>• The new tests don't catch it: they compare `band_hidden` with outputs that are themselves computed by `band_hidden`. | Canonicalise once, at intake. In `from_raw` (and `as_pilot_table`), map `source` and `country` through `name_key` to one canonical spelling, and keep the original in a display column. Then every unit, count, status entry and tool lookup uses the same key. Add a test where a pilot with one writer spelled two ways has the same `sources with enough wines`, units and decision as the canonical pilot. In `pilot_eval.py`, print the canonical source list with counts, so the analyst can spot near-duplicates such as "Smith Imports" vs "Smith Imports Ltd" that the key can't merge. |
| 2 | MINOR | **The schedule's arithmetic doesn't reconcile with its own assumptions.**<br>• A8 is defined as a 10% yield *within 12 months*, yet the 10% row expects a decision in 6–9 months. That needs most reviews to arrive within 2–5 months, a lag distribution that is never stated.<br>• The 5% row expects 10–14 months, but the cap is "12 months of candidate rounds". So in that scenario the pilot would probably stop with no deployment. The table presents it as a normal timeline.<br>• The executive summary says "capped at 12 months", though the cap is on rounds, not calendar time.<br>• The timeline assumes 400 scored wines is enough. But the decision also needs ≥ 3 sources with ≥ 50 wines each. Your own simulation shows one- or two-writer pools never get there, and the retailer's note-source mix is not assumed anywhere.<br>• Matching checks only precision (48 of 50 right, a 95% lower bound of about 86%). Missed matches, which cut the yield, are never measured.<br>• The fallback trigger ("after 3 rounds, projected time > 12 months") can't be computed when the lag is unknown. | Add assumption A10, the review-lag distribution (for example, the median months from candidate to published score), and A11, the note-source mix (the share of notes from the top 3 sources). Recompute the timeline from A8 × A10, and state for each yield whether a decision comes before the cap. Define the cap in calendar months from round 1. Add a match-recall check (of a hand-searched sample of reviewed wines, the share the rule finds). Base the fallback trigger on observed yield and lag after 3 rounds, with the formula written down. |
| 3 | MINOR | **The pilot's cost is stated three ways.**<br>• §6.1 says the main route uses published reviews (about $1,200 of analyst time) and the $10,000 panel is a fallback.<br>• The executive summary's Recommendation still says "a pilot on 400 retailer notes (about $10,000 at $25 a sample)", and its Deployment paragraph gives no cost.<br>• Slide 8 says "~400 retailer notes, ~$10,000".<br>• The §5.3 cost bullet has no "superseded in §6.1" pointer, unlike conditions 2 and 7.<br>• A5's "2 analyst-hours per cycle to re-score" now has to cover logging, matching, hand checks and a check every 100 scores, and the licence cost is unknown. | Give one cost line everywhere: main route about $1,200 plus a licence (as a range or "to be quoted"); fallback +$10,000. Add a superseded note to the §5.3 cost bullet. Restate A5 for the larger task, or give a range. |
| 4 | MINOR | **BSC4 timing is stale in four places.** Notebook 6.1c and `phase6_bsc4_timing.csv` (re-execution 5) give a median of **0.026 s** and a maximum of **0.030 s**. Report §6.1, `model_card.md`, `monitoring_plan.md` §4 and slide 9 still say 0.027 / 0.031 s, from re-execution 4. This breaks the report's own "every number comes from a cell". | Update all four. Since the figure is wall-clock, write "about 0.03 s (median, notebook 6.1c)" so it doesn't go stale again. |
| 5 | MINOR | **The integrity check accepts a `NaN` or incomplete reproduction record.**<br>• `load_value_finder` tests `max(rep.values()) > REPRO_TOL`, and `save_value_finder` does the same through pandas `max()`. Both pass `NaN`: I confirmed the loader serves such a manifest, and the saver went on to `joblib.dump`.<br>• The loader also accepts a manifest that records only one output.<br>• `reproduces_lockbox` uses pandas `.max()`/`np.nanmax`, which skip `NaN`, so a rebuild that returns `NaN` for some lockbox rows would still "reproduce". | Require the four expected keys, all finite and ≤ 1e-8 (`all(np.isfinite(v) and v <= tol …)`). In `reproduces_lockbox`, fail if any prediction is `NaN` or if the row count differs. Add both cases to `test_serving_refuses…`. |
| 6 | MINOR | **The alerts' false-alert rate is close to circular, and no detection rate is reported.**<br>• The 500 simulated rounds come from the reference sets themselves, and the limits sit at 2–3× those references, so "no alert in any round" was close to certain.<br>• §6.2 says the alerts catch "another language, truncated blurbs, a new grape list, price inflation", but nothing was simulated to show it.<br>• In my perturbation tests they did fire on gross breaks: 15-word notes, 5% unknown words, prices × 1.3, appended superlatives.<br>• They **missed notes truncated to 25 words**, which pushed mean P(90+) from 0.30 to 0.13 and the share above the development P90 from 26% to 5%. That is a large shift in the ranker's input with no alert, because both of those alerts are one-sided (high only). | Add a detection table to notebook 6.2a: rounds of perturbed lockbox notes (truncation to 15 / 25 / 30 words, unknown-word rates, price × 1.1–1.5, a grape-list change, promotional phrasing), with the share of rounds that alert. Make the P(90+) and percentile-share alerts two-sided, for example "below 0.10 / below 5%". Report the detection rate next to the false-alert rate. |
| 7 | MINOR | **Freeze wording (round-1 issue 9; the pending commit is fine).**<br>• The rollout prerequisite is the right approach. But §6.1's heading ("frozen before any pilot data") and the executive summary ("frozen in code") read as if the freeze has already happened.<br>• No tag name is given.<br>• The model card's version line still ends at `wine-phase5-rev4`.<br>• The run log hashes the outputs but not the protocol code (`pilot.py`, `config.py`). | Add one sentence to §6.1 and the run log: "As of revision 2, the Phase 6 state is not yet committed; it will be tagged `wine-phase6-rev2` before rollout step 0." Add that tag to the model card's version line. Once committed, cite the hash. Optionally, add `pilot.py`, `monitoring.py`, `artifacts.py` and `config.py` to the run log's SHA-1 block. |
| 8 | MINOR | **The development-percentile label still reaches buyers.**<br>• `score.py` writes a `shortlist tier` column ("Above the development 90th percentile") next to `round tier`. On my 1,000 lockbox candidates it was on 104 of the 402 ≤ $25 rows (26%).<br>• The one-wine metric reads "Top 10% (dev.)", the old "top 10%" wording with the caveat moved to a tooltip. | Drop `shortlist tier` from the batch output, or rename it "development percentile (not a sampling tier)". In the one-wine view, show the percentile as a number ("above 93% of development candidates") instead of "Top 10%". |
| 9 | MINOR | **Logging the full round is required but only half supported.**<br>• §6.2 and rollout step 2 require every round's full scored file and monitoring report to be kept, but the app's shortlist view only offers a download and saves neither.<br>• `deployment/README.md`'s pilot workflow step 1 ("collect at least 400 notes for wines that will later get a critic score") contradicts §6.1, where every candidate is logged and pilot wines are the ones later reviewed. | State that pilot rounds must be scored with `score.py`, or have the app write the scored file and the monitoring JSON to a dated folder. Rewrite README step 1 to match §6.1. |
| 10 | MINOR | **BSC4 still lacks its pre-registered evidence.** BSC4 was "All shown in the recorded demo". The heading says "**passes**", and the qualifier "recording pending" comes three sentences later. There is no screenshot in `reports/figures/`, and slide 9 depends on one. | Change the heading to "passes on screen and timing; recorded demo pending". Save the screenshot now: it doesn't need to wait for the video. |
| 11 | MINOR | **Wording that goes past the evidence.**<br>• "Long shot is close to the base rate in development (0.19–0.36 against 0.10–0.22)": in folds 1 and 3 it is 1.6–1.9× the base rate (0.196 vs 0.102; 0.360 vs 0.223).<br>• "Masking evidently pushes [fold 4] over": the masked pool's residual is not saved, as the text itself admits.<br>• "The band is shown in 67–94% of unmasked development pilots *that reach a decision*": the rates are over all pilots. Conditional on reaching a decision they are 69–95%. | Say "above the base rate in development (1.0–1.9×), below it on the lockbox". Compute and save the masked fold-4 residual, or drop "evidently". Drop "that reach a decision", or report the conditional rate. |

## Most important improvement
Fix issue 1: canonicalise note-source and country names once, when pilot rows come in, and prove it with an independent test.

Revision 2's main claim is that the guard rails buyers get are exactly the ones that were simulated. That claim is now true for hiding the band, but not for the rule that decides whether the pilot may decide at all. The ≥ 3-source minimum is what stops a one- or two-writer pilot (the lockbox lesson) from reaching a deployment decision, and one writer typed two ways gets past it.

The fix is a few lines in `from_raw` and `as_pilot_table`. The test should compare against ground truth, not against `band_hidden` itself: a pilot with spelling variants must give the same units, source count, withdrawals and decision as the canonical pilot.

After that, reconcile the schedule with its assumptions (issue 2) and remove the stale cost and timing figures (issues 3–4). Then the phase is ready to commit and tag.

## Changes made (revision 3, 2026-11-08; re-execution 6)
| # | Change | Where |
|---|---|---|
| 1 | `pilot.canonical_names` gives each note source and country one spelling (most frequent form of its `name_key`; the original kept as `<col> (as given)`), applied at intake in `from_raw`, `as_pilot_table` and `run_protocol`, so units, the source minimum, intercepts and the status file all use one name. `pilot_eval.py` writes `sources.csv` with the spellings merged per source. Test against ground truth: a pilot with spelling variants gives the same units, source count, withdrawals and decision as the clean pilot. No-op on the development and lockbox pools (protocol tables byte-identical to re-execution 5) | `src/winevalue/pilot.py`, `deployment/pilot_eval.py`, tests, report §6.1 and §6.4 |
| 2 | Schedule rebuilt from stated assumptions: A8 yield (5–20%), A9 monthly rounds, A10 log-normal review lag (median 3 months, 2–6), A11 source mix checked at round 1. `phase6.pilot_timeline` (notebook 6.1e, `phase6_pilot_timeline.csv`): 400 scored wines by month 8 under A8/A10, not within the cap at 5% yield and a 6-month lag. Cap 12 calendar months or 800 wines. Fallback rule written as a formula at month 6 (factor 2.77 under A10). A matching-recall check joins the precision check | `src/winevalue/phase6.py`, `config.PILOT_*`, notebook 6.1e, report §6.1 |
| 3 | One cost everywhere: $1,200–2,400 of analyst time for 12 rounds plus a data licence; +$10,000 panel only as the fallback. §5.3's figure marked superseded | report executive summary, §5.3, §6.1; slide 8; notebook cell 5.3 |
| 4 | Timing "about 0.03 s" (median 0.026 s) in the report, model card, monitoring plan and slide 9 | same |
| 5 | `artifacts.reproduction_passed`: all four outputs present, finite and in [0, 1e-8]; used on save and load; refusal tests for partial, NaN, inf and negative records. The stricter check exposed that the ranker gives no score to 1,097 no-price lockbox rows (Phase 5 imputed a price); `reproduces_lockbox` now compares the ranker on the 16,699 priced rows and treats any shape or NaN-pattern mismatch as a failure (`_maxdiff`). All four outputs 0.0 | `src/winevalue/artifacts.py`, `production.py`, tests, notebook 6.1b, report §6.1 and §6.4 |
| 6 | The two ranker-level alerts are two-sided (lower limits 0.10 and 5%, below every development fold, set before the run). Detection simulated on 12 kinds of deliberately broken lockbox feeds (`monitoring.PERTURBATIONS`, `detection_rates`, `phase6_alert_detection.csv`): gross faults caught in 86–100% of rounds; notes cut to 30 words, 2% unknown words and prices × 1.1 are missed or rarely caught, which the report states. False alerts still 0 | `config.MONITOR_ALERTS`, `src/winevalue/monitoring.py`, notebook 6.2a, report §6.2, `deployment/monitoring_plan.md`, slide 11 |
| 7 | Freeze wording: "fixed before any pilot data (to be frozen by the tag `wine-phase6-rev3`)"; the prerequisite states the Phase 6 state is not yet committed | report §6.1, model card |
| 8 | `score.py` no longer writes a development-percentile tier; the one-wine screen shows "69 / 100 (dev.)" with a plain-language caption (`production.percentile_text`) | `deployment/score.py`, `deployment/app.py`, `src/winevalue/production.py` |
| 9 | The app's shortlist view also downloads the monitoring JSON and says pilot rounds must be scored with `score.py` so the full file is kept; README pilot step 1 rewritten to match the report | `deployment/app.py`, `deployment/README.md` |
| 10 | Screenshot of the one-wine screen with every BSC4 output (`reports/figures/phase6_app_one_wine.png`, 0.05 s); heading now "passes on screen and timing; the recorded demo is pending" | report §6.1, slide 9 |
| 11 | "Long shot" stated as 1.0–1.9× the base rate (0.65× on the lockbox); band shown "67–94% (69–95% of pilots that reach a decision)"; masked fold 4's whole-pool residual now measured (+1.09) instead of inferred | report §6.1, notebook reading 6.1 |
