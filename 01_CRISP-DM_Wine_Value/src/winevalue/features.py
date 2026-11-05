"""Phase 3 (Data Preparation): deduplication, vintage/origin features, rare-category grouping, text preprocessing.

Scaffold only. Functions get added when that phase is worked on.
"""

# ---- Phase 3: model-ready inputs (used by Phase 4) ----
# One grape encoding (canonical grape + a "label differs" flag) instead of raw variety AND grape (critic round 1, #9)
QUALITY_INPUTS_V2 = ["note", "country", "province_model", "grape", "label_differs", "colour", "vintage", "is_nonvintage",
                     "n_words", "has_designation", "has_region_1"]
RANKER_INPUTS_V2 = QUALITY_INPUTS_V2 + ["price"]


def build_preprocessor(with_price: bool = False):
    """ColumnTransformer for the prepared table. Fit it INSIDE each training fold only (pipelines do this)."""
    import numpy as np
    from sklearn.compose import ColumnTransformer
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.impute import SimpleImputer
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, StandardScaler
    parts = [
        ("text", TfidfVectorizer(min_df=5, ngram_range=(1, 2), max_features=100_000, sublinear_tf=True), "note"),
        ("cat", OneHotEncoder(handle_unknown="infrequent_if_exist", min_frequency=20),
         ["country", "province_model", "grape", "colour"]),
        ("num", make_pipeline(SimpleImputer(strategy="median"), StandardScaler()), ["vintage", "n_words"]),
        ("flags", "passthrough", ["is_nonvintage", "has_designation", "has_region_1", "label_differs"]),
    ]
    if with_price:
        parts.append(("log_price", make_pipeline(SimpleImputer(strategy="median"), FunctionTransformer(np.log), StandardScaler()), ["price"]))
    return ColumnTransformer(parts)
