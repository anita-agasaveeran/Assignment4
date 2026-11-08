"""Phase 4 test design: critic-grouped outer CV on development data, inner folds for tuning and stacking.

Design in ``config`` (Phase 4 block; history in reports/phase4_run_log.md). The lockbox (fold 2) never enters.

- Outer fold f: train = other development folds + anonymous notes, minus anonymous notes attributed to fold f's
  critics (per-fold R8); test = fold f minus titles seen in training (R-3).
- Inner folds (inside an outer training set): the remaining named folds. Each anonymous note goes to the inner fold of
  its top-guess critic, so it is held out together with that writer (revision 2); notes whose top guess is in the outer
  held-out fold or the lockbox go to a random inner fold. A title's anonymous copies stay together.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import config
from .splits import anon_attribution, anon_lockbox_like, drop_titles_seen_in_training


def fold_critics(fold: int) -> list[str]:
    return sorted(c for c, f in config.CRITIC_FOLDS.items() if f == fold)


def per_fold_anon_drop(prep: pd.DataFrame, attribution: pd.DataFrame | None = None) -> dict[int, pd.Index]:
    """Anonymous notes attributed (p > threshold) to each development fold's critics (text only, no scores)."""
    a = anon_attribution(prep) if attribution is None else attribution
    return {f: anon_lockbox_like(prep, critics=fold_critics(f), attribution=a) for f in config.OUTER_FOLDS}


def top_guess_fold(attribution: pd.DataFrame) -> pd.Series:
    """Critic fold of each anonymous note's top-guess critic (includes the lockbox fold; used only to place notes)."""
    return attribution["critic"].map(config.CRITIC_FOLDS)


def development(prep: pd.DataFrame) -> pd.DataFrame:
    dev = prep[~prep["is_lockbox"]]
    assert not dev["fold"].eq(config.LOCKBOX_FOLD).any()
    return dev


def outer_split(prep: pd.DataFrame, fold: int, anon_drop: dict[int, pd.Index]) -> tuple[pd.DataFrame, pd.DataFrame]:
    if fold not in config.OUTER_FOLDS:
        raise ValueError(f"fold {fold} is not a development CV fold")
    dev = development(prep)
    train = dev[(dev["fold"] != fold) & ~dev.index.isin(anon_drop[fold])]
    test = drop_titles_seen_in_training(dev[dev["fold"] == fold], train)
    return train, test


def inner_groups(train: pd.DataFrame, seed: int = config.SEED, top_fold: pd.Series | None = None) -> pd.Series:
    """Inner fold label per training row: the critic fold for named rows. Anonymous rows are placed by title: a random
    named fold, or, with ``top_fold``, the inner fold of the title's most common top-guess fold when that is one of the
    inner folds (so an anonymous note is held out with its likely writer)."""
    named = sorted(f for f in train["fold"].unique() if f >= 0)
    g = train["fold"].copy()
    anon = train["fold"].eq(-1)
    titles = pd.Series(train.loc[anon, "title"].unique())
    rng = np.random.default_rng([seed, 4])
    pick = dict(zip(titles, rng.choice(named, size=len(titles))))
    if top_fold is not None:
        t = pd.DataFrame({"title": train.loc[anon, "title"], "f": top_fold.reindex(train.index[anon])})
        t = t[t["f"].isin(named)]
        pick.update(t.groupby("title")["f"].agg(lambda s: s.value_counts().index[0]).to_dict())
    g[anon] = train.loc[anon, "title"].map(pick).astype(int)
    return g


def inner_splits(train: pd.DataFrame, groups: pd.Series):
    """Yield (inner_train, inner_valid) with R-3 applied to the validation side."""
    for g in sorted(groups.unique()):
        itr = train[groups != g]
        iva = drop_titles_seen_in_training(train[groups == g], itr)
        yield g, itr, iva


def oof_predict(train: pd.DataFrame, groups: pd.Series, fit_predict) -> pd.Series:
    """Out-of-fold predictions for every training row: ``fit_predict(fit_rows, predict_rows) -> array``.

    No R-3 filter here (every row needs a prediction); rows whose title also appears in another inner fold are
    predicted by a model that saw that title, which makes the stacked feature slightly optimistic on training rows,
    so the stack is, if anything, under-regularised. It is judged on named inner rows and the outer test folds.
    """
    out = pd.Series(np.nan, index=train.index)
    for g in sorted(groups.unique()):
        m = groups == g
        out[m] = fit_predict(train[~m], train[m])
    return out
