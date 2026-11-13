"""KDD step 3 - Transformation: shares, trade ratios, deseasonalising, STL residuals, cluster feature vectors."""

from __future__ import annotations

import numpy as np
import pandas as pd
from statsmodels.tsa.seasonal import STL

from . import config as c


def add_features(p: pd.DataFrame) -> pd.DataFrame:
    """Monthly derived series (shares are fractions of total generation; ratios are fractions of availability)."""
    f = pd.DataFrame(index=p.index)
    g, a = p["gen_total"], p["availability"]
    f["hydro_share"] = p["hydro"] / g
    f["nuclear_share"] = p["nuclear"] / g
    f["windsolar_share"] = (p["wind"] + p["solar"]) / g
    f["combustion_share"] = p["combustion"] / g
    f["nonemitting_share"] = p[["hydro", "nuclear", "wind", "solar", "tidal"]].sum(axis=1) / g
    f["net_import_ratio"] = (p["receipts"] - p["deliveries"]) / a
    f["trade_intensity"] = (p["receipts"] + p["deliveries"]) / a
    f["us_net_export_ratio"] = (p["del_us"] - p["rec_us"]) / a
    f["log_availability"] = np.log(a)
    f["log_gen_total"] = np.log(g)
    f["availability_yoy"] = a.groupby(level="geography").pct_change(12)
    return f


def calendar_climatology(s: pd.Series) -> pd.DataFrame:
    """geography x calendar month (1..12) mean of a monthly (geography, month) series."""
    cm = s.index.get_level_values("month").str[5:7].astype(int)
    return s.groupby([s.index.get_level_values("geography"), cm]).mean().unstack()


def deseasonalize(s: pd.Series, clim: pd.DataFrame) -> pd.Series:
    """Subtract a (geography x calendar month) climatology, e.g. one estimated on the discovery period only."""
    geo = s.index.get_level_values("geography")
    cm = s.index.get_level_values("month").str[5:7].astype(int)
    return s - clim.stack().reindex(list(zip(geo, cm))).to_numpy()


def robust_z(x: np.ndarray, scale: float | None = None, center: float | None = None) -> np.ndarray:
    med = np.nanmedian(x) if center is None else center
    s = scale if scale is not None else 1.4826 * np.nanmedian(np.abs(x - med))
    return np.zeros_like(x) if not s or not np.isfinite(s) else (x - med) / s


def stl_residuals(s: pd.Series, period: int = 12) -> pd.Series:
    """Robust STL residual of one geography's monthly series (constant series -> zeros)."""
    v = s.astype(float)
    if v.std() == 0 or v.isna().any():
        return pd.Series(np.where(v.isna(), np.nan, 0.0), index=s.index)
    return pd.Series(STL(v.to_numpy(), period=period, robust=True).fit().resid, index=s.index)


def stl_z_table(f: pd.DataFrame, series=c.K3_SERIES, scale_end: str | None = None) -> pd.DataFrame:
    """Per-geography robust z-scores of STL residuals. The z scale is the MAD over months <= scale_end."""
    out = {}
    for col in series:
        parts = []
        for geo, s in f[col].groupby(level="geography"):
            r = stl_residuals(s)
            m = r.index.get_level_values("month")
            base = (r[m <= scale_end] if scale_end else r).to_numpy()
            med = np.nanmedian(base)
            scale = 1.4826 * np.nanmedian(np.abs(base - med))
            parts.append(pd.Series(robust_z(r.to_numpy(), scale, med) if scale > 0 else np.zeros(len(r)), index=r.index))
        out[col] = pd.concat(parts)
    return pd.DataFrame(out)


def cluster_features(p: pd.DataFrame, start: str, end: str) -> pd.DataFrame:
    """One feature vector per geography over [start, end], calendar-month balanced.

    Each raw series is first averaged by calendar month (so a window with Jan-Aug twice counts each calendar
    month once), then shares/ratios are computed from those 12-month climatologies.
    """
    m = p.index.get_level_values("month")
    w = p[(m >= start) & (m <= end)]
    cm = w.index.get_level_values("month").str[5:7].astype(int)
    clim = w.groupby([w.index.get_level_values("geography"), cm]).mean()      # geography x calendar month rows
    yr = clim.groupby(level=0).sum()                                           # balanced "typical year"
    a = clim["availability"].unstack()
    f = pd.DataFrame(index=yr.index)
    f["hydro_share"] = yr["hydro"] / yr["gen_total"]
    f["nuclear_share"] = yr["nuclear"] / yr["gen_total"]
    f["windsolar_share"] = (yr["wind"] + yr["solar"]) / yr["gen_total"]
    f["combustion_share"] = yr["combustion"] / yr["gen_total"]
    f["net_import_ratio"] = (yr["receipts"] - yr["deliveries"]) / yr["availability"]
    f["trade_intensity"] = (yr["receipts"] + yr["deliveries"]) / yr["availability"]
    f["us_net_export_ratio"] = (yr["del_us"] - yr["rec_us"]) / yr["availability"]
    f["winter_summer_ratio"] = a[[12, 1, 2]].mean(axis=1) / a[[6, 7, 8]].mean(axis=1)
    f["seasonal_amplitude"] = (a.max(axis=1) - a.min(axis=1)) / a.mean(axis=1)
    return f.loc[[g for g in c.GEOS if g in f.index], c.K1_FEATURES]


def seasonal_profiles(p: pd.DataFrame, start: str, end: str, col: str = "availability") -> pd.DataFrame:
    """geography x calendar month availability profile, normalised to mean 1 (for plots / shape comparison)."""
    m = p.index.get_level_values("month")
    clim = calendar_climatology(p.loc[(m >= start) & (m <= end), col])
    return clim.div(clim.mean(axis=1), axis=0).loc[[g for g in c.GEOS if g in clim.index]]


def stl_z_onesided(f: pd.DataFrame, months: list[str], scale_end: str = c.DISCOVERY_END,
                   series=c.K3_SERIES) -> pd.DataFrame:
    """Confirmation-period z-scores without look-ahead: for each month t in ``months`` the STL is fit on data up to t
    and the residual at t is kept. Centre and scale = median and MAD of the discovery-period residuals."""
    out = []
    for geo, d in f[list(series)].groupby(level="geography"):
        d = d.droplevel("geography")
        row = {}
        for col in series:
            full = stl_residuals(d[col].loc[:scale_end])
            med = np.nanmedian(full); scale = 1.4826 * np.nanmedian(np.abs(full - med))
            vals = {}
            for t in months:
                r = stl_residuals(d[col].loc[:t]).iloc[-1]
                vals[t] = (r - med) / scale if scale > 0 else 0.0
            row[col] = pd.Series(vals)
        out.append(pd.DataFrame(row).assign(geography=geo))
    z = pd.concat(out).rename_axis("month").reset_index().set_index(["geography", "month"])
    return z[list(series)]
