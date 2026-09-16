"""Regression guard for the 'THE REPORT IS OUT' detector.

The bug this locks down: gauntlet_sentinel used to full-text-search EDGAR for the ticker STRING
(`q="NOW"`), so a common-word ticker matched UNRELATED companies' 8-Ks that merely contained the
word 'now' and false-fired an earnings alert (the NOW email, 2026-07-22). The fix resolves the
FILER by CIK and requires the company's own 8-K carrying Item 2.02 (Results of Operations), plus a
session (AMC/BMO) timing gate. These tests assert the detector keys on the referent, not the token.
"""
import datetime
import io
import json

import desk.gauntlet_sentinel as gs


class _FakeResp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()
        return False


def _install(monkeypatch, payload):
    def fake_urlopen(req, timeout=None):
        return _FakeResp(json.dumps(payload).encode())
    monkeypatch.setattr(gs.urllib.request, "urlopen", fake_urlopen)


def _submissions(rows):
    """rows: list of (form, filingDate, items, accession) -> EDGAR submissions 'recent' shape."""
    return {"filings": {"recent": {
        "form": [r[0] for r in rows],
        "filingDate": [r[1] for r in rows],
        "items": [r[2] for r in rows],
        "accessionNumber": [r[3] for r in rows],
    }}}


def test_cik_resolves_the_entity_not_the_token():
    assert gs._cik("NOW") == "0001373715"      # ServiceNow, the filer we mean
    assert gs._cik("now") == "0001373715"      # case-insensitive
    assert gs._cik("ZZZZQ") is None            # unresolved -> caller must not guess


def test_common_word_ticker_does_not_false_fire(monkeypatch):
    """The core regression: a same-day 8-K from the filer that is NOT an earnings release
    (e.g. Item 5.02 officer change) must NOT report 'the report is out'."""
    today = datetime.date.today().isoformat()
    _install(monkeypatch, _submissions([
        ("8-K", today, "5.02", "0000000000-26-000001"),   # officer change, not earnings
        ("4",   today, "",     "0000000000-26-000002"),   # insider form 4
    ]))
    assert gs._efts_hits("NOW") == []


def test_earnings_8k_today_fires(monkeypatch):
    today = datetime.date.today().isoformat()
    _install(monkeypatch, _submissions([
        ("8-K", today, "2.02,9.01", "0001373715-26-000099"),   # Results of Operations = the tell
        ("8-K", today, "5.02",      "0001373715-26-000098"),
    ]))
    assert gs._efts_hits("NOW") == ["0001373715-26-000099"]


def test_stale_earnings_8k_does_not_fire(monkeypatch):
    """A 2.02 8-K from a PRIOR day must not re-fire today."""
    yesterday = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
    _install(monkeypatch, _submissions([
        ("8-K", yesterday, "2.02,9.01", "0001373715-26-000097"),
    ]))
    assert gs._efts_hits("NOW") == []


def test_unresolved_ticker_never_hits_network(monkeypatch):
    def boom(*a, **k):
        raise AssertionError("must not call the network for an unresolved ticker")
    monkeypatch.setattr(gs.urllib.request, "urlopen", boom)
    assert gs._efts_hits("ZZZZQ") == []


def test_session_inference_from_prose():
    assert gs._session({"catalyst": "ServiceNow Q2 — CONFIRMED Jul-22 after close"}) == "amc"
    assert gs._session({"adjudication": "prints before the open on Friday"}) == "bmo"
    assert gs._session({"session": "amc"}) == "amc"            # explicit wins
    assert gs._session({"adjudication": "a political vote, no company print"}) is None


def test_open_earnings_calls_on_amc_prints_carry_session(root):
    """The backfill must leave no OPEN AMC/BMO earnings call ungated: every open earnings call
    whose sibling on the same (ticker,cat_date) has a session must itself carry one."""
    p = root / "desk" / "data" / "calibration_ledger.jsonl"
    rows = [json.loads(l) for l in p.read_text().splitlines() if l.strip()]
    known = {(r["ticker"], r.get("cat_date")) for r in rows if r.get("session")}
    orphans = [
        (r["ticker"], r.get("event_type"))
        for r in rows
        if r.get("status", "OPEN") == "OPEN"
        and str(r.get("event_type", "")).startswith("earnings")
        and not r.get("session")
        and (r["ticker"], r.get("cat_date")) in known
    ]
    assert orphans == [], f"open earnings calls missing session on a known print: {orphans}"
