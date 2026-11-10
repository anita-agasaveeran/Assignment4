# Deployment: Wine Value Finder (CRISP-DM Phase 6)

An **internal pilot tool** for a retailer's buying team (report §5.3, option F; §6.1). Customers never see its output.

| File | Purpose |
|---|---|
| `app.py` | Streamlit app with two views. **One wine** is the BSC4 screen: estimated score band, P(90+), value verdict, flavour profile, 5 similar wines. **Shortlist a buying round** uploads a CSV and returns the ranked ≤ $25 shortlist. |
| `score.py` | Batch scoring for one buying round, from the command line, with data-quality flags and the round's monitoring report (`<out>.monitoring.json`) |
| `pilot_eval.py` | Pilot evaluation: the stop-rule and futility checks every 100 scores, the decision point, the final per-output gate, the Option F decision, `band_status.json` |
| `build_artifact.py` | Rebuilds `../models/value_finder.joblib` and writes its manifest only if it reproduces every saved lockbox prediction (about 4 minutes) |
| `band_status.json` | *(written by `pilot_eval.py --update-status`; absent = band shown everywhere)* Note sources, member sources of a withdrawn pooled unit, and countries whose score band the stop rule withdrew. The app, `score.py` and the protocol all read it through `pilot.band_hidden` |
| `model_card.md` | Intended use, data, lockbox results, limitations, licence |
| `monitoring_plan.md` | What is monitored during and after the pilot, thresholds, actions, retraining policy |
| `requirements.txt` | Runtime dependencies for the app |
| `../models/value_finder.joblib` | The fitted models (4 MB); `../models/manifest.json` holds its SHA-1 and the lockbox reproduction check |

## The models
These are the frozen Phase 4 selections, refitted on all 100,530 development reviews exactly as in the Phase 5 lockbox run (`winevalue.production.build`). They are **not** refitted on the lockbox critics: that would be an untested model (§5.3 condition 1). Notebook 6.1b checks the artifact against `reports/tables/phase5_lockbox_predictions.csv.gz` row by row (largest difference 0.0).

| Output | Model | Shown as |
|---|---|---|
| Shortlist (BO1) | Ridge on TF-IDF of the note, plus origin, grape, vintage and log price | Rank in the buying round; round tier (top 10% / top 20% of this round). The one-wine view shows a development percentile, with a caveat |
| Score band (BO2) | Calibrated ridge, price-free: points = 7.957 + 0.917 × ridge score, ± 2.67 | "Estimated 85–90", internal only; hidden where the stop rule fired |
| Value verdict | The price-free estimate against the 90-point / $25 bar (R-2) | Likely / Probable / Long shot / Unlikely, with the base rate; hidden with the band |
| P(90+) | Logistic map of the ranker's out-of-fold score | A relative indicator (it over-predicted by 10 pp on the lockbox) |
| Flavour profile | Lexicon NMF, k = 8 | Both blind reviewers' names for the profile |
| 5 similar wines | TF-IDF cosine over the 118,378 reviewed notes, same colour | Title, critic score, price; DM5 near-duplicate flag (Jaccard ≥ 0.5) |

## Run locally
```bash
# from the repository root, with requirements installed
streamlit run 01_CRISP-DM_Wine_Value/deployment/app.py
python 01_CRISP-DM_Wine_Value/deployment/score.py candidates.csv -o scored.csv --round 1   # buying round number; 0 for a test file
python 01_CRISP-DM_Wine_Value/deployment/pilot_eval.py pilot_scored.csv --out 01_CRISP-DM_Wine_Value/reports/pilot --update-status
```
On first start the app builds the prepared table from `data/raw/` (about 2 minutes) and the similarity index (about 2 seconds). The app and scripts **refuse** to serve the models unless `models/manifest.json` records a passed lockbox reproduction and the file's SHA-1 matches. They never refit on their own: after a scikit-learn upgrade, or if the file is lost, run `python 01_CRISP-DM_Wine_Value/deployment/build_artifact.py`.

