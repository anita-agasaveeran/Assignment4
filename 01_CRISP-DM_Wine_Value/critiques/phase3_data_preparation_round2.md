# Phase 3 · Data Preparation: Critic Round 2

- **Date:** 2026-11-04
- **Reviewer:** Claude critic (independent subagent session), persona from `critic_prompt.md`. Read-only access. It reproduced every pipeline count from `prepare(load_raw())`; 32/32 tests pass. No score statistic was computed on lockbox critics (the token probe uses development rows only; lockbox checks used text and counts only).
- **Draft reviewed:** revision 2

## Score: 8 / 10 (up from 7) · Major issues remaining: **no**, so Phase 3 passes its exit criterion

Both round-1 majors are fixed in substance. The revision introduced a few new defects, all minor; the colour fix (N1) must land before any colour × value table (H5).

## Round-1 issues
| # | Status | Note |
|---|---|---|
| 1 (MAJOR) DM5(c) | **Fixed** | Corpus reproduces (119,280); rule self-contained (a junk `vintage` column leaves 35/43); (c) exploratory at 0.81, not re-tuned. Caveats N4, N5 |
| 2 (MAJOR) lockbox pin | **Fixed** | `config.CRITIC_FOLDS` = `critic_folds(dedup)`; the raw frame still gives a different lockbox, so the pin was needed; `assign_folds` raises on unknown critics. Residue N6 |
| 3 Residual leaks | Mostly fixed | "bang for the buck" (22) and "price point" (59) remain (N3) |
| 4 Tautological audit | Fixed | State why the 1% threshold was chosen (0.59% observed) |
| 5 `n_words` | Fixed | `short_note` 38 (was 39 on raw text) |
| 6 Colour re-freeze | Partly fixed, **regression** | US Port, Clairet and negative tests fine; still-Blanc-de-Noir rule wrong for ~30 of 47 rows (N1) |
| 7 Unmapped grapes | Fixed | 1.5%, excluded from H5 |
| 8 R8 residue | Carried, acceptable | 1,257 lockbox-top-guess anonymous notes, all p ≤ 0.5 (N7) |
| 9 Redundant encoding | Fixed | |
| 10 R-3 key; lockbox rows | Fixed | 36 lockbox rows lost to text rules, logged |
| (3.1) | Partly fixed | Designation count off by one (N8); mojibake repair damages text (N2); `has_region_1` definition combined with another column's |

## New issues (all minor)
| # | Severity | Issue | Suggested fix |
|---|---|---|---|
| N1 | MINOR (before H5) | The still-Blanc-de-Noir rule runs before the sparkling patterns and its lookahead only looks after the phrase, so "Brut … Blanc de Noirs", Crémant, Franciacorta, Spumante, Bruto and "Champagne/Sparkling Blend" labels become white. Of 47 changed rows ~30 are wrong (19 in the ≤ $25 pool, 10 lockbox) | Apply only when no sparkling cue in title, region or variety label; tests from the 47 titles; dated re-freeze |
| N2 | MINOR | The mojibake repair deletes every "Â" when the round trip fails ("d'Âge" → "d'ge", "Âme" → "me"); fixes only one real case | Repair only when latin-1 → utf-8 succeeds; test "Âme", "d'Âge" |
| N3 | MINOR | "a point" alternative strips descriptive text (~15 of 26); "bang for the buck" (22), "price point" (59) survive and are mislabelled benign in §3.5; "bucks the trend" → `_price_` | Restrict "a point" to verdict contexts; add those phrases + "QPR" to `PRICE_RELATIVE`; correct §3.5 examples |
| N4 | MINOR | §1.3 says DM5 was made operational "before any DM5 run", but (c) was run in round 1 and the demotion and rule change came after | One dated sentence in §1.3 and config |
| N5 | MINOR | DM5(a) is close to non-discriminating (b = 37, r = 3 ⇒ P(candidate \| J = 0.5) = 0.993) | Say (a) checks the implementation, not the data; optionally report the 0.5–0.6 band |
| N6 | MINOR | Notebook cells 9 and 18 derive the lockbox from `critic_folds(df)` | Use `config` or assert equality; mark `critic_folds` derivation-only |
| N7 | MINOR (Phase 4) | `anon_lockbox_like` hard-codes the lockbox; per-fold attribution would drop 2,048 / 1,823 / 4,039 / 3,095 (folds 0/1/3/4) vs 859 | Add `critics=`; pre-register CV vs final filtering; report the size difference |
| N8 | MINOR | Note-length outliers 1,969 in text vs 1,965 in code; designations 37,666 vs 37,665 | Correct the text |
| N9 | MINOR | `_price_` placeholder (364 notes) reaches the price-free model's TF-IDF | Include it in the strict DM1b mask; disclose as R-2 residual |
| N10 | INFO | `prepare.py`, two tests and the dictionary are untracked | Commit with the phase |

