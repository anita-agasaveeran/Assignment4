# Phase 1 · Business Understanding: Critic Round 2

- **Date:** 2026-11-03
- **Reviewer:** Claude critic (independent subagent session), persona from `critic_prompt.md`. Read-only access. It re-ran the development-fold analysis independently (exact match), and respected the lockbox seal (counts and categorical coverage only).
- **Draft reviewed:** revision 2

## Score: 8 / 10 (up from 7) · Major issues remaining: yes (2)

Shortlist redefined over simulated cycles; fixed simple-rule set with random ties; region confound measured; masking pre-registered; development-only score statistics; no lockbox leakage; tests pass.

## Round-1 issues
Resolved: 2, 3, 4, 6, 7, 8, 10, 11, 12. Partially resolved: 1 (pilot gate too weak), 5 (targets not below the worst fold), 9 (number inconsistencies; notional saving), 13 (BSC5 not pre-specified; BSC3 reviewers not independent), 14 (due date).

## New issues
| # | Severity | Issue | Suggested fix |
|---|---|---|---|
| 1 | MAJOR | "Targets sit below the worst development fold" is false for **DM1** (20% vs fold 3's 11.9%) and the **BSC2 gain** (+10 pp vs fold 3's +7.3 pp). The BSC2 level margin is 0.8 pp. Fold 3 is the fold most like the lockbox | Lower the targets, or call them stretch targets. Fix the claim in all 4 places. Report per-fold gains (+16.3 / +22.5 / +7.3 / +17.8 pp) |
| 2 | MAJOR | **The pilot gate can't test A1.** ≥ 55% within ±2 is met by variety × country without reading the note (fold 3: 0.555). n = 100 → ±10 pp. It also only checks BO2 | Make it relative (≥ +8 pp over variety × country on the same pilot wines, 90% lower bound > 0). Add a BO1 check (ranker's top 20% precision ≥ 1.3× the price rule) |
| 3 | MINOR | One RNG draws both cycles and tie-breaks, so cycle composition depends on the rule dict. The simple-rule set lives only in the notebook | Separate RNG streams; move the rules into `winevalue.rules`; add a test |
| 4 | MINOR | BSC1's uncertainty condition (wins ≥ 90% of cycles) is close to automatic: the cycles overlap within one finite pool | Use a 90% cluster-bootstrap lower bound on the lift ≥ 1.2× |
| 5 | MINOR | Per-critic BSC1 isn't computable (Jeff Jenssen has 336 ≤ $25 candidates; O'Keefe is 50% of the pool) | Per-critic precision at the top 10% of each critic's pool; state that one critic dominates |
| 6 | MINOR | Best-rule labels wrong: folds 3 and 4 are "winery track record, then price" | Print the best rule per fold |
| 7 | MINOR | Inconsistent figures (0.37 vs 0.36; 0.18 vs 0.17; "15" vs 17.5 finds) | One table, one precision; explain the base-rate difference |
| 8 | MINOR | The $1,970 saving is notional (sampling spend is fixed) | Show the cash framing (samples needed to match) plus running costs |
| 9 | MINOR | Masking list misses drinking windows (7.2% of notes) and verdict words; "fine" hits descriptive phrases; DM1b's ratio is unstable. A broader mask keeps about 85% (not 91%) | Broaden the list (+ regex); report both; make DM1b an absolute MAE increase |
| 10 | MINOR | R8 threshold p > 0.9 not justified; at p > 0.5, 859 lockbox-attributed notes (99.2% accuracy) | Use 0.5 or report sensitivity |
| 11 | MINOR | BSC5 not pre-specified; "same sign" unclear for critic calibration; BSC3 reviewers not independent | Pre-register 5–8 directional hypotheses (≥ 3 replicate); spread statistic; non-analyst reviewers |
| 12 | MINOR | Uncertainty conditions incomplete; bootstrap unit and sidedness unstated | Winery-clustered bootstrap, one-sided; mark point-estimate-only criteria |

## Single most important remaining improvement
Re-set the targets and gates against the development evidence (fold 3 included), make the pilot gate beat the note-blind rule, and freeze the simple-rule set and RNG streams in `src/`.

## Changes made in response (revision 3)
| # | What I changed | Where |
|---|---|---|
| 1 | Targets re-set so every development fold (incl. fold 3) passes, with lower bounds: DM1 ≥ 10% (LB > 5%; fold 3 11.9%/10.5%); BSC2 ≥ 0.60 and ≥ +5 pp (fold 3 0.63, +7.3/LB +6.0). "Below the worst fold" claim replaced by a per-fold table against each target | config; §1.1 BSC table; §1.2 per-fold table |
| 2 | Pilot gate made relative to note-blind rules on the same pilot wines: ±2 gain ≥ +5 pp over variety × country (LB > 0) **and** BO1 check (top-20% precision ≥ 1.3× price rule) | §1.1; `config.PILOT_*` |
| 3 | Separate RNG streams for cycles vs ties (test proves cycle composition doesn't depend on the rule dict). Simple-rule set frozen in `winevalue.rules` | value.py; rules.py; tests |
| 4 | BSC1 uncertainty condition replaced with a winery-clustered bootstrap LB on top-10% lift ≥ 1.2× (dev 1.43–1.92×) | value.py; BSC1 |
| 5 | Per-critic reporting = top-10% precision of each critic's pool; lockbox composition table; O'Keefe dominance stated (R11); with/without O'Keefe | §1.1; R11 |
| 6 | Best rule printed per fold (price in folds 0–1; winery then price in folds 3–4) | Per-fold table |
| 7 | All figures from single tables at 2 dp. Background uses the pool base rate (17.6% → ~18 finds) and explains the 15.0% | Background; tables |
| 8 | Economics in two framings: cash (≈ 50 samples to match → ≈ $1,150/cycle after running cost; break-even ≈ 3 cycles) and opportunity value (≈ $1,874; ≈ 2 cycles) | §1.2 economics |
| 9 | Masking list broadened (verdict words + drinking-window regex; "fine" removed). Retention reported under both lists (87% vs 91%). DM1b now an absolute MAE increase ≤ 0.15 (dev 0.03–0.11). Wording: "fixed in Phase 1, broadened once after critic round 2" | config; DM1b; masking table |
| 10 | Attribution threshold sensitivity table (0.5/0.7/0.9); 0.5 chosen (99.2% accurate) → 859 rows dropped | §1.2; R8; config |
| 11 | BSC5 = pre-registered hypotheses H1–H6 (≥ 3 must replicate in both datasets); H4 as a spread statistic. BSC3 reviewers = two independent, mutually blind agents, not the analyst | §1.1; `config.HYPOTHESES` |
| 12 | Uncertainty specified: one-sided 90%, 500 winery-clustered resamples. Uncertainty column added to DM table; DM1b/DM4/DM5 marked point-estimate only | §1.1; §1.3 |
| (r1 #14) | Due date still unconfirmed (`instructions.txt` has none); asked of the project owner | §1.4 |
