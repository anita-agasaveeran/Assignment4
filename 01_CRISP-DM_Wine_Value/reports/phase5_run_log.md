# Phase 5 run log

The order of every Phase 5 step. Times are Pacific, from the Claude Code session record. The models, rules and targets were frozen in commit `8632fba` (tag `wine-phase4`, pushed 2026-11-07) before any Phase 5 code was written.

## Before the lockbox was unsealed (2026-11-07)

| Step | Data used | Lockbox scores read? |
|---|---|---|
| `phase5.py` written: a generic `run_split`, the sealed `lockbox_split` loader, and `evaluate` (every target and sensitivity); tests for the seal | – | No |
| **Dress rehearsal 1** on development fold 3. Stopped on a division by zero: a tiny critic pool where the simple rule's top 10% held no value wine. Fixed by reporting that lift as undefined | Development fold 3 | No (lockbox `points` also blanked in memory) |
| **Dress rehearsal 2** on fold 3: reproduces Phase 4's fold-3 numbers exactly (MAE 1.742, reduction 23.0%, ±2 0.686, P@100 0.678, lift 1.96×, LB 1.77, Brier 0.140, band coverage 0.778). Found two further issues: the sensitivity refit showed DM1b as failed instead of "not run" (fixed), and H6 fails on fold 3 alone (LB −0.02), a risk for BSC5 recorded before unsealing | Development fold 3 | No |
| **BSC3 blind naming:** two reviewer agents on different models (Sonnet, Haiku), no tools, term lists only, blind to each other and to which set is primary. Both named 8 of 8 primary profiles with confidence ≥ 3, and 6 of 8 secondary (`reports/bsc3_naming/`) | Development notes (text only) | No |
| Notebook Phase 5 cells added: rehearsal (with an equality assertion against Phase 4), naming tally, lockbox cell guarded by `config.LOCKBOX_UNSEALED`; full notebook run in sealed mode (no errors; rehearsal assertion holds; lockbox cell printed "sealed") | Development data | No |

## Unsealing

_Not yet. Waiting for the project owner's go-ahead._
