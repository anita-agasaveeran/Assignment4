# Monitoring & Maintenance Plan (CRISP-DM 6.2)

> Status: scaffold. Thresholds get set after Evaluation (Phase 5).

| What | How it is measured | Frequency | Alert threshold | Action |
|---|---|---|---|---|
| Forecast accuracy | WAPE of last 4 weeks vs test-period WAPE | Weekly | _TODO_ | Investigate → retrain |
| Waste rate | Unsold ÷ baked, per store × category | Daily | _TODO_ | Review bake policy quantile |
| Fill rate | Demand met ÷ demand | Daily | _TODO_ | Raise quantile for that category |
| Input drift | PSI on key features (weekday mix, festival days, prices) | Monthly | PSI > 0.2 | Retrain |
| Data quality | Schema check (`bakery.data.load_raw`), null and arithmetic checks | Every load | Any failure | Block scoring |

**Retraining policy:** _TODO (schedule and triggers)_

**Ownership:** _TODO (who acts on each alert)_
