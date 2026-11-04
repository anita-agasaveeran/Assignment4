# KDD Front Pass: Critic Round 1

- **Date:** 2026-11-03
- **Reviewer:** Claude critic (independent subagent session), persona: world authority on the KDD process. Read-only access; it recomputed figures. It disclosed computing one pooled seasonal-naive WAPE that included the dataset's pre-computed origin-2024-12 errors (not reported or used).
- **Draft reviewed:** front pass v1 (`reports/front_pass.md`, notebook front-pass section)

## Score: 6 / 10 · Major issues remaining: yes (3)

| # | Severity | Issue | Suggested fix |
|---|---|---|---|
| 1 | MAJOR | **The 2016 break is a coverage expansion, visible in the data**: Canada total +9.0% (592.8 → 646.3 TWh), wind 3.4× (Quebec 0.77 → 9.76 TWh), BC wind first reported 2016, industry total 42.7 → 59.1 TWh, industry solar/tidal/other only from 2016-01, Alberta total +31%, availability 534.3 → 582.5 TWh. Pre-2016 MB/NB totals exclude suppressed wind. The residual proves additivity *within* eras, not comparability *across* them | Coverage table 2014–2017; freeze a rule: no cross-2016 comparisons (or a known level shift), never "discover" a 2016 change point; the break affects K1–K3, not only thermal |
| 2 | MAJOR | **The "first lead" is overstated**: it ends on 2025 (sealed confirmation period) and starts at the 2020 minimum. On development data it's ~flat 2016 → 2022, then rises 2022–24 with low hydro (392.4 → 341.8 TWh) and nuclear refurbishments (95.5 → 81.7 TWh) | Restate on ≤ 2024 only, with the drivers; treat the 2025 national share as viewed; drop the headline until an adjusted analysis exists |
| 3 | MAJOR | **"Thermal share" isn't "cleanliness"**: Alberta's coal-to-gas switch cut emissions while its thermal share barely moved | Reframe K2 as non-emitting / combustion share (+ non-renewable vs biomass from 2020); emissions out of scope without external data |
| 4 | MINOR | Interestingness not operationalised per goal | Acceptance rules per goal (ARI, change-point persistence, event catalogue compiled before mining) |
| 5 | MINOR | The seal holds by convention only; the raw backtest file already contains sealed-origin errors; the published 3.30% includes them | Loaders with `allow_sealed=False`; test; never quote 3.30% |
| 6 | MINOR | Feasibility: no assertion against the file; 4.08% vs published 3.30% unexplained; pooled gain fragile (wins 49/78 pairs) | Assert vs file; explain; per-origin WAPE + bootstrap; pre-declare the K4 margin; note latest-vintage revisions |
| 7 | MINOR | 652 negative values; 8 geo-months where the residual identity isn't exact (max +4,000 MWh); partial 2026 year shown next to full years | Report max \|diff\| and the exceptions; a negative-value decision; no partial years |
| 8 | MINOR | `front_pass.md` and the figure have no StatCan attribution | Add the footer and caption |

## Single most important improvement
Settle the 2016 break as a coverage expansion and freeze a preprocessing rule for every goal. Then restate the K2 lead on development data only, as a non-emitting/combustion share with hydro and nuclear controlled.

## Changes made in response (front pass v2)
| # | What I changed | Where |
|---|---|---|
| 1 | The 2016 break is documented as a coverage expansion (coverage table by producer class × type, 2014–2017; totals/wind/solar/Alberta step). Frozen rule `CONSISTENT_START = "2016-01"` for every cross-year analysis; a 2016 change point is never a discovery | Notebook F.2; config; report |
| 2 | The lead is restated on 2016–2024 only (non-emitting share flat 2016–22, falling 2023–24), with hydro/nuclear/wind+solar drivers shown; the headline is dropped; national 2025–26 K2 confirmation declared spent; K2 confirmed at province level | F.3; report |
| 3 | K2 reframed as non-emitting / combustion share (+ non-renewable share from 2020); emissions intensity out of scope without ECCC data | F.1; report |
| 4 | Per-goal acceptance rules pre-registered (K1 ARI ≥ 0.7; K2 province change-point persistence ±3 months; K3 catalogue precision ≥ 0.5 with the catalogue built before mining; K4 ≤ 0.90× and better at both origins); novelty baseline = CER provincial profiles | F.1; config |
| 5 | Sealed loaders (`allow_sealed=False` default) + tests; the published 3.30% is never quoted | data.py; tests; F.4 |
| 6 | Row-by-row assertion against the dataset's backtest (936 forecasts); 3.30% vs 4.08% explained; per-origin table; bootstrap ratio CI (0.862–0.961); 69% pair wins; latest-vintage caveat | F.5 |
| 7 | Max \|diff\| and the 8 exceptions listed; the test bounds them; 652 negatives kept as net generation (decision); no partial years displayed | F.2; tests |
| 8 | Attribution footer in the report and notebook; source caption on the figure | Report; notebook |
