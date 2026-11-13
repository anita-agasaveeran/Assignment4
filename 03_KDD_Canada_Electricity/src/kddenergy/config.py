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

# =====================================================================================================
# KDD steps 1-3 (Selection, Preprocessing, Transformation) and the OPERATIONAL acceptance rules.
# Everything below was written before any data-mining step ran (critic round 2 carried items N3-N5, N9).
# =====================================================================================================
EXTERNAL = PROJECT_DIR / "data" / "external"
PROCESSED = PROJECT_DIR / "data" / "processed"
EVENT_CATALOGUE = EXTERNAL / "event_catalogue.csv"
CONFIRM_START, DATA_END = "2025-01", "2026-08"

PROVINCES = ["Newfoundland and Labrador", "Prince Edward Island", "Nova Scotia", "New Brunswick", "Quebec",
             "Ontario", "Manitoba", "Saskatchewan", "Alberta", "British Columbia"]
TERRITORIES = ["Yukon", "Northwest Territories", "Nunavut"]
GEOS = PROVINCES + TERRITORIES          # the Canada aggregate is kept out of every mining step
ABBR = {"Newfoundland and Labrador": "NL", "Prince Edward Island": "PE", "Nova Scotia": "NS", "New Brunswick": "NB",
        "Quebec": "QC", "Ontario": "ON", "Manitoba": "MB", "Saskatchewan": "SK", "Alberta": "AB",
        "British Columbia": "BC", "Yukon": "YT", "Northwest Territories": "NT", "Nunavut": "NU", "Canada": "CA"}

# Selection: non-overlapping generation types (all producers). In 2016+ combustion is reported directly as a
# fuel total, which equals the residual total - non-thermal types (front pass); nested subtotals are dropped.
GEN_SELECT = {"Total all types of electricity generation": "gen_total", "Hydraulic turbine": "hydro",
              "Nuclear steam turbine": "nuclear", "Wind power turbine": "wind", "Solar": "solar",
              "Tidal power turbine": "tidal", "Other types of electricity generation": "other",
              "Total electricity production from combustible fuels": "combustion"}
# Flow components fully observed in 2016+. Firm / non-firm splits and 'other receipts from the US' are discontinued
# ('..' throughout 2016+) and not selected; total receipts = provincial + purchased US receipts exactly (checked).
FLOW_SELECT = {"Total generation": "gen_flows_table", "Total receipts": "receipts", "Total deliveries": "deliveries",
               "Receipts from other provinces": "rec_prov", "Deliveries to other provinces": "del_prov",
               "Purchased receipts from the United States": "rec_us",
               "Deliveries to the United States": "del_us",
               "Total electricity available for use within specific geographic border": "availability"}

# --- K1 (clustering), fixed before mining (revised after critic round 1, item 4) ---
# seasonal_amplitude dropped: r = 0.97 with winter_summer_ratio (seasonality would count twice). The four shares are
# compositional (about 3 free dimensions); kept because each is a distinct, interpretable archetype axis.
K1_FEATURES = ["hydro_share", "nuclear_share", "windsolar_share", "combustion_share",
               "net_import_ratio", "trade_intensity", "us_net_export_ratio", "winter_summer_ratio"]
K1_K_RANGE = range(2, 7)            # k chosen by the best k-means silhouette on 2016-2024 features (ties -> smaller k)
K1_N_INIT = 100
# PRIMARY confirmation: the SAME pipeline (standardize within window, k-means with the chosen k, same seed) re-run on
# 2025-01..2026-08 features; ARI vs the 2016-2024 labels >= K1_MIN_ARI. SECONDARY: 2025-26 features scaled with the
# DEVELOPMENT scaler and assigned to the nearest development centroid; co-assignment reported per geography.
# Every feature comes from a calendar-month climatology, so the 20-month window (Jan-Aug twice) weighs like one year.
# What ARI >= 0.7 means at n = 13 is reported for the chosen k (all single-geography moves, `ari_if_one_moves`).

# --- K2 (change points), fixed before mining (revised after critic round 1, item 1) ---
K2_GEOS = PROVINCES                 # territories (diesel/hydro micro-grids) excluded from K2
K2_SERIES = "combustion_share"      # combustion share of IN-PROVINCE generation, deseasonalized by its 2016-24
                                    # calendar-month means. Not consumption-side dependence: importers (PE, NS) noted.
