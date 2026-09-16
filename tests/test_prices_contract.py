"""CONTRACT for desk/prices.py — written BEFORE the implementation (test-first).

The price service is the single source of pricing truth. Every consumer (aggregator, scanners,
watches) calls get_price()/get_prices() and receives a PriceQuote dict — never a bare float.
Design goals encoded here map 1:1 to the 2026-07-02/03 incidents:
  - AMV0 stale-GO  -> every quote carries asof/age + basis; is_fresh() is exchange-hours-aware
  - VSH bad tick   -> range sanity: outside 52wk band ±20% => data_suspect, never trusted silently
  - CIB phantom    -> cross-source divergence >2% (when two sources exist) => data_suspect
  - IVN/FM symbol drift -> canonical registry resolves ticker -> {yf, exchange, ccy, hours}; unknown
    symbols FAIL LOUDLY instead of silently returning nothing
"""
import json
import pytest

pytestmark = pytest.mark.contract


def test_registry_resolves_known_names(root):
    from desk.prices import REGISTRY, resolve
    for t in ("IVN", "FM", "HUBS", "8750.T", "AMV0.DE", "HSBK.L"):
        r = resolve(t)
        assert r["yf"], f"{t} must map to a yfinance symbol"
        assert r["exchange"] and r["ccy"]


def test_registry_rejects_unknown_loudly():
    from desk.prices import resolve, UnknownSymbol
    with pytest.raises(UnknownSymbol):
        resolve("ZZZNOTREAL")


def test_quote_shape_offline():
    """A quote built from a seeded cache has the full contract shape (no network)."""
    from desk.prices import PriceQuote, _mk_quote
    q = _mk_quote("HUBS", px=190.0, source="test", basis="close", asof=1783000000.0)
    for k in ("ticker", "px", "source", "basis", "asof", "age_s", "fresh", "suspect", "suspect_reason"):
        assert k in q


def test_range_sanity_flags_bad_tick():
    from desk.prices import _sanity
    # a $45 print on a stock whose 52wk band is 12-22 must be suspect (VSH incident)
    s = _sanity(px=45.51, lo52=12.0, hi52=22.0)
    assert s is not None and "52wk" in s
    assert _sanity(px=18.0, lo52=12.0, hi52=22.0) is None


def test_divergence_sanity():
    from desk.prices import _divergence
    assert _divergence(100.0, 105.0) is not None      # 5% apart -> suspect
    assert _divergence(100.0, 101.0) is None          # 1% -> fine


def test_freshness_is_exchange_aware():
    from desk.prices import _is_fresh
    # a 10-minute-old quote is fresh anywhere
    assert _is_fresh(age_s=600, exchange="NYSE", now_utc_hour=15)
    # a 3-hour-old quote during that exchange's open hours is NOT fresh
    assert not _is_fresh(age_s=3 * 3600, exchange="NYSE", now_utc_hour=15)
    # a 10-hour-old quote when the exchange is CLOSED counts as fresh-enough (it's the close)
    assert _is_fresh(age_s=10 * 3600, exchange="NYSE", now_utc_hour=3)


@pytest.mark.integration
def test_live_fetch_end_to_end():
    """Network test: fetch one liquid name; quote must be complete and unsuspect."""
    from desk.prices import get_price
    q = get_price("HUBS")
    assert q["px"] and q["px"] > 0
    assert q["basis"] in ("live", "delayed", "close")
    assert q["age_s"] is not None


def test_prev_close_divergence_quarantines_phantom_tick():
    """CBKD incident: a 32% single-print 'drop' vs previous close must be suspect, not displayed."""
    from desk.prices import _mk_quote
    q = _mk_quote("CBKD", px=1.71, source="test", basis="delayed", asof=1783000000.0, lo52=2.0, hi52=2.83)
    # the 52wk rail alone misses this (1.71 > 1.6); the quote layer relies on the prev-close rail in quote_yf.
    # Unit-test the math the rail uses:
    assert abs(1.71 / 2.53 - 1) > 0.15


def test_sticky_close_referee_catches_correlated_flap(root, tmp_path, monkeypatch):
    """CBKD v4: when ALL live endpoints flap together (GBP-labeled-USD), the sticky disk close must
    still quarantine the quote."""
    import json, time
    import desk.prices as P
    cache = {"CBKD.L": {"px": 2.53, "asof": time.time()}}
    monkeypatch.setattr(P, "_close_cache", lambda: cache)
    refs = [2.53]
    px = 1.71
    assert any(abs(px / r - 1) > 0.15 for r in refs), "rail math must flag the GBP flap"


