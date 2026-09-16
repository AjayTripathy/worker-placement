"""Pre-order card rules engine + TCA scoring math (offline)."""
import json


def test_tca_scoring_math():
    from desk.execution_tca import score_fill
    f = score_fill({"symbol": "X", "side": "BUY", "qty": 100, "price": 101.0, "date": "2026-07-01",
                    "benchmarks": {"open": 100.0, "vwap": 100.5, "close": 102.0}})
    assert f["slip_vs_open_bps"] == 100.0          # paid 1% over open (bad)
    assert f["slip_vs_vwap_bps"] == 49.8           # ~50bps over vwap
    assert f["slip_vs_close_bps"] == -98.0         # beat the close (good)
    s = score_fill({"symbol": "X", "side": "SELL", "qty": 100, "price": 101.0, "date": "2026-07-01",
                    "benchmarks": {"vwap": 100.5}})
    assert s["slip_vs_vwap_bps"] == -49.8          # sold ABOVE vwap = good for a sell


def test_card_recommends_midprice_for_thin_float(monkeypatch):
    import desk.preorder_card as PC
    import desk.prices as P
    monkeypatch.setattr(P, "resolve", lambda t: {"yf": "IBEX", "ccy": "USD", "exchange": "US"})
    monkeypatch.setattr(P, "get_price", lambda t: {"px": 32.0, "basis": "delayed", "fresh": True, "suspect": False})
    class FakeT:
        info = {"averageVolume": 200_000, "floatShares": 10_700_000, "bid": 31.95, "ask": 32.05}
    import yfinance
    monkeypatch.setattr(yfinance, "Ticker", lambda s: FakeT())
    card = PC.build_card("IBEX", 5000, cap=32.5)
    assert "MIDPRICE" in card["recommendation"]["order_type"]
    assert "32.5" in card["recommendation"]["params"]


def test_card_refuses_suspect_quotes(monkeypatch):
    import desk.preorder_card as PC
    import desk.prices as P
    monkeypatch.setattr(P, "resolve", lambda t: {"yf": "CBKD.L", "ccy": "USD", "exchange": "LSE"})
    monkeypatch.setattr(P, "get_price", lambda t: {"px": 1.71, "basis": "delayed", "fresh": True, "suspect": True})
    card = PC.build_card("CBKD", 5000)
    assert card["recommendation"]["order_type"] == "DO_NOT_STAGE"


def test_card_warns_on_stale_basis(monkeypatch):
    import desk.preorder_card as PC
    import desk.prices as P
    monkeypatch.setattr(P, "resolve", lambda t: {"yf": "HUBS", "ccy": "USD", "exchange": "US"})
    monkeypatch.setattr(P, "get_price", lambda t: {"px": 190.0, "basis": "close", "fresh": True, "suspect": False})
    class FakeT:
        info = {"averageVolume": 2_000_000, "floatShares": 50_000_000, "bid": None, "ask": None}
    import yfinance
    monkeypatch.setattr(yfinance, "Ticker", lambda s: FakeT())
    card = PC.build_card("HUBS", 5000)
    assert any("LIVE SCREEN" in w for w in card["why"])