K2_MODEL, K2_MIN_SIZE = "l2", 12    # mean-shift cost; segments >= 12 months (so no change point inside 2016)
K2_SIGMA = "mad_diff"               # noise sigma = 1.4826 * MAD(first differences) / sqrt(2) (white-noise scale)
K2_SIGMA_SENSITIVITY = "sd"         # sensitivity run: sigma = s.d. of the deseasonalized series (far more conservative)
K2_PEN_FACTOR = 3.0                 # penalty = 3 * log(n) on x / sigma
K2_MIN_SHIFT_PP = 1.0               # a primary change point needs |post - pre| >= 1 percentage point
# Primary change point per province = the largest |mean shift| between adjacent PELT segments.
# STABILITY (non-model-based): PELT re-run on the OBSERVED series with 0, 6, 12, 18 or 24 months trimmed from the
# start and from the end (25 sub-series); stable if >= K2_MIN_STABILITY of them have a change point within +/- 3 months.
K2_TRIMS = (0, 6, 12, 18, 24)
K2_MIN_STABILITY = 0.70
K2_BOOT_REPS, K2_BOOT_BLOCK = 200, 6   # residual block bootstrap: reported as secondary only (model-based)
# PERSISTENCE (margin test): with mid = (pre + post) / 2 and d = sign(post - pre),
#   (i)  d * (conf_mean - mid) >= K2_MIN_SHIFT_PP / 2 pp   (2025-26 mean, same dev climatology), AND
#   (ii) d * (last_dev_segment_mean - mid) > 0             (the change had not reversed by 2024-12).
# DIRECTION pre-declared: d < 0 (falling combustion share) = "less combustion-dependent".
# ATTRIBUTION: dln(share) = dln(combustion GWh) - dln(total generation GWh), pre vs post segment means.
#   "burning" if dln(combustion) / dln(share) >= 0.5, else "denominator" (total generation moved, burning didn't).
# VERDICT: K2 is MET if >= 3 provinces other than Ontario have a primary change point that is stable AND persistent.
# Every province is reported with direction + attribution regardless. Ontario is reported separately (partly spent).

# --- K3 (anomalies), fixed before mining (revised after critic round 1, item 2) ---
K3_GEOS = GEOS
K3_SERIES = ["log_availability", "log_gen_total", "net_import_ratio"]   # STL(period 12, robust) residual z-scores
K3_FLAG_SHARE = 0.02                # flag budget: top 2% of eligible geo-months (Isolation Forest on the STL z's)
K3_IF_TREES = 500
K3_MATCH_MONTHS = 1                 # a flag matches an event in the same geography within +/- 1 month
# PRIMARY score = EVENT-LEVEL precision: each catalogue event credits at most one flag; precision = credited / flags.
# NULL: each geography's flags are circularly shifted within that geography's eligible months (K3_PERM_REPS reps);
# p = share of shifts with event-level precision >= observed.
# ACCEPTANCE (scored period 2016-01..2024-12): event-level precision >= 0.5 AND p <= K3_MAX_P.
# Flag-level precision and lift over the base rate are reported as secondary (lift cannot bind at a 12% base rate).
# 2016 and 2024 are edge years for STL (lower power); reported separately.
# CONFIRMATION (2025-01..2026-08, after unsealing): one-sided STL - for each month t, STL is fit on data up to t and the
# residual at t is used; z scale = discovery-period MAD; the Isolation Forest AND its score threshold (score of the
# last discovery flag) are frozen; no re-ranking. Secondary evidence only.
K3_PERM_REPS, K3_MAX_P = 1000, 0.05
# Event classes in scope: weather/climate (storm, cold, heat, flood, drought), wildfire, pandemic. OUT of scope: plant
# outages, refurbishments, commissioning, industrial closures (e.g. Northern Pulp, NS, 2020): they are structural or
# not reliably dated from public memory.

# --- K4 (forecasting), fixed before mining (formulas in kddenergy.forecast; revised after critic round 1, item 5) ---
# All candidates use availability from CONSISTENT_START onward only:
#   avg3_growth    = mean of the same calendar month in the last 3 years x sqrt(last-12-month total / previous 12)
#   ets_damped_log = Holt-Winters on log availability, damped additive trend, additive seasonality (period 12)
#   combo_avg3_ets = equal-weight mean of the two
# ONE model is chosen by the lowest pooled WAPE over the six development origins (ties within 0.01 pp -> the simpler,
# in the order listed). Bootstrap unit: (geography, origin) pairs, iid, 2,000 reps, 90% interval.
# The sealed origin 2025-12 covers only Jan-Aug 2026 (8 months) but keeps its veto ("better at both origins").
K4_CANDIDATES = ["avg3_growth", "ets_damped_log", "combo_avg3_ets"]
K3_CATALOGUE_SHA256 = "ee336e9b5e7c57829f92b229eaa7b1e5aaa6ad92feeccd0542af0a905785a22b"   # frozen before mining

# Data-break register (found in Preprocessing, before mining). Industrial producers in Nunavut are first reported
# in 2024-10 (industry-class generation goes from ~0 to ~14 GWh/month; total doubles). It is a coverage change, not
# an event: Nunavut geo-months from this month on are excluded from K3 flagging and scoring.
DATA_BREAKS = {"Nunavut": "2024-10"}
# Smaller coverage step (critic round 1, item 6): NL industrial hydro first reported 2021-02 (+56-67 GWh/month, about
# 1.5% of NL generation; utility hydro unchanged). A level step only distorts STL residuals around the break, so
# NL 2021-01..2021-03 are excluded from K3 flagging and scoring.
BREAK_WINDOWS = {"Newfoundland and Labrador": ("2021-01", "2021-03")}
