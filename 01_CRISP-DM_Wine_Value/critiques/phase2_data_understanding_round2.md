# Phase 2 · Data Understanding: Critic Round 2

- **Date:** 2026-11-04
- **Reviewer:** Claude critic (independent subagent session), persona from `critic_prompt.md`. Read-only access; it verified figures (score statistics on development data only) and simulated the DM5 spec.
- **Draft reviewed:** revision 2

## Score: 7.5 / 10 (up from 6) · Major issues remaining: yes (1)

Round-1 issues: 3, 4, 6, 8–15, 17, 18 resolved. 1, 2, 7, 16 partial. 5 not resolved (DM5 still unmeasurable).

## New issues
| # | Severity | Issue | Fix applied (revision 3) |
|---|---|---|---|
| 1 | MAJOR | DM5 still unmeasurable: 10–30% edits give median J 0.19, so "recall vs exact Jaccard" has no threshold and too few positives | **DM5 re-specified in §1.3** (original struck through, dated): τ = 0.5; 5-word shingles; 2,000 synthetic copies with 2–8% word edits (simulation: ~1,670 reach J ≥ 0.5); recall ≥ 0.9; false-flag ≤ 1% on 2,000 random pairs; precision ≥ 0.9 on the 43 real pairs with a labelling rule fixed in advance; parameters in `config.DM5_*` |
| 2 | Minor | Leak statistics wrong: 671 not 630 (em dashes); the midpoint equals the score 99.7% (MAE 0.008), not "inside 99.4% / 0.22"; regex could match "14-15% alcohol" | Regex: `[-–—]`, scores limited to 80–100 incl. "100"; tested; numbers corrected |
| 3 | Minor | Explicit-score and price regexes miss forms ("90-point", "90+ rating", "worth 100", "bucks"); WineEnthusiast labels ("Best Buy" 159, "Editors' Choice", "Cellar Selection") | Regexes broadened (20 / 184 / 333 found); labels stripped for all models; tests |
| 4 | Minor | NV wines got brand/solera years | NV-before-first-year → non-vintage; 17 titles change; 69 → 52 pre-1990, all genuine; tested |
| 5 | Minor | Noise ceiling framed on the same-critic value; the model is scored on unseen critics | Reframed as a range of ~0.64–0.83 with n, "likely but uncertain headroom" |
| 6 | Minor | Colour and synonym gaps (blends, title styles like Pinot Noir rosé / Chardonnay Brut, Silvaner, Prugnolo, Tinta Fina, Gamay Noir, Carignano, Assyrtico, Turbiana = Verdicchio) | `wine_colour(variety, title)` with title style override + first-grape blend rule (97.9% coverage); synonyms added (43 labels / 5,891 reviews); H5 config text updated |
| 7 | Minor | Near-duplicate counts from 64-permutation LSH undercount | Exact Jaccard on loose 128-permutation LSH candidates: 50 / 43 / 20 / 8 (matches the critic's exact all-pairs check) |
| 8 | Minor | Process docs: README tracker; barrel effect on fold 0 only | Tracker updated; all folds shown (1/3/4 change ≤ 0.2 pp) |
| r1-7 | Minor | "Drop all duplicated-note rows" throws away genuine relisted reviews | Keep one row per duplicated note |

## Single most important remaining improvement
Make DM5 measurable (done in revision 3). The minor fixes were all applied rather than carried.
