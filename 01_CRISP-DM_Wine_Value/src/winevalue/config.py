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
# Every target is met by every development fold of the untuned feasibility models (Phase 1 statement; Phase 4 found that
# plain ridge fails fold 3 once the per-fold R8 filter is applied, see report section 4.4)
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
          "Colour from winevalue.grapes.wine_colour(variety, title, winery, note), frozen in Phase 2 revision 3 and re-frozen with dated amendments in Phase 3 (grape knowledge + title and note style words; text only, before any colour x value table or lockbox use)",
    "H6": "Among <= $25 wines, a strong winery track record (GroupMeanBaseline(keys=('winery',), shrink=20) on "
          "training >= 89) goes with a higher value-wine rate: difference > 0, LB > 0",
}
BSC5_MIN_REPLICATED = 4

# --- DM5 (re-specified 2026-11-04 in a Phase 2 -> Phase 1 loop-back; text only, no scores) ---
DM5_SHINGLE_WORDS = 5
DM5_NUM_PERM = 128
DM5_TAU = 0.5                 # near-duplicate = exact Jaccard >= 0.5 on 5-word shingles
DM5_N_SYNTH = 2000            # synthetic copies, seed = SEED
DM5_EDIT_RATE = (0.02, 0.08)  # share of words replaced by random corpus words; 1,694 of 2,000 clear TAU (seed 42, Phase 3 corpus)
DM5_LSH_THRESHOLD = 0.3      # loose LSH candidate stage; every candidate is then verified by EXACT Jaccard >= TAU
DM5_MIN_RECALL = 0.90         # (a) PASS/FAIL: share of synthetic positives (exact J >= TAU) that the detector flags.
                              #     It checks the IMPLEMENTATION, not the data: with b = 37 bands x r = 3 rows,
                              #     P(candidate | J = 0.5) = 0.993, so it is close to guaranteed (critic round 2 N5)
DM5_MAX_CANDIDATE_SHARE = 1e-4  # (b) reported engineering check (not discriminating: Phase 3 measured 1.7e-7)
DM5_MIN_PRECISION = 0.90      # (c) EXPLORATORY only: the 43 real pairs were inspected in Phase 2, so precision under
                              #     similarity.is_true_duplicate is reported, not used as a pass/fail test.
                              #     Timeline (critic round 2 N4): (c) was first RUN in Phase 3 critic round 1 (0.81 < 0.90);
                              #     it was demoted to exploratory and the content-word rule amended AFTER that run;
                              #     the result was unchanged (35/43).
# DM5 corpus: distinct notes after exact de-duplication, barrel-sample removal and duplicated-note removal,
# i.e. prepare(..., stop_before="near_duplicates"). prepare() drops near-duplicates by Jaccard >= TAU alone.

# --- Frozen critic -> fold mapping (Phase 1 design; pinned in Phase 3 after critic round 1) ---
# Derived once by splits.critic_folds() on the DE-DUPLICATED reviews. Computing it on other row sets (e.g. the raw
# file with duplicates) gives a different lockbox, so the mapping is frozen here and splits.assign_folds() uses it.
# Keys are normalised critic names (whitespace collapsed; the raw "Anne Krebiehl\xa0MW" maps to "Anne Krebiehl MW").
CRITIC_FOLDS = {
    "Roger Voss": 0,
    "Michael Schachner": 1, "Jim Gordon": 1,
    "Kerin O’Keefe": 2, "Sean P. Sullivan": 2, "Anne Krebiehl MW": 2, "Jeff Jenssen": 2,
    "Paul Gregutt": 3, "Joe Czerwinski": 3, "Anna Lee C. Iijima": 3, "Carrie Dykes": 3, "Fiona Adams": 3, "Christina Pickard": 3,
    "Virginie Boone": 4, "Matt Kettmann": 4, "Lauren Buzzeo": 4, "Susan Kostrzewa": 4, "Mike DeSimone": 4, "Alexander Peartree": 4,
}
LOCKBOX_FOLD = 2
LOCKBOX_CRITICS = sorted(c for c, f in CRITIC_FOLDS.items() if f == LOCKBOX_FOLD)

