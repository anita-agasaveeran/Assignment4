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
    """DERIVATION ONLY (Phase 1 record): assign every named critic to a fold and pick the lockbox fold.

    The pipeline never calls this; it uses the frozen ``config.CRITIC_FOLDS`` / ``LOCKBOX_FOLD`` via ``assign_folds``.
    The result depends on the input frame (raw vs de-duplicated give different lockboxes), which is why it is frozen.

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


def _norm_name(s: pd.Series) -> pd.Series:
    return s.str.replace("\xa0", " ", regex=False).str.replace(r"\s+", " ", regex=True).str.strip()


def assign_folds(df: pd.DataFrame) -> pd.Series:
    """Fold number per review from the FROZEN mapping (config.CRITIC_FOLDS); -1 for anonymous reviews.

    Raises on a critic that isn't in the frozen mapping, so a new writer can never silently join a fold.
    """
    from .config import CRITIC_FOLDS
    names = _norm_name(df["taster_name"])
    unknown = set(names.dropna()) - set(CRITIC_FOLDS)
    if unknown:
        raise ValueError(f"critics not in the frozen fold mapping: {sorted(unknown)}")
    return names.map(CRITIC_FOLDS).fillna(-1).astype(int)


def drop_titles_seen_in_training(test: pd.DataFrame, train: pd.DataFrame) -> pd.DataFrame:
    """Remove test reviews whose wine ``title`` also appears in the training data.

    Critic-defined folds can't keep every repeat title in one fold (124 titles span folds), so evaluation drops
    those rows from the test side instead (R-3). It matches on TITLE ONLY, deliberately more conservative than the
    title + variety wine key of Phase 2 (it also drops a different wine sold under the same title).
    """
    return test[~test["title"].isin(set(train["title"]))]


def anon_attribution(df: pd.DataFrame, seed: int = SEED) -> pd.DataFrame:
    """Top-guess critic and probability for every anonymous note, from a text classifier on named notes (Phase 1 R8).

    Uses note text and critic names only (no scores). Returns columns ``critic`` (normalised name) and ``p``.
    """
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import SGDClassifier
    from sklearn.model_selection import train_test_split
    named = df[df["taster_name"].notna()]
    tr, _ = train_test_split(named, test_size=0.2, random_state=seed, stratify=named["taster_name"])
    vec = TfidfVectorizer(min_df=3, ngram_range=(1, 2), max_features=100_000, sublinear_tf=True).fit(tr["description"])
    clf = SGDClassifier(loss="log_loss", alpha=2e-6, max_iter=30, random_state=seed).fit(vec.transform(tr["description"]), tr["taster_name"])
    anon = df[df["taster_name"].isna()]
    proba = clf.predict_proba(vec.transform(anon["description"]))
    return pd.DataFrame({"critic": _norm_name(pd.Series(clf.classes_[proba.argmax(1)])).to_numpy(), "p": proba.max(1)}, index=anon.index)


def anon_lockbox_like(df: pd.DataFrame, threshold: float | None = None, seed: int = SEED,
                      critics=None, attribution: pd.DataFrame | None = None) -> pd.Index:
    """Anonymous reviews whose writing style a text classifier attributes to one of ``critics`` (Phase 1 R8).

    ``critics`` defaults to the frozen lockbox critics (``config.LOCKBOX_CRITICS``); Phase 4 CV passes each development
    fold's critics instead (pre-registered in report §3.5; critic round 2 N7). Uses note text and critic names only
    (no scores). The default threshold is config.ATTRIBUTION_THRESHOLD.
    """
    from .config import ATTRIBUTION_THRESHOLD, LOCKBOX_CRITICS
    threshold = ATTRIBUTION_THRESHOLD if threshold is None else threshold
    critics = LOCKBOX_CRITICS if critics is None else list(critics)
    a = anon_attribution(df, seed) if attribution is None else attribution
    return a.index[(a["p"] > threshold) & a["critic"].isin(critics)]
