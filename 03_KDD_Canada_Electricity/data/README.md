# Data: Canada Electricity, Generation and Trade (2008-01 to 2026-08)

| Item | Value |
|---|---|
| Source | Kaggle: [Canada Electricity: Generation and Trade](https://www.kaggle.com/datasets/hgultekin/canada-monthly-electricity-benchmark) by Habib Gultekin (hgultekin), last updated 2026-11-01 |
| Original | Statistics Canada, Table 25-10-0015-01 (monthly generation by type) and Table 25-10-0016-01 (receipts, deliveries, availability). Real official statistics |
| Licence | **Statistics Canada Open Licence** (not CC0). Required notices are in `raw/SOURCE_NOTICES.md`. Adapted from Statistics Canada; this does not constitute an endorsement by Statistics Canada |
| Files (`raw/`) | `generation_monthly.csv` (76,776 rows), `flows_monthly.csv` (37,888), `availability_panel.csv` (3,136), `seasonal_naive_backtest.csv`, `backtest_metrics.csv`, `cross_table_generation_checks.csv`, `data_quality.json`, `provenance.json` (source hashes), `DATA_DICTIONARY.md`, `column_descriptions.csv`, `README.md`, `SOURCE_NOTICES.md` |
| Units | MWh, monthly. `Canada` is an aggregate (not to be added to provinces). Status codes: `..` unavailable, `x` suppressed (kept as missing) |
