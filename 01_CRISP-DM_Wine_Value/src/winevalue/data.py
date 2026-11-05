"""Loading the raw Wine Reviews file (WineEnthusiast, scraped June 2017)."""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from .config import DATA_RAW

EXPECTED_COLUMNS = [
    "country", "description", "designation", "points", "price", "province",
    "region_1", "region_2", "taster_name", "taster_twitter_handle", "title",
    "variety", "winery",
]


def load_raw(path: str | Path = DATA_RAW) -> pd.DataFrame:
    """Read the raw CSV (gzip OK) and check its schema.

    The unnamed first column is the scraper's row number. It's kept as
    ``review_id`` so every row can be traced back to the raw file.
    Nothing is cleaned or dropped here; that happens in Data Preparation.
    """
    df = pd.read_csv(path, index_col=0)
    df.index.name = "review_id"
    missing = set(EXPECTED_COLUMNS) - set(df.columns)
    extra = set(df.columns) - set(EXPECTED_COLUMNS)
    if missing or extra:
        raise ValueError(f"Schema mismatch. Missing: {sorted(missing)}; unexpected: {sorted(extra)}")
    if not df["points"].between(80, 100).all():
        raise ValueError("points outside the published 80-100 range")
    return df


def extract_vintage(title: pd.Series, winery: pd.Series | None = None) -> pd.Series:
    """Vintage year parsed from the wine title (e.g. 'Nicosia 2013 Vulkà Bianco').

    Takes the FIRST 4-digit year from 1900 to 2017 (the scrape year). NaN for non-vintage wines.

    With ``winery`` (the revised Phase 2 rule), the winery name is removed from the start of the title
    first, so years inside winery names ("1912 Winemakers", "Guidi 1929") aren't taken as vintages.
    Later years in a title are usually planting or cuvée years ("Vignes de 1939"), so the first
    remaining year is kept. Called without ``winery`` it reproduces the Phase 1 behaviour exactly.
    """
    if winery is not None:
        title = pd.Series([t[len(w):] if isinstance(t, str) and isinstance(w, str) and t.startswith(w) else t
                           for t, w in zip(title, winery)], index=title.index)
    year_re = re.compile(r"\b(19\d{2}|20(?:0\d|1[0-7]))\b")
    out = []
    for t in title:
        m = year_re.search(t) if isinstance(t, str) else None
        if m is None:
            out.append(float("nan")); continue
        # Revised rule only: "NV" before the first year means it's a brand/solera year ("Alvear NV Solera 1927")
        if winery is not None and re.search(r"\bNV\b", t[:m.start()]):
            out.append(float("nan")); continue
        out.append(float(m.group(1)))
    return pd.Series(out, index=title.index)
