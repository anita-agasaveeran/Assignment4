# Will My Flight Be Disrupted Tomorrow? A SEMMA Study of 11.7 Million US Flights

*CMPE 255 · Assignment 4 · Project 2. Every number below comes from `notebooks/SEMMA_Flight_Disruption.ipynb` (saved with outputs) or the tables in `reports/tables/`. Critic reviews: `critiques/`.*

## Summary
A hypothetical airline care team can proactively help passengers on about **2% of tomorrow's flights** (~380 of ~19k). It must choose them at **16:45 US Eastern** the evening before. Following SAS's **SEMMA** methodology (Sample → Explore → Modify → Model → Assess), plus a front pass and a Score step, the project builds a ranking from the published schedule and trailing history only.

On the **sealed test summer (May–Aug 2026, 2.46M flights, scored once)** the champion, a logistic regression trained on an 800k-flight stratified sample, does the following:
- **63% of the flights it selects are actually disrupted**, against 47% for the best simple rule and 27% overall.
- **Per-day top-2% lift is 2.39**, against 1.70 for the best simple rule.
- **The gap is +0.69**, with a 90% 7-day-block interval of +0.53 to +0.86, and the champion is better on 91% of days.
- **All three pre-registered targets are met.**

## Front pass (before SEMMA)
SEMMA has no business-understanding step, so a front pass framed the decision, audited the data, removed a target leak (tail numbers are missing exactly when a flight is cancelled), and froze a time partition:
- **Train:** 2025.
- **Validation:** Jan–Apr 2026.
- **Summer check:** Jan–Apr 2025 → May–Aug 2025.
- **Sealed test:** May–Aug 2026.

Details: `reports/front_pass.md` (critic rounds: 6 → 8/10).

## Sample
SAS's *Data Mining and the Case for Sampling* is the template: access → sample size → draw → check → partition.
- **Frame:** 9,248,154 train + validation flights in the scored population.
- **Sample size by learning curve, pre-registered:**
  - **Setup:** 5 nested stratified samples at each of 8 sizes (25k–3.2M), plus 3 full-window refits, in two windows. Each fit was scored by per-day top-2% lift and AUC on the full validation window.
  - **Rule:** the smallest size within 0.02 lift and 0.002 AUC of the full window, for both LightGBM capacities.
  - **Result:** n\* = 3.2M (main) and 1.6M (summer), so **f = 72%** for gradient boosting.
  - **Logistic regression** is within 0.017 lift of its full-window value from **400k** rows, which is the SAS case study's result. The simpler models therefore use an **800k** sample.
- **Draw:** proportional stratified random samples (year-month × carrier × target, largest-remainder allocation, no oversampling at a 23.5% base rate). Three samples: 5% for exploration, 800k for the simpler models, 72% for boosting.
- **Check:** all pre-registered representativeness criteria pass:
  - |SMD| ≤ 0.0025;
  - level-share gaps ≤ 0.11 pp;
  - every day present;
  - |z| > 3 for target rates no more often than chance.
  - Stratification cuts month × carrier rate error from 1.18 pp (simple random) to 0.02 pp.
- **Assess targets fixed here:**
  - **T1:** the champion beats the better simple rule on test, with a 90% interval above 0.
  - **T2:** the gap is ≥ +0.15.
  - **T3:** T1 still holds with tail-less cancellations scored as disrupted.

## Explore (5% sample; daily and airport views on the full frame)
| Finding | Consequence for Modify |
|---|---|
| Time of day dominates: summer disruption rises from 10.7% at 06h to 40.9% at 18h (other months 12.2% → 29.5%) | hour inputs; carrier × hour and origin × hour history |
| Late-arriving aircraft cause 34–42% of delay minutes every month | the same flight number's 4-week record |
| Summer day-to-day persistence is weaker (0.58 vs 0.66); summer afternoon departures carry more weather + NAS delay (34.5% vs 27.8%) | week and 4-week windows, not just yesterday |
| Airports and routes vary widely (10.8–38.4%; routes 15–34%) | route history; origin and destination as categories |
| Extreme days: 4 days above 50% disrupted (worst: 2026-01-25, 65.1% disrupted, 46.5% cancelled) | kept; Assess also reports results without storm days |
| Airport delay profiles (k-means) are weak (silhouette 0.30) | descriptive only |

## Modify
- **One decision clock:** a flight counts as "known" if its arrival in ET (departure in ET + scheduled time) is at or before 16:45 ET. DST is handled, as are split-zone airports. This is stricter than the front pass's local 17:00 rule, which counted 8.6% of flights as known that actually land later.
- **Inputs (28):**
  - schedule;
  - congestion, counted on the full schedule;
  - holiday distance;
  - yesterday, last week and last 4 weeks of outcomes, as **trailing windows over strictly earlier days** shrunk toward the base rate.
  - This design needs no train-only target encoding. Unit tests (and the critic, on real data) confirm that changing day D's outcomes never changes a day-D input.
