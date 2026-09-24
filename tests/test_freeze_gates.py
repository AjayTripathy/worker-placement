"""Tests for the 2026-07-27 anchor-and-adjust freeze gates (reaction driver, implied-anchor
deviation rule, Mode-B disconfirm on narrative conviction, base-effect guard).
LEDGER is monkeypatched to tmp; implied_binary network calls are stubbed."""
import json
from datetime import date, timedelta
import pytest

import desk.freeze_call as fc
import desk.implied_binary as ib


GOOD_FRAME = {"we_believe": "x" * 20, "market_believes": "y" * 20,
              "our_edge": "z" * 20, "why_priced_in": "w" * 20}
GOOD_PLAIN = {"what": "test call", "how": "test method", "conclusion": "test conclusion"}
MECH = "our lab scheduler-exhaust nowcast reads demand ahead of the options market's implied move"
DISC = "checked the primary H1 release comp base and the venue's own resolution criteria first"


@pytest.fixture
def ledger(tmp_path, monkeypatch):
    p = tmp_path / "ledger.jsonl"
    p.write_text("")
    monkeypatch.setattr(fc, "LEDGER", p)
    return p


@pytest.fixture
def no_network(monkeypatch):
    monkeypatch.setattr(ib, "implied_up_prob", lambda *a, **k: {"p": 0.45, "anchor": 100.0,
                        "expiry": "2026-08-21", "method": "stub", "source": "options_implied:stub"})
    monkeypatch.setattr(ib, "reaction_context", lambda *a, **k: {"stub": True})


def _freeze(**over):
    kw = dict(ticker="TEST", cat_date=(date.today() + timedelta(days=30)).isoformat(), our_p=0.55, direction="UP",
              catalyst="test catalyst", reasoning="r" * 50, plain=dict(GOOD_PLAIN),
              event_type="earnings_print", frame=dict(GOOD_FRAME))
    kw.update(over)
    return fc.freeze(**kw)


def test_reaction_requires_driver(ledger, no_network):
    with pytest.raises(AssertionError, match="reaction_driver"):
        _freeze(ticker="TEST-STK", event_type="stock_reaction")


def test_reaction_anchor_deviation_needs_mechanism(ledger, no_network):
    # stub anchor 0.45; our_p 0.70 deviates > 0.05 -> must fail without mechanism
    with pytest.raises(AssertionError, match="anchor-and-adjust"):
        _freeze(ticker="TEST-STK", event_type="stock_reaction", our_p=0.70,
                reaction_driver="the FY guide, not the quarter itself")


def test_reaction_within_tolerance_freezes_and_stamps(ledger, no_network):
    rec = _freeze(ticker="TEST-STK", event_type="stock_reaction", our_p=0.47,
                  reaction_driver="the FY guide, not the quarter itself")
    assert rec["market_p"] == 0.45 and "options_implied" in rec["market_p_source"]
    assert rec["reaction_driver"] and rec["reaction_context"] == {"stub": True}
    assert json.loads(ledger.read_text().strip().splitlines()[-1])["ticker"] == "TEST-STK"


def test_reaction_deviation_with_mechanism_ok(ledger, no_network):
    rec = _freeze(ticker="TEST-STK", event_type="stock_reaction", our_p=0.70,
                  reaction_driver="the FY guide, not the quarter itself", mechanism=MECH)
    assert rec["mechanism"] == MECH


def test_narrative_conviction_requires_disconfirm(ledger, no_network):
    with pytest.raises(AssertionError, match="disconfirm"):
        _freeze(event_type="peer_read", our_p=0.65, catalyst="peer read no numbers")


def test_narrative_coin_zone_needs_no_disconfirm(ledger, no_network):
    rec = _freeze(event_type="peer_read", our_p=0.55, catalyst="peer read no numbers")
    assert rec["status"] == "OPEN"


def test_base_effect_requires_comp_and_flags(ledger, no_network):
    # %-continuation claim without base_comp -> refused
    with pytest.raises(AssertionError, match="base_comp"):
        _freeze(event_type="peer_read", our_p=0.65, disconfirm=DISC,
                catalyst="order intake still growing 20%+ yoy")
    # extreme base + conviction, no mechanism -> refused
    with pytest.raises(AssertionError, match="BASE-EFFECT"):
        _freeze(event_type="peer_read", our_p=0.65, disconfirm=DISC,
                catalyst="order intake still growing 20%+ yoy",
                base_comp={"prior_growth_pct": 38, "claimed_growth_pct": 20})
    # same call haircut to the coin zone -> freezes
    rec = _freeze(event_type="peer_read", our_p=0.45, catalyst="order intake still growing 20%+ yoy",
                  base_comp={"prior_growth_pct": 38, "claimed_growth_pct": 20})
    assert rec["base_comp"]["prior_growth_pct"] == 38


def test_ops_class_unaffected(ledger, no_network):
    rec = _freeze(event_type="earnings_print", our_p=0.80)
    assert rec["status"] == "OPEN" and "reaction_driver" not in rec
