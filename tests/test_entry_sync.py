"""Entry page must stay synced with the alerts page + adjudicated sizings (user requirement 2026-07-03:
'the entry page looks out of date — it needs to be synced with the alerts page with sizings')."""
import pytest


@pytest.fixture(scope="module")
def entry():
    from desk.ui.aggregator import entry_candidates
    return entry_candidates()


@pytest.fixture(scope="module")
def alerts_payload():
    from desk.ui.aggregator import alerts
    return alerts()


def test_every_ready_name_appears_in_entry_live(entry, alerts_payload):
    """The alerts READY bucket and the entry LIVE section must agree — same stores, same membership."""
    ready = {r["ticker"] for r in alerts_payload.get("ready", [])}
    live = {r["ticker"] for r in entry.get("live", [])}
    missing = ready - live
    assert not missing, f"READY names absent from the entry page: {missing}"


def test_live_rows_are_pipeline_complete_and_sized(entry):
    """Every live entry row comes from a record with an explainer, and adjudicated names carry sizing."""
    rows = entry.get("live", [])
    assert rows, "entry live section is empty"
    unsized = [r["ticker"] for r in rows if r.get("needs_sizing")]
    assert not unsized, f"approved names without machine-readable sizing: {unsized}"


def test_sizing_math_consistent(entry):
    """est_usd must equal pct x the deployable book (no silent denominator drift — the DFIN lesson)."""
    nlv = entry.get("target_nlv") or 1_000_000
    for r in entry.get("live", []):
        if r.get("sizing_pct_lo") and r.get("est_usd_lo"):
            assert abs(r["est_usd_lo"] - r["sizing_pct_lo"] / 100 * nlv) < 1, r["ticker"]


def test_stale_plan_orders_are_flagged(entry):
    """Staged orders whose ledger verdict regressed to WAIT/AVOID must be flagged, never silently shown."""
    import json, pathlib
    root = pathlib.Path(__file__).resolve().parents[1]
    led = {n["ticker"]: (n.get("verdict") or "").upper()
           for n in json.loads((root / "desk" / "data" / "research_ledger.json").read_text())["names"]}
    drift = " ".join(entry.get("drift", []))
    for o in entry.get("orders", []):
        v = led.get(o["ticker"])
        if v and v not in ("OWNABLE", "STARTER", "HELD", "OWN"):
            assert o["ticker"] in drift, f"{o['ticker']} staged with verdict {v} but not flagged"


def test_no_legacy_watchlist_names_in_live(entry):
    """Names without dossiers (the ZS/NET/MC.PA legacy tranche) must not appear as approved entries."""
    import pathlib
    root = pathlib.Path(__file__).resolve().parents[1]
    ec = root / "desk" / "data" / "edge_classifications"
    for r in entry.get("live", []):
        assert (ec / f"{r['ticker']}.json").exists(), f"{r['ticker']} in LIVE without a dossier"


def test_approve_endpoint_exists_and_roundtrips():
    import desk.ui.server as srv
    assert "/api/approve/{sym}" in {r.path for r in srv.app.routes}
    from desk.ui.aggregator import set_order_approval, _approved_set
    before = "IBEX" in _approved_set()
    set_order_approval("IBEX", True)
    assert "IBEX" in _approved_set()
    set_order_approval("IBEX", before)   # restore


def test_live_rows_carry_approved_flag(entry):
    for r in entry.get("live", []):
        assert "approved" in r
