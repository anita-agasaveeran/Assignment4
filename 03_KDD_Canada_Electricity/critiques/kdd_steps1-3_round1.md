# KDD Steps 1–3 · Selection, Preprocessing, Transformation: Critic Round 1

- **Date:** 2026-11-11
- **Reviewer:** Claude critic (independent subagent), persona from `critic_prompt.md` ("world-renowned speaker and authority on the KDD process who has written many award-winning books on it"). Read-only; re-ran numbers with the repo `.venv`.
- **Seal:** every loader call used `allow_sealed=False`; no months after 2024-12, no sealed-origin errors, no mining results. It read (did not run) the newly written `mining.py` / `forecast.py` to see how the rules were defined. The catalogue's 2025 confirmation rows are visible in the CSV (event descriptions, not StatCan data). **No sealed-data exposure.**
- **Draft reviewed:** notebook sections KDD 1–3, `config.py` rules, `selection.py`, `preprocess.py`, `transform.py`, `data/external/event_catalogue.csv` v1 (SHA-256 `db90cb67…f1b8`), `tests/test_kdd_steps.py`.

## Score: 7 / 10 · Major issues remaining: yes (3)

## Task coverage
| KDD task / output | Present / Partial / Missing |
|---|---|
| 1 Selection: geographies, period, producer class, non-overlapping types, flows, exclusions with reasons | Present |
| 1 Selection: seal enforced in the target data | Present |
| 2 Cleaning: status codes, structural zeros vs real gaps, negatives | Present |
| 2 Integration: cross-table totals, parts vs totals, availability identity | Present (all reproduced exactly) |
| 2 Noise / data-break screening | Partial (NL 2021-02 step missed) |
| 2 K3 event catalogue compiled and hashed before mining | Partial (no external timestamp; drought windows look data-shaped) |
| 3 Shares, trade ratios, seasonality, calendar-balanced K1 vectors | Present |
| 3 K2 deseasonalized series with discovery-only climatology | Present |
| 3 K3 STL robust z with discovery-only scale | Present; confirmation procedure undefined |
| 3 K4 training window from 2016-01 | Present in prose; formulas only in code |
| K1 / K2 / K3 / K4 rules operational | Partial / Partial / Partial / Partial |
| Notebook conclusions match outputs | Mostly |

## Issues raised
| # | Severity | Issue (critic's evidence) | Suggested fix |
|---|---|---|---|
| 1 | MAJOR | **K2 isn't a real test.** (a) The σ estimator isn't named in config, and it changes the effective penalty about 13× (AB s.d. 5.08 pp vs MAD-diff/√2 1.38 pp). (b) A step model is fit to ramps, and the residual bootstrap around fitted step means is nearly self-confirming. (c) "Closer to post than pre" persistence is almost automatic on a monotone decline. (d) Only 1 of 2 provinces is needed, and AB and NS ramps were already visible. (e) Direction and the burning-vs-denominator controls are ignored | σ estimator + sensitivity; pre-declared direction; attribution threshold; margin-based persistence; non-model-based stability; ≥ 3 qualifying provinces |
| 2 | MAJOR | **K3 is gameable.** Base rate 12.1%, so precision ≥ 0.5 implies lift ≥ 4.1: the lift rule never binds. Flag-level precision lets flags pile up inside long droughts (72 of 170 covered geo-months). Coverage is very uneven (MB 32%, QC 31%, BC 28% vs YT/NU 0%); the \|z\| > 3 share peaks in 2023 (25.6%), the same months as the drought entries. STL endpoint effects in 2024. "Frozen detector" is undefined for confirmation | Event-level precision; geography-stratified circular-shift permutation null (≥ 1,000 reps, p ≤ 0.05); one-sided STL with a frozen IF and threshold; report edge years |
| 3 | MAJOR | **No verifiable pre-registration timestamp:** config, catalogue and rule code are uncommitted, and `mining.py` / `forecast.py` appeared during the review | Commit the rule files before mining and cite the hash |
| 4 | MINOR | K1: winter/summer ratio and amplitude r = 0.97; NL drives both trade features; outliers will form singletons; one move at k = 2 gives ARI 0.69–0.87 | Drop one seasonality feature; freeze the one-move ARI table; dev-scaler nearest-centroid check; per-geography co-assignment |
| 5 | MINOR | K4 candidate formulas, bootstrap unit and tie rule only in code; the 2025-12 origin covers 8 months | Freeze in config; state the 8 months |
| 6 | MINOR | Break scan overstated: NL industrial hydro first appears 2021-02 (+56–67 GWh/mo); NS industrial generation collapses in 2020 (Northern Pulp) | Register NL; reword |
| 7 | MINOR | "Nunavut ≈ 0.003% of availability" is wrong: 0.040% | Correct |
| 8 | MINOR | Annual shares were means of monthly shares; ON sentence wrong (6.7–8.6% in 2017–20) | Ratio of sums; fix the sentence |
| 9 | MINOR | Catalogue: E32 (QC drought from 2023-01) dubious; drought ends sit exactly at the window edge; possible omissions (Feb 2021 Prairie cold, Dec 2022 AB cold, Point Lepreau outages, commissioning); weather-only scope | Tighten E32; explain the ends; state out-of-scope classes; re-hash before mining |
| 10 | MINOR | Combustion share of generation isn't consumption-side dependence for importers (PE, NS) | Scope sentence |
| 11 | MINOR | Tests miss `DATA_BREAKS`, `scale_end`, and rule edge cases | Add tests |

