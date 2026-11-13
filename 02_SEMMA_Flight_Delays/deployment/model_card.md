# Model Card: Flight Disruption Risk (Champion)

| | |
|---|---|
| **Model** | One-hot logistic regression (C = 0.1), the SAS Enterprise Miner *Regression* node in Python. `models/champion.joblib` |
| **Trained on** | 800,000-flight proportional stratified sample (year-month × carrier × outcome) of Jan 2025 – Apr 2026, the Assess refit |
| **Predicts** | Probability that a scheduled US domestic flight is **disrupted**: arrives 15+ min late, is cancelled, or is diverted |
| **Decision use** | At **16:45 US Eastern** the evening before, rank all of tomorrow's flights; a care team acts on the top 2% (~380 flights) |
| **Data** | US BTS On-Time Performance via Kaggle (Samuel_Pbq, CC0), dataset version 1 |
| **Code fingerprint** | `d61fb8986e66c36d` (SHA-256 over `src/`, `scripts/` and the Model choice; `reports/tables/assess_freeze.json`) |

## Inputs (28, all known at 16:45 ET the day before)
- **Schedule:** departure/arrival hour, weekday, distance, scheduled time, carrier, origin, destination, departure time in ET.
- **Congestion** (counted on the full published schedule): flights per origin-hour, origin-day, destination-hour and carrier-day.
- **Calendar:** days to the nearest US federal holiday.
- **History**, as trailing windows over earlier days, shrunk toward the 2025 base rate:
  - yesterday's rates (flights landing by 16:45 ET) by origin, destination, carrier and nationally;
  - last week's rates (D−7..D−2);
  - last 4 weeks' rates (D−29..D−2) by route, carrier × hour, origin × hour and flight number.

**Never used:** tail numbers or anything derived from them, any flight-day outcome, delay causes, `month`, `daily_airport_stats.csv`, or the whole-period aggregates in `airlines.csv`/`airports.csv`.

## Performance (sealed test summer, May–Aug 2026, scored once)
| Metric | Champion | Better simple rule (schedule) |
|---|---|---|
| Per-day top-2% lift | **2.39** | 1.70 |
| Per-day top-2% precision | **0.63** | 0.47 |
| Gap (90% 7-day-block interval) | **+0.69 (+0.53 to +0.86)**, better on 91% of days | — |
| Pooled ROC-AUC / PR-AUC | 0.718 / 0.471 | 0.668 / 0.397 |

The pre-registered targets T1–T3 are all met (`reports/tables/assess_targets.csv`). Two flexible models scored slightly higher on test (neural network 2.46, gradient boosting 2.44). The champion was fixed by a validation rule before unsealing and was not swapped.

## Where it works less well
- **Late summer** (lift 2.17–2.24 in July–August vs 2.5–2.6 in May–June): convective weather is hard to call a day ahead.
- **High-base-rate carriers** (OH 1.73, B6 1.92, AA 1.99), partly because the lift ceiling is 1 / rate.
- **Extreme storm days** cap lift: on a day with 65% disrupted, the maximum possible lift is 1.5.
- **Calibration:** predicted rates run up to 4 pp low in the upper-middle deciles in a hotter summer. Use the ranking, not the raw probability.

## Assumptions and limitations
- **A-pop:** flights without a tail number (all cancelled) are treated as cancellations known in advance. The result is unchanged when they are scored as disrupted (T3).
- **A-sched:** the BTS schedule for day D is what's visible at 17:00 on D−1.
- **Time zones** come from the state, with split-zone airport overrides. Pacific-island arrivals are approximate (about 1.6k flights).
- **One constant shrinkage prior** for all rate families (not tuned).
- **Explore saw the validation months**, so validation gains were optimistic. The test result above is the unbiased one.
- **No weather data.** Weather enters only through recent outcomes.

## Ethical and practical notes
The score ranks flights, not people. It is meant to *add* help (rebooking offers, alerts), never to deny service. A missed disruption costs a passenger no more than the status quo does. Retraining and monitoring: see `monitoring_plan.md`.
