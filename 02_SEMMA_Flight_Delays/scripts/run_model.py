"""Model stage: fit the four SAS-style model families on the training sample, tune on validation, rehearse on the
summer check, save the comparison tables. Test months are never loaded.   python scripts/run_model.py"""
import json, sys, time
from pathlib import Path
PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR / "src"))
import numpy as np, pandas as pd                                                    # noqa: E402
from sklearn.metrics import average_precision_score, roc_auc_score                  # noqa: E402
from flightdelay import config, models, modify, sampling                            # noqa: E402
from flightdelay.data import assert_no_test_targets, load_flights, period           # noqa: E402
from flightdelay.metrics import block_bootstrap, per_day                            # noqa: E402

TABLES = PROJECT_DIR / "reports" / "tables"
SAMPLE_RATE = float(sys.argv[1]) if len(sys.argv) > 1 else 1.0


def evaluate(name, y, s, dates):
    p2, l2 = per_day(dates, y, s, 0.02); _, l10 = per_day(dates, y, s, 0.10)
    return {"scorer": name, "top2_lift": l2.mean(), "top2_precision": p2.mean(), "top10_lift": l10.mean(),
            "roc_auc": roc_auc_score(y, s), "pr_auc": average_precision_score(y, s)}, l2


GRID = {"logistic regression": [{"C": 0.1}, {"C": 1.0}],
        "decision tree": [{"max_depth": 8}, {"max_depth": 12}, {"max_depth": 16}],
        "neural network": [{"hidden": (64, 32), "alpha": 1e-4}, {"hidden": (128, 64), "alpha": 1e-3}],
        "gradient boosting": [{"num_leaves": 63}, {"num_leaves": 255, "min_child_samples": 500}]}

if __name__ == "__main__":
    t0 = time.time()
    raw = load_flights(columns=modify.RAW_COLUMNS); raw["row_id"] = np.arange(len(raw), dtype="int32")
    raw = assert_no_test_targets(raw[period(raw["flight_date"]).isin(["train", "valid"])])
    fr = modify.build_frame(raw); fr["year_month"] = fr["flight_date"].dt.to_period("M").astype(str)
    print(f"frame {fr.shape} {time.time() - t0:.0f}s", flush=True)
    rows, daily, tuning, chosen = [], {}, [], {}
    for wname, (trr, var) in config.LC_WINDOWS.items():
        pool = fr[fr.flight_date.between(*trr)]; va = fr[fr.flight_date.between(*var)]
        big = pool if SAMPLE_RATE >= 1 else sampling.stratified_sample(pool, int(SAMPLE_RATE * len(pool)), config.SAMPLE_STRATA, config.SEED)
        small = sampling.stratified_sample(pool, min(config.SMALL_MODEL_ROWS, len(pool)), config.SAMPLE_STRATA, config.SEED)
        y, dates = va[config.TARGET].to_numpy(), va["flight_date"].to_numpy()
        for rname, s in models.rules(pool, va).items():
            r, l2 = evaluate(rname, y, s, dates); rows.append({"window": wname, **r}); daily[(wname, rname)] = l2
        for mname, grid in GRID.items():
            tr = big if mname == "gradient boosting" else small
            best = None
            for params in (grid if wname == "main" else [chosen[mname]]):
                t = time.time(); m = models.fit(mname, tr, **params); s = models.predict(m, va)
                r, l2 = evaluate(mname, y, s, dates)
                trees = int(getattr(m, "best_iteration_", 0) or getattr(m, "best_epoch_", 0) or 0)   # trees, or MLP epochs
                tuning.append({"window": wname, "model": mname, "params": json.dumps(params, default=str), "train rows": len(tr),
                               **{k: v for k, v in r.items() if k != "scorer"}, "trees": trees, "seconds": time.time() - t})
                print(tuning[-1], flush=True)
                if best is None or r["top2_lift"] > best[0]["top2_lift"]:
                    best = (r, l2, params)
            if wname == "main":
                chosen[mname] = best[2]
            rows.append({"window": wname, **best[0], "params": json.dumps(best[2], default=str)}); daily[(wname, mname)] = best[1]
        # critic M4: gradient boosting at the SAME 800k sample as the other families (equal-n comparison; reported only)
        m = models.fit("gradient boosting", small, **chosen["gradient boosting"]); s = models.predict(m, va)
        r, l2 = evaluate("gradient boosting (800k)", y, s, dates)
        rows.append({"window": wname, **r, "params": json.dumps(chosen["gradient boosting"]), "trees": int(m.best_iteration_)})
        daily[(wname, "gradient boosting (800k)")] = l2
    res = pd.DataFrame(rows)
    # gap vs best simple rule per window, 7-day block bootstrap
    gaps = []
    for w in config.LC_WINDOWS:
        rr = res[(res.window == w) & res.scorer.isin(models.BENCHMARK_RULES)]
        best_rule = rr.loc[rr.top2_lift.idxmax(), "scorer"]
        for m in list(GRID) + ["gradient boosting (800k)"]:
            g = daily[(w, m)] - daily[(w, best_rule)]; lo, hi = block_bootstrap(g)
            gaps.append({"window": w, "model": m, "best rule": best_rule, "gap": g.mean(), "lo90": lo, "hi90": hi, "days better": (g > 0).mean()})
    res.to_csv(TABLES / "model_comparison.csv", index=False)
    pd.DataFrame(tuning).to_csv(TABLES / "model_tuning.csv", index=False)
    pd.DataFrame(gaps).to_csv(TABLES / "model_gap_vs_rule.csv", index=False)
    # Champion by the rule pre-declared in config (critic round 2, N3): best mean per-day top-2% lift over the two
    # windows among the four operational models (rules and the 800k equal-n check are not candidates).
    cand = res[res.scorer.isin(list(GRID))].groupby("scorer")["top2_lift"].mean().sort_values(ascending=False)
    json.dump({"chosen_params": chosen, "sample_rate": SAMPLE_RATE, "champion": cand.index[0],
               "mean_lift": cand.round(4).to_dict()}, open(TABLES / "model_chosen.json", "w"), indent=1, default=str)
    print(res.round(3).to_string()); print(pd.DataFrame(gaps).round(3).to_string()); print(f"done {(time.time() - t0) / 60:.0f} min")
