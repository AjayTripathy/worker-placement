"""Every validator guard must FIRE on a synthetic violation (an unfired guard is decoration —
proven twice on 2026-07-02)."""
import json


def test_ui_integrity_guard_fires(root):
    from desk.consistency_check import check_ui_static_integrity
    p = root / "desk" / "ui" / "static" / "index.html"
    bak = p.read_text()
    try:
        p.write_text(bak + "\nstray")
        flags = []
        check_ui_static_integrity(flags)
        assert any("stray content" in f for f in flags)
    finally:
        p.write_text(bak)


def test_guards_are_actually_invoked_by_main(root):
    src = (root / "desk" / "consistency_check.py").read_text()
    body = src[src.find("def main("):]
    for guard in ("check_held_not_in_go", "check_alert_records_complete", "check_ui_static_integrity"):
        assert f"{guard}(flags)" in body, f"{guard} defined but never invoked — decoration, not protection"


def test_alert_record_schema_guard_fires(root, tmp_record):
    """Plant a headless record for a name on the alerts page; the guard must flag it."""
    from desk.ui.aggregator import alerts
    a = alerts()
    surfaced = [r["ticker"] for r in a.get("go", []) + a.get("no_go", [])
                if (root / "desk" / "data" / "edge_classifications" / f"{r['ticker']}.json").exists()]
    if not surfaced:
        import pytest
        pytest.skip("no alerts-page name has a record right now")
    t = surfaced[0]
    from desk.consistency_check import check_alert_records_complete

    def strip(d):
        d.pop("edge_explainer", None)
    with tmp_record(t, strip):
        flags = []
        check_alert_records_complete(flags)
        assert any(t in f and "edge_explainer" in f for f in flags)
