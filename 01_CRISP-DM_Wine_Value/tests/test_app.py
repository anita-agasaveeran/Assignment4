"""BSC4 smoke test of the Streamlit app (Phase 6 critic round 1 issue 12): one screen shows every output in < 3 s."""
import re
from pathlib import Path

import pytest

from winevalue import artifacts

APP = Path(__file__).resolve().parents[1] / "deployment" / "app.py"


@pytest.mark.skipif(not artifacts.PREP_PATH.exists(), reason="prepared table not built (run notebook §3 or the app once)")
def test_one_wine_screen_shows_every_bsc4_output_in_under_3_s():
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(str(APP), default_timeout=300).run()
    assert not at.exception
    at.button[0].click().run()                 # the form's "Estimate" button, with the default Tempranillo note
    assert not at.exception
    labels = {m.label for m in at.metric}
    assert {"Estimated score band", "P(90+), relative", "Ranker percentile"} <= labels
    text = " ".join(m.value for m in at.markdown)
    assert "Value verdict:" in text and "Flavour profile:" in text and "5 similar reviewed wines" in text
    assert len(at.dataframe[0].value) == 5
    secs = float(re.search(r"Computed in ([\d.]+) s", " ".join(c.value for c in at.caption)).group(1))
    assert secs < 3
