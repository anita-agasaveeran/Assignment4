"""Assess stage: the ONE run on the sealed test months (May-Aug 2026).

Refits every model with its Model-stage settings on the train + validation sample (refit policy), scores every test
flight once, and saves all Assess tables, the curves, and the champion. Run only after the Model stage is committed.
    python scripts/run_assess.py
"""
import json, sys, time
from pathlib import Path
PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR / "src"))
import joblib, numpy as np, pandas as pd                                               # noqa: E402
from sklearn.metrics import average_precision_score, roc_auc_score, roc_curve, precision_recall_curve  # noqa: E402
from flightdelay import config, models, modify, sampling                               # noqa: E402
from flightdelay.data import load_flights, period                                      # noqa: E402
from flightdelay.metrics import block_bootstrap, per_day                               # noqa: E402

TABLES, MODELS_DIR = PROJECT_DIR / "reports" / "tables", PROJECT_DIR / "models"
chosen = json.load(open(TABLES / "model_chosen.json"))
champion = chosen["champion"]
# Guards (critic round 2, N3): the champion must follow from the saved Model table by the pre-declared rule, and the
# boosting sample rate must be the one the Sample stage chose.
comp = pd.read_csv(TABLES / "model_comparison.csv")
rule_champ = comp[comp.scorer.isin(list(chosen["chosen_params"]))].groupby("scorer")["top2_lift"].mean().idxmax()
assert champion == rule_champ, (champion, rule_champ)
assert abs(chosen["sample_rate"] - 0.72) < 1e-9, chosen["sample_rate"]
# Freeze record, written BEFORE any test row is read: SHA-256 of every file in src/ and scripts/ and of the Model choice.
import hashlib
FREEZE = TABLES / "assess_freeze.json"
files = sorted([*(PROJECT_DIR / "src").rglob("*.py"), *(PROJECT_DIR / "scripts").glob("*.py"), TABLES / "model_chosen.json",
                TABLES / "model_comparison.csv"])
digest = {str(f.relative_to(PROJECT_DIR)): hashlib.sha256(f.read_bytes()).hexdigest() for f in files}
CODE_FINGERPRINT = hashlib.sha256("".join(digest.values()).encode()).hexdigest()[:16]   # combined code fingerprint
# Single-run guard with a crash protocol (critic round 3, R3-3): a finished run can't be repeated; a run that died
# ("started") may be restarted only with byte-identical code, and every restart is logged in the freeze file.
if FREEZE.exists():
    prev = json.load(open(FREEZE))
    assert prev["status"] == "started" and prev["fingerprint"] == CODE_FINGERPRINT, \
        "Assess already completed, or the code changed since the first start: the test months are not re-scored"
    prev.setdefault("restarts", []).append(time.strftime("%Y-%m-%d %H:%M:%S"))
    freeze = prev
else:
    freeze = {"created": time.strftime("%Y-%m-%d %H:%M:%S"), "fingerprint": CODE_FINGERPRINT, "files": digest, "status": "started"}
json.dump(freeze, open(FREEZE, "w"), indent=1)
print("Assess run; code fingerprint", CODE_FINGERPRINT, flush=True)

t0 = time.time()
raw = load_flights(columns=modify.RAW_COLUMNS); raw["row_id"] = np.arange(len(raw), dtype="int32")
fr = modify.build_frame(raw, keep_tailless=True)          # FULL timeline: test features use only earlier days' outcomes
fr["period"] = period(fr["flight_date"]); fr["year_month"] = fr["flight_date"].dt.to_period("M").astype(str)
dev = fr[fr.period.isin(["train", "valid"]) & ~fr.tailless]
test_all = fr[fr.period == "test"]
test = test_all[~test_all.tailless]
print(f"frame {fr.shape}, test {len(test):,} (+{int(test_all.tailless.sum()):,} tail-less) {time.time() - t0:.0f}s", flush=True)

rate = chosen["sample_rate"]
big = dev if rate >= 1 else sampling.stratified_sample(dev, int(rate * len(dev)), config.SAMPLE_STRATA, config.SEED)
small = sampling.stratified_sample(dev, config.SMALL_MODEL_ROWS, config.SAMPLE_STRATA, config.SEED)

