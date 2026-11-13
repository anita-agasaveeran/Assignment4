# Source notices: Statistics Canada Open Licence

This dashboard, its `artifacts/`, and every figure and table in this project are derived from:

- **Statistics Canada. Table 25-10-0015-01**, *Electric power generation, monthly generation by type of electricity*
  (reference periods 2008-01 to 2026-08). DOI: https://doi.org/10.25318/2510001501-eng
- **Statistics Canada. Table 25-10-0016-01**, *Electric power generation, monthly receipts, deliveries and
  availability* (reference periods 2008-01 to 2026-08). DOI: https://doi.org/10.25318/2510001601-eng

obtained through the Kaggle dataset *Canada Electricity: Generation and Trade* by Habib Gultekin
(https://www.kaggle.com/datasets/hgultekin/canada-monthly-electricity-benchmark), which redistributes the tables
under the same licence (its own notice is kept in `../data/raw/SOURCE_NOTICES.md`).

**Required attribution:** Adapted from Statistics Canada, Tables 25-10-0015-01 and 25-10-0016-01. This does not
constitute an endorsement by Statistics Canada of this product.

**Licence:** Statistics Canada Open Licence, https://www.statcan.gc.ca/en/terms-conditions/open-licence

**What was changed ("adapted"):** the Canada aggregate is excluded from analysis; status-coded cells are treated
as missing; series a geography never publishes are set to zero (structural zeros); shares, trade ratios, seasonal
decompositions, clusters, change points, anomaly scores and forecasts are derived by this project. None of these
derived results are official Statistics Canada statistics.

**Other inputs:** `../data/external/event_catalogue.csv` is the project's own list of public-record events (storms,
cold snaps, wildfires, droughts), compiled by the analyst. It is not Statistics Canada data.
