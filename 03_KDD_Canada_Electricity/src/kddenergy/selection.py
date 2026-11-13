"""KDD step 1 - Selection: the target dataset (13 geographies x months, non-overlapping series)."""

from __future__ import annotations

import pandas as pd

from . import config as c
from .data import load_flows, load_generation


def select_generation(allow_sealed: bool = False, start: str = c.CONSISTENT_START) -> pd.DataFrame:
    """(geography, month) x selected generation types, all producers, MWh. Canada aggregate excluded."""
    g = load_generation(allow_sealed)
    g = g[(g["producer_class"] == c.TOTAL_PRODUCERS) & g["generation_type"].isin(c.GEN_SELECT)
          & g["geography"].isin(c.GEOS) & (g["month"] >= start)]
    w = g.pivot_table(index=["geography", "month"], columns="generation_type", values="generation_mwh",
                      dropna=False, aggfunc="first")
    return w.rename(columns=c.GEN_SELECT)[list(c.GEN_SELECT.values())]


def select_flows(allow_sealed: bool = False, start: str = c.CONSISTENT_START) -> pd.DataFrame:
    """(geography, month) x selected flow components, MWh. Territories publish no trade rows (isolated grids)."""
    f = load_flows(allow_sealed)
    f = f[f["flow_component"].isin(c.FLOW_SELECT) & f["geography"].isin(c.GEOS) & (f["month"] >= start)]
    w = f.pivot_table(index=["geography", "month"], columns="flow_component", values="flow_mwh",
                      dropna=False, aggfunc="first")
    return w.reindex(columns=list(c.FLOW_SELECT)).rename(columns=c.FLOW_SELECT)


def build_panel(allow_sealed: bool = False, start: str = c.CONSISTENT_START) -> pd.DataFrame:
    """Integrated raw panel (before preprocessing): generation table joined to the flows table."""
    gen, flows = select_generation(allow_sealed, start), select_flows(allow_sealed, start)
    months = sorted(set(gen.index.get_level_values("month")) | set(flows.index.get_level_values("month")))
    idx = pd.MultiIndex.from_product([c.GEOS, months], names=["geography", "month"])
    return gen.reindex(idx).join(flows.reindex(idx))
