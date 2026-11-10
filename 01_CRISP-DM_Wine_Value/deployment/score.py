"""Batch scoring for one buying round (CRISP-DM 6.1).

    python deployment/score.py candidates.csv -o scored.csv --round 7 [--k 100]

The candidate file is EVERY candidate of the round, at any price: the ≤ $25 test is applied after ``config.PRICE_DEFLATOR``,
so a file filtered at a nominal $25 would lose wines that are ≤ $25 in 2017 dollars (the ≤ $25-share alert flags a file
that looks pre-filtered). Input columns: ``note`` (or ``description``), ``country``, ``variety``, ``price``; optional ``province``, ``vintage``,
``title``, ``winery``, ``designation``, ``region_1``, ``source``, ``wine_id``. Output: every input row with the shortlist
rank and round tier (≤ $25 candidates only), shortlist flag, P(90+), estimated band, value
verdict, flavour profile and data-quality flags. Country, province, grape, region and winery names are mapped to the training
spellings (winery too), and prices converted with ``config.PRICE_DEFLATOR`` (2017 dollars; written as ``price (2017 $)`` with the ``price deflator`` column). The band and verdict are blanked where ``deployment/band_status.json``
withdrew them (``pilot.band_hidden``). The round's monitoring report (drift indicators against ``config.MONITOR_ALERTS``,
flag counts, and the self-referenced rule against the earlier rounds' reports in the same folder) is written next to the
output as ``<out>.monitoring.json``, with the round number. A file without the required columns is refused.

``--round`` is the buying round's number (1, 2, ...). The self-referenced rule uses only reports of EARLIER rounds,
ordered by round number, one per round (the most recently written if a round was re-scored), and leaves out rounds that
raised the rule's own alert until the analyst sets ``"accepted": true`` in that round's report (the drop was checked and
is real, e.g. a new writer mix). Use ``--round 0`` for a test file (rollout step 1): round 0 is never anyone's history.
The rule runs only here, not in the app's shortlist view (which scores one file with no history).
"""

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR / "src"))

from winevalue import config, monitoring, pilot  # noqa: E402
from winevalue.artifacts import load_value_finder  # noqa: E402

STATUS_PATH = PROJECT_DIR / "deployment" / "band_status.json"


def load_history(out_dir: Path, before: int, exclude: Path | None = None) -> list[dict]:
    """The earlier rounds' indicator dicts, for the self-referenced drift rule (``monitoring.relative_alerts``): every
    ``*.monitoring.json`` in ``out_dir`` with a round number from 1 to ``before`` - 1, one per round (the most recently
    written wins if a round was re-scored), ordered by round number, each with its ``self-referenced alert`` and
    ``accepted`` flags (critic round 6 issue 3: file times alone mis-order re-scored rounds and count test files)."""
    by_round = {}
    for f in sorted(out_dir.glob("*.monitoring.json"), key=lambda f: f.stat().st_mtime):
        if exclude is not None and f.resolve() == exclude.resolve():
            continue
        try:
            r = json.loads(f.read_text())
            n = int(r["round"])
            h = dict(r["indicators"])
        except (OSError, ValueError, KeyError, TypeError):
            continue
        if 1 <= n < before:
            h[monitoring.RELATIVE_ALERTED] = bool(r.get(monitoring.RELATIVE_ALERTED, False))
            h[monitoring.ACCEPTED] = bool(r.get(monitoring.ACCEPTED, False))
            by_round[n] = h
    return [by_round[n] for n in sorted(by_round)]


def score_round(cand: pd.DataFrame, k: int = config.SHORTLIST_K, status: dict | None = None, vf=None,
                history: list[dict] | None = None) -> tuple[pd.DataFrame, dict]:
    """Score one buying round. Returns every input row with the outputs and data-quality flags, plus the round's
    monitoring report (drift indicators and alerts, report §6.2). The band and verdict are hidden with the same rule the
    pilot uses (``pilot.band_hidden``)."""
    vf = vf or load_value_finder()
    flags, report = monitoring.round_report(vf, cand, history)
    d = vf.prepare(cand)
    s = vf.score(d, prepared=True)
    sl = vf.shortlist(d, k=k, prepared=True)
    out = cand.join(s[["price (2017 $)", "estimate", "band low", "band high", "P(90+)", "value verdict", "profile name"]])
    out["price deflator"] = config.PRICE_DEFLATOR       # pilot_eval.py refuses a pilot file scored on another basis   # no development-percentile label: the round tier is the sampling tier
    out = out.join(sl[["rank", "round tier", "on shortlist"]]).join(flags)
    out["on shortlist"] = out["on shortlist"].fillna(False).astype(bool)
    hide = pilot.band_hidden(d, status)
    out.loc[hide, ["estimate", "band low", "band high"]] = float("nan")
    out.loc[hide, "value verdict"] = "hidden: band withdrawn by the pilot stop rule"
    report["bands hidden"] = int(hide.sum())
    return out.sort_values("rank", na_position="last"), report


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("candidates")
    ap.add_argument("-o", "--out", default="scored.csv")
    ap.add_argument("--k", type=int, default=config.SHORTLIST_K)
    ap.add_argument("--round", type=int, required=True, help="buying round number (1, 2, ...); 0 for a test file")
    ap.add_argument("--history", default=None, help="folder of earlier rounds' .monitoring.json files (default: the output's folder)")
    a = ap.parse_args(argv)
    try:
        status = json.loads(STATUS_PATH.read_text())
    except (OSError, ValueError):
        status = {}
    try:
        mon_path = Path(a.out).with_suffix(".monitoring.json")
        history = load_history(Path(a.history) if a.history else Path(a.out).resolve().parent, a.round, exclude=mon_path)
        out, report = score_round(pd.read_csv(a.candidates), a.k, status, history=history)
    except ValueError as e:
        sys.exit(f"refused: {e}")
    out.to_csv(a.out, index=False)
    mon = Path(a.out).with_suffix(".monitoring.json")
    report = {"round": a.round, **report}
    mon.write_text(json.dumps(report, indent=2, default=float))
    print(f"{len(out):,} wines scored; {int(out['on shortlist'].sum())} on the shortlist -> {a.out}")
    print(f"monitoring report -> {mon}; alerts: {'; '.join(report['alerts']) or 'none'}; flags: {report['flag counts']}")


if __name__ == "__main__":
    main()
