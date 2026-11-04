# Data: US Flight Delays & Cancellations 2025-2026 (BTS)

| Item | Value |
|---|---|
| Source | Kaggle: [US Flight Delays & Cancellations 2025-2026](https://www.kaggle.com/datasets/samuelpombourcq/us-flight-delays-and-cancellations-2025-2026) by Samuel_Pbq, last updated 2026-10-28 |
| Origin | US Bureau of Transportation Statistics, Reporting Carrier On-Time Performance table. Real data |
| Licence | CC0: Public Domain |
| Files | `flights.parquet` (11,730,351 flights × 40 columns, 314 MB), `flights_sample.csv` (500k), `airlines.csv`, `airports.csv`, `daily_airport_stats.csv` |
| In this repo | **Not committed** (too large for GitHub). Locally the files sit in `../../data/flight_delays/` (git-ignored). In Colab, `flightdelay.data.locate_raw_dir()` downloads them with `kagglehub`, which needs Kaggle credentials. The SEMMA *Sample* stage will commit a stratified sample to `sample/` |