scores, fitted = models.rules(dev, test), {}
for name, params in chosen["chosen_params"].items():
    t = time.time()
    fitted[name] = models.fit(name, big if name == "gradient boosting" else small, **params)
    scores[name] = models.predict(fitted[name], test)
    print(f"{name}: {time.time() - t:.0f}s", flush=True)

y, dates = test[config.TARGET].to_numpy(), test["flight_date"].to_numpy()
rows, daily = [], {}
for name, s in scores.items():
    p2, l2 = per_day(dates, y, s, 0.02); p10, l10 = per_day(dates, y, s, 0.10)
    daily[name] = l2
    rows.append({"scorer": name, "top2_lift": l2.mean(), "top2_precision": p2.mean(), "top10_lift": l10.mean(),
                 "top10_precision": p10.mean(), "roc_auc": roc_auc_score(y, s), "pr_auc": average_precision_score(y, s)})
res = pd.DataFrame(rows).set_index("scorer")
best_rule = res.loc[models.BENCHMARK_RULES, "top2_lift"].idxmax()
gaps = []
for name in chosen["chosen_params"]:
    g = daily[name] - daily[best_rule]; lo, hi = block_bootstrap(g)
    gaps.append({"model": name, "best rule": best_rule, "gap": g.mean(), "lo90": lo, "hi90": hi, "days better": (g > 0).mean()})
gaps = pd.DataFrame(gaps).set_index("model")

# T3: tail-less cancellations scored as disrupted (they are all cancelled)
ya, da = test_all[config.TARGET].to_numpy(), test_all["flight_date"].to_numpy()
sa = {n: models.predict(fitted[n], test_all) for n in [champion]}
sa.update({k: v for k, v in models.rules(dev, test_all).items()})
t3 = {n: per_day(da, ya, s, 0.02)[1] for n, s in sa.items()}
best_rule_a = max(models.BENCHMARK_RULES, key=lambda r: t3[r].mean())
g3 = t3[champion] - t3[best_rule_a]; lo3, hi3 = block_bootstrap(g3)
# Robustness (critic round 1, m7): the champion's gap without the 5% highest-disruption test days (storm days cap lift)
day_rate = test.groupby("flight_date")[config.TARGET].mean().sort_index()
calm = (day_rate <= day_rate.quantile(0.95)).to_numpy()
gc = daily[champion][calm] - daily[best_rule][calm]; loc, hic = block_bootstrap(gc)
targets = pd.DataFrame([
    ("T1 champion beats the better rule (90% interval > 0)", f"gap {gaps.loc[champion, 'gap']:+.3f} [{gaps.loc[champion, 'lo90']:+.3f}, {gaps.loc[champion, 'hi90']:+.3f}] vs {best_rule}", bool(gaps.loc[champion, "lo90"] > 0)),
    (f"T2 gap >= +{config.ASSESS_T2_GAP}", f"{gaps.loc[champion, 'gap']:+.3f}", bool(gaps.loc[champion, "gap"] >= config.ASSESS_T2_GAP)),
    ("T3 T1 with tail-less cancellations scored as disrupted", f"gap {g3.mean():+.3f} [{lo3:+.3f}, {hi3:+.3f}] vs {best_rule_a}", bool(lo3 > 0)),
    ("(robustness) T1 without the 5% highest-rate days", f"gap {gc.mean():+.3f} [{loc:+.3f}, {hic:+.3f}] on {int(calm.sum())} days", bool(loc > 0)),
], columns=["target", "result", "met"])

# Breakdowns and curves for the champion
s = scores[champion]
te = test.assign(score=s)
te["decile"] = pd.qcut(te["score"].rank(method="first"), 10, labels=False)
calib = te.groupby("decile").agg(mean_score=("score", "mean"), observed=(config.TARGET, "mean"), flights=("score", "size"))
by_carrier = []
for c, g in te.groupby("carrier"):
    if g["flight_date"].nunique() < 30 or len(g) < 20_000: continue
    p, l = per_day(g["flight_date"].to_numpy(), g[config.TARGET].to_numpy(), g["score"].to_numpy(), 0.02)
    by_carrier.append({"carrier": c, "flights": len(g), "rate": g[config.TARGET].mean(), "top2_lift": l.mean(), "roc_auc": roc_auc_score(g[config.TARGET], g["score"])})
