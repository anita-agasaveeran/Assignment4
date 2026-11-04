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