**Candidate CSV columns** (a file without the required ones is refused):
- **Required:** `note` (or `description`), `country`, `variety`, `price`.
- **Optional:** `province`, `vintage` (else parsed from `title`), `title`, `winery`, `designation`, `region_1`, `source` (the note's writer, importer or producer), `wine_id`.

**Pilot CSV:** the same columns, plus `points` (the critic score, once it arrives), `source` (required: a row without one, or with a placeholder such as "unknown", "N/A" or "-", never counts toward the source minimum), `order` (1 = first score to arrive), `scorer` (who published the score; only WineEnthusiast scores, including "Wine Enthusiast Magazine" and "winemag", enter the gate, others are a sensitivity), `sampled` (true if the team sampled or listed the wine; the gate on unsampled wines is a sensitivity) and `shortlist used` (true if that round's samples were picked with the shortlist; for the business KPI). Keep `score.py`'s `price deflator` column: `pilot_eval.py` refuses a file scored with a deflator other than `config.PRICE_DEFLATOR`, or without the column (unless you pass `--deflator-confirmed`).

**Inputs are normalised before scoring:** country, province, grape, region and winery names that are not an exact training spelling are mapped to one (case, spaces, apostrophes, accents, punctuation, and aliases such as USA → US; grape names the grape lexicon knows are matched too; a winery differing only in letter case is the training spelling it equals, as its exact spelling would be; accent and punctuation variants of a winery only within its country); a country the models never saw is flagged per row and counted in the round's drift report, and so is the share of wineries the training data never saw (the shortlist's comparator knows only those). Prices are converted to 2017 dollars with `config.PRICE_DEFLATOR`, which is set from CPI-U before round 1 (report §6.1, prerequisites) and recorded in every monitoring report; `score.py` writes the converted `price (2017 $)` and the app shows it.

## Pilot workflow (frozen in `config.PILOT_*` and `winevalue.pilot` before any pilot data)
1. **Log every round:** score the **whole candidate file** of every buying round (every candidate, at any price; the ≤ $25 test is applied after the price deflator, so never filter at $25 first) with `score.py --round N` before anyone tastes it, all rounds into one folder (the self-referenced drift rule compares each round with the earlier ones there, by round number; a re-scored round replaces its earlier report; if a round raised that rule's alert and the drop is real, set `"accepted": true` in its `.monitoring.json` so later rounds can use it as a reference), keep the scored file and its `.monitoring.json`, and record each note's source. Buyers may use the shortlist as usual. A candidate becomes a pilot wine when a published critic score for it is matched to it (report §6.1, "Outcome data and schedule"); the pilot wines are therefore chosen by critics, not by the model. The app's shortlist view is for browsing and keeps no files.
   - **Round 1 source check (no scores needed):** if fewer than 3 named note sources each supply at least 15% of the round's ≤ $25 candidates (re-checked on the first 100 scored wines), the pilot can't reach its source minimum; fix the note sourcing before round 2 (assumption A11).
2. **Check as scores arrive:** run `pilot_eval.py --update-status` after every 100 scores (report §6.1 has where the scores come from, how they are matched, and the schedule).
   - **Score band:** a note source (or a country, or the whole pilot) loses it once it has 50 or more scored wines and the 80% winery-bootstrap CI of its mean error lies wholly outside ±1.0 point. Small sources are pooled into one unit.
   - **Shortlist:** the pilot pauses if, from 200 wines on, the shortlist's top-20% lift falls below 1.0.
3. **Final gate, at the decision point** (the first check with ≥ 400 wines and ≥ 3 sources with ≥ 50 wines each; at most 800 wines), on all wines up to it:
   - The shortlist deploys if its top-20% lift is at least 1.3× the best simple rule, with LB > 1.0. If fewer than 50% of the wines used have a winery from the training data, it must also pass on those matched wines alone, at least 100 of them (`gate.json` reports the coverage and the result after this rule; `sensitivity.json` the matched-winery gate). Before the decision point both flags are blank and the console says "interim reading".
   - The band is shown internally only if the ±2 gain is at least +5 pp, with LB > 0. It is shown only next to a deployed shortlist.
   - The joint pre-registered gate is always reported.
4. **Secondary analysis (reported only):** each source's intercept, fitted on its first 50 wines and applied to its later wines.

## Deploy to Streamlit Community Cloud (course demonstration only)
A real buying team would run the app locally or on a private, authenticated host, and would first need a commercial licence for the review data (report §6.1, prerequisites).
1. Make the GitHub repository public, or connect a private one in Streamlit Cloud.
2. At share.streamlit.io, choose **New app**: repository `anita-agasaveeran/Assignment4`, branch `main`, main file `01_CRISP-DM_Wine_Value/deployment/app.py`.
3. Under **Advanced settings**, choose Python 3.12. Streamlit Cloud installs `deployment/requirements.txt`, the file next to the app. It pins scikit-learn to the version that saved the model file.
4. The first start takes a few minutes, because it builds the prepared table from the raw file. The model artifact is in the repository.

The app has no login. Keep the link internal, as the band and verdict are not for customers (R10).
