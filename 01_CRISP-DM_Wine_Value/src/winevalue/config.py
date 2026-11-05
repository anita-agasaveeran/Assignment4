"""Project-wide paths, constants and assumptions.

Values marked "Phase 1" come from Business Understanding. Later phases
add to this file. Changes are recorded in the final report.
"""

from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[2]
DATA_RAW = PROJECT_DIR / "data" / "raw" / "winemag-data-130k-v2.csv.gz"
DATA_PROCESSED = PROJECT_DIR / "data" / "processed"
MODELS_DIR = PROJECT_DIR / "models"
FIGURES_DIR = PROJECT_DIR / "reports" / "figures"

SEED = 42

# --- Phase 1: business definitions ---
VALUE_MAX_PRICE = 25.0   # USD (2017 prices). "Great Value" shelf price cap
VALUE_MIN_POINTS = 90    # WineEnthusiast score that counts as a value pick at or below the cap
SCORE_TOLERANCE = 2.0    # a score prediction is "usable" if within +/- 2 points
SHORTLIST_K = 100        # wines a buying team can sample in a cycle (assumption A4)
CANDIDATES_PER_CYCLE = 1000   # unscored <= $25 wines the team chooses from per cycle (assumption A7)
N_SIM_CYCLES = 200            # simulated cycles per evaluation

# Evaluative language: words and phrases that state a verdict rather than describe the wine.
# Fixed in Phase 1 for the masking test (DM1b). Broadened once after critic round 2: drinking
# windows and more verdict words added; "fine" removed (mostly descriptive: "fine tannins").
EVALUATIVE_TERMS = [
    # quality verdicts
    "superb", "outstanding", "excellent", "exceptional", "extraordinary", "stunning", "brilliant",
    "gorgeous", "beautiful", "beautifully", "impressive", "impressively", "delicious", "lovely",
    "terrific", "great", "good", "nice", "decent", "pleasant", "solid", "classic", "masterpiece",
    "profound", "remarkable", "magnificent", "sublime", "spectacular", "wonderful", "fantastic",
    "complex", "complexity", "elegant", "elegance", "balanced", "harmonious", "finesse", "polished",
    "refined", "best", "value", "bargain", "worth", "potential", "serious",
    "simple", "basic", "everyday", "ordinary", "mediocre", "bland", "dull", "thin", "dilute", "diluted",
    "flawed", "awkward", "rustic", "clumsy", "disjointed", "lacks", "lacking", "unbalanced", "hollow",
    "short", "quaffable", "easygoing", "easy-drinking",
    # ageing / drinking advice
    "cellar", "cellaring", "cellared", "ageworthy", "age-worthy", "aging", "ageing", "age",
    "drink now", "drink up", "drink soon", "best after", "will age", "needs time", "long-term",
    "for the long haul", "keep", "hold",
]
# Regex patterns for drinking windows ("Drink from 2020", "Drink 2018-2025", "through 2030").
EVALUATIVE_PATTERNS = [
    r"\bdrink\b[^.;]*?\b(?:19|20)\d{2}\b(?:\s*[-–]\s*(?:19|20)?\d{2,4})?",
    r"\b(?:through|until|till|by|after|from)\s+(?:19|20)\d{2}\b",
    r"\b(?:19|20)\d{2}\s*[-–]\s*(?:19|20)\d{2}\b",
]
# The round-1 list, kept so DM1b can be reported under both lists.
EVALUATIVE_TERMS_V1 = [
    "superb", "outstanding", "excellent", "exceptional", "extraordinary", "stunning", "brilliant",
    "gorgeous", "beautiful", "beautifully", "impressive", "delicious", "lovely", "terrific", "great",
    "fine", "good", "nice", "decent", "pleasant", "solid", "classic", "masterpiece", "profound",
    "simple", "basic", "everyday", "ordinary", "mediocre", "bland", "dull", "thin", "dilute", "diluted",
    "flawed", "awkward", "rustic", "clumsy", "disjointed", "lacks", "lacking",
    "cellar", "cellaring", "ageworthy", "age-worthy", "drink now", "drink up", "drink soon",
    "best after", "will age", "needs time", "long-term", "for the long haul",
]

# Anonymous notes attributed to a lockbox critic with probability above this are dropped (R8).
ATTRIBUTION_THRESHOLD = 0.5

