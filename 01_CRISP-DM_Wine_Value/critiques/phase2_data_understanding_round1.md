# Phase 2 · Data Understanding: Critic Round 1

- **Date:** 2026-11-04
- **Reviewer:** Claude critic (independent subagent session), persona from `critic_prompt.md`. Read-only access; score statistics on development data only.
- **Draft reviewed:** first Phase 2 draft (report §2, notebook Phase 2)

## Score: 6 / 10 · Major issues remaining: yes (5)

## Task coverage
2.1 Present · 2.2 Present · 2.3 Partial (thin for DM3–DM6, H2/H6, score heaping) · 2.4 Partial (missed the score leak, title-as-key failures, synonyms, pseudo-provinces, implausible prices, duplicate notes, winery variants; two decisions wrong)

## Issues raised
| # | Severity | Issue | Suggested fix |
|---|---|---|---|
| 1 | MAJOR | **Target written into the notes.** 630 notes (all fold 0, Roger Voss barrel samples) open with a score range ("90–92. Barrel sample."); the score falls inside it 99.8% of the time. The "92" in the vocabulary table is this leak. Also 17 "rated 92 points"-type notes | Log in 2.4; strip or drop in Phase 3 (671 barrel-sample titles); re-check fold-0 feasibility and disclose; scan for other leaks |
| 2 | MAJOR | **The proposed vintage fix is wrong.** "Year nearest the end" picks planting/cuvée years in 65/82 multi-year titles; the "< 1970 = non-vintage" rule voids real old vintages | Strip the winery prefix, then take the **first** year 1900–2017; unit-test the counter-examples |
| 3 | MAJOR | **The noise floor is invalid as stated.** It's a range over groups (87 have 3–7 reviews), not pairwise; `title` isn't a wine key (27% of repeat titles are different wines); no √2 correction; not matched to the model's population | Pairwise, same title + critic + variety, ≤ $25; implied single-read σ and ceiling; cross-critic version; reword |
| 4 | MAJOR | **Variety synonyms not flagged** (Syrah/Shiraz, Pinot Gris/Grigio, Grenache/Garnacha, Zinfandel/Primitivo, …); Gris 26% vs Grigio 4% shown as different findings | Keep raw `variety` for the frozen rules; add a documented `grape_canonical` map (frozen before lockbox use) for DM4/H5/app |
| 5 | MAJOR | **DM5 is untestable:** only ~18 distinct-text pairs with Jaccard ≥ 0.8 corpus-wide (< 1 expected in a 10k sample); no near-duplicate exploration done | Explore the Jaccard distribution; loop back to Phase 1 to re-specify DM5; disclose |
| 6 | MINOR | Seal: the duplicate-note score check ran on all data (20 of 33 groups include lockbox rows) | Recompute on dev; disclose |
| 7 | MINOR | Duplicate notes are attached to *different* wines (scrape errors), not "same note, different score" | Drop them from evaluation |
| 8 | MINOR | "808 same critic" counts anonymous-only titles (named: 712) | Fix |
| 9 | MINOR | Prices > $1,000 not verified ($2,013 = vintage; $3,300 "Sorbet" Médoc) | Hand-check; set errors to NaN; add a price = year check |
| 10 | MINOR | Pseudo-provinces ("Other", "France Other", province = country) | List; "Unknown" for models; the frozen rule stays unchanged |
| 11 | MINOR | Winery case/whitespace variants (29), NBSP in titles/wineries/designations, mojibake | Encoding check across text columns; case-folded keys; disclose the effect on frozen rules |
| 12 | MINOR | Jenssen (lockbox) and DeSimone (fold 4) share a handle (@worldwineguys) | Limitation; text-only attribution check |
| 13 | MINOR | Price leaks into the "price-free" input ("$amounts" in 324 notes) | Mask currency in Phase 3 (R-2) |
| 14 | MINOR | Mask residual gaps ("now–2025", "decade", "N years") | Report what's left as a DM1b limitation; don't change the frozen list |
| 15 | MINOR | Score heaping at the 90 threshold (89 avoided) not explored | Add; link to A2 |
| 16 | MINOR | H5 forking paths: the colour map was built after viewing value-by-variety; 21% unmapped | Freeze the colour map now from a documented rule; list unmapped |
| 17 | MINOR | Report tables trimmed selectively; "R3 gate passed" and "early-release" claims unsupported | Full lists; evidence cells |
| 18 | MINOR | Barrel samples are a different review type | Flag; exclude from evaluation |

## Single most important improvement
A systematic leakage and identity audit of text and keys before Phase 3: strip or drop the barrel-sample score ranges; recognise that `title` isn't a wine ID; fix the vintage rule; restate the noise floor (pairwise, same wine, matched band, √2).

## Changes made in response (revision 2)
| # | What I changed | Where |
|---|---|---|
| 1 | Leak audit (`winevalue.text_audit`): 630 score-range notes (99.4% inside the range), 7 explicit scores, 324 currency mentions; decision: drop barrel samples, strip scores, mask prices. Fold-0 feasibility re-run without them: MAE reduction 32.7% → 34.9% (Phase 1 conservative; targets stand) | §2.4a; text_audit.py; tests |
| 2 | Vintage rule corrected: strip the winery prefix, then the first year (`extract_vintage(title, winery)`); 13 titles change; pre-1990 69 → 56, all genuine; unit test with counter-examples | data.py; §2.4c |
| 3 | Noise floor redone: pairwise, same title + variety, development data, ≤ $25 band, √2 correction, implied σ and ceiling (0.82), cross-critic version; conclusion reworded (headroom, not "close") | §2.4b |
| 4 | `grape_canonical` synonym map (36 labels / 5,717 reviews); raw label kept for frozen rules; Gris/Grigio example shown | grapes.py; §2.3, §2.4c |
| 5 | Near-duplicate exploration (39 pairs ≥ 0.5, 8 ≥ 0.8); **DM5 re-specified in §1.3** (full corpus, synthetic-recall + hand-checked precision) as a documented loop-back | §2.3f; §1.3 |
| 6 | The duplicate-note check is now on development data; breach disclosed here | §2.4 table |
| 7 | Duplicate notes characterised (all on different wines); decision: drop | §2.4c |
| 8 | Named-critic count recomputed (titles reviewed only by one named critic: 729, counting titles with ≥ 2 named reviews) | §2.4 table |
| 9 | Prices > $1,000 hand-checked; 3 set missing; price = year check (1 row) | §2.4c |
| 10 | Pseudo-provinces listed (1,921); "Unknown" for models; frozen rule unchanged | §2.4c |
| 11 | Encoding check across text columns; 29 winery case groups; normalisation decision | §2.4c |
| 12 | Jenssen/DeSimone: text-only confusion 6–7%; limitation | §2.4c |
| 13 | Currency mask for the price-free model (R-2) | text_audit.py |
| 14 | Mask residuals quantified (920 / 250 / 1,038); a DM1b upper-bound note; stricter mask as a Phase 4 sensitivity check | §2.4a |
| 15 | Score heaping at 89 shown; linked to A2 | §2.3g |
| 16 | Colour map frozen from grape knowledge (96% coverage) before any colour × value table; unmapped labels listed | grapes.py; §2.4c |
| 17 | Full ≥ 300 value lists; R3 evidence cell (40 / 30 / 16 / 51); price-by-vintage evidence | §2.3g |
| 18 | Barrel samples flagged and excluded (as #1) | §2.4a |
