"""Robinhood adapter — detect states + a read-only positions fetch via an
injected fake robin_stocks (no live account, no credentials handled by us).
Plus the new detect-only trailheads stay registered."""
import sys
import types

import officekit_adapters as A


def _clear_rh_env(mp):
    for v in ("ROBINHOOD_USERNAME", "ROBINHOOD_USER", "ROBINHOOD_PASSWORD",
              "ROBINHOOD_PASS", "ROBINHOOD_TOTP", "ROBINHOOD_MFA"):
        mp.delenv(v, raising=False)


def test_new_integrations_registered():
    for name in ("robinhood", "etrade", "webull", "public", "binance", "gemini"):
        assert name in A.ADAPTERS, name
    # robinhood is FIRST-CLASS (has a fetcher), the others are trailheads
    assert A.ADAPTERS["robinhood"]["factory"]().get("fetch") is not None
    assert A.ADAPTERS["webull"]["factory"]().get("fetch") is None


def test_robinhood_detect_absent_without_lib_or_creds(monkeypatch):
    _clear_rh_env(monkeypatch)
    monkeypatch.setattr("importlib.util.find_spec", lambda n: None)
    r = A.ADAPTERS["robinhood"]["factory"]()["detect"]({})
    assert r["found"] is False and r["status"] == "absent"


def test_robinhood_detect_needs_key_when_lib_but_no_creds(monkeypatch):
    _clear_rh_env(monkeypatch)
    monkeypatch.setattr("importlib.util.find_spec", lambda n: object())
    r = A.ADAPTERS["robinhood"]["factory"]()["detect"]({})
    assert r["found"] is True and r["status"] == "needs_key"


def test_robinhood_detect_ready_with_lib_and_creds(monkeypatch):
    monkeypatch.setenv("ROBINHOOD_USERNAME", "u")
    monkeypatch.setenv("ROBINHOOD_PASSWORD", "p")
    monkeypatch.setattr("importlib.util.find_spec", lambda n: object())
    r = A.ADAPTERS["robinhood"]["factory"]()["detect"]({})
    assert r["found"] is True and r["status"] == "ready"


def test_robinhood_fetch_maps_equities_and_crypto(monkeypatch):
    monkeypatch.setenv("ROBINHOOD_USERNAME", "u")
    monkeypatch.setenv("ROBINHOOD_PASSWORD", "p")
    monkeypatch.delenv("ROBINHOOD_TOTP", raising=False)
    monkeypatch.delenv("ROBINHOOD_MFA", raising=False)

    # inject a fake robin_stocks.robinhood
    login_calls = {}
    rh = types.SimpleNamespace(
        login=lambda u, p, **kw: login_calls.update({"u": u, "kw": kw}),
        build_holdings=lambda: {"AAPL": {"quantity": "10", "equity": "2000.00", "name": "Apple"},
                                "MSFT": {"quantity": "5", "equity": "1500.00", "name": "Microsoft"}},
        get_crypto_positions=lambda: [{"quantity": "0.5", "currency": {"code": "BTC"}}],
        get_crypto_quote=lambda code: {"mark_price": "60000.00"},
        logout=lambda: None)
    pkg = types.ModuleType("robin_stocks")
    pkg.robinhood = rh
    monkeypatch.setitem(sys.modules, "robin_stocks", pkg)
    monkeypatch.setitem(sys.modules, "robin_stocks.robinhood", rh)

    rows = A.fetch_positions("robinhood")
    by = {r["symbol"]: r for r in rows}
    assert by["AAPL"]["value"] == 2000.0 and by["AAPL"]["sec_type"] == "STK"
    assert by["BTC"]["sec_type"] == "CRYPTO" and by["BTC"]["value"] == 30000.0   # 0.5 * 60000
    assert login_calls["u"] == "u"                                               # logged in read-only


def test_connectors_are_default_dependencies():
    """The connector libs ship by default: named in the product pyproject's CORE
    dependencies block AND mirrored in CONNECTOR_PACKAGES (what `wp doctor` uses).
    Text scan keeps this py3.9-safe (no tomllib) and catches an extras-only regression."""
    from pathlib import Path
    txt = (Path(__file__).resolve().parents[1] / "officekit_dist" / "pyproject.toml").read_text()
    core = txt.split("dependencies = [", 1)[1].split("]", 1)[0]   # the core block only
    for imp in A.CONNECTOR_PACKAGES:
        name = A.CONNECTOR_PACKAGES[imp].split(">")[0].split("=")[0].strip()
        assert name in core, f"{name} is not a core (default) dependency of worker-placement"
    assert {"robin_stocks", "pyotp", "ib_insync"} <= set(A.CONNECTOR_PACKAGES)


def test_missing_connectors_shape():
    m = A.missing_connectors()
    assert isinstance(m, dict)
    for imp, spec in m.items():
        assert imp in A.CONNECTOR_PACKAGES and spec == A.CONNECTOR_PACKAGES[imp]
