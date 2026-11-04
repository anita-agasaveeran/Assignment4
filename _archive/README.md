# Archive

## `01_CRISP-DM_Bakery_Waste/`: abandoned first dataset for the CRISP-DM project

The CRISP-DM project started on a bakery sales dataset ([Kaggle: sdcloud, CC0](https://www.kaggle.com/datasets/sdcloud/historical-bakery-sales-dataset)). Two critic rounds on Phase 1 (Business Understanding) found that the dataset couldn't support the business goal:

- The production and waste fields are generated per order line (ordered quantity + at least 1 unit), so they aren't real production records (round 1, 5/10).
- The publisher confirms the data is synthetic. Volumes are tiny (about 9 orders a day for the whole chain), so the best simple policy is to bake nothing, and the value any forecast could add is only about ₹3–13k per quarter (round 2, 7/10).

On 2026-11-03 the project switched to the real **Wine Reviews** dataset (`../01_CRISP-DM_Wine_Value/`). The bakery folder stays here as a record of CRISP-DM's Business Understanding ↔ Data Understanding loop catching an unsuitable dataset early. See its `critiques/` folder for the full reviews.
