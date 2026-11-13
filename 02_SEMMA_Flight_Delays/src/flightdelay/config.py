"""Project-wide paths and frozen front-pass decisions (SEMMA project)."""

from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[2]
REPO_DIR = PROJECT_DIR.parent
KAGGLE_DATASET = "samuelpombourcq/us-flight-delays-and-cancellations-2025-2026"
LOCAL_RAW_DIR = REPO_DIR / "data" / "flight_delays"      # git-ignored local download
SAMPLE_DIR = PROJECT_DIR / "data" / "sample"              # SEMMA Sample-stage output (committed)
FIGURES_DIR = PROJECT_DIR / "reports" / "figures"
SEED = 42

# --- Front pass: target ---
# "Disrupted" = arrived 15+ min late OR cancelled OR diverted. Cancellations and diversions are
# kept because they're the worst outcomes for a passenger; dropping them would hide the worst days.
TARGET = "disrupted"

# --- Front pass: frozen time partition (SEMMA "Sample -> Partition") ---
TRAIN_START, TRAIN_END = "2025-01-01", "2025-12-31"
VALID_START, VALID_END = "2026-01-01", "2026-04-30"
TEST_START, TEST_END = "2026-05-01", "2026-08-31"        # SEALED until the Assess stage

# --- Front pass: prediction horizon and leakage rules ---
# Prediction is made at 17:00 the day before the flight date (DECISION_CUTOFF_HHMM). Allowed inputs: the
# published schedule (carrier, route, times, distance, scheduled congestion) and outcomes of flights known by
# the cutoff. No tail_number-derived features (aircraft rotation needs the tail actually flown). Never any field observed on the flight day itself.
FLIGHT_DAY_OUTCOME_COLUMNS = [
    "dep_time", "dep_delay", "dep_del15", "taxi_out", "wheels_off", "wheels_on", "taxi_in",
    "arr_time", "arr_delay", "arr_del15", "cancelled", "cancellation_code", "cancellation_reason",
    "diverted", "actual_elapsed_time", "air_time", "carrier_delay", "weather_delay", "nas_delay",
    "security_delay", "late_aircraft_delay",
]

# --- Front pass v2 (after critic round 1) ---
# Decision clock: the care team decides at 17:00 local on the day before. Previous-day outcomes may only use
# flights SCHEDULED to arrive by then (same-day arrivals; red-eyes excluded).
DECISION_CUTOFF_HHMM = 1700
# Capacity: the team can act on about 2% of tomorrow's flights (~380 of ~19k per day); 10% also reported.
TOP_FRACTIONS = (0.02, 0.10)
# HA's network is reported under AS from 2026-01; one carrier group keeps "airline" meaning stable.
CARRIER_GROUP = {"HA": "AS"}
# Excluded from the scored population: flights with no tail_number (100% cancelled in train+valid; these are
# early cancellations the team already knows about).
EXCLUDE_MISSING_TAIL = True
# Files that aggregate the WHOLE period (test months included): never used as features.
FORBIDDEN_FILES = ["airlines.csv", "airports.csv (departures/arrivals columns)"]
# Rolling-origin check inside non-test data, so a summer validation exists before Assess (test = summer 2026).
SUMMER_CHECK = {"train": ("2025-01-01", "2025-04-30"), "valid": ("2025-05-01", "2025-08-31")}
# Refit policy: the final model is refit on train + valid (2025-01 .. 2026-04) before the single Assess run.

# --- Sample stage (pre-registered on 2026-11-09, BEFORE any learning-curve run) ---
# Pin the Kaggle dataset version so Colab downloads exactly the file analysed here (anonymous download works).
KAGGLE_DATASET_VERSION = 1
# Proportional stratified random sampling (SAS EM Sampling node, "stratified"). Strata = year-month x carrier group
# x target: few levels, many flights per level (the SAS paper warns against strata with too few records per level).
SAMPLE_STRATA = ["year_month", "carrier", "disrupted"]
# Learning curve: repeated, nested stratified samples of the training window; the full window is the reference.
LC_SIZES = (25_000, 50_000, 100_000, 200_000, 400_000, 800_000, 1_600_000, 3_200_000)
LC_REPS = 5
LC_WINDOWS = {"main": ((TRAIN_START, TRAIN_END), (VALID_START, VALID_END)),
              "summer": (SUMMER_CHECK["train"], SUMMER_CHECK["valid"])}
# LightGBM tree counts are set by early stopping on 10% of each training sample (added after a 1-rep smoke test at
# 25k/400k showed fixed-size boosting over-fits small samples; no curve had been run). The full window is refit 3x.
# Selection rule: n*_w = the smallest grid size whose mean shortfall vs the full-window mean is <= LC_DELTA_LIFT in per-day
# top-2% lift AND <= LC_DELTA_AUC in pooled ROC-AUC, for BOTH LightGBM capacities, in window w. Sampling rate
# f = max_w(n*_w / N_w), rounded UP to the next whole percent; the same f is used for train and validation months.
# 0.02 lift = the largest effect of any single minor front-pass issue; well inside the +/-0.1 day-to-day intervals.
LC_DELTA_LIFT = 0.02
LC_DELTA_AUC = 0.002
# Representativeness acceptance (sample vs its population): |SMD| < 0.05 on numerics, max level-share gap < 0.5 pp
# on categoricals, every day present, and target rates by level within |z| < 3 except at the chance rate.
REP_SMD_MAX, REP_GAP_PP_MAX, REP_Z_MAX = 0.05, 0.5, 3.0
SAMPLE_FILE = SAMPLE_DIR / "semma_sample.parquet"

# --- Assess targets (pre-registered in the Sample stage, 2026-11-11, from validation-period evidence only) ---
# T1 (must): champion beats the BETTER of the two simple rules ON THE TEST MONTHS in per-day top-2% lift, with the
#     90% 7-day-block bootstrap interval of the daily gap above 0.
# T2 (target): that gap is >= +0.15 lift (front-pass summer-check gap +0.19, 90% interval +0.10..+0.28; a new summer
#     and Spirit's exit argue for less).
# T3 (robustness): T1 still holds when the tail-less cancellations are scored as disrupted.
ASSESS_T2_GAP = 0.15
# Champion choice (Model stage): highest mean per-day top-2% lift averaged over the main and summer-check windows.
# Simpler / slower models: LR, decision tree and MLP are fit on an 800k stratified sample. Justified directly only for
# the logistic regression (within 0.007 lift / 0.0005 AUC of its full window at 800k); for the tree and MLP it is an
# extrapolation (critic round 1, M4), so Model also reports gradient boosting at 800k as an equal-n comparison.
SMALL_MODEL_ROWS = 800_000
