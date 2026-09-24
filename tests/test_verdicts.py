"""Structured verdict system — the fix for the free-text bug class (OWN/OWNABLE substring,
first-32-chars bucketing, PENDING_RED_TEAM smuggled into prose)."""
import json, pathlib
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]


@pytest.fixture
def isolated_verdicts(tmp_path, monkeypatch):
    import desk.verdicts as verdicts
    import desk.ledger_add as ledger_add
    ledger = tmp_path / 'research_ledger.json'
    ledger.write_text(json.dumps({'names': [dict(ticker=t, verdict='OWNABLE', state='OWNABLE', stage='ADJUDICATED', conviction='Synthetic test', thesis='Synthetic') for t in ('IBEX', 'FNF')]}))
    ec = tmp_path / 'classifications'
    ec.mkdir()
    monkeypatch.setattr(verdicts, 'LEDGER', ledger)
    monkeypatch.setattr(verdicts, 'EC', ec)
    monkeypatch.setattr(verdicts, 'AUDIT', tmp_path / 'audit.jsonl')
    monkeypatch.setattr(ledger_add, 'LEDGER', ledger)
    monkeypatch.setattr(ledger_add, '_regen', lambda: None)
    return ledger


def test_states_are_closed_enum():
    from desk.verdicts import set_verdict, InvalidVerdict
    with pytest.raises(InvalidVerdict):
        set_verdict("IBEX", "MAYBE_BUY")
    with pytest.raises(InvalidVerdict):
        set_verdict("IBEX", "OWNABLE", stage="VIBING")


def test_unknown_ticker_rejected(isolated_verdicts):
    from desk.verdicts import set_verdict, InvalidVerdict
    with pytest.raises(InvalidVerdict):
        set_verdict("ZZZNOTREAL", "WATCH")


def test_set_and_get_roundtrip_with_audit(isolated_verdicts):
    from desk.verdicts import set_verdict, get_verdict, AUDIT
    before = AUDIT.read_text().count("\n") if AUDIT.exists() else 0
    v0 = get_verdict("IBEX")
    r = set_verdict("IBEX", v0["state"] or "OWNABLE", stage="ADJUDICATED",
                    note=v0["note"], source="test-roundtrip")
    assert r["state"] in ("OWNABLE",) or r["state"] == v0["state"]
    after = AUDIT.read_text().count("\n")
    assert after == before + 1, "audit log must append exactly one entry"
    last = json.loads(AUDIT.read_text().splitlines()[-1])
    assert last["source"] == "test-roundtrip" and last["ticker"] == "IBEX"


@pytest.mark.corpus
def test_every_ledger_name_has_valid_state():
    from desk.verdicts import STATES
    led = json.loads((ROOT / "desk" / "data" / "research_ledger.json").read_text())["names"]
    bad = [n["ticker"] for n in led if n.get("verdict") not in STATES]
    assert not bad, f"ledger names with non-enum verdicts: {bad}"


@pytest.mark.corpus
def test_every_record_has_verdict_state():
    from desk.verdicts import STATES
    ec = ROOT / "desk" / "data" / "edge_classifications"
    bad = [f.stem for f in ec.glob("*.json")
           if json.loads(f.read_text()).get("verdict_state") not in STATES]
    assert not bad, f"records without structured verdict_state: {bad}"


def test_ownable_never_parses_as_own():
    """The IBEX bug, unit-tested at the parser."""
    from desk.verdicts import parse_legacy
    state, _ = parse_legacy("OWNABLE — blue-team corrected: 0.5% starter")
    assert state == "OWNABLE"
    state2, stage2 = parse_legacy("PENDING_RED_TEAM — DD verdict: BUY-starter 7/10")
    assert stage2 == "RED_TEAM_PENDING"


def test_routing_groups_are_the_single_source():
    from desk.verdicts import BUYISH, HELDISH, DEADISH, STATES
    assert set(HELDISH) < set(BUYISH)
    assert not set(DEADISH) & set(BUYISH)
    assert set(BUYISH) | set(DEADISH) < set(STATES) | set(BUYISH)


def test_api_endpoints_exist():
    import desk.ui.server as srv
    routes = {r.path for r in srv.app.routes}
    assert "/api/verdicts" in routes and "/api/verdict/{sym}" in routes


def test_upsert_syncs_structured_state(isolated_verdicts):
    """FNF stale-state bug: upsert updated 'verdict' but left 'state' stale — the validator read WATCH
    while the verdict said OWNABLE."""
    import json, pathlib
    from desk.ledger_add import upsert
    from desk.verdicts import get_verdict
    led = json.loads(isolated_verdicts.read_text())
    probe = next(n for n in led["names"] if n["ticker"] == "FNF")
    orig = probe.get("verdict")
    upsert({"ticker": "FNF", "verdict": "WATCH", "conviction": probe.get("conviction"), "thesis": probe.get("thesis")})
    assert get_verdict("FNF")["state"] == "WATCH"
    upsert({"ticker": "FNF", "verdict": orig, "conviction": probe.get("conviction"), "thesis": probe.get("thesis")})
    assert get_verdict("FNF")["state"] == orig
