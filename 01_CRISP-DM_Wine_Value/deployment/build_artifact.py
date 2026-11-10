"""Rebuild models/value_finder.joblib (CRISP-DM 6.1; report §6.1, §5.3 condition 1).

    python deployment/build_artifact.py

Refits the frozen selections on all development rows (``winevalue.production.build``, about 4 minutes), compares the
lockbox predictions with ``reports/tables/phase5_lockbox_predictions.csv.gz`` row by row, and writes the artifact and
``models/manifest.json`` only if every difference is ≤ 1e-8. The app and scripts refuse any artifact whose manifest lacks
that record or whose SHA-1 doesn't match. Needed after a scikit-learn upgrade or if the file is lost.
"""

import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR / "src"))

from winevalue.artifacts import rebuild_value_finder  # noqa: E402

if __name__ == "__main__":
    _, man = rebuild_value_finder()
    print("saved", man["artifact"], man["sha1"], man["lockbox reproduction (max abs difference)"])