## Single most important improvement
Turn K2 and K3 into tests that can actually fail, and freeze them before any mining cell runs.

## Changes made in response
| # | What I changed | Where |
|---|---|---|
| 1 | **K2 rewritten in config before mining:** σ = 1.4826·MAD(diff)/√2, with a σ = s.d. sensitivity run reported per province. Direction pre-declared (falling = less combustion-dependent). Attribution: Δln share = Δln combustion − Δln total; "burning" if Δln combustion / Δln share ≥ 0.5. Persistence is a margin test (2025–26 mean beyond the pre/post midpoint by ≥ 0.5 pp, and the last development segment not reversed). Stability is non-model-based (PELT on 25 trimmed sub-series of the observed data, ±3 months, ≥ 70%); the block bootstrap is kept as secondary. Verdict needs ≥ 3 non-Ontario provinces | `config.py` K2 block; `mining.trim_stability`, `persistence`, `attribution`, `noise_sigma(method)`; notebook 4b; tests |
| 2 | **K3 rewritten:** event-level precision (each event credits at most one flag, via bipartite matching) is primary. A geography-stratified circular-shift permutation null (1,000 reps) replaces lift; acceptance = event-level precision ≥ 0.5 and p ≤ 0.05. Flag-level precision and lift are secondary. Edge years reported. Confirmation uses one-sided STL (fit up to *t*), with the Isolation Forest and its score threshold frozen and no re-ranking | `config.py` K3 block; `mining.event_level_credit`, `permutation_p`; `transform.stl_z_onesided`; notebook 2 (rule text) and 4c; tests |
| 3 | **Partly addressed.** I can't commit (every commit needs the user's approval), so a **pre-registration manifest** (`PREREGISTRATION.json`) records SHA-256 hashes of config, the catalogue, all rule code and its tests, written 2026-11-11T21:14:59Z before any K1–K3 mining. The notebook's first mining cell calls `prereg.verify()`, which raises if any rule file changed. A copy was placed outside the repo (session notes folder). **Disclosure:** the K4 development backtest (development origins only, which is legitimate model selection) was run once before the manifest; it changed no K4 rule. Only the K4 text (formulas, tie rule, bootstrap unit) was written into config afterwards | `src/kddenergy/prereg.py`; `PREREGISTRATION.json`; notebook 4 (first cell) |
| 4 | `seasonal_amplitude` dropped from K1 features. The one-move ARI table for the chosen k is printed. A secondary nearest-centroid check with the development scaler and per-geography co-assignment are pre-registered | config K1 block; notebook 4a and 5 |
| 5 | K4 formulas, tie rule (ties within 0.01 pp → simpler model), bootstrap unit ((geography, origin) pairs, 2,000 reps, 90%) and the 8-month 2025-12 origin written into config | config K4 block |
| 6 | NL industrial hydro step registered (`BREAK_WINDOWS`: NL 2021-01 → 2021-03 excluded from K3). NS 2020 industrial collapse documented as a real change (Northern Pulp), not a break; the "no other break" wording is corrected | config; notebook 2 |
| 7 | 0.003% → 0.04% | notebook 2 |
| 8 | Annual shares are now ratios of annual sums; the AB / NS / ON / NB sentences are rewritten from the recomputed values | notebook 3 |
| 9 | Catalogue revision 2 (before mining): E32 starts 2023-05; added E36–E40 (Feb 2021 and Dec 2022 Prairie cold); drought ends documented as truncation of ongoing events; out-of-scope classes declared; re-hashed (`ee336e9b…a22b`) | `data/external/event_catalogue.csv`, `README.md`; config |
| 10 | Scope sentence added (generation-side share; PE and NS importers) | notebook 3; config K2 comment |
| 11 | Tests added: break windows, `scale_end`, one-sided STL with no look-ahead, persistence margin and reversal, trimmed stability, attribution, event-level credit, permutation null calibration, σ methods (28 tests pass) | `tests/test_kdd_steps.py`, `tests/test_mining.py` |

## Issues not addressed (with reason)
- **#3, external timestamp via a git commit:** not possible in this session (no commits without the user's approval). The hash manifest and its copy outside the repo are the substitute. Recommended: commit `PREREGISTRATION.json` together with the rule files as the first commit of the KDD steps.
- **#9, omissions such as Point Lepreau outages and commissioning dates:** declared out of scope rather than added, because they couldn't be dated to the month from public memory without a source check.
