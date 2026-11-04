# KDD Project: Front Pass

*Working title: Is Canada's Grid Becoming Less Combustion-Dependent?*

*Domain goals, data checks, preprocessing rules and frozen holdouts, done before the KDD steps. Every figure comes from the front-pass section of `notebooks/KDD_Canada_Electricity.ipynb` (saved with outputs).*

> **Revision 2**, after critic round 1 (6/10; `critiques/frontpass_round1.md`).

## Goals (KDD step 0) and pre-registered acceptance rules
**Audience (hypothetical):** energy analysts and policy staff.

| Goal | Question | Acceptance (validity) |
|---|---|---|
| K1 Archetypes | Which provinces behave alike (mix, seasonality, trade dependence)? | Adjusted Rand index ≥ 0.7 between clusters from 2016–2024 features and from 2025–26 features |
| K2 Structural change | When did each province's **non-emitting share** (hydro + nuclear + wind + solar + tidal) or **combustion share** change? Did the grid get *less combustion-dependent*? | Province-level change point found on 2016–2024 data; post-change direction persists in 2025–26; date stable to ±3 months |
| K3 Anomalies | Which months were unusual? | Precision ≥ 0.5 against an event catalogue compiled from public sources **before** mining |
| K4 Prediction | Can monthly availability be forecast better than seasonal naive? | Pooled WAPE on sealed origins ≤ 0.90 × seasonal naive, **and** better at both sealed origins |

