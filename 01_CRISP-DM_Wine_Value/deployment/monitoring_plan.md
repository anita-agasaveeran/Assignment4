# Monitoring & Maintenance Plan (CRISP-DM 6.2)

> Status: scaffold. Thresholds get set after Evaluation (Phase 5).

| What | How it is measured | Frequency | Alert threshold | Action |
|---|---|---|---|---|
| Score accuracy | MAE / within ±2 on wines that later receive a critic score | Each buying cycle | _TODO_ | Investigate → retrain |
| Shortlist precision | Share of sampled shortlist wines the team rates value-worthy | Each cycle | _TODO_ | Review threshold / retrain |
| Input drift | Vocabulary / TF-IDF distribution shift, new grapes or regions | Quarterly | _TODO_ | Retrain |
| Writer drift | Accuracy split by note source (importer / staff / producer) | Quarterly | _TODO_ | Calibrate per source |
| Data quality | Schema check (`winevalue.data.load_raw`), empty notes, duplicates | Every load | Any failure | Block scoring |
