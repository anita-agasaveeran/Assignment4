"""Sample stage: run the pre-registered learning curve (about 1.5 h on a 14-core laptop) and save the table.

    python scripts/run_learning_curve.py            # from 02_SEMMA_Flight_Delays/

The notebook loads reports/tables/sample_learning_curve.csv by default; set RUN_LEARNING_CURVE = True there to redo it.
"""
import sys
import time
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR / "src"))

from flightdelay import config, lcurve                                    # noqa: E402
from flightdelay.data import assert_no_test_targets, load_flights, period  # noqa: E402
from flightdelay.features import build_feature_frame                       # noqa: E402

COLS = ["flight_date", "day_of_week", "airline_code", "tail_number", "flight_number", "origin", "dest",
        "sched_dep_time", "sched_arr_time", "arr_del15", "cancelled", "diverted", "sched_elapsed_time", "distance"]

if __name__ == "__main__":
    t0 = time.time()
    d = load_flights(columns=COLS)
    d = assert_no_test_targets(d[period(d["flight_date"]).isin(["train", "valid"])])
    feat = build_feature_frame(d)
    out = PROJECT_DIR / "reports" / "tables" / "sample_learning_curve.csv"
    # Revision 2 (critic round 1, M1): LightGBM refit with day-grouped early stopping. The logistic regression has no
    # early stopping, so its rows from revision 1 are kept (reps 0-4 main; the interrupted summer arm is completed here).
    import pandas as pd
    lgbm = [m for m in lcurve.MODELS if m.startswith("LightGBM")]
    res = lcurve.run(feat, models=lgbm, log=lambda m: print(m, flush=True))
    old = pd.read_csv(PROJECT_DIR / "reports" / "tables" / "sample_learning_curve_rev1_rowES.csv")
    lr_old = old[old.model == "logistic regression"]
    lr_new = lcurve.run(feat, windows={"summer": config.LC_WINDOWS["summer"]}, models=["logistic regression"],
                        log=lambda m: print(m, flush=True))
    lr_new = lr_new[~lr_new.set_index(["grid", "rep"]).index.isin(lr_old[lr_old.window == "summer"].set_index(["grid", "rep"]).index)]
    res = pd.concat([res, lr_old, lr_new], ignore_index=True)
    res.to_csv(out, index=False)
    print(f"saved {out} ({len(res)} rows) in {(time.time() - t0) / 60:.0f} min", flush=True)
