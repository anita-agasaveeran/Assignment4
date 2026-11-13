# Walkthrough Video: Script & Shot List (KDD · Canadian electricity)

> Target length about 12 minutes. Recorded by Anita. Screen recording of the GitHub repo, the Colab notebook (or a local Jupyter with saved outputs) and the Streamlit dashboard. The spoken lines are a guide; say them in your own words.

**Before recording:**
- Run `.venv/bin/python 03_KDD_Canada_Electricity/deployment/refresh.py`.
- Start `.venv/bin/streamlit run 03_KDD_Canada_Electricity/deployment/app.py` and keep it open in a browser tab.
- Open the notebook with outputs.
- Zoom the browser to 125%.

## Shot list
| # | Segment | On screen | Talking points | ~Time |
|---|---|---|---|---|
| 1 | Hook | Dashboard → "Validated findings" tab, national combustion-share line | "Is Canada's grid getting less dependent on burning fuel? Nationally: no. 21% in 2016, 23% in 2025. But two provinces are moving fast in opposite directions." | 0:45 |
| 2 | Why KDD | Repo README, then the notebook's opening cell (step list) | KDD = selection → preprocessing → transformation → mining → interpretation, with goals first and use last. Most of the work is before the mining, and patterns must be *validated* (interestingness) | 1:00 |
| 3 | Goals and the seal | `reports/front_pass.md` goals table; `config.py` K1–K4 rules; `PREREGISTRATION.json` | Four questions, each with a way to fail. 2025–26 sealed: loaders refuse it and tests check it. Rule files hashed before mining | 1:30 |
| 4 | Selection | Notebook KDD 1: selection table + missingness output | 13 geographies, Canada aggregate out; non-overlapping types; discontinued flow series out; missing = structural zeros | 0:45 |
| 5 | Preprocessing | KDD 2: integration checks; the Nunavut table; the catalogue cell | The two tables agree exactly; one BC residual flagged, not fixed. The 2016 survey break (front pass). Nunavut and NL coverage breaks. Event catalogue frozen *before* mining | 1:30 |
| 6 | Transformation | KDD 3: feature table + `t_profiles_shares_trade.png` + STL Quebec | Shares, trade ratios, calendar-balanced features, deseasonalized share, STL residuals. Point at Alberta, Nova Scotia and Ontario in the middle panel | 1:00 |
| 7 | Critic rounds | `critiques/kdd_steps1-3_round1.md`, then `kdd_steps4-6_round2.md` | Round 1 (7/10): self-confirming K2, a K3 rule that couldn't fail, no timestamp. Round 2 (7.5/10): the BC/PEI "declines" and the NB explanation were over-claims; what changed | 1:15 |
| 8 | Mining | KDD 4: dendrogram/PCA figure; `m_k2_changepoints.png`; flags table; K4 development table | Five archetypes (k-means = Ward). Alberta's drop in 2023 (burning less) vs Ontario's rise. Flags in NB, MB, NU. The forecasting combination wins on development data | 2:00 |
| 9 | Opening the seal | KDD 5e acceptance table, then 5f interpretation | K1 met (ARI 1.00, at k = 5). K2 met *as written*, but in substance AB and NS (+ small NL); show the post-hoc sensitivity table. K3 not met; the NB story the critic corrected; why not to edit the catalogue. K4 not met (ratio 1.015) | 2:00 |
| 10 | Using the knowledge | Dashboard: Archetypes tab → Structural change (pick Alberta, then Ontario) → Anomalies (pick New Brunswick) → Forecast | Seasonal naive deployed, challenger dotted; `refresh.py` = monitoring with frozen rules; `SOURCE_NOTICES.md` | 1:30 |
| 11 | Wrap-up | `reports/final_report.md` summary table | Three lessons: read the source's methodology notes, write failure conditions first, report failures as knowledge | 0:45 |

## Narration notes per segment
1. **Hook:** "Nationally, the combustion share didn't fall. Underneath, Alberta went from about 92% in 2016 to 72% so far in 2026, and Ontario from 7% in 2017 to 23%."
3. **Seal:** show `data.py` (`allow_sealed=False`) for two seconds. Say "the loaders enforce this; it's not an honour system."
5. **Preprocessing:** the line to land: "January 2016 isn't a renewables boom, it's a survey change."
8. **Mining:** in the K2 figure, the dashed lines are the primary change points and the red bars are the segment means.
9. **Evaluation:** say plainly that two of four tests failed and why that's still knowledge. Don't rush this segment.
10. **Dashboard:** keep each tab on screen for at least 5 seconds, and read the forecast caption aloud.

## Captions / on-screen text
- "Data: Statistics Canada Tables 25-10-0015-01 & 25-10-0016-01 (Open Licence). Not endorsed by Statistics Canada." Keep it on screen for the whole video, or in the description.
- Chapter markers in the YouTube description: 0:00 Hook · 0:45 KDD · 1:45 Goals & seal · 3:15 Selection · 4:00 Preprocessing · 5:30 Transformation · 6:30 Critic · 7:30 Mining · 9:30 Evaluation · 11:30 Dashboard · 13:00 Wrap-up

## YouTube description (draft)
> Knowledge discovery (KDD process) on 18 years of Statistics Canada electricity data: which provinces are alike, when their grids changed, which months were anomalous, and whether demand can be forecast better than "same month last year". Four pre-registered tests: two pass, two fail, all reported. Code and Colab: https://github.com/anita-agasaveeran/Assignment4/tree/main/03_KDD_Canada_Electricity
> Data adapted from Statistics Canada, Tables 25-10-0015-01 and 25-10-0016-01, Statistics Canada Open Licence. This does not constitute an endorsement by Statistics Canada.
