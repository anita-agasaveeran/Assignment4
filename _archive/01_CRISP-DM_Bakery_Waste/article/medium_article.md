# _TODO title, e.g. "Baking Less, Selling More: A CRISP-DM Walkthrough on Bakery Waste"_

*Subtitle: _TODO_ · ~10–12 min read · Code: [GitHub](https://github.com/anita-agasaveeran/Assignment4/tree/main/01_CRISP-DM_Bakery_Waste) · [Colab](TODO) · [Video](TODO)*

> Status: outline. Written after the notebook is finished. The draft goes through critic rounds too (see `critiques/`).

## Outline
1. **Hook:** about a quarter of what this bakery bakes is thrown away. What would it take to fix that with data?
2. **Why CRISP-DM:** the six phases at a glance, and why business understanding and deployment matter (most published projects skip deployment; Schröer et al., 2021).
3. **Phase 1, Business Understanding:** objectives, success criteria, cost of waste vs stockout.
4. **Phase 2, Data Understanding:** the most interesting EDA findings (weekends, festivals, baskets), the data quality checks, and what's suspicious about the data.
5. **Phase 3, Data Preparation:** why we aggregate to store × category × day, the features, and the outlier handling.
6. **Phase 4, Modeling:** baseline vs models, the newsvendor idea in plain language, basket rules, customer segments.
7. **Phase 5, Evaluation:** the backtest of waste, fill rate and profit against the business targets.
8. **Phase 6, Deployment:** the Production Planner app, monitoring and retraining.
9. **Lessons learned & limitations**
10. **Resources & references**

## Figures to include
- _TODO (pick 5–7 from reports/figures/)_
