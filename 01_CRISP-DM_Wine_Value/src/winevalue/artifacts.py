"""Phase 6: where the deployed artifacts live and how they are (re)built.

- ``data/processed/wine_prepared.parquet``: the prepared table (git-ignored); rebuilt from the raw file by
  ``prepare.prepare`` exactly as notebook §3 does.
- ``models/value_finder.joblib``: the fitted ``production.ValueFinder``. Served only by ``load_value_finder`` (which never
  rebuilds); rebuilt only by ``rebuild_value_finder`` (``deployment/build_artifact.py``), which saves after the reproduction check.
- ``models/manifest.json``: SHA-1 of the artifact, the reproduction check and the build settings.
"""

from __future__ import annotations

import hashlib
import json

import numpy as np
import pandas as pd

from . import config

PREP_PATH = config.DATA_PROCESSED / "wine_prepared.parquet"
MODEL_PATH = config.MODELS_DIR / "value_finder.joblib"
MANIFEST_PATH = config.MODELS_DIR / "manifest.json"


def load_prepared() -> pd.DataFrame:
    if PREP_PATH.exists():
        return pd.read_parquet(PREP_PATH)
    from .data import load_raw
    from .prepare import prepare
    from .splits import anon_lockbox_like
    raw = load_raw()
    prep, _ = prepare(raw, anon_lockbox_like=anon_lockbox_like(raw.drop_duplicates()))
    PREP_PATH.parent.mkdir(parents=True, exist_ok=True)
    prep.to_parquet(PREP_PATH)
    return prep


def sha1(path) -> str:
    return hashlib.sha1(open(path, "rb").read()).hexdigest()


REPRO_TOL = 1e-8
REPRO_KEYS = ("ridge", config.SELECTED_DM1, config.SELECTED_DM2, "P(90+)", "serving path (raw inputs, prepare_new)")   # last: critic round 4 #3


def reproduction_passed(rep) -> bool:
    """A reproduction record passes only if it has every output in ``REPRO_KEYS``, each a finite difference ≤ ``REPRO_TOL``
    (a missing, partial, NaN or infinite record fails; Phase 6 critic round 2 issue 5)."""
    try:
        vals = [float(rep[k]) for k in REPRO_KEYS]
    except (KeyError, TypeError, ValueError, IndexError):
        return False
    return all(np.isfinite(v) and 0 <= v <= REPRO_TOL for v in vals)


def save_value_finder(vf, reproduction: pd.Series) -> dict:
    """Write the artifact and its manifest. Refuses unless ``reproduction`` (``production.reproduces_lockbox``) shows every
    saved lockbox prediction reproduced (§5.3 condition 1)."""
    import joblib
    if not reproduction_passed(reproduction):
        raise ValueError(f"lockbox reproduction failed or missing ({reproduction}); not saving the artifact")
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(vf, MODEL_PATH, compress=3)
    man = {"artifact": MODEL_PATH.name, "sha1": sha1(MODEL_PATH), "bytes": MODEL_PATH.stat().st_size,
           "info": {k: (list(v) if isinstance(v, tuple) else v) for k, v in vf.info.items()},
           "lockbox reproduction (max abs difference)": {k: float(v) for k, v in reproduction.items()}}
    MANIFEST_PATH.write_text(json.dumps(man, indent=2, default=str))
    return man


def load_value_finder():
    """The serving path (app, ``score.py``, ``pilot_eval.py``). Refuses to serve unless the manifest exists, records a
    passed lockbox reproduction, and its SHA-1 matches the file (monitoring plan §4). It never rebuilds: a rebuild goes
    through ``rebuild_value_finder`` (``deployment/build_artifact.py`` or notebook 6.1b)."""
    import joblib
    if not MODEL_PATH.exists() or not MANIFEST_PATH.exists():
        raise RuntimeError(f"{MODEL_PATH.name} or {MANIFEST_PATH.name} is missing; rebuild with deployment/build_artifact.py")
    man = json.loads(MANIFEST_PATH.read_text())
    rep = man.get("lockbox reproduction (max abs difference)") or {}
    if not reproduction_passed(rep):
        raise RuntimeError(f"{MANIFEST_PATH.name} records no passed lockbox reproduction; rebuild with deployment/build_artifact.py")
    if sha1(MODEL_PATH) != man.get("sha1"):
        raise RuntimeError(f"{MODEL_PATH.name} does not match the SHA-1 in {MANIFEST_PATH.name}; rebuild with deployment/build_artifact.py")
    return joblib.load(MODEL_PATH)


def rebuild_value_finder(verbose: bool = True):
    """Refit the frozen selections (``production.build``), check them against the saved lockbox predictions and save
    them only if every prediction is reproduced. About 4 minutes."""
    from .production import build, reproduces_lockbox
    prep = load_prepared()
    vf = build(prep, naming_dir=config.PROJECT_DIR / "reports" / "bsc3_naming", verbose=verbose)
    saved = pd.read_csv(config.PROJECT_DIR / "reports" / "tables" / "phase5_lockbox_predictions.csv.gz").set_index("review_id")
    rep = reproduces_lockbox(vf, prep, saved)
    return vf, save_value_finder(vf, rep)


def load_catalogue() -> pd.DataFrame:
    from .production import catalogue
    return catalogue(load_prepared())
