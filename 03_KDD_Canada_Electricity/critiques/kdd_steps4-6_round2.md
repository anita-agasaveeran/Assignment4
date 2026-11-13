# KDD Steps 4–6 · Data Mining, Interpretation/Evaluation, Using the Knowledge: Critic Round 2

- **Date:** 2026-11-11
- **Reviewer:** Claude critic (independent subagent), KDD-authority persona (`critic_prompt.md`). Read-only; the seal had been lifted, so it re-ran every verdict on all data. Scratch scripts were kept outside the repo; no repo file was modified.
- **Draft reviewed:** notebook sections KDD 4–6 (executed), `src/kddenergy/*`, `PREREGISTRATION.json`, `deployment/`, tests.

## Score: 7.5 / 10 · Major issues remaining: yes (2)

## Task coverage
| KDD task / output | Present / Partial / Missing |
|---|---|
| 4 · K1 k-means + Ward, k by silhouette, one-move ARI | Present (reproduced) |
| 4 · K2 PELT, σ sensitivity, controls, attribution | Present (reproduced exactly) |
| 4 · K3 STL-z → Isolation Forest, 2% budget, comparator | Present (reproduced) |
| 4 · K4 one model picked on development origins | Present |
| 5 · `prereg.verify()` before mining and before unsealing | Present (manifest still matches) |
| 5 · K1–K4 scored as written | Present (all four verdicts reproduced) |
| 5 · K3 confirmation (one-sided STL, frozen IF and threshold) | Present (low power) |
| 5 · Interpretation vs public record | Partial (BC/PE, NB, ON readings) |
| 5 · Interestingness ranking | Partial |
| 6 · `knowledge.json`, `refresh.py`, dashboard, licence | Present / Partial (K3 in refresh isn't the evaluated procedure) |
| External pre-registration timestamp (git commit) | Partial (hash manifest only) |

## Issues raised
| # | Severity | Issue (critic's evidence) | Suggested fix |
|---|---|---|---|
| 1 | MAJOR | **K2 is "MET" as written but in substance by two provinces.** "Largest adjacent shift" picked up the end of a 12-month episode in BC (+0.61 pp first-to-last; annual 9.5% in 2016 vs 9.4% in 2023–24) and PE (−0.54 pp vs 2016–17, below the 1 pp floor). NL is one 1.4 pp step of a staircase; the "1.7% base" was the deseasonalized offset. `knowledge.json` and the dashboard said "MET · 5 qualify" with no caveat | Keep "MET (as written)"; add a disclosed post-hoc sensitivity (first-segment change, ≥ 18-month segments, burning-driven); correct the BC/PE/NL sentences and the knowledge base; pre-register a minimum segment length and materiality next time |
| 2 | MAJOR | **The NB explanation and rank-4 finding misread the data.** NB nuclear in summer 2023 was *normal* (475–488 GWh); the anomaly is combustion (386–577) and total generation (1,272–1,442 vs ≈ 900–1,000) with high exports, consistent with the QC drought (E32). Only 4 of 11 NB flags coincide with an outage; the longest outage (Jun–Sep 2024) isn't flagged. Max-\|z\| beats the stratified null (0.21, p = 0.012), which undercuts "supply-side, not weather" | Rewrite the NB row; recast rank 4 as a hypothesis (validity 1) below K1/K4; report max-\|z\| p next to the IF result; fix `knowledge.json` |
| 3 | MINOR | Ontario explanation contradicts itself (flat hydro + nuclear across the 2023 step vs "refurbishment"). Since 2019, nuclear −12.2 TWh/yr and combustion +22 TWh; across the step, net exports +413 GWh/month | One consistent sentence |
| 4 | MINOR | Rank 1's validity "3 (K2 rule)", but no rule tests the national series (and it was spent). Decomposition: ON +18.6 vs AB −6.7 TWh; holding generation at 2016 gives 22.2%, so the denominator is ≈ 40% of the rise | Relabel validity; add the decomposition |
| 5 | MINOR | K1 persistence is k-specific: ARI 0.27 (k = 3), 0.61 (k = 4), 0.84 (k = 6); large feature drift | Report adjacent-k ARIs; soften the wording |
| 6 | MINOR | K3 confirmation has low power (one-sided \|z\| > 3: 1.7–4.6% vs 10–15%); the MB 2025-07 match is coincidental | Say so |
| 7 | MINOR | Deployment K3 (two-sided STL, re-ranked, 33 flags) isn't the evaluated procedure; the tab has no "not validated" warning or NL-window note | Label it unvalidated monitoring; mention NL |
| 8 | MINOR | "Only cells below call `allow_sealed=True`" is false (front pass F.2, structure only); manifest not committed | Reword; commit the manifest with the rule files |
| 9 | MINOR | Stale numbers (12% base rate → 13.2%; MB 35%); NL and PE "bases" wrong; the K4 failure explanation is untested (QC is 32% of the combination's 2025-12 error); K4 tie rule in config but not in code (moot: gap 0.055 pp) | Correct; call the K4 explanation a conjecture and show the error split; code the tie rule |

## Single most important improvement
Separate "the rule fired" from "the knowledge holds" for K2, and carry that into `knowledge.json` and the dashboard. Pair it with the NB rewrite, so step 6 deploys only knowledge the evaluation supports.

## Changes made in response
| # | What I changed | Where |
|---|---|---|
| 1 | The verdict is now labelled **"MET as written"**. A new, clearly labelled **post-hoc sensitivity** table per province covers (a) net first-to-last change ≥ 1 pp in the same direction, (b) pre and post segments ≥ 18 months, and (c) attribution = burning. Under (a) + (c), NL, NS and AB remain (3, the bar exactly); adding (b) would also remove AB (its ramp is cut into 16- and 12-month segments), and that's stated. The 5e/5f text says the substance is "two large burning-driven declines (AB, NS) plus a small NL decline; BC and PE qualified because a 12-month blip ended". The NL, PE and BC sentences are corrected (raw shares). `knowledge.json` gets a `k2_note`, and the dashboard shows it under the acceptance table | Notebook 4b text, 5b (new cell), 5e, 5f; step-6 cell; `app.py` |
| 2 | NB row rewritten from the data. A new output shows NB summer nuclear / combustion / total generation for 2019, 2021–24: 2023 nuclear 480 (normal), combustion 490, total 1,360. Only 4 of 11 flags are outages; the 2024 outage isn't flagged; a QC-drought export spill-over is a hypothesis. Rank 4 is recast as a **hypothesis (validity 1), ranked last**. The max-\|z\| comparator's p = 0.012 is printed next to the IF result, and the text now says "weather is invisible monthly" is too strong | 5c, 5f, `knowledge.json` |
| 3 | One Ontario sentence everywhere: since 2019 about half nuclear substitution (−12 TWh/yr), the rest demand and exports; the 2023 step itself is demand + exports | 5f; `knowledge.json`; report; article |
| 4 | National finding relabelled "descriptive; national figure seen in the front pass" (validity 2). A decomposition cell is added: combustion 136.7 → 143.4 TWh, ON +18.6, AB −6.7; share at 2016 generation 22.19%, so the denominator explains 42% of the rise | 5b (new cell), 5f |
| 5 | Adjacent-k ARIs printed (0.03 / 0.27 / 0.60 / **1.00** / 0.84) along with the largest feature drifts; wording is now "the k = 5 partition persists … k-specific" | 5a (new cell), 5f, `knowledge.json` |
| 6 | Confirmation power printed (\|z\| > 3: 1.7 / 4.6 / 2.5% vs 10.5 / 15.1 / 10.7%); the MB 2025-07 match is called coincidental | 5c, 5f |
| 7 | Dashboard Anomalies tab: "Unvalidated monitoring: K3 was NOT MET" warning; caption names the two-sided STL and both break exclusions (NU, NL) | `deployment/app.py` |
| 8 | Seal wording corrected (front pass F.2 read sealed months for structure only and printed a count). Committing the manifest is recommended to the user | Notebook 5 intro; report limitations |
| 9 | Base rate and coverage corrected (13.2%; MB 35%, QC 31%, BC 28%). The K4 explanation is labelled a conjecture, with a per-geography share of 2025-12 error (QC 32% of the combination's error vs 25% for seasonal naive) and the note that even ETS alone (0.986) would fail | Notebook 2, 5d, 5f |

## Issues not addressed (with reason)
- **#9, coding the K4 tie rule:** `forecast.py` is a hashed rule file, and editing it after evaluation would break the pre-registration manifest. The rule is moot here (the gap was 0.055 pp, above the 0.01 pp tie band). Left as written in config.
- **#7, making `refresh.py` use one-sided STL with a frozen threshold:** not changed. The tab is now labelled unvalidated monitoring, which is the honest status, since K3 failed and no detector has been validated.
- **#8, the git commit:** needs the user's approval (see the round-1 log).

**Status after round 2:** both MAJOR issues addressed in the notebook, knowledge base and dashboard. The notebook re-executes cleanly, all 30 tests pass and `prereg.verify()` still passes (no rule file changed after the manifest). The two rounds of the KDD steps are complete; no third round was run under the time budget.
