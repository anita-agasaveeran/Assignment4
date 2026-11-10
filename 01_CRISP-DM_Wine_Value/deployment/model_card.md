# Model Card: Wine Value Finder (shortlist ranker, score band, profiles)

*Version: the Phase 4 model selections frozen in commit `8632fba`, evaluated on the lockbox with the Phase 5 code frozen in `a140a70` (results and amendments in tag `wine-phase5-rev4`). Deployment tool and pilot protocol: Phase 6 revision 7, to be tagged `wine-phase6-rev7` before any pilot data (not yet committed). Artifact: `models/value_finder.joblib`; SHA-1 in `models/manifest.json`. Report: `reports/final_report.md` §5–6.*

## Intended use
- **Users:** the buying team of an online wine retailer (hypothetical stakeholder, report §1.2). Internal use only.
- **Primary use (BO1):** in each buying round, rank about 1,000 unscored ≤ $25 candidates so that the ~100 wines sampled are more likely to score 90+ later.
- **Secondary use (BO2):** an *estimated* score band for planning until a real review arrives. It is shown only while the pilot gate and stop rule allow.
- **Not intended for:**
  - showing estimates to customers as points (R10);
  - wines above $25 (the shortlist and verdict apply only at ≤ $25);
  - judging a wine without tasting it;
  - comparing critics or writers.

## Inputs and outputs
- **Inputs:**
  - the tasting note;
  - country, province, grape label and vintage;
  - designation and sub-region flags;
  - price (shortlist ranker only), converted to 2017 dollars with a deflator set before the pilot;
  - winery (for the "winery track record" simple rule that the shortlist is compared with, for clustering, and to strip the winery name from the title before reading colour and vintage).
- **Name matching:** country, province, grape, region and winery names that are not exactly as in training are matched to the training spelling (case, spaces, accents, punctuation, a few country aliases) before scoring (a winery differing only in letter case is matched as its exact spelling would be, except for the 24 training wineries spelled two ways in case only, whose variants go to the more frequent spelling; accent and punctuation variants of a winery only within its country); a country the training data never saw is flagged per row and counted, and the share of wineries it never saw is reported per round.
- **Excluded:**
  - critic identity (R-2);
  - price from the score band and the value verdict, so "quality vs price" isn't circular.
- **Outputs:** shortlist rank and round tier, estimated score band (±2.67), value verdict, P(90+) (a relative indicator), flavour profile, 5 similar reviewed wines.

## Training data
- **Source:** 100,530 WineEnthusiast reviews (scraped June 2017; Kaggle, CC BY-NC-SA 4.0), after the Phase 3 cleaning.
- **Excluded:** four critics (Krebiehl, Jenssen, O'Keefe, Sullivan) were held out as a lockbox and never used for training.
- **Price filter:** only 80+ point wines are published. Prices are 2017 US dollars.

## Evaluation (lockbox: four unseen critics, scored once; report §5.1)
| Output | Result | Pre-registered target |
|---|---|---|
| Shortlist precision@100 (cycles of 1,000) | **0.761**, against 0.39 for the best simple rule (1.95×, LB 1.76) | ≥ 0.55 and ≥ 1.4×, LB ≥ 1.2 ✅ |
| Score: MAE reduction vs variety × country | **31.5%** (LB 30.2%) | ≥ 10%, LB > 5% ✅ |
| Score band: within ±2 at ≤ $25 | **0.736**, +7.5 pp over the baseline (LB +6.4) | ≥ 0.60, ≥ +5 pp, LB > 0 ✅ |
| Score band on masked notes (stand-in for retailer notes) | +2.7 pp (LB +1.6) | below the +5 pp target ⚠️ |
| P(90+) | Brier 0.126 vs 0.169 for the base rate; mean 0.32 against an actual rate of 0.22 | over-predicts by 10 pp ⚠️ |
| Flavour profiles | 8 profiles, each named by both blind reviewers (thin margin) | ✅ |
| Value verdict (defined in Phase 6, not pre-registered) | Value rate by tier on the lockbox: Likely 0.88, Probable 0.52, Long shot 0.14, Unlikely 0.02, against a base rate of 0.22 (development folds: 0.85–1.00 / 0.55–0.74 / 0.19–0.36 / 0.01–0.07) | – |
| Shortlist percentile label (one-wine view) | 30% of lockbox ≤ $25 candidates score above the development 90th percentile (6–20% per development fold), so the round view ranks within the round instead | ⚠️ |
| BSC4: one screen, < 3 s per query | All outputs on one screen; about 0.03 s per query (median, notebook 6.1c) | ✅ |

**Simulated pilots** (masked notes, the stand-in for retailer notes; rates move by up to 0.10 between random seeds, report §6.1):
- **Phase 5, the gate alone on 400 wines** (report §5.3): the shortlist passes its part 67–99.5% of the time, depending on the writer mix; the band passes 24% of the time in the lockbox's masked mixed pool.
- **Phase 6, the whole protocol** (report §6.1; checks, pause, source minimum, stop rule, decision): on the lockbox's masked mixed pool the shortlist is deployed in 97.5% of pilots and the band shown in 16%. Pilots from development pools with only one or two writers never reach a decision and stop with nothing deployed.

## Known limitations
- **Writer level.**
  - The band's accuracy depends on how the writer's scores sit relative to the training critics. For one lockbox writer (O'Keefe, all of the lockbox's Italian wines) the ±2 gain was only +1.4 pp.
  - Another writer (Jenssen) was predicted worse than the baseline (−26%).
  - The stop rule exists for this reason.
- **Note source.** The model was trained on critic notes. Retailer, importer and producer notes may phrase verdicts differently or praise more. Masking verdict words is only a stand-in, and the pilot is the first real test.
- **Price and time.** All prices and scores are from 2017 or earlier. Prices are converted to 2017 dollars with a CPI-U deflator fixed before the pilot (report §6.1), so inflation does not move wines across the $25 bar, but a wrong or missing deflator would; the app shows the converted price. Styles and vocabulary drift, and only the drift checks watch for that.
- **Data selection.** Only wines that scored 80+ were published, so the model has not seen poor wines.
- **Flavour profiles barely reproduce across writers** (critic-disjoint Jaccard 0.23 against a chance level of 0.17).
- **Similar wines** are similar notes (TF-IDF cosine within the same colour), not similar tastes.
- **Licence:** the review data's NC licence does not allow a retailer's commercial use; a real deployment needs a licence or a retrain on licensed data.

## Ethical and legal considerations
- **Licence:** derived from CC BY-NC-SA 4.0 data. Non-commercial use only; share-alike.
- **Scores:** estimated scores must not be presented as WineEnthusiast ratings (R10).
- **Bias:** the model inherits each critic's biases, for example region specialisation and writer level, and it can favour wines described in the training critics' style.

## Maintenance
See `monitoring_plan.md`. No automatic retraining. A new version must pass the same pre-registered gate on new data before it replaces this one.