**Scope of "cleaner":** the data records *sources*, not emissions. A coal-to-gas switch (Alberta) cuts emissions without changing the combustion share. K2 therefore answers "less combustion-dependent?", and emissions intensity is out of scope without external data (e.g. ECCC's National Inventory Report).

**Other interestingness criteria:**
- **Novelty:** judged against the Canada Energy Regulator's provincial profiles.
- **Usefulness and understandability:** one chart and one sentence per finding.

## Data checks
**Structure (full table):**
- The generation table has 76,776 rows: 58,707 observed, 17,955 unavailable (`..`) and 114 suppressed (`x`).
- Canada = Σ provinces on 224/224 months.
- Utilities + industries = all producers on all 15,483 fully observed cells.
- The availability accounting balances except for the Feb 2019 BC residual (+70,931 MWh) and a 1 MWh rounding residual (Oct 2019). Both are flagged, not fixed.

**Thermal residual (total − hydro − nuclear − wind − solar − tidal − other)** matches StatCan's reported thermal categories within 1 MWh on 99.74% of geo-months. The 8 exceptions (max |diff| 4,000 MWh, Alberta/Canada Nov 2008) are listed in the notebook.

**652 negative values** are net generation, e.g. station service at New Brunswick's nuclear plant during the 2008–2012 refurbishment, and PEI thermal units. They're kept as net generation (a Preprocessing decision).

**The 2016 break is a reporting-coverage expansion plus a thermal reclassification:**

| | 2014 | 2015 | 2016 | 2017 |
|---|---|---|---|---|
| Canada total generation (TWh) | 599.9 | 592.8 | **646.3** | 649.4 |
| Wind (TWh) | 8.98 | 8.85 | **30.48** | 30.91 |
| Solar (TWh) | 0.25 | 0.26 | **1.79** | 2.05 |
| Alberta total (TWh) | 65.7 | 60.6 | **79.2** | 81.4 |
| Industrial wind reported (province-months) | 12 | 12 | **122** | 132 |

- From January 2016, the survey covers producers it didn't before: industrial wind, solar, tidal and "other" first appear. Some are published zeros: industrial wind goes from 12 to 64 non-zero province-months, utility solar from 12 to 35.
- In 2008–09, Manitoba and New Brunswick totals exclude their suppressed wind.
- Thermal output was also *reclassified* from technology types to fuel types.
- The residual is additive *within* each era, but nothing is comparable *across* 2016: thermal, wind, solar, totals and availability are all affected.

**Frozen rule (`config.CONSISTENT_START = "2016-01"`):**
- every cross-year comparison, cluster feature, trend, change point and anomaly baseline uses 2016-01 onward;
- pre-2016 data is used only within its own era;
- a 2016 change point is never reported as a discovery.

## First look at K2 (development data only, 2016–2024)
| | 2016 | 2018 | 2020 | 2022 | 2023 | 2024 |
|---|---|---|---|---|---|---|
| Non-emitting share | 78.8% | 79.6% | 80.9% | 80.8% | 79.3% | 77.9% |
| Combustion share | 21.2% | 20.3% | 19.1% | 19.2% | 20.6% | 22.1% |
| Non-renewable combustion share | – | – | 17.7% | 17.9% | 19.1% | 20.5% |
| Hydro (TWh) | 381.4 | 381.6 | 382.6 | 392.4 | 359.3 | 341.8 |
| Nuclear (TWh) | 95.7 | 95.0 | 92.7 | 82.3 | 84.6 | 81.7 |
| Wind + solar (TWh) | 32.3 | 34.1 | 38.8 | 42.3 | 44.3 | 51.1 |

- **The non-emitting share** was roughly flat from 2016 to 2022, then fell in 2023–24.
- **What changed from 2022 to 2024** (corrected after critic round 2):
  - hydro fell 50.5 TWh (Quebec −30.7, BC −10.9, Manitoba −7.3), mostly matched by **lower total generation** (−30.6 TWh), not more burning;
  - combustion rose 11.5 TWh, almost all in **Ontario** (+10.2);
  - nuclear was flat (its decline came in 2020–22, while the share stayed flat);
  - wind + solar grew 8.8 TWh.
  - About half of the combustion-share rise is a shrinking denominator. K2's controls will include total generation and trade.
- **The question for K2:** *is the recent rise in combustion structural, or a hydro/nuclear availability dip that wind and solar can't yet cover?* It's answered by province, with hydro and nuclear controlled.

*Disclosure:* front pass v1 displayed the national annual thermal share for 2025–2026. National K2 confirmation on 2025–26 is therefore treated as spent, and **Ontario's** as partly spent (it drives about 90% of the national combustion change). The K2 verdict rests on the other provinces.

## Frozen holdouts (enforced in code)
| Goal | Development | Sealed / confirmation |
|---|---|---|
| K1–K3 | 2016-01 → **2024-12** | **2025-01 → 2026-08** (acceptance rules above) |
| K4 | Forecast origins 2018-12 → 2023-12 (the dataset's backtest design, 12-month horizon) | **Origins 2024-12 and 2025-12**, scored once |

- **Enforcement:** the loaders drop months after 2024-12 and the sealed backtest origins unless called with `allow_sealed=True`, and tests check this.
- **Published benchmark:** the dataset's 3.30% WAPE includes the sealed 2024-12 origin and the Canada aggregate, so it's never quoted.

## Feasibility (K4, development origins)
The reimplemented seasonal naive matches the dataset's own backtest **row by row** (936 forecasts; asserted).

| Origin | Seasonal naive | 3-year seasonal mean | 3-year mean × √growth |
|---|---|---|---|
| 2018-12 | 3.25% | 3.34% | 3.29% |
| 2019-12 | 3.90% | 3.92% | 3.93% |
| 2020-12 | 4.24% | 3.75% | 3.78% |
| 2021-12 | 4.56% | 4.49% | 4.19% |
| 2022-12 | 4.52% | 3.57% | 3.65% |
| 2023-12 | 4.03% | 3.64% | 3.46% |
| **Pooled** | **4.08%** | 3.78% | **3.71%** |

- The pooled ratio is 0.910 (90% bootstrap interval 0.862–0.961), and the growth-adjusted mean is better on 69% of 78 province-origin pairs. It isn't better at every origin, so the pre-registered K4 margin is a real test.
- *Caveat:* the data is StatCan's latest revised vintage, not what was known in real time.

---
*Adapted from Statistics Canada, Tables 25-10-0015-01 and 25-10-0016-01 (reference periods 2008-01 to 2026-08), Statistics Canada Open Licence. This does not constitute an endorsement by Statistics Canada.*
