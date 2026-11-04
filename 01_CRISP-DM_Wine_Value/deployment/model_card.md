# Model Card: Wine Score Estimator & Value Shortlist

> Status: scaffold. Completed in Phase 6.

- **Intended use:** rank unscored candidate wines for sampling; provisional score bands for merchandising. Not a replacement for tasting or for critic reviews.
- **Inputs:** tasting note, country/province, grape, vintage. **Not** price (avoids a circular value verdict) and **not** critic identity.
- **Training data:** WineEnthusiast reviews (scraped June 2017), development critic folds + anonymous reviews.
- **Evaluation:** lockbox critics (Anne Krebiehl MW, Jeff Jenssen, Kerin O'Keefe, Sean P. Sullivan), scored once in Phase 5. _TODO results_
- **Limitations:** trained on professional critic notes (style may differ from retailer notes); 2017 prices; only 80+ wines in the data; critic bias.
- **Licence:** CC BY-NC-SA 4.0 (derived from the dataset). Non-commercial.
