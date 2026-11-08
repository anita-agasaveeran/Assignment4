"""Phase 4 DM4: descriptor <-> grape association rules (FP-Growth), text and grape labels only (no scores).

Items: descriptors from the fixed ``config.DESCRIPTOR_LEXICON`` found in ``note`` (whole word, English plural of the last word)
and the wine's canonical grape (grapes with >= DM4_MIN_SUPPORT of the mining data). Rules: {descriptors} -> {grape}.
"""

from __future__ import annotations

import re

import pandas as pd

from . import config


def descriptor_terms() -> list[str]:
    return sorted({t for terms in config.DESCRIPTOR_LEXICON.values() for t in terms})


def term_pattern(term: str) -> str:
    """Whole-word pattern with English plurals of the last word: cherry -> cherries, peach -> peaches, plum -> plums.
    (Fixed 2026-11-04 after a unit test showed the first rule, optional "s", missed "-ies"/"-es" plurals; the only
    earlier use was one smoke run, not a reported result.)"""
    head, _, last = term.rpartition(" ")
    if re.search(r"[^aeiou]y$", last):
        alt = rf"{re.escape(last[:-1])}(?:y|ies)"
    elif re.search(r"(?:s|x|z|ch|sh)$", last):
        alt = rf"{re.escape(last)}(?:es)?"
    else:
        alt = rf"{re.escape(last)}s?"
    return rf"\b{re.escape(head) + ' ' if head else ''}{alt}\b"


def item_matrix(df: pd.DataFrame, grapes: list[str] | None = None) -> pd.DataFrame:
    """Boolean item matrix: 'd:<descriptor>' columns plus 'g:<grape>' columns (``grapes`` fixed from mining data)."""
    text = df["note"].str.lower()
    cols = {f"d:{t}": text.str.contains(term_pattern(t), regex=True) for t in descriptor_terms()}
    if grapes is None:
        share = df["grape"].value_counts(normalize=True)
        grapes = sorted(share[share >= config.DM4_MIN_SUPPORT].index)
    for g in grapes:
        cols[f"g:{g}"] = df["grape"].eq(g)
    return pd.DataFrame(cols, index=df.index)


def mine_rules(items: pd.DataFrame, min_support: float = config.DM4_MIN_SUPPORT,
               min_lift: float = config.DM4_MIN_LIFT) -> pd.DataFrame:
    """FP-Growth, then rules whose antecedents are descriptors only and whose consequent is one grape."""
    from mlxtend.frequent_patterns import association_rules, fpgrowth
    fi = fpgrowth(items, min_support=min_support, use_colnames=True, max_len=4)
    rules = association_rules(fi, metric="lift", min_threshold=min_lift)
    keep = rules["consequents"].map(lambda c: len(c) == 1 and next(iter(c)).startswith("g:")) & \
        rules["antecedents"].map(lambda a: all(x.startswith("d:") for x in a))
    r = rules[keep].copy()
    r["antecedents"] = r["antecedents"].map(lambda a: " + ".join(sorted(x[2:] for x in a)))
    r["consequents"] = r["consequents"].map(lambda c: next(iter(c))[2:])
    return r[["antecedents", "consequents", "support", "confidence", "lift"]].sort_values("lift", ascending=False).reset_index(drop=True)


def rule_stats_on(items: pd.DataFrame, rules: pd.DataFrame) -> pd.DataFrame:
    """Support, confidence and lift of already-mined rules on OTHER data (replication check)."""
    out = []
    for a, c in zip(rules["antecedents"], rules["consequents"]):
        ant = items[[f"d:{x}" for x in a.split(" + ")]].all(axis=1)
        con = items[f"g:{c}"] if f"g:{c}" in items else pd.Series(False, index=items.index)
        sup, pa, pc = (ant & con).mean(), ant.mean(), con.mean()
        out.append({"support": sup, "confidence": sup / pa if pa else float("nan"),
                    "lift": sup / (pa * pc) if pa and pc else float("nan")})
    return pd.DataFrame(out, index=rules.index)


def prune_rules(rules: pd.DataFrame) -> pd.DataFrame:
    """Drop a multi-descriptor rule when a rule with a subset of its descriptors and the same consequent has lift at least as high."""
    best = {(a, c): l for a, c, l in zip(rules["antecedents"], rules["consequents"], rules["lift"])}
    keep = []
    for a, c, l in zip(rules["antecedents"], rules["consequents"], rules["lift"]):
        parts = a.split(" + ")
        keep.append(not any(p != a and best.get((p, c), -1) >= l for p in parts))
    return rules[keep].reset_index(drop=True)
