"""DM5: near-duplicate notes with MinHash LSH (operational spec fixed in Phase 3, before any DM5 run).

Pipeline: 5-word shingles -> MinHash (config.DM5_NUM_PERM) -> LSH candidates at a LOOSE threshold
(config.DM5_LSH_THRESHOLD) -> EXACT Jaccard verification >= config.DM5_TAU. Exact verification means a flagged
pair always has J >= tau, so "false flags vs Jaccard" can't occur. What DM5 tests is (a) whether LSH finds the
pairs (recall on synthetic copies), (b) whether it does so cheaply (candidate share) and (c) whether flagged pairs
are useful duplicates (precision under an operational labelling rule).
"""

from __future__ import annotations

import re

import numpy as np
import pandas as pd

from . import config


def shingles(text: str, n: int = config.DM5_SHINGLE_WORDS) -> set[str]:
    w = text.lower().split()
    return {" ".join(w[i:i + n]) for i in range(max(1, len(w) - n + 1))}


def jaccard(a: set, b: set) -> float:
    return len(a & b) / len(a | b) if (a or b) else 0.0


def candidate_pairs(texts: pd.Series, threshold: float = config.DM5_LSH_THRESHOLD,
                    num_perm: int = config.DM5_NUM_PERM, seed: int = config.SEED) -> set[tuple]:
    """LSH candidate pairs (index labels), before exact verification."""
    from datasketch import MinHash, MinHashLSH
    lsh, sigs = MinHashLSH(threshold=threshold, num_perm=num_perm), {}
    for i, t in texts.items():
        m = MinHash(num_perm=num_perm, seed=seed)
        m.update_batch([s.encode() for s in shingles(t)])
        sigs[i] = m
        lsh.insert(i, m)
    return {tuple(sorted((i, j))) for i in sigs for j in lsh.query(sigs[i]) if i != j}


def detect_near_duplicates(texts: pd.Series, tau: float = config.DM5_TAU, **kw) -> pd.DataFrame:
    """Pairs with exact Jaccard >= tau (after LSH candidate generation). Columns: i, j, jaccard."""
    cand = candidate_pairs(texts, **kw)
    sh = {k: shingles(texts[k]) for p in cand for k in p}
    rows = [(i, j, jaccard(sh[i], sh[j])) for i, j in cand]
    out = pd.DataFrame(rows, columns=["i", "j", "jaccard"])
    out.attrs["n_candidates"] = len(cand)
    return out[out["jaccard"] >= tau].reset_index(drop=True)


def synthetic_copies(texts: pd.Series, n: int = config.DM5_N_SYNTH, rate=config.DM5_EDIT_RATE,
                     seed: int = config.SEED) -> pd.DataFrame:
    """The DM5(a) construction, fully specified.

    - Sample ``n`` notes from the DISTINCT notes (without replacement, ``seed``).
    - Per copy: edit rate r ~ Uniform(rate); k = max(1, round(r * n_words)) word positions chosen without
      replacement; each is replaced by a word drawn from the corpus token distribution (all words of all notes).
    - Shingles are lower-cased 5-word shingles; positives are copies with exact Jaccard >= DM5_TAU.
    """
    rng = np.random.default_rng(seed)
    distinct = texts.drop_duplicates()
    sample = distinct.sample(n, random_state=seed)
    vocab = np.array(" ".join(distinct).split())
    rows = []
    for idx, t in sample.items():
        w = t.split()
        k = max(1, int(round(rng.uniform(*rate) * len(w))))
        for pos in rng.choice(len(w), size=min(k, len(w)), replace=False):
            w[pos] = vocab[rng.integers(len(vocab))]
        copy = " ".join(w)
        rows.append((idx, copy, jaccard(shingles(t), shingles(copy))))
    return pd.DataFrame(rows, columns=["source", "copy", "jaccard"])


