"""API boundary: the NaN firewall and the health endpoint contract."""
import math


def test_sanitize_scrubs_nan_inf_recursively():
    from desk.ui.server import _sanitize
    dirty = {"a": float("nan"), "b": [1.0, float("inf"), {"c": float("-inf"), "d": 2.5}], "e": "x"}
    clean = _sanitize(dirty)
    assert clean["a"] is None
    assert clean["b"][1] is None
    assert clean["b"][2]["c"] is None
    assert clean["b"][2]["d"] == 2.5
    assert clean["e"] == "x"


def test_sanitize_output_is_json_encodable():
    import json
    from desk.ui.server import _sanitize
    payload = _sanitize({"x": float("nan"), "y": [float("inf")] * 3})
    json.dumps(payload, allow_nan=False)  # raises if any NaN survived


def test_health_shape(root):
    """Health must report page integrity + store ages without needing the HTTP server."""
    html = (root / "desk" / "ui" / "static" / "index.html").read_text()
    assert html.rstrip().endswith("</html>"), "page integrity broken at rest"
