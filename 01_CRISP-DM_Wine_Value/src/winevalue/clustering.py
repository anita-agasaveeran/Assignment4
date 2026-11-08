"""Phase 4 DM3: flavour profiles from tasting notes (text only, development notes only).

NMF and k-means on TF-IDF of ``note``. Stability (the BSC3 lower-bound condition): fit on two disjoint halves, match
profiles with the Hungarian algorithm on top-term Jaccard. Revision 1 used one winery split; revision 2 uses
``DM3_N_SEEDS`` winery splits plus critic-disjoint splits, because the same writers sit on both sides of a winery split.
Rules are in ``config`` (DM3_*).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment
from sklearn.cluster import MiniBatchKMeans
from sklearn.decomposition import NMF
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, TfidfVectorizer
from sklearn.preprocessing import normalize

from . import config


def revised_stopwords() -> list[str]:
    """4.4 REVISED parameter setting (2026-11-04, after viewing the pre-registered profiles, two of which were led by
    grape names and two contained verdict words). Fixed by rule, not by hand: tokens of every grape name in the frozen
    grape tables (``grapes.RED``, ``WHITE``, ``SYNONYMS``), minus English stop words and minus any token of the frozen
    descriptor lexicon (so "black", "orange", "melon" stay), plus the single words of the frozen Phase 1 evaluative list."""
    import re
    from . import grapes
    names = set(grapes.RED) | set(grapes.WHITE) | set(grapes.SYNONYMS) | set(grapes.SYNONYMS.values())
    lexicon = {w for terms in config.DESCRIPTOR_LEXICON.values() for t in terms for w in t.split()}
    tokens = {w.lower() for n in names for w in re.findall(r"[A-Za-zÀ-ÿ]+", n) if len(w) > 2}
    tokens -= set(ENGLISH_STOP_WORDS) | lexicon
    return sorted(tokens | {t for t in config.EVALUATIVE_TERMS if " " not in t})


def profile_vectorizer(notes: pd.Series, extra_stop=()) -> TfidfVectorizer:
    stop = sorted(set(ENGLISH_STOP_WORDS) | set(config.PROFILE_STOPWORDS) | set(extra_stop))
    return TfidfVectorizer(stop_words=stop, ngram_range=(1, 2), min_df=20, max_features=5000, sublinear_tf=True,
                           token_pattern=r"(?u)\b[a-zA-Z][a-zA-Z'-]+\b").fit(notes)


def fit_profiles(X, k: int, method: str, seed: int = config.SEED):
    """Returns (term weights per profile [k x terms], assignment per note)."""
    if method == "nmf":
        m = NMF(n_components=k, init="nndsvda", random_state=seed, max_iter=400)
        W = m.fit_transform(X)
        return m.components_, W.argmax(1), W
    if method == "kmeans":
        Xn = normalize(X)
        m = MiniBatchKMeans(n_clusters=k, random_state=seed, n_init=3, batch_size=4096).fit(Xn)
        return m.cluster_centers_, m.labels_, None
    raise ValueError(method)


def doc_term(df: pd.DataFrame, vocabulary: str):
    """Document-term matrix and vocabulary for a DM3 setting: 'pre-registered', 'revised' or 'lexicon'."""
    if vocabulary == "lexicon":
        from sklearn.feature_extraction.text import TfidfTransformer
        from .descriptors import item_matrix
        items = item_matrix(df, grapes=[])
        X = TfidfTransformer(sublinear_tf=True).fit_transform(items.to_numpy(dtype=float))
        return X.tocsr(), np.array([c[2:] for c in items.columns])
    vec = profile_vectorizer(df["note"], revised_stopwords() if vocabulary == "revised" else ())
    return vec.transform(df["note"]), vec.get_feature_names_out()


def writer_capped(df: pd.DataFrame, cap: int = config.DM3_WRITER_CAP, seed: int = config.SEED) -> np.ndarray:
    """Positions of a sample with at most ``cap`` notes per critic (the anonymous notes count as one group)."""
    w = df["critic"].fillna("(anonymous)").to_numpy()
    rng = np.random.default_rng([seed, 6])
    keep = [rng.permutation(np.flatnonzero(w == c))[:cap] for c in np.unique(w)]
    return np.sort(np.concatenate(keep))


def winery_half(wineries: pd.Series, seed: int) -> np.ndarray:
    """Boolean half of the rows, split by winery. ``seed = SEED`` reproduces the revision 1 split."""
    uniq = pd.Series(wineries.unique())
    rng = np.random.default_rng([seed, 3])
    return wineries.isin(set(uniq[rng.random(len(uniq)) < 0.5])).to_numpy()


def critic_disjoint_splits(folds: pd.Series) -> list[tuple[np.ndarray, np.ndarray]]:
    """The three splits of the named development folds into two pairs; anonymous notes are in neither half."""
    f = folds.to_numpy()
    return [(np.isin(f, a), np.isin(f, b)) for a, b in (((0, 1), (3, 4)), ((0, 3), (1, 4)), ((0, 4), (1, 3)))]


def split_jaccards(X, vocab, half_a, half_b, k: int, method: str, seed: int = config.SEED) -> np.ndarray:
    Ha, _, _ = fit_profiles(X[half_a], k, method, seed)
    Hb, _, _ = fit_profiles(X[half_b], k, method, seed)
    return matched_jaccard(top_terms(Ha, vocab), top_terms(Hb, vocab))


def seed_stability(df: pd.DataFrame, X, vocab, ks=config.DM3_K_RANGE, methods=("nmf", "kmeans"), n_seeds: int = config.DM3_N_SEEDS,
                   seed: int = config.SEED, n_jobs: int = -1) -> pd.DataFrame:
    """One row per (method, k, split seed): minimum and mean matched Jaccard over winery-disjoint halves, plus the
    smallest profile share of the full fit."""
    from joblib import Parallel, delayed

    def one(method, k, i):
        a = winery_half(df["winery_key"], seed + i)
        mj = split_jaccards(X, vocab, a, ~a, k, method, seed)
        return {"method": method, "k": k, "split": i, "min J": mj.min(), "mean J": mj.mean(), "passes": bool((mj >= config.DM3_MIN_JACCARD).all())}

    def share(method, k):
        _, lab, _ = fit_profiles(X, k, method, seed)
        return {"method": method, "k": k, "smallest share": (np.bincount(lab, minlength=k) / len(lab)).min()}

    runs = pd.DataFrame(Parallel(n_jobs=n_jobs)(delayed(one)(m, k, i) for m in methods for k in ks for i in range(n_seeds)))
    shares = pd.DataFrame(Parallel(n_jobs=n_jobs)(delayed(share)(m, k) for m in methods for k in ks))
    return runs.merge(shares, on=["method", "k"])


def choose_k_seeds(runs: pd.DataFrame) -> pd.DataFrame:
    """Revision 2 rule per method: the largest k with every profile >= 1% and at least DM3_MIN_SEEDS_PASSING splits with
    every matched Jaccard >= 0.5. One row per method; k is NaN if none qualifies (``best`` is the most stable k)."""
    s = runs.groupby(["method", "k"]).agg(splits_passing=("passes", "sum"), min_J=("min J", "min"), median_min_J=("min J", "median"),
                                          mean_J=("mean J", "mean"), smallest_share=("smallest share", "first")).reset_index()
    out = []
    for method, t in s.groupby("method"):
        ok = t[(t["smallest_share"] >= config.DM3_MIN_SHARE) & (t["splits_passing"] >= config.DM3_MIN_SEEDS_PASSING)]
        best = t.sort_values(["splits_passing", "median_min_J"], ascending=False).iloc[0]
        row = ok.loc[ok["k"].idxmax()] if len(ok) else best
        out.append({**row.to_dict(), "passes rule": bool(len(ok))})
    return pd.DataFrame(out)


def matched_null(doc_freq: np.ndarray, k: int, n_terms: int = config.DM3_TOP_TERMS, n_sims: int = 500,
                 seed: int = config.SEED) -> dict:
    """Chance level of the matched mean Jaccard: two fits of k random top-term sets (drawn without replacement, with
    probability proportional to ``doc_freq``), Hungarian-matched. ``doc_freq`` uniform gives the uniform null."""
    rng = np.random.default_rng([seed, 7])
    p = np.asarray(doc_freq, dtype=float) / np.sum(doc_freq)
    draw = lambda: [list(rng.choice(len(p), n_terms, replace=False, p=p)) for _ in range(k)]
    m = np.array([matched_jaccard(draw(), draw()).mean() for _ in range(n_sims)])
    return {"mean": float(m.mean()), "95th percentile": float(np.quantile(m, 0.95))}


def critic_disjoint_stability(df: pd.DataFrame, X, vocab, k: int, method: str, seed: int = config.SEED) -> pd.DataFrame:
    rows = []
    for i, (a, b) in enumerate(critic_disjoint_splits(df["fold"])):
        mj = split_jaccards(X, vocab, a, b, k, method, seed)
        rows.append({"split": i, "min J": mj.min(), "mean J": mj.mean(), "profiles J >= 0.5": int((mj >= config.DM3_MIN_JACCARD).sum())})
    return pd.DataFrame(rows)


def writer_association(labels: np.ndarray, df: pd.DataFrame) -> dict:
    """Cramer's V of profile with critic and with colour, and each profile's largest writer share against that writer's base."""
    from scipy.stats import chi2_contingency

    def v(a, b):
        t = pd.crosstab(a, b).to_numpy()
        return float(np.sqrt(chi2_contingency(t)[0] / (t.sum() * (min(t.shape) - 1))))
    w = df["critic"].fillna("(anonymous)")
    base = w.value_counts(normalize=True)
    tab = pd.crosstab(pd.Series(labels, index=df.index, name="profile"), w, normalize="index")
    top = pd.DataFrame({"top writer": tab.idxmax(1), "share": tab.max(1)})
    top["writer base share"] = top["top writer"].map(base)
    return {"V critic": v(labels, w), "V colour": v(labels, df["colour"]), "by profile": top}


