# Phase 1 · Business Understanding: Critic Round 1

- **Date:** 2026-11-03
- **Reviewer:** Claude critic (independent subagent session), persona from `critic_prompt.md`. Read-only access; it re-computed figures on development folds only and respected the lockbox seal (row counts only).
- **Draft reviewed:** first Phase 1 draft (report §1 + notebook Phase 1, saved with outputs)

## Score: 7 / 10

All CRISP-DM outputs are present. Timing and excluded inputs are explicit, the evaluation design is frozen in code, and the feasibility check reproduces exactly. Not passed: the headline shortlist claim ("0.85 vs 0.33, ~2.5×") comes from an unstated ~10k-candidate pool, file-order tie-breaks and a baseline the critic split itself weakens.

## Task coverage
| CRISP-DM task / output | Status | Note |
|---|---|---|
| 1.1 Background | Present | "1,148 titles" should be "1,148 repeat reviews of 934 titles" |
| 1.1 Business objectives | Present | BO2 needs a guardrail on showing estimated points |
| 1.1 Business success criteria | Partial | BSC1 has an unstated pool size and the wrong benchmark; BSC3–5 vague; no rule for deciding under uncertainty |
| 1.2 Inventory of resources | Present | |
| 1.2 Requirements, assumptions & constraints | Partial | R-3 can't be followed when folds are critic-defined; A1 overstated; no pool-size assumption |
| 1.2 Risks & contingencies | Partial | Missing: critic folds are confounded with region; anonymous notes may be by lockbox critics |
| 1.2 Terminology | Present | |
| 1.2 Costs & benefits | Partial | Inconsistent numbers; P@100 used at other depths; no break-even |
| 1.3 Data mining goals | Present | |
| 1.3 DM success criteria | Partial | DM2 inherits BSC1's problems; DM1 baseline weakened by the split |
| 1.4 Project plan | Partial | Due date unconfirmed; no slack for loop-backs |
| 1.4 Tools & techniques | Present | |

