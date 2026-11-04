"""The fixed set of simple shortlist rules (frozen in Phase 1).

Every rule uses only what a buyer knows at decision time: the candidate's price,
origin and grape, and the past critic scores in the training data. The benchmark
for BSC1 is the best of these rules on the evaluation pool. Ties are broken at
random by the evaluator.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .models import GroupMeanBaseline

SIMPLE_RULES = (
    "price (pricier first)",
    "winery track record",
    "province track record",
    "variety × country",
    "winery track record, then price",
)


def simple_rule_scores(train: pd.DataFrame, pool: pd.DataFrame) -> dict[str, np.ndarray]:
    """Score every pool wine under each simple rule (higher = sample first)."""
    y = train["points"]
    winery = GroupMeanBaseline(keys=("winery",)).fit(train, y).predict(pool)
    price = pool["price"].to_numpy(dtype=float)
    return {
        "price (pricier first)": price,
        "winery track record": winery,
        "province track record": GroupMeanBaseline(keys=("province",)).fit(train, y).predict(pool),
        "variety × country": GroupMeanBaseline().fit(train, y).predict(pool),
        # lexicographic: winery history first, then price as tie-breaker (price < $1,000, so /1e4 never overrides)
        "winery track record, then price": winery + price / 1e4,
    }
