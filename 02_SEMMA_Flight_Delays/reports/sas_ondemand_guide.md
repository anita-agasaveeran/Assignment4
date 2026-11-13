# Rebuilding the Flow in SAS (OnDemand for Academics)

The assignment suggests demoing SEMMA in SAS. Claude can't run SAS, so this guide lets you rebuild the same flow in **SAS OnDemand for Academics** (free for students) and record it. The Python notebook stays the reference analysis. The SAS demo shows the same SEMMA steps as Enterprise Miner / SAS Model Studio nodes.

## 0. Prepare a file SAS can take
OnDemand's upload limit and the Studio interface handle a sample better than 11.7M rows. That also fits the SAS paper's point that sampling is the normal way in. From the repo root:

```bash
.venv/bin/python - <<'EOF'
import pandas as pd
ex = pd.read_parquet("02_SEMMA_Flight_Delays/data/sample/explore_sample.parquet")
keep = ["flight_date", "period", "carrier", "origin", "dest", "day_of_week", "dep_hour", "arr_hour", "distance",
        "sched_elapsed_time", "origin_hour_sched", "origin_day_sched", "origin_prev_day", "dest_prev_day",
        "carrier_prev_day", "disrupted"]
ex[keep].to_csv("flights_semma_sas.csv", index=False)
EOF
```
This writes about 460k flights (the 5% stratified exploration sample, train + validation months only) with the front-pass inputs.

## 1. Sample: upload and partition
1. Sign in at <https://welcome.oda.sas.com>, then open **SAS Studio**. Upload `flights_semma_sas.csv` to *Files (Home)*.
2. **Tasks → Data → Import Data** creates `WORK.FLIGHTS`. Check that `disrupted` is numeric 0/1.
3. **Tasks → Data → Sample Data** (the SAS paper's Sampling node): use *Stratified* sampling with strata `carrier` and `disrupted`. Draw 50% to show the dialog, then compare the target rate in the output with the input rate.
4. Partition **by time**, like the Python project, rather than at random:
   ```sas
   data train valid;
     set work.flights;
     if period = "train" then output train;
     else output valid;
   run;
   ```

## 2. Explore
- **Tasks → Statistics → One-Way Frequencies** for `disrupted` by `carrier`, and **Summary Statistics** for `distance` and `origin_hour_sched`.
- **Tasks → Graph → Bar Chart:** mean `disrupted` by `dep_hour`. The time-of-day gradient from E.1 should appear.

## 3. Modify
- **Tasks → Data → Transform Data:** log-transform `origin_day_sched`; group rare `origin` levels (fewer than 1,000 flights) into `OTHER`.
- Impute the missing previous-day rates with the median (**Tasks → Data Mining → Impute** or `PROC STDIZE REPONLY METHOD=MEDIAN`).

## 4. Model (the Enterprise Miner model nodes)
```sas
proc logistic data=train outmodel=lr_model;
  class carrier dep_hour / param=ref;
  model disrupted(event='1') = carrier dep_hour arr_hour day_of_week distance sched_elapsed_time
        origin_hour_sched origin_day_sched origin_prev_day dest_prev_day carrier_prev_day;
run;
proc hpsplit data=train maxdepth=10;              /* Decision Tree node */
  class disrupted carrier;
  model disrupted = carrier dep_hour arr_hour distance origin_hour_sched origin_prev_day dest_prev_day carrier_prev_day;
  code file="/home/&sysuserid/tree_score.sas";
run;
proc hpneural data=train;                          /* Neural Network node */
  input dep_hour arr_hour distance origin_hour_sched origin_prev_day dest_prev_day carrier_prev_day / level=int;
  input carrier / level=nom;
  target disrupted / level=nom;
  hidden 32; train numtries=1 maxiter=200;
  score out=nn_valid; code file="/home/&sysuserid/nn_score.sas";
run;
```
If your OnDemand account includes **SAS Viya / Model Studio**, the same flow can be built as a pipeline (Data → Partition → Logistic Regression / Decision Tree / Neural Network / Gradient Boosting → Model Comparison) with a drag-and-drop canvas. That's the closest thing to Enterprise Miner and the best view for the video.

## 5. Assess
```sas
proc logistic inmodel=lr_model; score data=valid out=lr_valid outroc=lr_roc; run;
```
Then **Tasks → Statistics → ROC curve** (or the Model Comparison node in Model Studio), and the cumulative lift chart. Compare with the Python Assess section. The SAS numbers come from a 5% sample with front-pass inputs only, so expect a lower lift than the Python champion's. Say so in the video.

## What to say in the recording
- SEMMA is SAS's own methodology; Enterprise Miner's toolbar is literally *Sample, Explore, Modify, Model, Assess*.
- The Python project follows the same node sequence. It adds a time-based partition, a per-day top-2% metric and a sealed test summer.
- The SAS sampling paper's claim (small samples lose nothing) held for logistic regression here but not for gradient boosting (Sample S.2). That's a good talking point.
