"""Pilot evaluation: interim checks and the final gate (report §5.3 conditions 3, 4 and 7; protocol in ``winevalue.pilot``).

    python deployment/pilot_eval.py pilot_scored.csv [--out reports/pilot] [--update-status]

``pilot_scored.csv``: one row per pilot wine whose critic score has arrived, with the scoring inputs (``note``,
``country``, ``variety``, ``price``, optional ``province``/``vintage``/``title``/``winery``/``designation``/``region_1``),
plus ``points`` (the critic score), ``source`` (note source: writer, importer or producer; required: rows without one never
count toward the source minimum), ``order`` (1 = first score to arrive), ``scorer`` (who published the score; only
``config.PILOT_PRIMARY_SCORER`` enters the gate, others are a sensitivity) and ``sampled`` (true if the team sampled or
listed the wine). Rows above $25 (after ``config.PRICE_DEFLATOR``) are ignored (the pilot is on ≤ $25 notes). The file
must carry ``score.py``'s ``price deflator`` column with every value equal to ``config.PRICE_DEFLATOR``, or it is refused
(the rounds were scored on another price basis); ``--deflator-confirmed`` accepts a file without the column.

Writes ``gate.json`` (both gate parts, joint gate, Option F decision), ``checks.csv`` (each interim check),
``band_withdrawn.csv``, ``source_intercept.csv`` (secondary, reported only), ``sensitivity.json`` (gate on all scorers
on unsampled wines and on matched-winery wines; reported only), ``per_scorer.csv`` and ``sources.csv`` (the note sources after
name canonicalisation, with the spellings merged into each; the analyst checks it for near-duplicates). With ``--update-status`` it also writes
``deployment/band_status.json``, which the app and ``score.py`` read to hide the band where the stop rule fired.
Checks run every ``config.PILOT_CHECK_EVERY`` scores. The decision is final at the first check with ≥ 400 wines from ≥ 3
sources with ≥ 50 wines each, after a futility pause, or at ``config.PILOT_MAX_WINES`` wines; before that it is interim.
"""

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR / "src"))

from winevalue import config, pilot  # noqa: E402
from winevalue.artifacts import load_value_finder  # noqa: E402

STATUS_PATH = PROJECT_DIR / "deployment" / "band_status.json"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("pilot_csv")
    ap.add_argument("--out", default=str(PROJECT_DIR / "reports" / "pilot"))
    ap.add_argument("--update-status", action="store_true")
    ap.add_argument("--deflator-confirmed", action="store_true",
                    help="accept a file without score.py's 'price deflator' column (the analyst confirms every round was "
                         "scored with config.PRICE_DEFLATOR)")
    a = ap.parse_args(argv)
    raw = pd.read_csv(a.pilot_csv)
    if "price deflator" not in raw and not a.deflator_confirmed:
        sys.exit("refused: the file has no 'price deflator' column (keep score.py's column, or rerun with "
                 "--deflator-confirmed once you have checked that every round used config.PRICE_DEFLATOR)")
    if "price deflator" in raw:
        d = pd.to_numeric(raw["price deflator"], errors="coerce")
        if d.isna().any():
            # critic round 6 issue 5: rows with a blank deflator were not scored by score.py (e.g. appended from another
            # source); --deflator-confirmed covers only a file without the column
            sys.exit(f"refused: {int(d.isna().sum())} rows have no readable 'price deflator' value; score them with "
                     "score.py or remove them")
        used = sorted(set(d.round(6)))
        if used != [round(config.PRICE_DEFLATOR, 6)]:
            sys.exit(f"refused: the rounds were scored with price deflator(s) {used}, but config.PRICE_DEFLATOR is "
                     f"{config.PRICE_DEFLATOR}; the pilot must use the deflator set at rollout step 0")
    res = pilot.evaluate_raw(raw, load_value_finder())
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    (out / "gate.json").write_text(json.dumps(res["gate"], indent=2, default=str))
    res["checks"].to_csv(out / "checks.csv", index=False)
    res["withdrawn"].to_csv(out / "band_withdrawn.csv", index=False)
    res["intercept"].to_csv(out / "source_intercept.csv", index=False)
    res["sources"].to_csv(out / "sources.csv", index=False)
    sens = res["sensitivity"]
    (out / "sensitivity.json").write_text(json.dumps({k: v for k, v in sens.items() if k != "per scorer"}, indent=2, default=str))
    sens["per scorer"].to_csv(out / "per_scorer.csv", index=False)
    if a.update_status:
        STATUS_PATH.write_text(json.dumps(res["status"], indent=2))
    g = res["gate"]
    if "scorer" in raw:
        print("scorer spellings (wines):", raw["scorer"].fillna("(blank)").value_counts().to_dict(),
              f"| counted as {config.PILOT_PRIMARY_SCORER}: {config.PILOT_PRIMARY_SCORER} and {', '.join(config.PILOT_PRIMARY_SCORER_ALIASES)}")
    if not g["wines"]:
        sys.exit(g["decision"])
    bo1 = g.get("BO1 passes (after comparator rule)")
    at_decision = g.get("decision at") is not None
    pf = lambda x: ("PASS" if x else "fail") if at_decision else "interim reading, no decision"
    print(f"{g['wines']} pilot wines | BO2 band: gain {g['within gain (pp)']:+.1f} pp (LB {g['within gain LB (pp)']:+.1f}) "
          f"{pf(g['BO2 passes'])} | BO1 shortlist: lift {g['top-20% lift']:.2f}× (LB {g['top-20% lift LB']:.2f}) "
          f"{pf(bo1)}{' (fails the comparator rule)' if at_decision and g['BO1 passes'] and not bo1 else ''} "
          f"| joint {pf(g['joint gate passes']) if at_decision else 'read at the decision point'}")
    print("decision:", g["decision"])
    print(f"final: {g['final']} (decision at {g['decision at']} of {g['wines received']} wines received)")
    print("band withdrawn:", res["status"])
    cov = g.get("winery coverage (BO1 comparator)")
    if cov is not None:
        m = res["sensitivity"].get("matched-winery wines")
        print(f"BO1 comparator: {cov:.0%} of the wines used have a winery from the training data (minimum "
              f"{config.PILOT_MIN_WINERY_COVERAGE:.0%}); matched-winery lift "
              + (f"{m['top-20% lift']:.2f}× (LB {m['top-20% lift LB']:.2f}) on {m['wines']} wines" if m else "not computed (fewer than "
                 f"{config.PILOT_CHECK_EVERY} matched wines)"))
        if g["comparator degraded"]:
            print(("DEGRADED comparator: the shortlist must also pass on the matched wines alone"
                   if at_decision else "Coverage below the minimum so far: at the decision point the shortlist will also have "
                   f"to pass on the matched wines alone (at least {config.PILOT_CHECK_EVERY} of them)")
                  + ("" if m or not at_decision else f"; too few matched-winery wines (< {config.PILOT_CHECK_EVERY}), so the shortlist is not deployed"))
    if g["wines without a note source"]:
        print(f"WARNING: {g['wines without a note source']} pilot wines have no note source; they do not count toward the "
              f"{config.PILOT_MIN_SOURCES}-source minimum. Record the source.")
    if g["wines from other scorers (sensitivity only)"]:
        print(f"{g['wines from other scorers (sensitivity only)']} wines scored by others than {g['primary scorer']}: "
              "sensitivity only (sensitivity.json, per_scorer.csv)")
    print("note sources (one spelling each; check for near-duplicates the name key can't merge):")
    print(res["sources"].to_string(index=False))


if __name__ == "__main__":
    main()
