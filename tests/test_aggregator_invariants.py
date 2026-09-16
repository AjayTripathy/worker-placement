"""Alerts-page invariants — the behaviors user catches forced us to guarantee."""
import pytest


@pytest.fixture(scope="module")
def alerts_payload():
    from desk.ui.aggregator import alerts
    return alerts()


def test_held_names_never_in_go(alerts_payload, root):
    import json
    led = json.loads((root / "desk" / "data" / "research_ledger.json").read_text())["names"]
    held = {n["ticker"] for n in led if (n.get("verdict") or "").upper() in ("HELD", "OWN")}
    assert not held & {r["ticker"] for r in alerts_payload.get("go", [])}


def test_ready_rows_are_pipeline_complete(alerts_payload):
    for r in alerts_payload.get("ready", []):
        assert r.get("edge_explainer"), f"{r['ticker']} in READY without an explainer"


def test_no_bucket_overlap(alerts_payload):
    b = {k: {r["ticker"] for r in alerts_payload.get(k, [])} for k in ("go", "no_go", "in_book", "ready")}
    names = list(b)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            assert not b[names[i]] & b[names[j]], f"{names[i]} ∩ {names[j]}"


def test_go_rows_have_dated_prices_or_are_blocked(alerts_payload):
    """The AMV0 rule: a GO must never rest on an undatable price."""
    for r in alerts_payload.get("go", []):
        assert r.get("px") is not None


def test_ownable_is_not_in_book(root):
    """'OWN' substring matched OWNABLE and routed un-bought names to the held bucket (IBEX 2026-07-03)."""
    import json
    from desk.ui.aggregator import alerts
    led = {n["ticker"]: (n.get("verdict") or "").upper()
           for n in json.loads((root / "desk" / "data" / "research_ledger.json").read_text())["names"]}
    for r in alerts().get("in_book", []):
        v = led.get(r["ticker"], "")
        assert v.split()[0] in ("HELD", "OWN"), f"{r['ticker']} (verdict {v}) in IN-BOOK without being held"


def test_event_enum_closed_and_calendar_carries_crowd():
    """Every ledger event_type must live in the closed enum; calendar events surface
    crowd odds (market_p_current) and event_type when present."""
    import json, pathlib
    from desk.events import EVENT_TYPES, validate_event_type
    root = pathlib.Path(__file__).resolve().parents[1]
    for l in (root / "desk" / "data" / "calibration_ledger.jsonl").read_text().splitlines():
        if not l.strip():
            continue
        r = json.loads(l)
        if r.get("event_type"):
            assert validate_event_type(r["event_type"]), f"free-typed event_type {r['event_type']}"
    import sys; sys.path.insert(0, str(root))
    from desk.ui.aggregator import predictions_calendar
    cal = predictions_calendar()
    allev = cal.get("upcoming", []) + cal.get("awaiting", []) + cal.get("resolved", [])
    fro = [e for e in allev if e.get("ticker") == "FRO" and e.get("date") == "2026-08-31"]
    assert fro and fro[0].get("crowd", {}).get("p") is not None, "FRO Aug-31 should carry the crowd pill"
    assert fro[0]["crowd"]["related"] is True, "the Hormuz-Dec map is RELATED, never EXACT"
    assert fro[0].get("event_type") == "monthly_data"
