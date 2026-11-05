# Phase 3 · Data Preparation: Critic Round 1

- **Date:** 2026-11-04
- **Reviewer:** Claude critic (independent subagent session), persona from `critic_prompt.md`. Read-only access; it reproduced every pipeline count and computed no score statistics on lockbox critics.
- **Draft reviewed:** first Phase 3 draft

## Score: 7 / 10 · Major issues remaining: yes (2)

`prepare()` is correct in substance (decisions applied in a sensible order; folds reproduce Phase 1; no duplicate group crosses folds; R8 attribution matches Phase 1).

## Issues raised
| # | Severity | Issue | Suggested fix |
|---|---|---|---|
| 1 | MAJOR | **DM5(c) isn't operational.** No evaluation corpus is named (`prepare()` already drops the 43 pairs, so DM5 on the prepared table flags 0); `is_true_duplicate` reads `row.get("vintage")`, so the answer depends on whether a column is present (35/43 vs 36/43); the frozen rule gives **0.81 < 0.90**, and those 43 pairs were seen in Phase 2; `content_word_difference` ignores all capitalised words, so sentence-initial changes cost nothing; `prepare()` and DM5 use different definitions of duplicate | Name the corpus; make the rule compute its own inputs; record that the pairs were seen; report DM5(c) as exploratory, or freeze and accept 0.81; align `prepare()` with the definition |
| 2 | MAJOR | **The lockbox isn't pinned.** `critic_folds(load_raw())` gives a different lockbox (Schachner, Gordon, Dykes, Pickard) from `critic_folds(raw.drop_duplicates())`; the tests check the raw-frame lockbox the project doesn't use | Freeze the critic → fold mapping and lockbox as constants; `assign_folds` uses them and fails on unknown critics; tests assert the four names |
| 3 | MINOR | Residual leaks in `note`: "Best Buys", "Editor's Choice", prices in words ("six bucks", ~30), score commentary ("loses a few points", 136), ~1,289 price-relative phrases | Widen patterns; strip score commentary; price-relative phrases as an R-2 residual / stricter DM1b mask |
| 4 | MINOR | The leakage audit is mostly tautological (it reuses the stripping regexes; checks true by construction) | Add checks that can fail: an independent term list; no `note` shared across folds; lockbox = frozen four; a development-only token probe |
| 5 | MINOR | `n_words` / `short_note` computed on the raw description (356 rows differ) | Compute on `note` |
| 6 | MINOR | The colour re-freeze lost true positives (US "Port Zinfandel/Syrah" without parentheses; still Blanc de Noir; Clairet); untested risks ("La Rose de Pez", "Sparkling Hill Vineyard", "Tawny Ridge") | Targeted patterns + tests; dated amendment before H5 |
| 7 | MINOR | 1.7% unmapped, incl. easy grapes (Claret, Saperavi, Petite Verdot, Pinot Meunier, Aligoté, Moschofilero, Insolia, Kerner, Dornfelder) | Map them, or exclude unmapped from H5 |
| 8 | MINOR | 1,257 anonymous notes still have a lockbox critic as top guess (the p > 0.5 rule is defensible); development CV folds have the same issue | Phase 5 sensitivity (drop all lockbox-top-guess anonymous); per-fold attribution filter in Phase 4 CV |
| 9 | MINOR | `variety` and `grape` both one-hot encoded (redundant) | Keep one + a "label differs" flag |
| 10 | MINOR | R-3 filter keys on title only (Phase 2 said title + variety); lockbox changed by 36 rows (text rules) and that isn't reported | State both |
| (3.1) | MINOR | Sparsity counts are raw, not prepared; mojibake not repaired; dictionary lacks definitions | Fix |

## Single most important improvement
Make DM5(c) unambiguous and honest (corpus named, rule self-contained, same definition in `prepare()`, seen pairs disclosed, result reported without re-tuning). Pin the lockbox mapping in the same revision.

## Changes made in response (revision 2)
| # | What I changed | Where |
|---|---|---|
| 1 | DM5 corpus named (`prepare(stop_before="near_duplicates")`, 119,280 notes); `is_true_duplicate` computes its own vintage and grape; sentence-initial words now count; `prepare()` documented as Jaccard-only; **(a) recall is the only pass/fail criterion**; (b) reported as an engineering check; (c) **exploratory** (pairs seen in Phase 2), 35/43 = 0.81, not re-tuned; §1.3 updated (dated) | similarity.py; prepare.py; config; §1.3; §3.3 |
| 2 | Frozen `config.CRITIC_FOLDS` / `LOCKBOX_FOLD` / `LOCKBOX_CRITICS`; `assign_folds` uses them and raises on unknown critics; tests assert equality with the Phase 1 derivation and the four lockbox names; split tests now on de-duplicated data | config; splits.py; tests |
| 3 | Widened patterns: "Best Buys", "Editor's", prices in words, score commentary incl. any score/rated word ("too ripe to score higher"; "rated at 12.5%" kept); text-only "barrel sample" notes (+6) dropped; price-relative wording a documented R-2 residual for the stricter DM1b mask | text_audit.py; tests |
| 4 | Leakage audit with checks that can fail: independent term list (0.59%, examples shown), no note shared across folds, lockbox = frozen four, development-only score-correlated token probe | prepare.py; §3.5 |
| 5 | `n_words` / `short_note` on `note` | prepare.py |
| 6 | Colour amendment (dated): US "Port Zinfandel/Syrah", still Blanc de Noir → white, Clairet → rosé; negative tests ("La Rose de Pez", "Sparkling Hill Vineyard", "Tawny Ridge") | grapes.py; tests |
| 7 | Claret, Saperavi, Petite Verdot, Pinot Meunier, Aligoté, Moschofilero, Insolia/Inzolia, Kerner, Dornfelder mapped; unmapped 1.5% excluded from H5 | grapes.py |
| 8 | Carried: per-fold R8 filter in Phase 4 CV; Phase 5 sensitivity without lockbox-top-guess anonymous notes | §3.5 |
| 9 | One grape encoding: `grape` + `label_differs` (raw variety only for frozen benchmarks) | features.py |
| 10 | R-3 title-only key stated; lockbox rows removed by text rules (36) reported in the log | splits.py; §3.2 |
| (3.1) | Sparsity counts from the prepared table; mojibake repaired; dictionary with definitions and provenance | prepare.py; notebook |
