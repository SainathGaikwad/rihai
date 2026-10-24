"""The Streamlit front end, run headlessly: the demo case, an unknown section, and the sample roster must all render."""
from pathlib import Path

import pytest

st_testing = pytest.importorskip("streamlit.testing.v1")

APP = str(Path(__file__).resolve().parents[1] / "rihai" / "app" / "streamlit_app.py")


def _app():
    return st_testing.AppTest.from_file(APP, default_timeout=60).run()


def test_demo_case_renders_eligible_with_gate_pass():
    at = _app()
    at.button[0].click().run()
    assert not list(at.exception)
    assert any(m.value == "### :green[ELIGIBLE]" for m in at.markdown)
    assert any(v.value.startswith("PASS") for v in at.success)


def test_unknown_section_does_not_crash():
    at = _app()
    at.text_input[0].set_value("BNS 9999").run()
    at.button[0].click().run()
    assert not list(at.exception)
    assert any(m.value == "### :red[UNKNOWN_SECTION]" for m in at.markdown)


def test_sample_roster_runs():
    at = _app()
    [b for b in at.button if b.label == "Run on the sample roster"][0].click().run()
    assert not list(at.exception)
    assert any(m.value.startswith("**Summary:** ELIGIBLE") for m in at.markdown)