## Single most important remaining improvement
Fix and re-freeze the colour map before any H5 table (the still-Blanc-de-Noir rule must yield to any sparkling cue), with tests built from the 47 affected titles and a dated amendment. In the same revision add the DM5(c) timeline sentence (N4) and the mojibake round-trip guard (N2).

## Changes made in response (revision 3)
| # | What I changed | Where |
|---|---|---|
| N1 | Colour rule reordered (dated amendment, text only, before any colour × value view): sparkling title cues first (now also "Bruto", "bubbles", "Dosage Zero", "Méthode champenoise/traditionnelle"); a sparkling variety label wins next; only then "Blanc de Noir(s)" → sparkling if the note describes bubbles (mousse, bead, tirage, "on the yeast", …), else white. 47 rows changed vs revision 2 (40 → sparkling, 4 → rosé; 14 in the ≤ $25 pool, 7 lockbox). 13 stay white (German/Austrian still Blanc de Noir, Malbec, Grenache, …); Treveri Cellars is ambiguous and left white rather than tuned. Test built from the affected titles | grapes.py; prepare.py; tests; §3.4 |
| N2 | Mojibake repaired only when the Latin-1 → UTF-8 round trip succeeds; otherwise unchanged. Test with "Âme", "d'Âge", "crÃ¨me" | prepare.py; tests |
| N3 | "a point" stripped only after a verdict verb (gains/loses/earns/deserves/docked/costs); "bucks the trend" no longer a price; "bang for the buck", "price point", "QPR" added to `PRICE_RELATIVE`; §3.5 examples corrected | text_audit.py; tests; §3.2, §3.5 |
| N4 | Dated timeline sentence in §1.3 and the config comment: (c) first run in round 1, demoted and rule amended afterwards, result unchanged | config; §1.3; notebook |
| N5 | Stated that (a) checks the implementation (b = 37, r = 3 ⇒ P(candidate \| J = 0.5) = 0.993); Phase 4 reports recall in the 0.5–0.6 band | config; §1.3; notebook |
| N6 | Notebook cells 9 and 18 assert the derivation equals `config.CRITIC_FOLDS` / `LOCKBOX_CRITICS` and then use the frozen constants; `critic_folds` docstring marked derivation-only | notebook; splits.py |
| N7 | `anon_lockbox_like(..., critics=)`; pre-registered: CV uses per-fold filtering, the Phase 5 fit uses the lockbox filter; the size difference (2,048 / 1,823 / 4,039 / 3,095 vs 859) is reported in Phase 4 | splits.py; §3.5 |
| N8 | Counts in the text taken from the re-executed notebook | §3.2; §3.5; notebook |
| N9 | `text_audit.strict_price_mask` removes price-relative wording and `_price_` for the DM1b / R-2 sensitivity check; disclosed as R-2 residual | text_audit.py; tests; §3.2 |
| N10 | Untracked files committed with the phase | git |
| (r1 #4) | The 1% bar is described honestly as a coarse tolerance that a single barrel-sample-sized leak family wouldn't trip on its own; it is backed by per-pattern counts and the probe | §3.5 |
| (3.1) | `has_designation` and `has_region_1` get separate definitions in the dictionary | notebook; §3.3 |
