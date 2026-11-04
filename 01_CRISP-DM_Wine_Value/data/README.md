# Data: Wine Reviews (WineEnthusiast)

| Item | Value |
|---|---|
| File | `raw/winemag-data-130k-v2.csv.gz` (gzip of the original `winemag-data-130k-v2.csv`; 129,971 rows × 13 columns + row index) |
| Source | Kaggle: [Wine Reviews](https://www.kaggle.com/datasets/zynicide/wine-reviews) by Zack Thoutt (zackthoutt), last updated 2017-11-27 |
| Origin | Scraped from WineEnthusiast (winemag.com) during the week of 2017-06-15. Real reviews |
| Licence | **CC BY-NC-SA 4.0**. Attribution required, non-commercial, share-alike. Derived outputs in this project are shared under the same licence |
| SHA-256 (uncompressed CSV) | `52af2643c8ac29f010f0cc629dfbdda1c74aa0f332d11762af9ef3de4e567ac9` |
| Grain | One row per published review |
| Not used | `winemag-data_first150k.csv` (older scrape without critic names) and `winemag-data-130k-v2.json` (same content as the CSV) |

`raw/` is never modified. Everything derived from it is written to `processed/`.

## Columns
| Column | Meaning |
|---|---|
| *(index)* → `review_id` | Scraper row number, kept for traceability |
| `country`, `province`, `region_1`, `region_2` | Origin, from broad to specific |
| `description` | The critic's tasting note (free text) |
| `designation` | Vineyard or cuvée name |
| `points` | WineEnthusiast score, 80–100 (only wines scoring 80+ are published) |
| `price` | Bottle price in USD at review time |
| `taster_name`, `taster_twitter_handle` | Critic who wrote the review |
| `title` | Wine name. Usually contains the vintage year |
| `variety` | Grape(s) |
| `winery` | Producer |
