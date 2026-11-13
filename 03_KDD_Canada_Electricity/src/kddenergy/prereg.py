"""Pre-registration manifest: SHA-256 of every file that defines a K1-K4 rule, written before mining.

The notebook calls ``verify()`` at the top of the Data-mining step; it raises if any rule file changed after the
manifest was written. (A git commit would give an external timestamp; commits need the user's approval here.)
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

from . import config as c

MANIFEST = c.PROJECT_DIR / "PREREGISTRATION.json"
RULE_FILES = ["src/kddenergy/config.py", "src/kddenergy/selection.py", "src/kddenergy/preprocess.py",
              "src/kddenergy/transform.py", "src/kddenergy/mining.py", "src/kddenergy/forecast.py",
              "data/external/event_catalogue.csv", "tests/test_kdd_steps.py", "tests/test_mining.py"]


def _sha(rel: str) -> str:
    return hashlib.sha256((c.PROJECT_DIR / rel).read_bytes()).hexdigest()


def write(note: str = "") -> dict:
    m = {"written_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "note": note,
         "files": {f: _sha(f) for f in RULE_FILES}}
    MANIFEST.write_text(json.dumps(m, indent=2))
    return m


def verify() -> dict:
    m = json.loads(MANIFEST.read_text())
    changed = [f for f, h in m["files"].items() if _sha(f) != h]
    if changed:
        raise RuntimeError(f"rule files changed after pre-registration: {changed}")
    return m
