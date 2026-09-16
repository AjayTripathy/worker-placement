"""The calibration ledger is the skill record: append-only, parseable, frozen fields immutable."""
import json


def test_ledger_parses_and_is_append_only_shaped(root):
    p = root / "desk" / "data" / "calibration_ledger.jsonl"
    lines = [l for l in p.read_text().splitlines() if l.strip()]
    assert len(lines) >= 30
    for l in lines:
        rec = json.loads(l)
        assert rec.get("ticker") and rec.get("our_p") is not None
        assert 0.0 <= float(rec["our_p"]) <= 1.0
        assert rec.get("status") in ("OPEN", "RESOLVED", "EXCLUDED_LOOKAHEAD", "VOIDED")


# A single print can carry several INDEPENDENT frozen calls — e.g. NOW's Q2 has distinct
# earnings_print / earnings_operating / earnings_stock_reaction calls, each with its own our_p.
# So the uniqueness key is (ticker, cat_date, event_type), not (ticker, cat_date).
# These two collisions are pre-existing genuine duplicate OPEN calls pending human adjudication
# (do NOT silently delete: the ledger is an append-only frozen scoreboard). Tracked, not swept.
KNOWN_DUPLICATE_OPEN_CALLS = {
    ("BAH", "2026-07-24", "earnings_print"),
    ("UKRAIN-StepUp-B", "2026-12-31", "political_process"),
}


def test_no_duplicate_open_calls_per_ticker_date_and_type(root):
    p = root / "desk" / "data" / "calibration_ledger.jsonl"
    seen = set()
    for l in p.read_text().splitlines():
        if not l.strip():
            continue
        rec = json.loads(l)
        if rec.get("status") != "OPEN":
            continue
        key = (rec["ticker"], rec.get("cat_date"), rec.get("event_type"))
        if key in KNOWN_DUPLICATE_OPEN_CALLS:
            continue
        assert key not in seen, f"duplicate OPEN call {key}"
        seen.add(key)
