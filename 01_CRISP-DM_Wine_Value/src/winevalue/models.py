"""Score models.

Phase 1 adds the two reference points used to size the problem:
- ``GroupMeanBaseline``: a buyer's rule of thumb ("Napa Cabernet averages 89").
- ``quick_text_model``: a plain TF-IDF + ridge model, to check feasibility.
Phase 4 adds the tuned models.

The quality model never uses ``taster_name`` (new notes come from writers the
model has never seen). It also excludes ``price`` by default, because the value
verdict compares predicted quality with price. ``with_price=True`` is allowed
only for the shortlist *ranker* (DM2), where price is a legitimate input known
at decision time. See Phase 1, requirement R-2.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, StandardScaler

QUALITY_INPUTS = ["description", "country", "province", "variety", "vintage"]
RANKER_INPUTS = QUALITY_INPUTS + ["price"]


class GroupMeanBaseline(BaseEstimator, RegressorMixin):
    """Mean score per group (default variety x country), shrunk toward the global mean.

    prediction = (n * group_mean + shrink * global_mean) / (n + shrink).
    Unseen groups get the global mean.
    """

    def __init__(self, keys=("variety", "country"), shrink: float = 20.0):
        self.keys = keys
        self.shrink = shrink

    def fit(self, X: pd.DataFrame, y):
        y = pd.Series(np.asarray(y, dtype=float), index=X.index)
        self.global_mean_ = float(y.mean())
        stats = y.groupby([X[k].fillna("NA") for k in self.keys]).agg(["mean", "count"])
        self.table_ = ((stats["mean"] * stats["count"] + self.global_mean_ * self.shrink)
                       / (stats["count"] + self.shrink)).to_dict()
        return self

    def predict(self, X: pd.DataFrame):
        keys = zip(*[X[k].fillna("NA") for k in self.keys])
        return np.array([self.table_.get(k if len(self.keys) > 1 else k[0], self.global_mean_) for k in keys])


def quick_text_model(alpha: float = 1.5, with_price: bool = False):
    """TF-IDF (1-2 grams) on the tasting note + one-hot origin/variety + vintage -> ridge.

    ``with_price`` adds log(price) (median-imputed). Use it only for the DM2 ranker.
    """
    extra = [("log_price", make_pipeline(SimpleImputer(strategy="median"),
                                         FunctionTransformer(np.log), StandardScaler()), ["price"])] if with_price else []
    pre = ColumnTransformer([
        ("text", TfidfVectorizer(min_df=5, ngram_range=(1, 2), max_features=60_000, sublinear_tf=True), "description"),
        ("cat", make_pipeline(SimpleImputer(strategy="constant", fill_value="NA"),
                              OneHotEncoder(handle_unknown="infrequent_if_exist", min_frequency=20)),
         ["country", "province", "variety"]),
        ("vintage", make_pipeline(SimpleImputer(strategy="median"), StandardScaler()), ["vintage"]),
        *extra,
    ])
    return make_pipeline(pre, Ridge(alpha=alpha))


def mask_evaluative(texts: pd.Series, terms=None, patterns=None) -> pd.Series:
    """Mask evaluative language: drinking-window patterns first, then verdict words.

    Defaults to ``config.EVALUATIVE_PATTERNS`` and ``config.EVALUATIVE_TERMS``.
    """
    import re
    from . import config
    terms = config.EVALUATIVE_TERMS if terms is None else terms
    patterns = config.EVALUATIVE_PATTERNS if patterns is None else patterns
    for pat in patterns:
        texts = texts.str.replace(re.compile(pat, re.IGNORECASE), " _masked_ ", regex=True)
    return mask_terms(texts, terms)


def mask_terms(texts: pd.Series, terms) -> pd.Series:
    """Replace whole-word occurrences of ``terms`` (case-insensitive) with a neutral token.

    Used for the evaluative-language test (Phase 1, DM1b): how much signal is left
    once words that state a verdict ("superb", "simple", "drink now") are removed?
    """
    import re
    pattern = re.compile(r"\b(" + "|".join(sorted(map(re.escape, terms), key=len, reverse=True)) + r")\b", re.IGNORECASE)
    return texts.str.replace(pattern, " _masked_ ", regex=True)
