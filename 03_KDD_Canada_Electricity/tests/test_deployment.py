import json
from pathlib import Path

import pytest

DEP = Path(__file__).resolve().parents[1] / "deployment"


@pytest.mark.skipif(not (DEP / "artifacts" / "meta.json").exists(), reason="run deployment/refresh.py first")
def test_artifacts_and_dashboard():
    meta = json.loads((DEP / "artifacts" / "meta.json").read_text())
    assert meta["k1_k"] == 5 and meta["forecast_deployed"] == "snaive"
    for f in ("panel", "clusters", "changepoints", "anomalies", "forecast"):
        assert (DEP / "artifacts" / f"{f}.csv").stat().st_size > 0
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(str(DEP / "app.py"), default_timeout=120).run()
    assert not at.exception


def test_source_notices_carry_the_statcan_attribution():
    t = (DEP / "SOURCE_NOTICES.md").read_text()
    assert "does not\nconstitute an endorsement by Statistics Canada" in t or "does not constitute an endorsement by Statistics Canada" in t
    assert "25-10-0015-01" in t and "25-10-0016-01" in t and "open-licence" in t