# --- Phase 4: test design and selection rules (written 2026-11-04 22:29 PT in the working copy, before the first Phase 4
# fit at 22:30, per the session record; no commit exists from before fitting, see reports/phase4_run_log.md) ---
# Outer CV: each development critic fold held out in turn. Training = the other development folds + anonymous notes,
# minus anonymous notes attributed (p > ATTRIBUTION_THRESHOLD) to the HELD-OUT fold's critics (per-fold R8). Test = the
# held-out fold minus titles seen in training (R-3). The lockbox (fold 2) is never touched in Phase 4.
OUTER_FOLDS = (0, 1, 3, 4)
# Inner CV (hyperparameters, stacking): inside each outer training set, the remaining named development folds are the
# inner folds. [SUPERSEDED by revision 2, below: anonymous notes go to their top-guess critic's inner fold and inner
# scores use named rows.] Revision 1: anonymous notes spread at random, grouped by title (seed SEED); R-3 on inner
# validation; no inner R8 filter.
RIDGE_ALPHAS = (0.25, 0.5, 1.0, 2.0, 4.0, 8.0)   # 4 and 8 added in revision 2 (2.0 was a grid edge in 4 of 8 cells)
LGBM_GRID = ({"num_leaves": 15, "min_child_samples": 50}, {"num_leaves": 63, "min_child_samples": 50})
LGBM_FIXED = {"learning_rate": 0.05, "n_estimators": 400, "subsample": 0.8, "subsample_freq": 1,
              "colsample_bytree": 0.8, "reg_lambda": 1.0, "verbose": -1,
              "deterministic": True, "force_row_wise": True}   # reproducible reruns (same data, params, threads)
LGBM_TREE_GRID = (25, 50, 100, 200, 400)   # revision 2: trees chosen on a pooled inner curve (replaces early stopping + mean best iteration)
N_BOOT = 500                    # winery-cluster bootstrap resamples (as Phase 1)
# Model selection (applied to OUTER-fold results; the lockbox in Phase 5 is the unbiased estimate):
#  DM1 [SUPERSEDED by the revision 2 rule below; kept as the record of revision 1] (price-free score model): lowest mean outer MAE among candidates that meet the DM1 and BSC2 targets in EVERY
#      development fold; within 0.01 points of the best, the simpler model wins (ridge < stack).
#  DM2 (ranker): highest mean expected P@100 (1,000-candidate cycles) among candidates that meet the BSC1 targets in
#      every fold; within 0.01, the simpler model wins.
#  Ties are reported, never re-tuned on the outer folds.
# DM3 (flavour profiles): NMF and k-means, k = 6..15, on a unigram + bigram TF-IDF of `note` (5,000 terms; English +
#  PROFILE_STOPWORDS removed), fitted on development notes only. Stability = each profile's top-10-term Jaccard with
#  its Hungarian-matched profile from the other half (halves split by WINERY, seed SEED). Chosen k: the largest k with
#  EVERY profile >= 1% of notes and EVERY matched Jaccard >= 0.5; if none, the k with the highest minimum Jaccard.
#  Technique: the one with the higher mean matched Jaccard at its chosen k.
DM3_K_RANGE = tuple(range(6, 16))
DM3_MIN_SHARE = 0.01
DM3_MIN_JACCARD = 0.5
DM3_TOP_TERMS = 10
PROFILE_STOPWORDS = ["wine", "wines", "flavor", "flavors", "flavour", "flavours", "aroma", "aromas", "palate", "finish",
                     "notes", "note", "nose", "drink", "bottle", "bottling", "vintage", "offers", "shows", "made",
                     "it's", "its", "that's", "there's", "just", "bit", "hint", "hints", "touch", "alongside", "along",
                     "accented", "followed", "carry", "carries", "mouth", "glass", "_price_"]
