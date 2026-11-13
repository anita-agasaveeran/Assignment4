# Step 6 · Using the knowledge: dashboard + refresh

| File | What it is |
|---|---|
| `refresh.py` | Rebuilds every artifact from the raw StatCan/Kaggle CSVs with the **frozen** project rules (k, PELT penalty, flag budget, forecasting model). Point `--raw-dir` at a newer download to refresh |
| `app.py` | Streamlit dashboard: validated findings, archetypes (K1), structural change (K2), anomalies (K3), 12-month forecast (K4) |
| `knowledge.json` | The evaluated knowledge base (acceptance verdicts + ranked findings), written by the notebook's step 6 |
| `artifacts/` | CSV/JSON outputs of `refresh.py` (small, committed so the app runs without a refresh) |
| `SOURCE_NOTICES.md` | Statistics Canada Open Licence attribution, required for any redistribution |

```bash
.venv/bin/python 03_KDD_Canada_Electricity/deployment/refresh.py
```

```bash
.venv/bin/streamlit run 03_KDD_Canada_Electricity/deployment/app.py
```

**Refresh is monitoring, not re-evaluation.** It extends the windows to the newest month but re-tunes nothing.
A new release can change past values (StatCan revises), so compare `meta.json` between refreshes. A refreshed
K2 change point or K3 flag is a *candidate* until someone checks it against the public record, as step 5 did.
