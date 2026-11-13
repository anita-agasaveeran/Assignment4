# Which 380 Flights Will Go Wrong Tomorrow? A SEMMA Walkthrough on 11.7 Million US Flights

*How SAS's five-step data-mining recipe, run honestly, turned a coin-flip-sized problem into a care team catching 63% of disruptions with 2% of the effort, and why the biggest lesson came from a bug a reviewer found.*

*~10 min read · Code and notebook: [GitHub](https://github.com/anita-agasaveeran/Assignment4/tree/main/02_SEMMA_Flight_Delays) · [Open in Colab](https://colab.research.google.com/github/anita-agasaveeran/Assignment4/blob/main/02_SEMMA_Flight_Delays/notebooks/SEMMA_Flight_Disruption.ipynb) · Video walkthrough: _link_*

---

## The decision
Picture an airline's customer-care desk at **4:45 pm Eastern**. Tomorrow, about 19,000 domestic flights will operate, and the team has capacity to reach out proactively on roughly **380 of them, or 2%**: offering rebookings, warning about tight connections, staffing the help desks. Which 380?

Nearly a quarter of US flights are *disrupted*: they land 15+ minutes late, are cancelled or are diverted. Pick 380 at random and about 90 of them will go wrong. Can data do much better, using only what is actually known the evening before?

I used the **US Bureau of Transportation Statistics on-time data** (11.7 million flights, January 2025 to August 2026, via Kaggle, CC0) and **SEMMA**, SAS Institute's methodology. It's the five-step sequence printed on SAS Enterprise Miner's toolbar: **Sample, Explore, Modify, Model, Assess**.

## Step 0: what SEMMA doesn't give you
SEMMA starts at *Sample*. It has no "understand the business" step, unlike CRISP-DM. So I ran a short **front pass** first:
- **Fix the decision clock:** 16:45 ET the day before.
- **Fix the success metric:** the share of the *day's* top 2% that is actually disrupted, relative to that day's overall rate. That's **per-day lift**, because the team ranks within one evening.
- **Seal a test set:** the summer of 2026, untouched until the very end.

The front pass caught a leak straight away. In BTS data, **the tail number is missing exactly when a flight is cancelled**, so a feature built from it "predicted" cancellations perfectly. It's gone.

## Sample: does sampling lose anything?
SAS's own white paper, *Data Mining and the Case for Sampling*, argues that a well-drawn sample loses almost nothing. Its case study shows the same accuracy from 0.03% to 20% samples. I tested that claim instead of assuming it, with a **pre-registered learning curve**:
- 5 stratified samples at each of eight sizes, from 25k to 3.2M flights;
- each scored on every flight of the validation months;
- a rule written down *before* the run: use the smallest size within 0.02 lift and 0.002 AUC of the full data.

The answer split by model:
- **Logistic regression** behaved exactly like the SAS case study. It was within 0.02 lift of its full-data value from **400k rows**.
- **Gradient boosting** kept learning up to 3.2 million rows (46%) in winter–spring and 1.6 million (72%) in summer.

So boosting trained on a 72% sample, and the simpler models on 800k. The samples were stratified by month × airline × outcome and passed every representativeness check: means within 0.0025 standard deviations, no excess of outlying daily rates.

## Explore: when and where it goes wrong
On a 5% exploration sample:
- **The clock is everything.** In summer, the disruption rate climbs from **11% for 6 am departures to 41% at 6 pm**, because delays pile up through the day.
- **Delays propagate.** Late-arriving aircraft cause 34–42% of all delay minutes, every month.
- **Summer is different.** Yesterday predicts today less well (day-to-day correlation 0.58 vs 0.66), and afternoon departures carry more weather and air-traffic delay. That pattern fits afternoon thunderstorms.
- **Storm days are extreme.** On January 25, 2026, 65% of flights were disrupted and 46% were cancelled. On a day like that, even a perfect list can only reach a lift of 1.5.

## Modify: one clock, and history that can't cheat
Two design decisions carried the project:
1. **A single national clock.** A flight from yesterday counts as "known" only if it was scheduled to land by **16:45 Eastern**. Its arrival time is computed from departure in ET plus scheduled duration, which handles daylight saving, Arizona and the Florida panhandle. The naive "17:00 local" rule had let 8.6% of flights, mostly in the West, leak in after the decision time.
2. **Every history feature is a trailing window over earlier days:**
   - yesterday's rate at the origin, destination, airline and nationally;
   - last week's rates;
   - the last four weeks for this route, this airline at this hour, this airport at this hour, and this exact flight number.

   Rates are shrunk toward the base rate, so a thin airport doesn't swing to extremes. A day's features never see that day, and unit tests prove it.

On the same model and the same sample, these inputs added **+0.21 per-day lift in winter–spring and +0.19 in summer**, with 90% intervals well clear of zero.

## Model: Enterprise Miner's nodes, in Python
I fit the classic SAS EM model families (**Regression, Decision Tree, Neural Network**) plus **Gradient Boosting**. Each was tuned on Jan–Apr 2026 and rehearsed on the summer of 2025. The pre-declared champion rule was the best average lift across the two windows.

- **Logistic regression won:** 2.44 in winter–spring and 2.23 in summer.
- **Gradient boosting** was essentially tied: 2.47 and 2.14.
- **The neural network** came next (2.47 and 2.07), and **the decision tree** trailed (2.09 and 1.81).

An additive model on 800k rows matching a 5-million-row ensemble is the SAS sampling paper's point, arriving through the side door. Once Modify has turned history into clean rates, there isn't much left for a flexible model to find.

## The bug that changed the story
I had the AI reviewer play a strict SEMMA authority. Its first review scored my Sample-to-Modify stages **6/10** and found a flaw I'd missed. **LightGBM's early stopping held out random rows from the same training days.** Several inputs take one value per day (yesterday's national rate, for example), so the model could memorise each day, and the held-out rows kept rewarding more trees. Every large fit ran to the 3,000-tree cap. My first learning curve had therefore concluded "don't sample; boosting needs all the data", and that conclusion was an artefact.

Holding out *whole days* fixed it:
- fits stopped at about 100 trees and took seconds instead of minutes;
- the sample-size verdict moved from 100% to 72%;
- boosting got better.

A second review found **the same flaw hiding in the neural network** (scikit-learn's built-in early stopping), and a third found that warm-starting restarted the optimiser every epoch. Each fix moved numbers, but **none changed the champion**, which is the reassuring part. The less comfortable part: the methodology looked rigorous, and the flaw was still there.

## Assess: one shot at the sealed summer
Then the 2026 summer, 2.46 million flights, was scored **once**. The code fingerprint was recorded first, and the script refuses to run a second time.

| May–Aug 2026 | Per-day top-2% lift | Share of selected flights disrupted |
|---|---|---|
| **Champion (logistic regression)** | **2.39** | **63%** |
| Best simple rule (airline × hour history) | 1.70 | 47% |
| All flights | 1.00 | 27% |

- The champion beats the best simple rule by **+0.69** (90% interval +0.53 to +0.86) and **on 91% of days**.
- The result holds when cancelled flights without a tail number are added back, and with storm days removed.
- **For the care team:** about **60 more disrupted flights reached every evening for the same effort.**

Two honest footnotes:
- On the test summer, the neural network (2.46) and boosting (2.44) edged the chosen regression. The champion was fixed before unsealing, so it stays, and all three cleared every target.
- Lift fades through the summer, from 2.6 in May to 2.2 in August, as thunderstorm season makes the evening-before call harder.

## Score: making it usable
SEMMA ends at Assess, but Enterprise Miner's **Score** node turns a model into code. The repo has:
- **`score.py`**, which ranks any day's flights from the raw table (blanking that day's outcomes first);
- **a Streamlit app** that replays the 2026 summer ("which flights would the team have called, and how many went wrong?");
- **a model card and a monitoring plan**: weekly lift against the simple rule, drift checks, and a refit every four months.

## What I'd tell someone starting a SEMMA project
1. **Write the success metric for the decision, not the dataset.** Pooled AUC rewarded spotting bad *days*. The team needs the bad *flights within a day*.
2. **Treat SAS's sampling claim as a hypothesis.** It held for the simple model and not for boosting. A learning curve with a rule written in advance settles it.
3. **Let time define every split, including the ones inside your model.** Random-row holdouts in time-structured data lie, even inside early stopping.
4. **Seal the test, and make breaking the seal hard.** The sealed result came out *better* than the validation preview, because the targets were set honestly and not tuned to it.

*Data: US BTS Reporting Carrier On-Time Performance, via Kaggle (Samuel_Pbq, CC0). Method: SAS Institute, "Data Mining and the Case for Sampling" (SEMMA). Code, notebook, critic reviews and the SAS OnDemand rebuild guide are in the GitHub repo.*