def _content_words(text: str) -> list[str]:
    """Lower-cased words, dropping numbers and NAMES. A name is a capitalised word that does NOT start a sentence,
    so changing a sentence's first word ("Ripe" -> "Bright") does count as a content change."""
    out, sentence_start = [], True
    for tok in re.findall(r"[A-Za-zÀ-ÿ][\w'’-]*|\d[\d.,%-]*|[.!?;]", text):
        if tok in ".!?;":
            sentence_start = True; continue
        if tok[0].isdigit():
            sentence_start = False; continue
        if tok[0].isupper() and not sentence_start:
            continue                      # a name mid-sentence
        out.append(tok.lower()); sentence_start = False
    return out


def content_word_difference(a: str, b: str) -> int:
    """Number of differing content words (multiset, symmetric) once names and numbers are removed."""
    ta, tb = _content_words(a), _content_words(b)
    from collections import Counter
    ca, cb = Counter(ta), Counter(tb)
    return sum(((ca - cb) + (cb - ca)).values())


def is_true_duplicate(row_a: pd.Series, row_b: pd.Series, max_content_diff: int = 3) -> bool:
    """DM5(c) labelling rule (fixed before any DM5 run).

    True if (i) the same wine relisted: same case-folded winery (or one winery name inside the other's title),
    same canonical grape and vintages equal or within 1 year (both NaN counts as equal); OR (ii) a recycled or
    mis-attached note: the notes differ by at most ``max_content_diff`` content words once names and numbers are
    removed. Partial reuse with more wine-specific changes is NOT a duplicate.
    """
    from .data import extract_vintage
    from .grapes import grape_canonical
    # self-contained: grape and vintage are always computed from the raw title/variety/winery
    wa, wb = str(row_a["winery"]).casefold(), str(row_b["winery"]).casefold()
    same_producer = wa == wb or wa in str(row_b["title"]).casefold() or wb in str(row_a["title"]).casefold()
    ga, gb = grape_canonical(pd.Series([row_a["variety"], row_b["variety"]])).tolist()
    va, vb = extract_vintage(pd.Series([row_a["title"], row_b["title"]]), pd.Series([row_a["winery"], row_b["winery"]])).tolist()
    close_vintage = (pd.isna(va) and pd.isna(vb)) or (pd.notna(va) and pd.notna(vb) and abs(va - vb) <= 1)
    relisting = same_producer and ga == gb and close_vintage
    recycled = content_word_difference(row_a["description"], row_b["description"]) <= max_content_diff
    return bool(relisting or recycled)


def synthetic_recall(texts: pd.Series, syn: pd.DataFrame, tau: float = config.DM5_TAU) -> dict:
    """DM5(a): add the synthetic copies to the corpus, run the detector once, and count how many positives
    (copies with exact J >= tau) are flagged as a pair with their source. Also reports recall in the 0.5-0.6 band
    (Phase 3 critic round 2, N5: (a) mostly checks the implementation, so the hardest band is shown separately)."""
    pos = syn[syn["jaccard"] >= tau].reset_index(drop=True)
    base = texts.reset_index(drop=True)
    src_pos = base.index[pd.Index(texts.index).get_indexer(pos["source"])]
    copies = pd.Series(pos["copy"].to_numpy(), index=range(len(base), len(base) + len(pos)))
    pairs = detect_near_duplicates(pd.concat([base, copies]), tau=tau)
    found = set(map(tuple, np.sort(pairs[["i", "j"]].to_numpy(), axis=1)))
    hit = np.array([tuple(sorted((s, c))) in found for s, c in zip(src_pos, copies.index)])
    band = (pos["jaccard"] < 0.6).to_numpy()
    return {"positives": len(pos), "recall": float(hit.mean()), "band 0.5-0.6 positives": int(band.sum()),
            "band 0.5-0.6 recall": float(hit[band].mean()) if band.any() else float("nan"),
            "passes": bool(hit.mean() >= config.DM5_MIN_RECALL)}