- **Transformations** for the non-boosting models: rare-level pooling, log1p counts, standardization.
- **Evidence:** the same LightGBM on the same 800k sample (3 seeds) gains **+0.21 per-day lift** in the main window (90% interval +0.14 to +0.28) and **+0.19** in summer (+0.14 to +0.24). Log-loss improves too.

## Model
The Enterprise Miner model nodes were tuned on validation and rehearsed on the summer check. Boosting and the network select trees and epochs on held-out *days*.

| Mean per-day top-2% lift (main, summer) | Main | Summer | Mean |
|---|---|---|---|
| **Logistic regression (800k), champion** | 2.44 | 2.23 | **2.334** |
| Gradient boosting (72% = 5.0M) | 2.47 | 2.14 | 2.304 |
| Neural network (800k) | 2.47 | 2.07 | 2.269 |
| Decision tree (800k) | 2.09 | 1.81 | 1.950 |
| Better simple rule | 1.95 | 1.74 | — |

The champion was chosen by the pre-declared rule (best mean). On validation it is **statistically tied** with boosting (paired gap −0.03 main, +0.09 summer).

## Assess (single run on May–Aug 2026)
| Test summer | Top-2% lift | Precision | ROC-AUC |
|---|---|---|---|
| **Logistic regression (champion)** | **2.39** | **0.63** | 0.718 |
| Neural network | 2.46 | 0.64 | 0.718 |
| Gradient boosting | 2.44 | 0.63 | 0.721 |
| Decision tree | 2.16 | 0.56 | 0.698 |
| Schedule rule (better rule) | 1.70 | 0.47 | 0.668 |
| Day-before rule | 1.60 | 0.42 | 0.583 |

- **Targets:**
  - **T1 ✅:** +0.69 (+0.53 to +0.86), better on 91% of days.
  - **T2 ✅:** the gap is above +0.15.
  - **T3 ✅:** +0.69 (+0.52 to +0.86).
  - **Without storm days:** +0.72.
- **Lift by month:** May 2.62, June 2.52, July 2.24, August 2.17.
- **Lift by carrier:** 1.73 (OH) to 2.94 (AS).
- **Calibration:** good at the extremes, with up to 4 pp under-prediction in deciles 6–8 in a hotter summer.
- **Honest caveat:** the neural network and boosting edged the pre-chosen regression on test. The champion isn't swapped, and all three clear every target.

## Score / deploy
- `models/champion.joblib` and `manifest.json`.
- `deployment/score.py` batch-scores any date. It blanks that day's outcomes first, scores every scheduled flight, and reproduces the Assess ranking.
- A Streamlit demo replays the test summer (`streamlit run deployment/app.py`).
- `model_card.md` and `monitoring_plan.md`: weekly lift against the better rule, PSI drift, a 4-monthly refit.
- `reports/sas_ondemand_guide.md` rebuilds the flow in SAS Studio / Model Studio for the optional SAS demo.

## Critic reviews
| Review | Score | Main outcome |
|---|---|---|
| Front pass, rounds 1–2 | 6 → 8 | tail-number leak removed; 17:00 clock; fair baselines |
| Sample + Explore + Modify, round 1 | 6 | **early stopping on random rows** (memorised days); X6 ×100 slip; benchmark clock |
| S/E/M round 2 + Model round 1 | 7 | the same flaw in the neural network; champion guards |
| S/E/M/Model round 3 (verification) | 8.5 | no blocking issue; continuous-Adam fix |

The biggest correction: early stopping on random *rows* let boosting memorise each training day. That kept every large fit at the 3,000-tree cap, wrongly implied "don't sample", and biased the comparison. Fixing it changed the Sample verdict (f from 100% to 72%) but not the champion.

## Limitations
- No weather or real-time operational data.
- One constant shrinkage prior.
- Pacific-island time zones are approximate.
- The tail-number assumption (A-pop) is untestable.
- Explore saw the validation months.
- Learning-curve deviations: the logistic regression's summer full-window reference is a single refit.
- The summer-check and test seasons are both summers of a fast-changing network (Hawaiian into Alaska, Spirit's exit).

## Reproduce
```bash
python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
cd 02_SEMMA_Flight_Delays && pytest tests          # 21 tests
python scripts/run_learning_curve.py               # ~35 min (optional; the table is saved)
python scripts/run_model.py 0.72                   # ~5 min
# run_assess.py has already run once; its single-run guard refuses a second completed run
```
In Colab the data downloads anonymously from Kaggle (version pinned). The notebook loads the saved tables by default.
