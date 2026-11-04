# The $20 Bottle That Drinks Like $60: Finding Value Wines with CRISP-DM

*Subtitle: _TODO_ · ~10–12 min read · Code: [GitHub](https://github.com/anita-agasaveeran/Assignment4/tree/main/01_CRISP-DM_Wine_Value) · [Colab](TODO) · [Video](TODO)*

> Status: outline. Written after the notebook is finished. The draft goes through critic rounds too (see `critiques/`).

## Outline
1. **Hook:** half of wines cost $25 or less, and 1 in 6 of those score 90+. Can you tell which from the label and a few sentences?
2. **Why CRISP-DM:** six phases; why Business Understanding and Deployment matter (most published projects skip deployment; Schröer et al., 2021). A short aside on the pivot from an unsuitable first dataset, as an example of CRISP-DM's feedback loop.
3. **Business Understanding:** the buying-team problem, success criteria, and the "lockbox critics" test that mimics new writers.
4. **Data Understanding:** price vs score, duplicates, critic bias ("your 90 isn't my 90").
5. **Data Preparation:** fold-safe dedup, text features, why price and critic are excluded.
6. **Modeling:** baselines vs text models; what words signal a 90-point wine; flavour profiles; descriptor–grape rules; LSH for near-duplicates.
7. **Evaluation:** one shot at the lockbox; shortlist precision vs simple rules; the sampling saving.
8. **Deployment:** the Value Finder app; monitoring; the pilot recommendation.
9. **Limitations & lessons**
10. **Resources & references**
