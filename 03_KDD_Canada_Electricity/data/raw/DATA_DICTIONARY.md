# Complete CSV column descriptions

This independent Canada Electricity dataset was adapted from official Statistics Canada data (tables 25-10-0015-01 and 25-10-0016-01).
These 47 descriptors are also available in column_descriptions.csv.

Published metadata that Kaggle API cannot persist as Data Explorer field tooltips is supplied as a separately downloadable dictionary.
Electricity units are megawatt-hours (MWh); availability is not metered customer demand.

## availability_panel.csv

| Column | Type | Description |
|---|---|---|
| month | string | Reference month, ISO YYYY-MM. |
| geography | string | Canada or a province/territory; Canada is an aggregate. |
| generation_mwh | numeric | Published generation in MWh; missing values remain missing. |
| receipts_mwh | numeric | Reported total electricity receipts in MWh. |
| deliveries_mwh | numeric | Reported total electricity deliveries in MWh. |
| availability_mwh | numeric | Published electricity available for use in MWh, not direct customer demand. |
| availability_status | string | Source status code for electricity availability. |
| balance_residual_mwh | numeric | Generation + receipts - deliveries - availability, MWh; missing if inputs missing. |

## backtest_metrics.csv

| Column | Type | Description |
|---|---|---|
| geography | string | Canada or a province/territory; Canada is an aggregate. |
| candidate_pairs | integer | Total historical candidate forecast-target pairs. |
| evaluated_pairs | integer | Count of comparable forecast-target pairs. |
| mae_mwh | numeric | Mean absolute forecast error in MWh. |
| wape_pct | numeric | Weighted absolute percentage error in percent. |

## cross_table_generation_checks.csv

| Column | Type | Description |
|---|---|---|
| month | string | Reference month, ISO YYYY-MM. |
| geography | string | Canada or a province/territory; Canada is an aggregate. |
| generation_table_mwh | numeric | Generation total from Statistics Canada table 25-10-0015-01, MWh. |
| flows_table_mwh | numeric | Generation total from Statistics Canada table 25-10-0016-01, MWh. |
| _merge | string | Pandas merge reconciliation source indicator. |
| difference_mwh | numeric | Generation total difference between the two original tables, MWh. |

## flows_monthly.csv

| Column | Type | Description |
|---|---|---|
| source_table | string | Official Statistics Canada table identifier. |
| month | string | Reference month, ISO YYYY-MM. |
| geography | string | Canada or a province/territory; Canada is an aggregate. |
| geography_id | string | Official Statistics Canada geographic DGUID. |
| flow_component | string | Official generation, receipt, delivery or availability category. |
| flow_mwh | numeric | Published electricity-flow value, MWh. |
| source_status | string | Published Statistics Canada status code; .. unavailable, x suppressed, blank observed. |
| source_vector | string | Original Statistics Canada vector/series identifier. |
| source_coordinate | string | Original Statistics Canada table dimension coordinate. |

## generation_monthly.csv

| Column | Type | Description |
|---|---|---|
| source_table | string | Official Statistics Canada table identifier. |
| month | string | Reference month, ISO YYYY-MM. |
| geography | string | Canada or a province/territory; Canada is an aggregate. |
| geography_id | string | Official Statistics Canada geographic DGUID. |
| producer_class | string | Producer class; categories include overlapping totals. |
| generation_type | string | Electricity generation technology; includes nested totals. |
| generation_mwh | numeric | Published generation in MWh; missing values remain missing. |
| source_status | string | Published Statistics Canada status code; .. unavailable, x suppressed, blank observed. |
| source_vector | string | Original Statistics Canada vector/series identifier. |
| source_coordinate | string | Original Statistics Canada table dimension coordinate. |

## seasonal_naive_backtest.csv

| Column | Type | Description |
|---|---|---|
| forecast_origin | string | Forecast origin at December year-end in ISO YYYY-MM. |
| forecast_horizon_month | integer | Forecast month beyond December origin, 1 through 12. |
| month | string | Reference month, ISO YYYY-MM. |
| geography | string | Canada or a province/territory; Canada is an aggregate. |
| actual_mwh | numeric | Reported revised historical monthly target electricity availability in MWh. |
| actual_status | string | Official status flag for observed availability. |
| seasonal_naive_mwh | numeric | Predicted availability using target from 12 months previously, MWh. |
| usable_prediction | boolean | True when both forecast and actual observed target exist. |
| absolute_error_mwh | numeric | Absolute forecast error in MWh; missing if target or prediction unavailable. |

## Attribution and restrictions

Original statistics are covered by the Statistics Canada Open Licence: https://www.statcan.gc.ca/en/terms-conditions/open-licence
Source tables: https://doi.org/10.25318/2510001501-eng and https://doi.org/10.25318/2510001601-eng.
See SOURCE_NOTICES.md for original-source reproduction and adapted-product attribution. No official endorsement is implied.
