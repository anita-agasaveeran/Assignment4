# Phase 4 run log

Every Phase 4 fit that informed a decision, in order. Times are Pacific, taken from the Claude Code session record. No Git commit exists between Phase 3 (`64acde6`, Nov 4 20:19) and the Phase 4 commit, so this log and the session record are the evidence for the order of events. It's an attestation, not cryptographic proof. **The lockbox (fold 2) was not touched by any run below.**

## Revision 1 (Nov 4)

| Time | Run | Data seen | What changed afterwards |
|---|---|---|---|
| 22:29 | Design block appended to `config.py`: outer and inner design, grids, selection rules, `PROFILE_STOPWORDS`, `DESCRIPTOR_LEXICON` | None | – |
| 22:30 | `smoke.py`: fold 3 ridge and stack | **Outer fold-3 MAE** of both models | No model setting changed. `cv.py` and `scoring.py` were already written |
| 22:31 | `abl.py`: fold-3 ablation (per-fold R8 / none / named only) | **Outer fold-3 MAE**, bias and slope | No model setting changed |
| 22:33 | `run4.py` started: all candidates on all four folds. `evaluate.py` written just before | Outer results when it finished at 22:52 | – |
| 22:34 | "date" removed from the lexicon (it matches calendar dates) | No DM4 output had been produced | Lexicon fixed |
| 22:36 | Plural rule fixed after a unit test failed on "cherries" and "peaches" | Unit test only | `descriptors.term_pattern` |
| 22:53 | `run4b.py`: DM3–DM6 and hypotheses | Development results | – |
| 22:58 | `SELECTED_*` outcomes and `SIMPLICITY_ORDER` added; LightGBM `deterministic` flags added so reruns reproduce | Selection results | The order written down matches the rule's "ridge < stack" from 22:29 |
| 22:59 | Notebook executed in full | Same results | – |
| 23:28 | DM3 profiles inspected | Top terms | `revised_stopwords()` written (23:30); config updated (23:32) |

**Consequences for the claims in the report:**
- The selection rules came before the first fit (22:29 vs 22:30), but **two outer-fold looks at fold 3 happened before the full run**. Neither led to a change in a model setting, which is what the log shows, and nothing stronger.
- `PROFILE_STOPWORDS` is hand-written. It was written before any NMF fit, but it reflects the analyst's reading of tasting notes in Phases 1–3, not a stated rule. Treat it as judgement.
- The final Phase 4 commit will be tagged before any Phase 5 run. The hash is recorded in §5.

## Revision 2 (Nov 7), after critic round 1

The critic had already seen outer-fold results for a calibrated ridge, and so had I by reading its report, so everything below is a **post-hoc revised parameter setting**. Times are Pacific.

| Time | Step | Data seen | Rule written first? |
|---|---|---|---|
| 13:16 | Revised DM1 selection rule written to `config.py`, then `dm1_inner.py` started in the same command: repaired inner design, five candidates, four folds | Inner and outer results of the five candidates (~13:24) | Yes, earlier in the same command |
| 13:17 | DM3 multi-split stability rule written to `config.py`, then `dm3_scan.py` started: 3 vocabularies × 2 fit sets × 2 methods × k = 6–15 × 10 splits, plus critic-disjoint splits | Stability tables (~13:21) | Yes, earlier in the same command |
| 13:18 | DM6 §1.3 fixed-effects model written; first run of specifications A and B | Critic effects in both | No rule: descriptive, nothing is selected |
| 13:19–13:27 | Ablation (matched control), per-critic, shortlist-mix and BSC4 mapping code; `SELECTED_DM1`, DM3 outcome and the P(90+) / band definitions frozen from the 13:16 / 13:17 rules | – | The P(90+) and band definitions were written before any outer check of them |
| 13:27, 14:01, 14:37 | Full notebook runs. The first two stopped on code errors (a price-name lookup, a read-only array); the third completed | All revision 2 outputs | – |
| 15:25–15:29 | Fold-3 gap diagnostic: Phase 1 vs Phase 4 inputs, dropping note length; per-critic length slopes | Outer fold-3 results | Diagnostic only; no setting changed |
| 15:29 | Full notebook run with the length cell added | – | – |

## Revision 3 (Nov 7), after critic round 2

| Time | Step | Data seen | What changed |
|---|---|---|---|
| 16:31 | Round 2 logged; all-fold length table, ablation decomposition, DM3 matched null, DM6 decomposition and H5 seed check added to the notebook; superseded config text marked | **New outer-fold look:** ridge with and without note length on folds 0, 1 and 4 (fold 3 already seen) | Interpretation and diagnostics only. **No model, rule or selection changed** |
| 16:32 | Full notebook run | All revision 3 outputs | – |

## Revision 4 (Nov 7), after critic round 3 (gate passed: no MAJOR issues)

| Time | Step | Data seen | What changed |
|---|---|---|---|
| ~17:05 | Per-writer ridge vs calibrated table, per-split critic-disjoint values and saved diagnostic tables added; wording fixes N2–N14 | Per-critic outer-fold results of ridge and the selected model (already in the fold predictions) | Interpretation only. **No model, rule or selection changed** |
| ~17:05 | Full notebook run | All revision 4 outputs | – |
