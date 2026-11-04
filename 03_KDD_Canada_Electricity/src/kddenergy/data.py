"""Loading StatCan tables 25-10-0015-01 / 25-10-0016-01 (Kaggle adaptation by hgultekin).

By default every loader enforces the front-pass seal: months after ``config.DISCOVERY_END`` are dropped,
and backtest rows for sealed forecast origins are removed. Pass ``allow_sealed=True`` only in the final
interpretation/evaluation step.
"""

from __future__ import annotations

import pandas as pd

from . import config as c


def _seal(df: pd.DataFrame, allow_sealed: bool, col: str = "month") -> pd.DataFrame:
    return df if allow_sealed else df[df[col] <= c.DISCOVERY_END].copy()


def load_generation(allow_sealed: bool = False) -> pd.DataFrame:
    return _seal(pd.read_csv(c.RAW / "generation_monthly.csv"), allow_sealed)


def load_flows(allow_sealed: bool = False) -> pd.DataFrame:
    return _seal(pd.read_csv(c.RAW / "flows_monthly.csv"), allow_sealed)


def load_availability(allow_sealed: bool = False) -> pd.DataFrame:
    return _seal(pd.read_csv(c.RAW / "availability_panel.csv"), allow_sealed)


def load_backtest(allow_sealed: bool = False) -> pd.DataFrame:
    """The dataset's seasonal-naive backtest. Sealed origins (2024-12 onward) are removed by default.

    Note: the dataset's published headline WAPE (3.30%, backtest_metrics.csv) includes the sealed
    2024-12 origin and the Canada aggregate, so it is never quoted in this project.
    """
    b = pd.read_csv(c.RAW / "seasonal_naive_backtest.csv")
    return b if allow_sealed else b[~b["forecast_origin"].isin(c.SEALED_ORIGINS)].copy()


def generation_wide(gen: pd.DataFrame) -> pd.DataFrame:
    """geography x month rows, generation_type columns, all producers, MWh. Status '..' / 'x' stay NaN."""
    tot = gen[gen["producer_class"] == c.TOTAL_PRODUCERS]
    return tot.pivot_table(index=["geography", "month"], columns="generation_type", values="generation_mwh")


def thermal_series(wide: pd.DataFrame) -> pd.Series:
    """Combustion (thermal) generation = total - (hydro + nuclear + wind + solar + tidal + other).

    Additive within each StatCan era (front-pass check). It is NOT comparable across 2016-01, because
    reporting coverage expanded then; see ``config.CONSISTENT_START``.
    """
    return wide[c.TOTAL_GEN] - wide[c.NON_THERMAL].fillna(0).sum(axis=1)
