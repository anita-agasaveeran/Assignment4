"""Building modeling tables from the raw order lines.

Phase 1 uses `demand_grid` to size the problem. Phase 3 (Data
Preparation) adds the calendar, festival and lag features here.
"""

from __future__ import annotations

import pandas as pd

CHAIN = "ALL"  # location label used when demand is pooled across stores


def demand_grid(df: pd.DataFrame, item: str = "Product", pooled: bool = False,
                start=None, end=None) -> pd.DataFrame:
    """Daily demand (sum of ``Quantity``) for every date x location x item.

    Days with no orders are filled with 0, so the table is a full grid.
    Leaving those days out would understate how intermittent demand is.

    Parameters
    ----------
    item : ``"Product"`` or ``"Category"``.
    pooled : if True, all stores are pooled into one location named ``CHAIN``
        (a central-bakery view). Otherwise the location is ``Store_ID``.
    start, end : grid date range. Defaults to the min/max ``Date`` in ``df``.
    """
    data = df.assign(Location=CHAIN) if pooled else df.rename(columns={"Store_ID": "Location"})
    dates = pd.date_range(start or df["Date"].min(), end or df["Date"].max(), freq="D")
    idx = pd.MultiIndex.from_product(
        [dates, sorted(data["Location"].unique()), sorted(data[item].unique())],
        names=["Date", "Location", item])
    return (data.groupby(["Date", "Location", item])["Quantity"].sum()
            .reindex(idx, fill_value=0).rename("demand").reset_index()
            .sort_values(["Location", item, "Date"], ignore_index=True))


def add_trailing_mean(grid: pd.DataFrame, item: str = "Product", window: int = 28) -> pd.DataFrame:
    """Add ``trailing_mean``: mean demand over the previous ``window`` days.

    Uses only days strictly before each date, so it's known the evening
    before. It's NaN until a full window of history exists.
    """
    out = grid.copy()
    out["trailing_mean"] = (out.groupby(["Location", item])["demand"]
                            .transform(lambda s: s.shift(1).rolling(window).mean()))
    return out