# DM4 (descriptor <-> grape rules): items = descriptors from DESCRIPTOR_LEXICON found in `note` (whole word, English
#  plural of the last word: cherries, peaches; fixed 2026-11-04 after a unit test, see descriptors.term_pattern), plus the wine's canonical grape (grapes with >= 0.5% of development wines). FP-Growth on development
#  data; rules {descriptors} -> {grape} with support >= 0.5% and lift >= 2. The lexicon is fixed from standard aroma
#  vocabulary (Noble et al.'s wine aroma wheel categories), not from this dataset's scores.
DM4_MIN_SUPPORT = 0.005
DM4_MIN_LIFT = 2.0
DM4_MIN_RULES = 10
DM4_LOCKBOX_MIN_LIFT = 1.5
DESCRIPTOR_LEXICON = {
    "citrus": ["lemon", "lime", "grapefruit", "orange", "tangerine", "citrus", "zest", "lemongrass", "pith"],
    "tree fruit": ["apple", "pear", "quince", "peach", "apricot", "nectarine", "stone fruit"],
    "tropical": ["pineapple", "mango", "papaya", "passion fruit", "guava", "banana", "melon", "lychee", "tropical"],
    "red fruit": ["cherry", "raspberry", "strawberry", "cranberry", "red currant", "pomegranate", "red fruit", "rhubarb"],
    "black fruit": ["blackberry", "black cherry", "cassis", "black currant", "blueberry", "plum", "boysenberry",
                    "black fruit", "dark fruit", "mulberry"],
    "dried fruit": ["raisin", "prune", "fig", "dried fruit", "jam", "jammy"],
    "floral": ["violet", "rose", "blossom", "honeysuckle", "jasmine", "lavender", "floral", "acacia", "elderflower"],
    "herbal": ["herb", "herbal", "grass", "grassy", "green pepper", "bell pepper", "mint", "eucalyptus", "sage",
               "thyme", "tomato leaf", "sagebrush", "dill", "fennel"],
    "spice": ["pepper", "black pepper", "white pepper", "clove", "cinnamon", "nutmeg", "anise", "licorice", "spice",
              "baking spice", "ginger"],
    "oak": ["oak", "vanilla", "toast", "toasty", "smoke", "smoky", "cedar", "coconut", "caramel", "butterscotch",
            "mocha", "coffee", "espresso", "chocolate", "cocoa"],
    "earth": ["earth", "earthy", "mushroom", "forest floor", "leather", "tobacco", "tar", "graphite", "mineral",
              "minerality", "slate", "flint", "chalk", "wet stone", "petrol", "gravel", "iron"],
    "dairy / lees": ["butter", "buttery", "cream", "creamy", "brioche", "yeast", "bread", "biscuit", "lees", "almond",
                     "hazelnut", "nut", "nutty", "honey", "beeswax"],
    "savory": ["meat", "meaty", "bacon", "olive", "game", "gamy", "soy", "savory", "herbes de provence"],
}

# Phase 4 per-fold R8 sizes are reported, and CV vs final filtering differ by design (Phase 3 critic round 2, N7).

