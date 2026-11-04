"""Evaluation splits, fixed in Phase 1 so later phases can't tune on the test set.

Deployment scenario: tasting notes come from writers whose notes the
model has never seen. So the primary split is **by critic**:
- Named critics are dealt into ``N_FOLDS`` groups with balanced row
  counts (largest critic first, into the currently smallest group).
- One group is the **lockbox**, scored once in Phase 5 (Evaluation). It's
  drawn with ``config.SEED`` from the groups with at least
  ``MIN_LOCKBOX_CRITICS`` critics, so the final test covers several writing
  styles (the largest critic alone writes about 25% of named reviews).
- The other groups are the cross-validation folds for Phases 1–4.
- Anonymous reviews (no ``taster_name``) can't be grouped by writer,
  so they are only ever used for training.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .config import SEED

N_FOLDS = 5
ANONYMOUS = "(anonymous)"
MIN_LOCKBOX_CRITICS = 3


def critic_folds(taster_name: pd.Series, n_folds: int = N_FOLDS, seed: int = SEED,
                 min_lockbox_critics: int = MIN_LOCKBOX_CRITICS) -> tuple[dict, int]:
    """Assign every named critic to a fold, and pick the lockbox fold.

    Returns ``(critic -> fold, lockbox_fold)``. The result is deterministic:
    critics are ordered by review count (ties by name) and greedily put
    into the fold with the fewest rows so far.
    """
    counts = taster_name.dropna().value_counts()
    order = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    load = [0] * n_folds
    mapping = {}
    for critic, n in order:
        f = int(np.argmin(load))
        mapping[critic] = f
        load[f] += n
    critics_per_fold = pd.Series(mapping).value_counts()
    eligible = sorted(critics_per_fold[critics_per_fold >= min_lockbox_critics].index)
    if not eligible:
        raise ValueError("No fold has enough critics to serve as the lockbox")
    lockbox = int(eligible[np.random.default_rng(seed).integers(len(eligible))])
    return mapping, lockbox


def assign_folds(df: pd.DataFrame) -> pd.Series:
    """Fold number per review: 0..N_FOLDS-1 for named critics, -1 for anonymous reviews."""
    mapping, _ = critic_folds(df["taster_name"])
    return df["taster_name"].map(mapping).fillna(-1).astype(int)


def drop_titles_seen_in_training(test: pd.DataFrame, train: pd.DataFrame) -> pd.DataFrame:
    """Remove test reviews whose wine ``title`` also appears in the training data.

    Critic-defined folds can't keep every repeat title in one fold (124 titles
    span folds), so evaluation drops those rows from the test side instead (R-3).
    """
    return test[~test["title"].isin(set(train["title"]))]
