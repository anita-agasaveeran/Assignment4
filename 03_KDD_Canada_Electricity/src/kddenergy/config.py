"""Paths and frozen front-pass decisions (KDD project)."""

from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[2]
RAW = PROJECT_DIR / "data" / "raw"
FIGURES_DIR = PROJECT_DIR / "reports" / "figures"
SEED = 42

TOTAL_PRODUCERS = "Total all classes of electricity producer"
TOTAL_GEN = "Total all types of electricity generation"
NON_THERMAL = ["Hydraulic turbine", "Nuclear steam turbine", "Wind power turbine", "Solar",
               "Tidal power turbine", "Other types of electricity generation"]
# StatCan classification break: technology types (2008-2015) vs fuel types (2016+, biomass split 2020+)
THERMAL_TECH_2008_2015 = ["Conventional steam turbine", "Combustion turbine", "Internal combustion turbine"]
THERMAL_FUEL_2016_ON = "Total electricity production from combustible fuels"

# --- Frozen holdouts (fixed in the front pass) ---
# Knowledge discovery (clusters, change points, anomalies) uses data up to DISCOVERY_END;
# 2025-01..2026-08 is a confirmation period: do the discovered patterns persist?
DISCOVERY_END = "2024-12"
# Forecasting: development origins match the dataset's own seasonal-naive backtest; the last two are SEALED.
DEV_ORIGINS = ["2018-12", "2019-12", "2020-12", "2021-12", "2022-12", "2023-12"]
SEALED_ORIGINS = ["2024-12", "2025-12"]   # 2025-12 forecasts only Jan-Aug 2026 (data end)
FORECAST_HORIZON = 12

# --- Front pass v2 (after critic round 1) ---
# StatCan coverage expanded in 2016-01 (industry-class wind/solar/tidal/other first reported; totals +9%).
# Frozen rule: anything compared ACROSS years (levels, shares, trends, clusters, change points, anomaly
# baselines) uses CONSISTENT_START onward. Pre-2016 data may be used only within its own era, and a 2016
# change point is never reported as a discovery.
CONSISTENT_START = "2016-01"
NON_EMITTING = ["Hydraulic turbine", "Nuclear steam turbine", "Wind power turbine", "Solar", "Tidal power turbine"]

# Pre-registered acceptance rules for knowledge (interestingness = validity first)
K1_MIN_ARI = 0.7            # cluster assignments 2016-24 vs 2025-26 features
K2_CHANGEPOINT_TOL_MONTHS = 3   # and the post-change direction must persist in 2025-26 (province level)
K3_MIN_CATALOGUE_PRECISION = 0.5  # flagged anomalous months vs an event catalogue compiled BEFORE mining
K4_MAX_WAPE_RATIO = 0.90    # pooled WAPE on sealed origins <= 0.90 x seasonal naive, and better at both origins