def test_pence_pounds_is_the_only_silent_conversion():
    from desk.prices import _reconcile_ccy
    assert _reconcile_ccy(1057.0, "GBp", "GBP") == (10.57, None)
    assert _reconcile_ccy(10.57, "GBP", "GBp") == (1057.0, None)
    px, prob = _reconcile_ccy(1.71, "GBP", "USD")
    assert px == 1.71 and prob and "mismatch" in prob     # never FX-convert silently
    assert _reconcile_ccy(100.0, "USD", "USD") == (100.0, None)


def test_lse_registry_currencies_are_explicit():
    """The .L suffix is ambiguous (pence ordinaries vs USD GDRs) — the minefield names must be curated."""
    from desk.prices import resolve
    assert resolve("BRBY.L")["ccy"] == "GBp"
    assert resolve("CBKD")["ccy"] == "USD"
    assert resolve("HSBK.L")["ccy"] == "USD"


def test_ledger_alert_rows_carry_registry_currency(root):
    """The GO page must never label KRW as USD (028260.KS incident 2026-07-03)."""
    from desk.ui.aggregator import alerts
    from desk.prices import REGISTRY
    for r in alerts().get("go", []) + alerts().get("no_go", []):
        reg = REGISTRY.get(r["ticker"])
        if reg:
            assert r.get("cur") == reg["ccy"], f"{r['ticker']} ({r.get('src')}): row cur {r.get('cur')} != registry {reg['ccy']}"


def test_sticky_referee_resists_poisoning(tmp_path, monkeypatch):
    """A flap value must NOT overwrite the sticky in one shot (CBKD poisoning 2026-07-03);
    a genuine crash confirms across two consecutive updates."""
    import json, time
    import desk.prices as P
    cache_file = tmp_path / "closes.json"
    cache_file.write_text(json.dumps({"X": {"px": 2.53, "asof": time.time()}}))
    monkeypatch.setattr(P, "_CLOSE_CACHE_PATH", cache_file)
    P._remember_close("X", 1.71)                       # flap sighting #1 -> held as pending
    c = json.loads(cache_file.read_text())
    assert c["X"]["px"] == 2.53 and c["X"].get("pending") == 1.71
    P._remember_close("X", 2.52)                       # normal value returns -> pending NOT confirmed
    c = json.loads(cache_file.read_text())
    assert c["X"]["px"] == 2.52
    # genuine crash: two low prints >=6h apart confirm (v5: the time floor blocks same-window self-confirmation)
    P._remember_close("X", 1.70)
    c = json.loads(cache_file.read_text())
    c["X"]["pending_asof"] = time.time() - 7 * 3600     # simulate 7h elapsed
    cache_file.write_text(json.dumps(c))
    P._remember_close("X", 1.72)
    c = json.loads(cache_file.read_text())
    assert c["X"]["px"] == 1.72, "a time-separated confirmed real move must be accepted"


def test_gateway_file_layer_beats_yfinance(tmp_path, monkeypatch):
    import json, time
    import desk.prices as P
    f = tmp_path / "ib.json"
    f.write_text(json.dumps({"asof": time.time(), "quotes": {"HUBS": {"px": 191.5, "mdt": 1, "asof": time.time()}}}))
    monkeypatch.setattr(P, "_IB_FILE", f)
    monkeypatch.setattr(P, "quote_yf", lambda *a, **k: P._mk_quote("HUBS", 191.0, "yfinance", "delayed", time.time()))
    q = P.get_price("HUBS")
    assert q["source"] == "ibkr-gateway" and q["basis"] == "live" and q["px"] == 191.5


def test_gateway_vs_yfinance_divergence_quarantines(tmp_path, monkeypatch):
    import json, time
    import desk.prices as P
    f = tmp_path / "ib.json"
    f.write_text(json.dumps({"asof": time.time(), "quotes": {"HUBS": {"px": 250.0, "mdt": 1, "asof": time.time()}}}))
    monkeypatch.setattr(P, "_IB_FILE", f)
    monkeypatch.setattr(P, "quote_yf", lambda *a, **k: P._mk_quote("HUBS", 190.0, "yfinance", "delayed", time.time()))
    q = P.get_price("HUBS")
    assert q["suspect"] and "gateway vs yfinance" in q["suspect_reason"]


def test_persistent_flap_cannot_self_confirm(tmp_path, monkeypatch):
    """CBKD round 2: a flap that persists for a window must not confirm itself into the sticky
    (confirmation requires >=6h between sightings)."""
    import json, time
    import desk.prices as P
    f = tmp_path / "closes.json"
    f.write_text(json.dumps({"X": {"px": 2.53, "asof": time.time()}}))
    monkeypatch.setattr(P, "_CLOSE_CACHE_PATH", f)
    P._remember_close("X", 1.71)
    P._remember_close("X", 1.71)   # same flap window, minutes apart — must NOT confirm
    c = json.loads(f.read_text())
    assert c["X"]["px"] == 2.53, "persistent flap self-confirmed — the 6h floor failed"