## Issues raised
| # | Severity | Issue | Suggested fix |
|---|---|---|---|
| 1 | MAJOR | **Wrong kind of notes.** All notes are critic-written after tasting; in use, notes come from producers and importers. Leave-critic-out tests a change of style, not of author | Reword to "unseen critics"; state that the BSCs are necessary, not sufficient; add a pilot gate; fix an evaluative-word list now and test masking in Phase 4 as a DM criterion |
| 2 | MAJOR | **Critic folds are confounded with region.** Kerin O'Keefe writes 97% of named Italian reviews (lockbox). Variety × country coverage ranges 29–87% by fold. A random split shows variety × country beating the global mean by 8.5%; the critic split, only 1% | Report coverage per fold; rewrite the baseline claim; add a confound risk; add a title-grouped random split as a secondary design; state what the lockbox measures |
| 3 | MAJOR | **Precision@100 depends on an unstated pool size** (6–13k candidates per fold, so the top 100 is the top ~1%). With 500-candidate pools, model P@100 is 0.49 | Add A7 (candidates per cycle); define BSC1/DM2 over simulated cycles; reset the floor and the economics |
| 4 | MAJOR | **"Best simple rule" is not the best.** ~857 ties at $25 are broken by file order (0.33; 0.37 with random ties). Winery track record gets 0.385 | Fix a full set of simple rules with random tie-breaks before Phase 5; benchmark = best of the set on the lockbox |
| 5 | MINOR | No decision rule under uncertainty; thin margins (BSC2 0.60 vs dev 0.62, fold 3 0.57) | Pre-register a pass rule with lower bounds; justify or lower the targets |
| 6 | MINOR | The seal is breached by descriptive statistics on all rows (score bands, corr 0.62, 50.6%/15.9%) | Recompute on development data only; say "development only" for Phase 2 EDA |
| 7 | MINOR | R-2 conflicts with R-1/BO1: price is legitimate for *ranking* | Allow a price-aware DM2 ranker; keep the price-free model for BO2 and the value verdict |
| 8 | MINOR | Wrong repeat-title count; 124 titles span folds; R-3 not applied in the feasibility check (effect negligible: P@100 0.848 → 0.845) | Fix the label; reword R-3 to drop test rows whose title appears in training; show the check |
| 9 | MINOR | Economics inconsistent (284/$7,100 vs 285/$7,125), wrong depth, no break-even | Generate once; use the correct depth; add break-even |
| 10 | MINOR | Critic calibration overclaimed ("the same wine") | "Same variety and country"; descriptive until DM6 |
| 11 | MINOR | Showing estimated points to customers could mislead / raise trademark issues | Internal use or a clearly labelled "estimated band"; add a risk |
| 12 | MINOR | Anonymous notes not checked for lockbox critics (the critic's classifier attributes 88 confidently to lockbox critics) | Document an attribution check; drop those rows |
| 13 | MINOR | BSC3/4/5 vague; BSC2 duplicates DM1 and covers all wines | Business-facing thresholds; BSC2 on ≤ $25 candidates |
| 14 | MINOR | Plan not anchored: no due date, no slack | Confirm the deadline; add a buffer and a fallback scope |

## Single most important improvement
Rebuild the shortlist criterion (BSC1/DM2) around the buying decision: state the candidates per cycle (A7), measure precision@k over simulated cycles, fix a full simple-rule set (incl. producer track record) with random tie-breaks before Phase 5, and report how much of each held-out fold's region the training data covers.

## Changes made in response (revision 2)
| # | What I changed | Where |
|---|---|---|
| 1 | Claims reworded to "unseen critics". BSCs labelled "necessary, not sufficient". Pilot gate with a numeric bar (≥ 100 notes, ≥ 55% within ±2). Evaluative-word list fixed in `config.EVALUATIVE_TERMS`; masking test run now (91% of the improvement retained) and pre-registered as DM1b (≥ 70%) | §1.1 BSC note; A1; DM1b; config |
| 2 | Fold coverage table (variety × country and winery coverage, top countries, incl. lockbox counts only). Title-grouped random split added (v×c beats global by 8% there vs 1% on the critic split). R2 confound risk added; lockbox statement ("new writers in a mix of regions; not the hardest fold") | §1.1 Evaluation design; Costs & benefits; R2 |
| 3 | A7 added (1,000 candidates/cycle). BSC1/DM2 redefined as expected precision@100 over 200 simulated cycles (`winevalue.value.simulate_cycles`), with sensitivity at 500/2,000. Targets re-set from the worst development fold | A7; BSC1; config |
| 4 | Fixed simple-rule set (price, winery and province track record, variety × country, winery then price) with random tie-breaks (`precision_at_k(rng=...)`). Benchmark = best of the set on the lockbox. Claims corrected (best simple 0.37; ratio ≥ 1.55× per fold) | BSC1; feasibility tables |
| 5 | Pre-registered pass rule (point estimate + uncertainty condition per BSC). Targets below the worst development fold where possible (BSC2 0.62 vs 0.63–0.72; BSC1 0.55 vs 0.61–0.71; DM1 20% with the fold-3 risk stated as R9) | §1.1 BSC table; config; R9 |
| 6 | All score statistics recomputed on development data, after the lockbox cell. Phase 2 plan says "development data only" | Notebook order; §1.4 |
| 7 | R-2 split by use: price allowed for the DM2 ranker, excluded for BO2 and the value verdict. `quick_text_model(with_price=True)` | R-2; DM2; models.py |
| 8 | Counts corrected (1,148 repeat reviews of 934 titles; 124 span folds). R-3 reworded and applied in the feasibility check (`drop_titles_seen_in_training`) | Overview; R-3; R3 |
| 9 | Economics generated once from the simulated cycles at the sampled depth; break-even added (~2 cycles); revenue upside stated as unquantified | Costs & benefits |
| 10 | "Same variety and country"; descriptive until DM6 | Costs & benefits; R6 |
| 11 | BO2 limited to an internal "estimated band"; R10 added | BO2; R10 |
| 12 | Own attribution check (98.4% accuracy; 341 confident, 29 to lockbox critics); those rows dropped in Phase 3 | R8; R-3 |
| 13 | BSC3 (naming agreement, Jaccard stability), BSC4 (feature checklist, < 3 s), BSC5 (same sign, CI in both datasets) given thresholds. BSC2 restricted to ≤ $25 candidates | BSC table |
| 14 | Buffer day and fallback scope added. Due date still to confirm with the project owner | §1.4 |