by_month = []
for mth, g in te.groupby(te.flight_date.dt.to_period("M").astype(str)):
    row = {"month": mth, "rate": g[config.TARGET].mean()}
    for n in [champion, best_rule]:
        row[f"{n} top2_lift"] = per_day(g.flight_date.to_numpy(), g[config.TARGET].to_numpy(), scores[n][te.index.get_indexer(g.index)], 0.02)[1].mean()
    by_month.append(row)
# pooled cumulative gains (SAS Assess style) for every scorer
gains = {}
for n, sc in scores.items():
    o = np.argsort(-sc, kind="stable"); cum = np.cumsum(y[o]) / y.sum()
    q = np.linspace(0.01, 1, 100); gains[n] = cum[(q * len(y)).astype(int) - 1]
gains = pd.DataFrame(gains, index=np.linspace(0.01, 1, 100)).rename_axis("depth")
fpr, tpr, _ = roc_curve(y, s); pr, rc, _ = precision_recall_curve(y, s)
curves = {"roc": pd.DataFrame({"fpr": fpr, "tpr": tpr}).iloc[::max(1, len(fpr) // 2000)],
          "pr": pd.DataFrame({"recall": rc, "precision": pr}).iloc[::max(1, len(rc) // 2000)]}

for name, df in [("assess_results", res), ("assess_gap_vs_rule", gaps), ("assess_targets", targets.set_index("target")),
                 ("assess_calibration", calib), ("assess_by_carrier", pd.DataFrame(by_carrier).set_index("carrier")),
                 ("assess_by_month", pd.DataFrame(by_month).set_index("month")), ("assess_gains", gains),
                 ("assess_roc", curves["roc"]), ("assess_pr", curves["pr"])]:
    df.to_csv(TABLES / f"{name}.csv")
pd.DataFrame({"date": pd.to_datetime(np.unique(dates)), "champion": daily[champion], best_rule: daily[best_rule]}).to_csv(TABLES / "assess_daily_lift.csv", index=False)
# deployment artifacts: champion + daily top-5% lists of the test period (for the demo app)
MODELS_DIR.mkdir(exist_ok=True)
joblib.dump(fitted[champion], MODELS_DIR / "champion.joblib")
top = te.assign(rank=te.groupby("flight_date")["score"].rank(ascending=False, method="first"), n_day=te.groupby("flight_date")["score"].transform("size"))
top = top[top["rank"] <= 0.05 * top["n_day"]]
top[["flight_date", "carrier", "flight_number", "origin", "dest", "sched_dep_time", "sched_arr_time", "score", "rank", "n_day", config.TARGET,
     "origin_d1", "dest_d1", "carrier_d1", "flight_w4", "origin_hour_w4"]].to_parquet(PROJECT_DIR / "deployment" / "test_period_top5pct.parquet", index=False)
json.dump({"champion": champion, "params": chosen["chosen_params"][champion], "trained_on": "Jan 2025 - Apr 2026 (train + validation)",
           "train_rows": len(big if champion == "gradient boosting" else small), "features": modify.V3_FEATURES,
           "test_top2_lift": res.loc[champion, "top2_lift"], "test_roc_auc": res.loc[champion, "roc_auc"],
           "decision_clock": "16:45 US Eastern, the day before", "created": time.strftime("%Y-%m-%d"), "code_fingerprint": CODE_FINGERPRINT},
          open(MODELS_DIR / "manifest.json", "w"), indent=1, default=float)
freeze.update(status="completed", completed=time.strftime("%Y-%m-%d %H:%M:%S")); json.dump(freeze, open(FREEZE, "w"), indent=1)
print(res.round(3).to_string()); print(gaps.round(3).to_string()); print(targets.to_string()); print(f"done {(time.time() - t0) / 60:.0f} min")