def top_terms(H, vocab, n: int = config.DM3_TOP_TERMS) -> list[list[str]]:
    return [[vocab[j] for j in np.argsort(-row)[:n]] for row in H]


def matched_jaccard(terms_a, terms_b) -> np.ndarray:
    """Hungarian matching of profiles between two fits on top-term Jaccard; returns the matched Jaccards."""
    J = np.array([[len(set(a) & set(b)) / len(set(a) | set(b)) for b in terms_b] for a in terms_a])
    r, c = linear_sum_assignment(-J)
    return J[r, c]


def dm3_settings(dev: pd.DataFrame, n_jobs: int = -1, seed: int = config.SEED) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Revision 2 scan over vocabulary x fit set x method. Returns (one row per setting and method at its chosen k, with the
    critic-disjoint result; all split-level runs)."""
    rows, runs_all = [], []
    for vocabulary in ("pre-registered", "revised", "lexicon"):
        for fit_set in ("all", "capped"):
            d = dev.iloc[writer_capped(dev, seed=seed)] if fit_set == "capped" else dev
            X, vocab = doc_term(d, vocabulary)
            keep = np.asarray(X.sum(1)).ravel() > 0
            d, X = d[keep], X[keep]
            runs = seed_stability(d, X, vocab, seed=seed, n_jobs=n_jobs)
            runs_all.append(runs.assign(vocabulary=vocabulary, fit_set=fit_set))
            for _, r in choose_k_seeds(runs).iterrows():
                cd = critic_disjoint_stability(d, X, vocab, int(r["k"]), r["method"], seed)
                rows.append({"vocabulary": vocabulary, "fit set": fit_set, "notes": len(d), **r.to_dict(),
                             "critic-disjoint mean J": cd["mean J"].mean(), "critic-disjoint best split": cd["mean J"].max()})
    return pd.DataFrame(rows), pd.concat(runs_all, ignore_index=True)


def choose_dm3(table: pd.DataFrame) -> pd.Series | None:
    """Revision 2 rule: among settings passing the seed rule, the highest critic-disjoint mean. None if nothing passes."""
    ok = table[table["passes rule"]]
    return None if ok.empty else ok.loc[ok["critic-disjoint mean J"].idxmax()]


def umass_coherence(X, terms_idx: list[list[int]]) -> np.ndarray:
    """UMass coherence per profile on binary document frequencies of its top terms (higher, i.e. closer to 0, is better)."""
    B = (X > 0).astype(np.int32).tocsc()
    out = []
    for idx in terms_idx:
        v, n = [], len(idx)
        for i in range(1, n):
            for j in range(i):
                dj = B[:, idx[j]].sum()
                co = B[:, idx[i]].multiply(B[:, idx[j]]).sum()
                v.append(np.log((co + 1) / max(dj, 1)))
        out.append(np.mean(v))
    return np.array(out)


def profile_summary(df: pd.DataFrame, k: int, method: str = "nmf", vocabulary: str = "lexicon", seed: int = config.SEED,
                    n_sil: int = 5000) -> dict:
    """Fit a profile model on all of ``df``: top terms, shares, cosine silhouette on a sample, UMass coherence, and
    weak-fit scores (NMF: strongest profile's share of a note's total weight). Notes with no vocabulary term get no profile."""
    from sklearn.metrics import silhouette_score
    X, vocab = doc_term(df, vocabulary)
    keep = np.asarray(X.sum(1)).ravel() > 0
    d, X = df[keep], X[keep]
    H, lab, W = fit_profiles(X, k, method, seed)
    terms = top_terms(H, vocab)
    share = np.bincount(lab, minlength=k) / len(lab)
    rng = np.random.default_rng([seed, 5])
    s = rng.choice(X.shape[0], size=min(n_sil, X.shape[0]), replace=False)
    pos = {t: i for i, t in enumerate(vocab)}
    out = {"terms": terms, "share": share, "labels": pd.Series(lab, index=d.index), "silhouette": float(silhouette_score(normalize(X[s]), lab[s], metric="cosine")),
           "coherence": umass_coherence(X, [[pos[t] for t in row] for row in terms]), "components": H, "vocabulary": vocab,
           "covered": float(keep.mean()), "notes": len(d)}
    if W is not None:
        out["weak_fit"] = pd.Series(W.max(1) / np.maximum(W.sum(1), 1e-12), index=d.index)
    return out


def fit_profile_model(df: pd.DataFrame, k: int, method: str = "nmf", vocabulary: str = "lexicon", seed: int = config.SEED):
    """Fit profiles on ``df`` (development notes) and return (top terms, assign) where ``assign(new_df)`` gives each new
    note's profile (-1 if it has no vocabulary term), using the transformer and model fitted on ``df`` only."""
    from sklearn.feature_extraction.text import TfidfTransformer
    from .descriptors import item_matrix
    if vocabulary == "lexicon":
        tf = TfidfTransformer(sublinear_tf=True).fit(item_matrix(df, grapes=[]).to_numpy(dtype=float))
        items = item_matrix(df.iloc[:1], grapes=[]).columns
        vocab = np.array([c[2:] for c in items])
        to_x = lambda d: tf.transform(item_matrix(d, grapes=[]).to_numpy(dtype=float)).tocsr()
    else:
        vec = profile_vectorizer(df["note"], revised_stopwords() if vocabulary == "revised" else ())
        vocab = vec.get_feature_names_out()
        to_x = lambda d: vec.transform(d["note"])
    X = to_x(df)
    keep = np.asarray(X.sum(1)).ravel() > 0
    if method != "nmf":
        raise ValueError("assignment of new notes is implemented for NMF only")
    m = NMF(n_components=k, init="nndsvda", random_state=seed, max_iter=400).fit(X[keep])

    def assign(new: pd.DataFrame) -> pd.Series:
        Xn = to_x(new)
        lab = m.transform(Xn).argmax(1)
        lab[np.asarray(Xn.sum(1)).ravel() == 0] = -1
        return pd.Series(lab, index=new.index)
    return top_terms(m.components_, vocab), assign
