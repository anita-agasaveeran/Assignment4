"""Project-wide paths, constants and assumptions.

Assumption values are placeholders until Business Understanding
(Phase 1) settles them. Every change gets recorded in the final report.
"""

from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[2]
DATA_RAW = PROJECT_DIR / "data" / "raw" / "bakery_sales_dataset.csv"
DATA_PROCESSED = PROJECT_DIR / "data" / "processed"
MODELS_DIR = PROJECT_DIR / "models"
FIGURES_DIR = PROJECT_DIR / "reports" / "figures"

SEED = 42

# --- Time-based split (proposed; finalised in Modeling > Generate Test Design) ---
TRAIN_END = "2024-06-30"
VALID_END = "2024-09-30"   # test = everything after VALID_END

# --- Business assumptions (set in Phase 1, Business Understanding) ---
# Scope: "fresh" = products whose median shelf life is <= 7 days. These are
# made or ordered daily, so whatever is left unsold is thrown away.
FRESH_MAX_SHELF_LIFE_DAYS = 7
# Newsvendor costs per unit (Phase 1, section 1.2 Costs & benefits):
#   cost of waste (Co)    = unit cost price - salvage value
#   cost of stockout (Cu) = unit selling price - unit cost price (lost margin)
SALVAGE_VALUE = 0.0      # unsold fresh items are discarded, not resold
GOODWILL_COST = 0.0      # extra cost of a stockout beyond lost margin (sensitivity-tested)

# --- Success criteria (Phase 1, sections 1.1 and 1.3) ---
TARGET_WASTE_REDUCTION = 0.20       # BSC2: >= 20% fewer unsold fresh units than the baseline
TARGET_FILL_RATE = 0.95             # BSC3: >= 95% of fresh demand met
TARGET_FORECAST_IMPROVEMENT = 0.10  # DM1: WAPE >= 10% (relative) below seasonal-naive
