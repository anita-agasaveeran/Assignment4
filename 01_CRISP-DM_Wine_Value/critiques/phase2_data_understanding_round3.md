# Phase 2 · Data Understanding: Critic Round 3

- **Date:** 2026-11-04
- **Reviewer:** Claude critic (independent subagent session), persona from `critic_prompt.md`. Read-only access; it re-simulated DM5 (1,693 positives at seed 42) and recomputed every figure from the raw file (score statistics on development data only).
- **Draft reviewed:** revision 3

## Score: 8.5 / 10 (6 → 7.5 → 8.5) · Major issues remaining: **no**, so Phase 2 passes

Round-2 issues resolved: DM5 now measurable (major), leak statistics, regexes, NV guard, noise framing, exact near-duplicate counts, process docs, duplicate-note decision. Partial: colour/synonym maps (N4, N5).

## New issues (all minor)
| # | Issue | Action |
|---|---|---|
| N1 | DM5(a) recall sits at ~0.90 with a plain τ = 0.5 LSH (0.884–0.905 by seed) but ~0.99 with a 0.3 candidate threshold + exact verification. Neither is registered; the synthetic construction isn't fully specified | **Carried to Phase 3, before any DM5 run:** register `DM5_LSH_THRESHOLD` + exact verification; specify the construction in full; implement in `similarity.py` |
| N2 | DM5(b) on random pairs can't fail (J ≈ 0) | **Carried:** replace with hard negatives (synthetic J in [0.3, 0.5)) |
| N3 | "Mostly the same wine relisted" is wrong: about a third are relistings; most are recycled or mis-attached notes on different wines (all within one fold). §1.3 "all flagged pairs" vs §2.3 "43 pairs" is inconsistent | **Finding fixed now** (notebook §2.3f prints 24 different-winery / 19 same-winery pairs, all within one fold; report reworded; ~80 rows flagged for Phase 3). **Carried:** an operational labelling rule and one evaluation set for DM5(c) |
| N4 | The colour title override fires on winery and wine names (~200 rows: "Château du Port", "Cava d'Onice", "Coste di Rose", "Tinto Fino", …) | **Carried to Phase 3, before H5 uses the map:** override on the title with the winery stripped; strict "Rosé / Rose of / Rose de" matching; exclusions; negative tests; dated re-freeze |
| N5 | Muscat-family merge incomplete; easy unmapped grapes (Müller-Thurgau, Traminer, Graciano, Frappato, …) | **Carried** (same Phase 3 step) |
| N6 | Untraceable figures (184 verdict labels, 33 groups, 41 em dash / 3 "98-100") and stale wording | **Fixed now:** `verdict_label` column added; the counts printed; wording aligned |

## Single most important remaining improvement
Pin DM5's operational parameters (LSH threshold + verification, construction, hard negatives, labelling rule) before it's ever run. Carried to Phase 3.
