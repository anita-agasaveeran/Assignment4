"""Rebuild every dashboard artifact from a (new) StatCan release, using the rules frozen in the KDD project.

Usage (from the repo root or anywhere):
    python 03_KDD_Canada_Electricity/deployment/refresh.py                 # uses data/raw/
    python 03_KDD_Canada_Electricity/deployment/refresh.py --raw-dir DIR   # a folder with the same CSV files

DIR must contain generation_monthly.csv, flows_monthly.csv, availability_panel.csv and
seasonal_naive_backtest.csv in the Kaggle layout (re-download the dataset, or rebuild them from StatCan tables
25-10-0015-01 and 25-10-0016-01). Outputs go to deployment/artifacts/. Nothing is re-tuned: k, the PELT penalty,
the anomaly flag budget and the forecasting model are the ones fixed and evaluated in the notebook. The discovery
window is extended to the newest month, so this is *monitoring* with frozen methods, not a new evaluation.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from kddenergy import config as c  # noqa: E402
from kddenergy import forecast as Fc  # noqa: E402
from kddenergy import mining as Mn  # noqa: E402
from kddenergy import transform as T  # noqa: E402
from kddenergy.data import load_availability  # noqa: E402
from kddenergy.preprocess import clean, integration_checks  # noqa: E402
from kddenergy.selection import build_panel  # noqa: E402

ART = HERE / "artifacts"

# Decisions taken in the notebook's evaluation step (kept here, not in config.py, whose hash is pre-registered):
DEPLOY_K = 5                       # K1: k chosen by silhouette on 2016-24; archetypes confirmed (ARI 1.00 in 2025-26)
DEPLOYED_FORECAST = "snaive"       # K4 NOT met on the sealed origins (ratio 1.015) -> seasonal naive stays the forecast
CHALLENGER = "combo_avg3_ets"      # shown for comparison only


def main(raw_dir: str | None = None) -> dict:
    if raw_dir:
        c.RAW = Path(raw_dir).resolve()
    ART.mkdir(exist_ok=True)
    panel, decisions = clean(build_panel(allow_sealed=True))
    months = sorted(panel.index.get_level_values("month").unique())
    last = months[-1]
    checks = integration_checks(panel)
    feat = T.add_features(panel)

    # panel + monthly derived series for the charts
    out = panel.join(feat[["hydro_share", "nuclear_share", "windsolar_share", "combustion_share", "nonemitting_share",
                           "net_import_ratio"]])
    out.reset_index().to_csv(ART / "panel.csv", index=False)

    # K1: clusters on the frozen discovery window and on the latest 12 complete months (balanced features)
    k = DEPLOY_K
    win = {"2016-01..2024-12": (c.CONSISTENT_START, c.DISCOVERY_END), f"latest 12 months (..{last})": (months[-12], last)}
    cl = {}
    for name, (a, b) in win.items():
        X = T.cluster_features(panel, a, b)
        cl[name] = pd.Series(Mn.kmeans_labels(X, k), index=X.index)
    ref = next(iter(cl.values()))
    clusters = pd.DataFrame({n: Mn.relabel_like(ref.to_numpy(), s.to_numpy()) for n, s in cl.items()}, index=ref.index)
    feats = T.cluster_features(panel, c.CONSISTENT_START, last)
    clusters.join(feats).reset_index().rename(columns={"index": "geography"}).to_csv(ART / "clusters.csv", index=False)

    # K2: PELT on each province's deseasonalized combustion share, 2016-01..latest, same rules
    cs = feat["combustion_share"]
    cs_sa = T.deseasonalize(cs, T.calendar_climatology(cs))
    rows = []
    for g in c.K2_GEOS:
        x = cs_sa.loc[g].to_numpy()
        bk = Mn.pelt(x)
        ch = Mn.primary_change(x, bk)
        for s0, s1, m in Mn.segment_means(x, bk):
            rows.append({"geography": g, "start": months[s0], "end": months[s1 - 1],
                         "share_mean": cs.loc[g].iloc[s0:s1].mean(), "deseasonalized_mean": m,
                         "primary_change": bool(ch and s0 == ch["index"])})
    pd.DataFrame(rows).to_csv(ART / "changepoints.csv", index=False)

    # K3: STL z (scale = discovery period) -> Isolation Forest fit on the discovery period; top 2% flagged overall
    z = T.stl_z_table(feat, scale_end=c.DISCOVERY_END)
    z = z[Mn.eligible_mask(z.index)]
    dev = z[z.index.get_level_values("month") <= c.DISCOVERY_END]
    sc = Mn.anomaly_scores(z, Mn.fit_isolation_forest(dev))
    n = int(round(c.K3_FLAG_SHARE * len(z)))
    an = z.join(sc)
    an["flagged"] = an.index.isin(Mn.top_flags(sc["iforest"], n))
    an.reset_index().to_csv(ART / "anomalies.csv", index=False)

    # K4: forecast the next 12 months from the latest month with the evaluated model (+ seasonal naive)
    A = Fc.availability_matrix(load_availability(allow_sealed=True))
    origin = A.index.max()
    tgt = pd.period_range(origin + 1, origin + c.FORECAST_HORIZON, freq="M")
    fc_rows = []
    for g in c.GEOS:
        h = A[g].dropna()
        f_snaive = Fc.seasonal_naive(h, tgt)
        f_a3, f_ets = Fc.avg3_growth(h, tgt), Fc.ets_damped_log(h, tgt)
        challenger = {"avg3_growth": f_a3, "ets_damped_log": f_ets, "combo_avg3_ets": (f_a3 + f_ets) / 2}[CHALLENGER]
        for t, a, b in zip(tgt, f_snaive, challenger):
            fc_rows.append({"geography": g, "month": str(t), "seasonal_naive_mwh": a, "challenger_mwh": b})
    pd.DataFrame(fc_rows).to_csv(ART / "forecast.csv", index=False)

    meta = {"refreshed_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "raw_dir": str(c.RAW),
            "data_months": [months[0], last], "forecast_origin": str(origin), "k1_k": k, "forecast_deployed": DEPLOYED_FORECAST, "forecast_challenger": CHALLENGER,
            "anomaly_flags": int(an["flagged"].sum()),
            "integration_checks": {k_: float(v) for k_, v in checks.items()},
            "preprocessing_decisions": decisions.to_dict("records"),
            "data_breaks": c.DATA_BREAKS}
    (ART / "meta.json").write_text(json.dumps(meta, indent=2))
    return meta


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--raw-dir", help="folder with a newer copy of the Kaggle/StatCan CSVs")
    m = main(ap.parse_args().raw_dir)
    print(json.dumps({k: m[k] for k in ("refreshed_utc", "data_months", "forecast_origin", "k1_k", "forecast_deployed", "anomaly_flags")}, indent=2))
