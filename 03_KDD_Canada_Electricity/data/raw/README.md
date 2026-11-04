# Canadian Electricity Generation, Trade and Availability | 2008-2026

Publisher of original tables: Statistics Canada. Independent benchmark adaptation by Habib Gultekin (@hgultekin). No Statistics Canada endorsement is implied.

LICENSE: Original Statistics Canada data are available under the Statistics Canada Open Licence, NOT CC0. Source and adaptation notices are included in SOURCE_NOTICES.md. https://www.statcan.gc.ca/en/terms-conditions/open-licence

SOURCE TABLES:
- 25-10-0015-01 (monthly electricity generation): https://doi.org/10.25318/2510001501-eng
- 25-10-0016-01 (monthly electricity receipts, deliveries and availability): https://doi.org/10.25318/2510001601-eng

CONTENT:
- generation_monthly.csv: 76,776 observations with source identifiers and preserved status codes.
- flows_monthly.csv: 37,888 observations with source identifiers and preserved status codes.
- availability_panel.csv: 3,136 geography-month panels for generation, receipts, deliveries and availability.
- cross_table_generation_checks.csv: 3,136 matching generation totals, all exactly equal across official tables.
- seasonal_naive_backtest.csv: 1,176 annual-lag baseline forecasts across 7 historical forecast origins.
- backtest_metrics.csv: per-geography MAE and WAPE.
- data_quality.json: missing values, anomalies and accounting checks.
- provenance.json: official source ZIP and metadata SHA-256 hashes, source links, build date and source periods.
- SOURCE_NOTICES.md: legally required reproduction and adaptation notices.
- DATA_DICTIONARY.md: source-status and column meanings.

NOTES:
- Time coverage is January 2008 through August 2026, in monthly frequency. Unit is megawatt-hours (MWh).
- Availability is NOT direct metered customer demand.
- Canada is an aggregate; do not add Canada to provinces.
- Subtypes and producer total categories may overlap; do not sum nested subtotals.
- No missing or suppressed observations have been replaced with made-up values.
- Published February 2019 balance residuals for Canada and BC are +70,931 MWh; original source values are retained and flagged.
- All historical observations came from the latest revised data version, so the annual-lag baseline is NOT a real-time-vintage backtest.
- Survey coverage and source historical figures may be revised; check official source tables for latest corrections.

CITATION:
Statistics Canada, Table 25-10-0015-01 and Table 25-10-0016-01; adapted by Habib Gultekin (2026), Canadian Electricity Generation, Trade and Availability. See SOURCE_NOTICES.md for the exact legal notices.

The original information remains under Statistics Canada's rights and licence. This derived dataset is independent and is not endorsed by Statistics Canada.


## Column-level data dictionary (v3)
The column_descriptions.csv file provides all 47 column names, field types and independent definitions; DATA_DICTIONARY.md has the same in readable tables. This is required because Kaggle's metadata API does not currently persist web-editor column descriptions (see Kaggle/kaggle-cli issue #1207). All six original CSV data files remain unchanged.
