"""Loading the raw Wine Reviews file (WineEnthusiast, scraped June 2017)."""

from __future__ import annotations

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


def extract_vintage(title: pd.Series) -> pd.Series:
    """Vintage year parsed from the wine title (e.g. 'Nicosia 2013 Vulkà Bianco').

    Takes the first 4-digit year between 1900 and 2017 (the scrape year).
    NaN when there is none (non-vintage wines).
    """
    years = title.str.extract(r"\b(19\d{2}|20(?:0\d|1[0-7]))\b", expand=False)
    return pd.to_numeric(years, errors="coerce")
