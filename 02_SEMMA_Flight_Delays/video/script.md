# Video Walkthrough Script: SEMMA Flight Disruption (~12 min)

*For the YouTube code-and-artifact walkthrough. **Screen** = what to show; **Say** = narration (paraphrase freely).*

| # | Time | Screen | Say |
|---|---|---|---|
| 1 | 0:00–0:45 | Repo README → `02_SEMMA_Flight_Delays/` | "Project 2 of 3 uses SAS's SEMMA methodology on 11.7 million real US flights. The question: at 4:45 pm Eastern, which 2% of tomorrow's flights should a care team call?" |
| 2 | 0:45–1:45 | Notebook top, front-pass F.1–F.4 | "SEMMA starts at Sample, with no business step, so I added a front pass. It fixes the decision clock and a per-day metric, and seals summer 2026 as the test. It also caught a leak: tail numbers are missing exactly when a flight is cancelled." |
| 3 | 1:45–3:30 | Sample S.2: the learning-curve figure and the rule table | "Following SAS's sampling paper: 5 stratified samples at 8 sizes, a rule written down first. Logistic regression is flat from 400k rows, just like SAS's case study. Boosting keeps learning to 3.2M, so the rule gives a 72% sample for boosting and 800k for the others." |
| 4 | 3:30–4:15 | S.4 representativeness table; `data/sample/` | "All three samples pass: SMD under 0.003, every day present, outlying daily rates at the chance level. Stratifying cuts month × airline error from 1.2 points to 0.02." |
| 5 | 4:15–5:30 | Explore E.1 and E.3 figures; E.6 storm days | "The clock dominates: 11% at 6 am, 41% at 6 pm in summer. Late aircraft cause 40% of delay minutes. On January 25 two-thirds of flights were disrupted, which caps any list's lift at 1.5." |
| 6 | 5:30–6:45 | `src/flightdelay/modify.py` (`known_by_clock`, `trailing_rate`); `tests/test_modify.py`; M.3 table | "Modify: one 16:45 Eastern clock (departure in ET plus duration), and history as trailing windows that can't see the day itself. The tests flip a day's outcomes and check nothing changes. Result: +0.2 lift in both windows." |
| 7 | 6:45–8:00 | `critiques/sample_explore_modify_round1.md`, the early-stopping table | "The critic found my biggest mistake. Early stopping held out random rows from the same days, so boosting memorised days and hit the 3,000-tree cap. Holding out whole days fixed it. Rounds 2 and 3 found the same flaw in the neural net." |
| 8 | 8:00–9:00 | Model MO.2 table and MO.3 bar chart; `model_chosen.json` | "Enterprise Miner's nodes: regression, tree, neural net, plus boosting. By the pre-declared rule the champion is logistic regression on 800k rows, statistically tied with boosting." |
| 9 | 9:00–10:30 | `scripts/run_assess.py` freeze block; Assess AS.1 targets; AS.2 gains/lift charts; AS.3 by month | "One shot at summer 2026: a fingerprint first, then a single scoring. 63% of the selected flights were disrupted, against 47% for the best rule. Gap +0.69, better on 91% of days, all three targets met. Honest note: the net and boosting edged the champion on test." |
| 10 | 10:30–11:30 | Terminal: `streamlit run deployment/app.py`; pick a July day | "Score: `score.py` ranks any day, and this app replays the test summer. Pick a day and see the 2% list and how many went wrong. The model card and monitoring plan are in `deployment/`." |
| 11 | 11:30–12:00 | `reports/sas_ondemand_guide.md` (or the SAS OnDemand screen if recorded) | "The guide rebuilds the same flow in SAS Studio. Lessons: write the metric for the decision, test the sampling claim, use time-based holdouts everywhere, seal the test." |

## Shot list / prep
- Open the notebook with saved outputs (no re-run needed). Zoom the learning-curve and Assess figures.
- Have `streamlit run deployment/app.py` already started in a terminal tab.
- Optional SAS segment: follow `reports/sas_ondemand_guide.md` in SAS OnDemand for Academics. Record the Sample (stratified), Partition, Regression and ROC steps (3–4 min) and splice it in after step 9.
