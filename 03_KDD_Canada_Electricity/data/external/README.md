# External data: K3 event catalogue

`event_catalogue.csv` lists public-record events (storms, cold snaps, heat, wildfires, droughts, the COVID-19
lockdown) that could plausibly make a province's monthly electricity data unusual. It is the ground truth for
goal **K3** (anomalies).

- **Compiled before any anomaly mining** (KDD Preprocessing step), from the analyst's knowledge of public
  reporting by the named organisations. Dates are at month level. Its SHA-256 is printed in the notebook's
  Preprocessing section and checked again before K3 is scored, so it can't be edited after seeing the flags.
- **Not verified line by line against primary sources.** Treat the `public_record` column as "where to check",
  not as a citation. Spot-check before publishing.
- `period = discovery` rows (2016-01 → 2024-12) score the K3 acceptance rule; `confirmation` rows (2025-01 →
  2026-08) are used only in the Interpretation step, once the seal is lifted.
- It lists events whether or not they are expected to show up in monthly totals (e.g. a one-day outage may not),
  so recall is expected to be low; precision and lift over the catalogue's base rate are what the rule tests.

## Revision 2 (after critic round 1, before any mining)
- **E32 (Quebec drought) now starts 2023-05**, not 2023-01: 2022 was a strong export year; the low runoff is the
  2023 spring/summer freshet onward.
- **Added E36–E40**: the February 2021 Prairie cold outbreak (AB, SK, MB) and the pre-Christmas 2022 Arctic
  outbreak (AB, SK), suggested by the critic from public memory, not from the data.
- **Drought end dates (E31–E33) are truncations, not endings:** the droughts were still ongoing at the end of the
  discovery window (2024-12), so the entries stop at the window edge.
- **Event classes in scope:** weather/climate, wildfire, pandemic. **Out of scope:** plant outages and
  refurbishments (e.g. Point Lepreau, Ontario nuclear), commissioning (Muskrat Falls, Keeyask, Site C) and industrial
  closures (Northern Pulp, NS, 2020): structural, or not datable to the month from public memory.
- The hash in `config.K3_CATALOGUE_SHA256` was updated with this revision. The first version's hash
  (`db90cb67…`) is recorded in `critiques/kdd_steps1-3_round1.md`.
