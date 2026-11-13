"""KDD step 2 - Preprocessing: missing-value decisions, integration checks, event catalogue."""

from __future__ import annotations

import hashlib

import numpy as np
import pandas as pd

from . import config as c

TRADE_COLS = ["receipts", "deliveries", "rec_prov", "del_prov", "rec_us", "del_us"]
NON_THERMAL_COLS = ["hydro", "nuclear", "wind", "solar", "tidal", "other"]


def missing_report(panel: pd.DataFrame) -> pd.DataFrame:
    """Share of missing values per geography x column."""
    return panel.isna().groupby(level="geography").mean().loc[c.GEOS]


def clean(panel: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Apply the preprocessing decisions. Returns (clean panel, decision log).

    * Structural zeros: a geography that publishes no row for a series has no such plant / interconnection
      (territories: no trade; PEI: no direct US tie; no nuclear outside ON/NB). Those are set to 0, not imputed.
    * Status-coded cells ('..', 'x') that are missing *inside* an otherwise reported series stay missing.
    * Negative generation (net of station service) is kept.
    """
    p = panel.copy()
    log = []
    for col in NON_THERMAL_COLS + TRADE_COLS:
        allna = p[col].isna().groupby(level="geography").transform("all")
        n = int(allna.groupby(level="geography").first().sum())
        if n:
            log.append({"column": col, "action": "structural zero (no series published)",
                        "geographies": ", ".join(sorted(p.index[allna].get_level_values(0).unique().map(c.ABBR)))})
        p.loc[allna, col] = 0.0
    remaining = p.isna().sum()
    for col, n in remaining[remaining > 0].items():
        log.append({"column": col, "action": f"{n} cell(s) still missing inside a reported series (left missing)",
                    "geographies": ", ".join(sorted(p.index[p[col].isna()].get_level_values(0).unique().map(c.ABBR)))})
    return p, pd.DataFrame(log)


def integration_checks(p: pd.DataFrame) -> pd.Series:
    """Cross-table and accounting checks on the integrated panel (MWh)."""
    cross = (p["gen_total"] - p["gen_flows_table"]).abs()
    resid = p["gen_total"] + p["receipts"] - p["deliveries"] - p["availability"]
    parts = p["combustion"] + p[NON_THERMAL_COLS].sum(axis=1) - p["gen_total"]
    rec = p["rec_prov"] + p["rec_us"] - p["receipts"]
    dlv = p["del_prov"] + p["del_us"] - p["deliveries"]
    return pd.Series({
        "geo-months": len(p),
        "max |generation table - flows table|": cross.max(),
        "geo-months with |availability identity residual| > 1": int((resid.abs() > 1).sum()),
        "max |availability identity residual|": resid.abs().max(),
        "max |types sum - total generation|": parts.abs().max(),
        "max |receipt parts - total receipts|": rec.abs().max(),
        "max |delivery parts - total deliveries|": dlv.abs().max(),
    })


def identity_exceptions(p: pd.DataFrame, tol: float = 1.0) -> pd.DataFrame:
    resid = p["gen_total"] + p["receipts"] - p["deliveries"] - p["availability"]
    return resid[resid.abs() > tol].rename("residual_mwh").to_frame()


def catalogue_sha256(path=c.EVENT_CATALOGUE) -> str:
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def load_event_catalogue(period: str | None = "discovery", verify: bool = True) -> pd.DataFrame:
    """The K3 event catalogue, frozen before mining (hash checked)."""
    if verify and catalogue_sha256() != c.K3_CATALOGUE_SHA256:
        raise ValueError("event catalogue changed after it was frozen")
    cat = pd.read_csv(c.EVENT_CATALOGUE)
    return cat if period is None else cat[cat["period"] == period].reset_index(drop=True)


def catalogue_months(cat: pd.DataFrame, window: int = 0) -> set[tuple[str, str]]:
    """(geography, month) pairs covered by the catalogue, widened by +/- window months."""
    out = set()
    for r in cat.itertuples():
        for m in pd.period_range(pd.Period(r.start_month, "M") - window, pd.Period(r.end_month, "M") + window, freq="M"):
            out.add((r.geography, str(m)))
    return out
