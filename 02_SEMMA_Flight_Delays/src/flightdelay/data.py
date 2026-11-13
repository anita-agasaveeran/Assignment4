"""Locating and loading the BTS flight data (Kaggle mirror, CC0)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .config import KAGGLE_DATASET, LOCAL_RAW_DIR, TARGET


def locate_raw_dir() -> Path:
    """Local download if present, otherwise fetch from Kaggle with kagglehub (Colab).

    ``flights.parquet`` (314 MB) is too large for GitHub, so it's never committed.
    """
    if (LOCAL_RAW_DIR / "flights.parquet").exists():
        return LOCAL_RAW_DIR
    import kagglehub  # public dataset: anonymous download works (checked 2026-11-09, kagglehub 1.0.3)
    from .config import KAGGLE_DATASET_VERSION
    return Path(kagglehub.dataset_download(f"{KAGGLE_DATASET}/versions/{KAGGLE_DATASET_VERSION}"))


def load_flights(columns=None) -> pd.DataFrame:
    """Load flights.parquet, parse ``flight_date`` and add the ``disrupted`` target."""
    df = pd.read_parquet(locate_raw_dir() / "flights.parquet", columns=columns)
    df["flight_date"] = pd.to_datetime(df["flight_date"])
    if {"arr_del15", "cancelled", "diverted"} <= set(df.columns):
        df[TARGET] = ((df["arr_del15"].fillna(0) == 1) | (df["cancelled"] == 1) | (df["diverted"] == 1)).astype("int8")
    return df


def period(dates: pd.Series) -> pd.Series:
    """'train' / 'valid' / 'test' label from the frozen time partition."""
    from . import config as c
    out = pd.Series("outside", index=dates.index)
    out[(dates >= c.TRAIN_START) & (dates <= c.TRAIN_END)] = "train"
    out[(dates >= c.VALID_START) & (dates <= c.VALID_END)] = "valid"
    out[(dates >= c.TEST_START) & (dates <= c.TEST_END)] = "test"
    return out


def assert_no_test_targets(df: pd.DataFrame) -> pd.DataFrame:
    """Guard: refuse to compute target statistics on the sealed test months (call before any target stat)."""
    from . import config as c
    if (df["flight_date"] >= c.TEST_START).any():
        raise ValueError("Sealed test months present: target statistics on test are only allowed in Assess")
    return df