# --- Phase 4 outcomes of the selection rules (the notebook asserts that its run reproduces them) ---
# REVISION 2 of the DM1 selection (2026-11-07, written BEFORE the runs below; critic round 1 #1). All outer-fold results of
# revision 1 have been seen, and the critic also saw outer results for a calibrated ridge, so this is a post-hoc revised
# parameter setting (CRISP-DM 4.4), not a fresh test. The lockbox stays the only unbiased estimate.
#  Repaired inner design: an anonymous note goes to the inner fold of its top-guess critic, so it is held out with that
#  writer (top guess in the outer held-out fold or the lockbox: random, as before). Metrics are on named rows only.
#  Candidates: ridge; calibrated ridge (a + b * OOF ridge score, OLS, fitted on all OOF rows, or on named OOF rows only);
#  stack; stack without origin inputs.
#  Rule: (1) lowest mean inner critic-held-out MAE over the four outer training sets, using no outer test row; within 0.01
#  points, the simpler candidate wins (SIMPLICITY_ORDER). (2) The winner must then meet the DM1 and BSC2 targets in every
#  outer fold; if it fails, the next candidate by inner MAE is taken and the failure is reported. Outer results of the
#  other candidates are reported but do not choose.
# Phase 5 refits each selected model with the SAME procedure on all development data (inner folds = the four named
# development folds + anonymous notes) and scores the lockbox once (R-3 against all development titles).
SELECTED_DM1 = "calibrated ridge (all OOF)"   # revision 2: lowest inner critic-held-out MAE, and meets targets in every outer fold (rev. 1: stack)
SELECTED_DM2 = "ridge + log price"     # all three rankers meet BSC1 in every fold; within 0.01 of the best, simplest wins
SELECTED_DM3 = ("nmf", 8)              # same k in revisions 1 and 2; see DM3_VOCABULARY for what changed
# 4.4 revised parameter setting for DM3 (dated 2026-11-04, after viewing the pre-registered profiles: two were led by
# grape names, two held verdict words): clustering.revised_stopwords() added to the vocabulary filter, same selection
# rule. It also selects ("nmf", 8). Phase 5 (BSC3 blind naming) uses the REVISED setting; both runs are reported.
# Superseded for the primary setting by revision 2 below; the revised filter stays as the secondary setting.
# REVISION 2 of the DM3 stability test (2026-11-07, written BEFORE these runs; critic round 1 #3). The frozen rule used one
# winery split (seed SEED); other seeds fail, and the same writers appear on both sides of every winery split.
#  Settings: vocabulary = pre-registered / revised (above) / lexicon (only the frozen DESCRIPTOR_LEXICON terms);
#  fit set = all development notes / writer-capped (each critic, and the anonymous notes as one group, capped at
#  DM3_WRITER_CAP notes). NMF and k-means, k in DM3_K_RANGE.
#  Rule per setting: the largest k with every profile >= 1% and, in at least DM3_MIN_SEEDS_PASSING of DM3_N_SEEDS winery splits,
#  EVERY matched Jaccard >= 0.5. A setting without such a k fails.
#  Writer independence: at that k, three critic-disjoint splits of the named development folds ({0,1} v {3,4}, {0,3} v
#  {1,4}, {0,4} v {1,3}). Bar: mean matched Jaccard >= 0.5. Among settings that pass the seed rule, the highest critic-
#  disjoint mean is selected. If no setting passes the seed rule, BSC3 stability is reported as FAILED in development;
#  if none reaches the critic-disjoint bar, the profiles are reported as not shown to be independent of writers.
DM3_N_SEEDS = 10
DM3_MIN_SEEDS_PASSING = 8
DM3_WRITER_CAP = 5000
# BSC3 in Phase 5 is decided on the PRIMARY setting only; the secondary is reported and cannot rescue a primary failure.
# Outcome of the rule: lexicon vocabulary, all development notes, NMF, k = 8 (10 of 10 splits; critic-disjoint mean 0.23, below
# the 0.5 bar, so writer independence is NOT shown). Phase 5 blind naming: primary = this setting, secondary = revised
# vocabulary, all notes, NMF, k = 8. Reviewers see term lists only, never the report or the analyst's labels.
DM3_VOCABULARY = "lexicon"
DM3_FIT_SET = "all"
DM3_SECONDARY = ("revised", "all", "nmf", 8)
SIMPLICITY_ORDER = ["ridge", "calibrated ridge (all OOF)", "calibrated ridge (named OOF)", "stack, no origin", "stack", "ridge + log price",
                    "stack P(90+) + log price", "stack P(90+) + log price + winery record"]
# BSC4 outputs, fixed before Phase 5 (critic round 1 #15): see evaluate.app_mappings
SCORE_BAND_COVERAGE = 0.80
