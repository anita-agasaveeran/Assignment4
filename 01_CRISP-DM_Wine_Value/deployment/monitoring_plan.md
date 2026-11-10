# Monitoring & Maintenance Plan (CRISP-DM 6.2)

*Applies to `models/value_finder.joblib` (SHA-1 in `models/manifest.json`). Thresholds are fixed before any pilot data (report §6.2) and live in `config.MONITOR_ALERTS`. Sections 1–2 run in code on every scored round (`winevalue.monitoring.round_report`, called by `deployment/score.py` and the app's shortlist view). Reference values and false-alert rates come from notebook 6.2a (`reports/tables/phase6_monitoring_reference.csv`, `phase6_alert_rates.csv`).*

The model needs an outcome, a critic score, to be judged, and that arrives weeks or months after a wine is shortlisted. So monitoring has two layers:
- **Leading checks** on the inputs, every buying round, with no outcomes needed.
- **Lagging checks** on outcomes, as scores arrive. During the pilot these are exactly the pilot protocol (`winevalue.pilot`). After deployment the same rules run on a rolling window.

## 1. Data quality (every load; blocks scoring)
| Check | Rule | Action |
|---|---|---|
| Schema | `note`/`description`, `country`, `variety` and `price` columns present (`price` may be empty) | Reject the file and report the missing columns |
| Empty or very short notes | Note under 10 words after leak stripping | Score the row but flag it: "too short to rank reliably" |
| Missing price | `price` empty | No shortlist rank or verdict; the band is still estimated |
| Duplicates | The same note twice in a round, or a near-duplicate of another candidate (DM5, Jaccard ≥ 0.5); near-duplicates of reviewed notes are flagged in the one-wine view | Flag the later row; the analyst keeps one |
| Scores or prices written in the note | Removed by `strip_leaks` (Phase 3) | Flagged per row; count in the round report |
| Origin, grape and winery spellings | Country, province, grape, region and winery values that are not an exact training spelling are mapped to one (case, spaces, apostrophes, accents, punctuation; aliases such as USA → US; grape-lexicon names) before scoring (`production.canonical_inputs`) | The count of mapped values per column is in the round report |
| Country unseen in training | After mapping, the country is not one of the 41 development countries | Score the row (as unknown origin) but flag it; counted in §2 |
| Price basis | Every price is multiplied by `config.PRICE_DEFLATOR` (2017 dollars; set from CPI-U before round 1) | The deflator is recorded in each round report and written per row by `score.py`; `pilot_eval.py` refuses a pilot file scored with a different deflator |

## 2. Input drift (every buying round; leading)
Measured on the round's candidates and compared with the references from notebook 6.2a: development rows for the training data (in-sample for vocabulary, P(90+) and the percentile share), and the lockbox for four unseen writers (the only out-of-sample reference).

| Indicator | Development | Lockbox (new writers) | Alert if a round is | Why it matters |
|---|---|---|---|---|
| Share of note words outside the model vocabulary | 0.7% | 0.9% | **above 3%** | Unfamiliar vocabulary, for example another language or a house style. The text models lose signal |
| Median note length (words) | 40 | 38 | **below 20 or above 80** | Length is a model input; retailer blurbs may be much shorter |
| Unmapped colour | 1.3% | 2.6% | **above 5%** | Unknown grape labels |
| Grapes rare or unseen in training | 2.0% | 4.0% | **above 8%** | New grapes get no grape effect |
| Countries unseen in training | 0% (by definition) | 0.4% | **above 2%** | An unseen country is scored as unknown origin, which moved estimates by about a point in critic round 3's test |
| ≤ $25 share of candidates | 48% | 41% | **below 25% or above 95%** (re-centred at rollout step 1 if the retailer's pre-tool share lies outside 35–60%: share − 0.20 to share + 0.45, `monitoring.share_band`) | Below: prices outside the 2017 basis (a wrong or missing deflator) move wines across the $25 bar. Above: the file looks pre-filtered at $25, so the deflator could not restore wines that are ≤ $25 in 2017 dollars; the candidate file must be every candidate of the round (§1) |
| Mean P(90+) on ≤ $25 candidates | 0.21 | 0.32 | **above 0.40, or below the limit for the round's size** (table below) | The ranker's level drifts; P(90+) is already 10 pp high on new writers |
| ≤ $25 candidates above the development 90th percentile | 17.4% (in-sample; 6–20% per fold out of fold) | 30.1% | **above 40%, or below the limit for the round's size** | The same level drift, in the units the one-wine label uses |
| Wineries unseen in training | 0% (by definition) | 27.4% | reported, no alert; the pilot gate has its own coverage rule (§3) | The shortlist's comparator ("winery track record") knows only training wineries |

**Lower limits of the two ranker alerts, by the round's number of ≤ $25 candidates** (`config.MONITOR_RANKER_LOWER`; a round uses the row for the largest size it reaches; below 200 the two alerts are not read):

| ≤ $25 candidates in the round | 200–299 | 300–599 | 600–999 | 1,000+ |
|---|---|---|---|---|
| Mean P(90+) below | 0.06 | 0.07 | 0.07 | 0.08 |
| Share above the development P90 below | 1% | 2% | 3% | 3% |

An A7 round holds about 1,000 ≤ $25 candidates (about 2,400 candidates in all), so it uses the 1,000+ row; smaller rows apply to smaller retailers or partial rounds. Below 200 only the upper limits are read.

**Self-referenced rule** (`config.MONITOR_RELATIVE_*`, `monitoring.relative_alerts`; runs only in `score.py`, which reads the earlier rounds' reports in the output folder by round number, `--round N`, one per round): from the 4th round on, alert if the share above the development P90 falls below half its median over the previous 3 reference rounds. **A round that raised this alert is not a reference round** until the analyst checks it and sets `"accepted": true` in its `.monitoring.json` (a real change in the writer mix, say), so a fault that persists alerts every round rather than becoming its own reference. The 0.5 drop and the 3 rounds are judgement calls; the rule sees a fall to about half the feed's own level or more, not milder ones. The fixed lower limits sit at the lowest development fold's level, so they can't see a feed fall from its own, higher level (the lockbox's 30% falling to 4–11% when notes are truncated); this rule can. It is read only in rounds with at least 600 ≤ $25 candidates, the smallest size from which its false-alert rate on consecutive out-of-fold development rounds is at most 2% in every fold (`monitoring.choose_relative_min_pool`). A real change in the writer mix also sets it off; the analyst checks which before acting.

The upper alert levels are set beyond the lockbox value (about 2× for unmapped colour and unseen grapes, over 3× for vocabulary). They are judgement calls, not tested rules. On 500 simulated A7 rounds (about 1,000 ≤ $25 candidates: 2,067 candidates drawn from the development rows, 2,442 from the lockbox), none fired, the self-referenced rule included (notebook 6.2a, `phase6_alert_rates.csv`): they would not have flagged the lockbox's writers either. They are for a feed that breaks; a writer's level is caught by the outcome checks in §3.

The two ranker-level alerts fire on a fall as well as a rise. Their **lower limits follow a stated rule, per round size** (`monitoring.choose_lower_limit_table`): the 1st percentile of 500 winery-clustered rounds of out-of-fold development candidates, in the lowest fold, rounded down, for rounds of 200, 300, 600 and 1,000 ≤ $25 candidates (table above). On those rounds ranker alerts fire in at most 1.4% of rounds per fold and size (none at 1,000); on a fresh seed in at most 2.4% (0.2% at 1,000); with each fold left out of the rule, in 0–0.2% of the left-out fold's rounds (`phase6_alert_rates_oof.csv`, `phase6_alert_limits_lofo.csv`). Detection on deliberately broken copies of the lockbox pool (`phase6_alert_detection.csv`, 200 A7 rounds of 2,442 candidates each, about 1,000 of them ≤ $25, after three rounds of the unaltered feed; report §6.2):
- **caught in 99–100% of rounds:** notes cut to 30, 25 or 15 words (30 and 25 by the self-referenced rule only; the fixed lower limits catch 25 words in 1.5% of rounds); 5% or more of note words unknown; prices × 1.3 or more; 10% of grapes unlisted; 5% of countries unrecognised; a promotional sentence on every note; a file pre-filtered at $25;
- **missed or rarely caught:** notes cut to 35 or 40 words (0%: the share above the P90 falls by a third or less; added in revision 7 as a test the rule was not designed against), 2% unknown words (1.5%: the vocabulary share sits just under its 3% limit), prices × 1.1 (0%); truncation in rounds 1–3 or in rounds under 600 ≤ $25 candidates, where only the fixed limits are read;
- **no change, as it should be:** countries upper-case or written as an alias (USA): every indicator equals the unaltered pool's.

Mild faults still move the shortlist's inputs, so the analyst reads the round's indicator values in the monitoring JSON, not just the alerts. An alert does not stop scoring. It is reviewed by the analyst within the round and logged with the round's file.

## 3. Outcomes (as critic scores arrive; lagging)
**During the pilot** (≥ 400 ≤ $25 notes, from at least 3 named sources with 50 or more scored wines each; WineEnthusiast scores only, `config.PILOT_PRIMARY_SCORER` and its aliases), these are run by `deployment/pilot_eval.py` after every 100 scores:

| Check | Rule (`config.PILOT_*`) | Action |
|---|---|---|
| Score band, per note source, per country, pooled small sources, whole pilot | Every 100 scores, once a unit has ≥ 50 scored wines: 80% winery-bootstrap CI of the mean error (estimate − score) wholly outside ±1.0 | Hide the band and the verdict for that unit, for the rest of the pilot (`band_status.json`, read by `pilot.band_hidden`) |
| Shortlist futility | From 200 scored wines: top-20% lift against the best simple rule < 1.0 | Pause the pilot and report |
| Final gate, at the decision point (first check with ≥ 400 wines and ≥ 3 sources with ≥ 50 each; at most 800 wines), on all wines up to it | Shortlist: lift ≥ 1.3×, LB > 1.0. Band: ±2 gain ≥ +5 pp, LB > 0. Joint gate reported | Option F decision (report §5.3) |
| Comparator coverage, at the decision point | Share of the wines used whose winery is in the training data; below 50% (`PILOT_MIN_WINERY_COVERAGE`), the shortlist part must also pass on the matched wines alone (≥ 100) | Otherwise the shortlist is not deployed; the matched-winery gate is always reported |
| Secondary, reported only | Per-source intercept from each source's first 50 wines, applied to its later wines | A candidate for a later model version, tested on new data |
| Sensitivities, reported only | The gate on all scorers and each scorer's mean error (`per_scorer.csv`); the gate on wines the team did not sample or list (`sensitivity.json`) | A large difference from the primary gate is reported to the buying lead with the decision |

**After deployment** (if the pilot passes), the same rules run each quarter on the most recent 400 scored ≤ $25 wines. These must be every logged candidate that later received a review, shortlisted or not, so every round's full scored file is kept:
- the shortlist lift falls below 1.3× → review;
- it falls below 1.0 → stop using the shortlist;
- the band's ±2 gain falls below +5 pp, or the stop rule fires → hide the band.

**Business outcome, each quarter** (owner: the buying lead; `monitoring.business_kpi`). The model checks above compare the shortlist with simple rules. What BO1 is for is fewer wasted samples. So each quarter, among the wines the team sampled that later received a WineEnthusiast score: the share scoring 90+, and the samples spent per value wine found. The baseline is the same figure for the last 12 rounds before the tool, extracted and matched to reviews with the same rule at rollout step 0 (picking at random finds about 18 value wines per 100 samples, report §1.1). Because buyers may or may not use the shortlist in a given round, each round records `shortlist used`, and the KPI is also reported for rounds with and without it. A quarter below the baseline is raised at the quarterly review; two in a row trigger the new-version review in §5. It is censored like every outcome here (only reviewed wines count) and is a reported business measure, not a gate.

## 4. Operations
| What | How | Threshold |
|---|---|---|
| Response time | The app shows the time per query | < 3 s per query (BSC4); measured about 0.03 s (median, notebook 6.1c) |
| Artifact integrity | At start: the manifest exists, records a passed lockbox reproduction, and its SHA-1 matches `value_finder.joblib` (`artifacts.load_value_finder`) | Anything missing or different → do not serve; never rebuild silently |
| Library versions | scikit-learn pinned (`deployment/requirements.txt`) | An upgrade requires `deployment/build_artifact.py`, which saves only after the reproduction check |

## 5. Maintenance and retraining policy
- **No automatic retraining.** The current model's only clean test is the lockbox. A refit on new data is a new model and must earn its place.
- **When to consider a new version:**
  - a lagging check fails;
  - two consecutive rounds raise the same input-drift alert;
  - after the pilot, CPI-U moves more than 10% from the pilot's deflator base (then the deflator is re-set in a logged change, and the ≤ $25-share reference is re-read);
  - otherwise, an annual review.
- **How a new version is accepted:**
  1. Refit with the frozen procedure (`winevalue.production.build`) on the old data plus new scored reviews.
  2. Evaluate on a holdout the model has never seen: post-2017 reviews by critics who are not in the training data (option E).
  3. Apply the same pre-registered gate.
  4. Keep the old artifact and its manifest. Replacing it is a logged decision.
- **Candidates already identified:**
  - writer-level calibration (the per-source intercept, if the pilot's secondary analysis supports it);
  - the no-origin stack or plain ridge, which did better on the lockbox but can't be chosen on it (report §5.3, option C).
- **Ownership:** the analyst runs the checks; the buying lead signs off on any change to what is shown.
