"""Turning demand expectations into bake quantities, and scoring them.

Used in Phase 1 (sizing the problem with simple rules), Phase 4 (model-based
policy) and Phase 5 (business backtest). All money is in INR.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


def critical_ratio(cost_of_stockout: float, cost_of_waste: float) -> float:
    """Newsvendor critical ratio Cu / (Cu + Co).

    The best bake quantity is the demand quantile at this ratio.
    ``cost_of_stockout`` (Cu) is the margin lost per unit of unmet
    demand. ``cost_of_waste`` (Co) is the cost of one unsold unit.
    """
    if cost_of_stockout < 0 or cost_of_waste < 0 or cost_of_stockout + cost_of_waste == 0:
        raise ValueError("Costs must be non-negative and not both zero")
    return cost_of_stockout / (cost_of_stockout + cost_of_waste)


@dataclass(frozen=True)
class PlanResult:
    demand: float
    baked: float
    sold_from_stock: float
    sold_preorder: float
    wasted: float
    margin_earned: float
    waste_cost: float

    @property
    def sold(self) -> float:
        return self.sold_from_stock + self.sold_preorder

    @property
    def fill_rate(self) -> float:
        return self.sold / self.demand if self.demand else float("nan")

    @property
    def waste_share(self) -> float:
        return self.wasted / self.baked if self.baked else 0.0

    @property
    def net_contribution(self) -> float:
        return self.margin_earned - self.waste_cost

    def as_dict(self) -> dict:
        return {"demand": self.demand, "baked": self.baked, "sold_from_stock": self.sold_from_stock,
                "sold_preorder": self.sold_preorder, "wasted": self.wasted, "fill_rate": self.fill_rate,
                "waste_share_of_baked": self.waste_share, "margin_earned": self.margin_earned,
                "waste_cost": self.waste_cost, "net_contribution": self.net_contribution}


def simulate_plan(demand, baked, unit_margin, unit_cost, preorder_retention=0.0) -> PlanResult:
    """Score a plan cell by cell.

    - sold from stock = min(baked, demand)
    - wasted = max(baked - demand, 0), discarded at ``unit_cost`` (no salvage)
    - unmet demand = demand - sold from stock. A ``preorder_retention`` share
      of it is still sold as a made-to-order item (no waste); the rest is lost.

    Pure make-to-order is ``baked = 0`` with ``preorder_retention > 0``. Pure
    bake-ahead is ``preorder_retention = 0``. Anything in between is a hybrid.
    ``preorder_retention`` can be a scalar or one value per cell.
    """
    d, b, m, c, r = (np.broadcast_to(np.asarray(x, dtype=float), np.shape(demand))
                     for x in (demand, baked, unit_margin, unit_cost, preorder_retention))
    if (b < 0).any():
        raise ValueError("Bake quantities must be non-negative")
    if ((r < 0) | (r > 1)).any():
        raise ValueError("preorder_retention must be in [0, 1]")
    from_stock = np.minimum(b, d)
    preorder = r * (d - from_stock)
    wasted = b - from_stock
    return PlanResult(d.sum(), b.sum(), from_stock.sum(), preorder.sum(), wasted.sum(),
                      float(((from_stock + preorder) * m).sum()), float((wasted * c).sum()))


def trailing_mean_rule(trailing_mean, k: float) -> np.ndarray:
    """Rule-of-thumb bake quantity: ceil(k x trailing mean demand)."""
    return np.ceil(k * np.asarray(trailing_mean, dtype=float))


def fit_multiplier(frame: pd.DataFrame, target_fill: float | None = None,
                   ks=np.arange(0.0, 8.0001, 0.05)) -> float:
    """Choose ``k`` for `trailing_mean_rule` on ``frame`` (training data only).

    With ``target_fill`` set, returns the smallest k whose fill rate reaches
    it, or NaN if none does. Otherwise returns the k that maximises net
    contribution. ``frame`` needs the columns demand, trailing_mean,
    unit_margin and unit_cost.
    """
    results = [simulate_plan(frame["demand"], trailing_mean_rule(frame["trailing_mean"], k),
                             frame["unit_margin"], frame["unit_cost"]) for k in ks]
    if target_fill is None:
        return float(ks[int(np.argmax([r.net_contribution for r in results]))])
    ok = [k for k, r in zip(ks, results) if r.fill_rate >= target_fill]
    return float(min(ok)) if ok else float("nan")


def recommend_bake_quantity(*args, **kwargs):
    """Phase 4/6: model-based bake quantity per product x location x day."""
    raise NotImplementedError("Implemented in Modeling (Phase 4)")