# --- Phase 1: pre-registered success criteria (lockbox critics, scored once in Phase 5) ---
# Every target is met by every development fold of the untuned feasibility models
# (per-fold table in report section 1.2). Fold 3, the fold most like the lockbox, is the
# weakest on DM1/BSC2; folds 1 and 4 are the weakest on BSC1.
# BSC1 / DM2: shortlist (price-aware ranker)
TARGET_PRECISION_FLOOR = 0.55      # expected P@100 over cycles of 1,000; dev folds 0.61-0.72
TARGET_PRECISION_LIFT = 1.4        # x best fixed simple rule (point estimate); dev 1.56-2.13x
TARGET_LIFT_LOWER = 1.2            # one-sided 90% winery-cluster bootstrap lower bound (top-10% lift); dev 1.43-1.92x
# BSC2: internal score band (price-free model) on <= $25 candidates
TARGET_WITHIN_TOL = 0.60           # dev folds 0.63-0.72
TARGET_WITHIN_GAIN_PP = 0.05       # over variety x country; dev folds +7.3 to +22.4 pp (LB >= +6.0)
# DM1: score estimate
TARGET_MAE_REDUCTION = 0.10        # vs variety x country; dev folds 11.9-33.2%
TARGET_MAE_REDUCTION_LOWER = 0.05  # one-sided 90% winery-cluster bootstrap lower bound; dev >= 10.5%
# DM1b: masking (absolute, stable even when the DM1 reduction is small)
TARGET_MASKED_MAE_INCREASE = 0.15  # masked-model MAE minus DM1 MAE, points; dev 0.03-0.11
# Pre-deployment pilot gate (A1), on the same pilot wines (all relative to note-blind rules)
PILOT_MIN_WINES = 400              # <= $25 wines that later get a critic score; ~80% power at fold-3-like effects (100 gave 39-67%)
PILOT_WITHIN_GAIN_PP = 0.05        # within +/-2 over variety x country (as BSC2); 90% bootstrap lower bound > 0
PILOT_TOP20_LIFT = 1.3             # ranker's top-20% precision for 90+ vs the BEST frozen simple rule (dev vs price 1.44-1.74x)
PILOT_TOP20_LIFT_LOWER = 1.0       # and its winery-clustered 90% lower bound must exceed 1.0

# --- Phase 1: pre-registered buyer-insight hypotheses (BSC5) ---
# Each is tested in development data AND the lockbox. One-sided 90% winery-clustered bootstrap.
# BSC5 passes if >= 4 of 6 replicate (stated direction AND condition met in both), including H5 or H6.
# H1-H3 are sanity checks (strong in development); H5-H6 are the actionable ones.
HYPOTHESES = {
    "H1": "(sanity) Longer tasting notes go with higher scores: Spearman rho > 0, LB > 0",
    "H2": "(sanity) Within variety x country, pricier wines score higher: partial corr(log price, score) > 0, LB > 0",
    "H3": "(sanity) A named designation goes with higher scores (same variety x country): difference > 0, LB > 0",
    "H4": "Critics differ: SD of critic effects (score minus training-fitted variety x country expectation) > 0.5, LB > 0.5. "
          "Limitation: the lockbox has only 4 critics, which a winery bootstrap doesn't capture",
    "H5": "Among <= $25 wines, whites are more often value wines (90+) than reds: difference > 0, LB > 0. "
          "Colour from winevalue.grapes.wine_colour(variety, title), frozen in Phase 2 revision 3 (grape knowledge + title style words; text only, before any colour x value table or lockbox use)",
    "H6": "Among <= $25 wines, a strong winery track record (GroupMeanBaseline(keys=('winery',), shrink=20) on "
          "training >= 89) goes with a higher value-wine rate: difference > 0, LB > 0",
}
BSC5_MIN_REPLICATED = 4

# --- DM5 (re-specified 2026-11-04 in a Phase 2 -> Phase 1 loop-back; text only, no scores) ---
DM5_SHINGLE_WORDS = 5
DM5_NUM_PERM = 128
DM5_TAU = 0.5                 # near-duplicate = exact Jaccard >= 0.5 on 5-word shingles
DM5_N_SYNTH = 2000            # synthetic copies, seed = SEED
DM5_EDIT_RATE = (0.02, 0.08)  # share of words replaced by random corpus words; ~1,670 copies clear TAU (Phase 2 simulation)
DM5_MIN_RECALL = 0.90         # on synthetic positives (exact J >= TAU)
DM5_MAX_FALSE_FLAG = 0.01     # on 2,000 random pairs of distinct notes
DM5_MIN_PRECISION = 0.90      # on all real flagged pairs, labelled with the rule in report section 1.3
