"""
Unit tests for the Japanese Cash Fortress Stager Engine (desk/japan_stager.py).
"""

import json
import pytest
from pathlib import Path
from desk.japan_stager import (
    build_staged_order_plan,
    log_attributed_order,
    ATTRIBUTED_ORDERS_FILE,
    STAGING_COHORT
)


def test_board_lot_compliance():
    """Verify that every single planned order strictly complies with TSE 100-share board lot rules."""
    orders = build_staged_order_plan()
    assert len(orders) > 0
    for o in orders:
        assert o["quantity"] % 100 == 0, f"Order for {o['ticker']} quantity {o['quantity']} is not a 100-share multiple"
        assert o["quantity"] >= 100
        assert o["limit_price_jpy"] > 0
        assert o["tif"] == "GTC"
        assert o["outside_rth"] is False


def test_tranche_structure_and_discounts():
    """Verify that Tranche 1 is at reference price and Tranche 2 rungs have genuine discounts."""
    orders = build_staged_order_plan()
    by_ticker = {}
    for o in orders:
        by_ticker.setdefault(o["ticker"], []).append(o)

    for ticker, t_orders in by_ticker.items():
        t1 = [o for o in t_orders if "Tranche 1" in o["tranche"]]
        t2 = [o for o in t_orders if "Tranche 2" in o["tranche"]]
        assert len(t1) == 1, f"Missing Tranche 1 for {ticker}"
        assert len(t2) >= 1, f"Missing Tranche 2 for {ticker}"

        t1_price = t1[0]["limit_price_jpy"]
        for r in t2:
            assert r["limit_price_jpy"] < t1_price, f"{ticker} Tranche 2 price {r['limit_price_jpy']} must be discounted vs Tranche 1 {t1_price}"


def test_sleeve_budget_constraints():
    """Verify that total planned sleeve does not exceed portfolio risk budget ($50k max)."""
    orders = build_staged_order_plan()
    total_usd = sum(o["approx_value_usd"] for o in orders)
    assert 30000.0 <= total_usd <= 50000.0, f"Total sleeve USD {total_usd} out of bounds"


def test_invalid_lot_raises_error():
    """Verify that odd-lot quantities trigger a validation error."""
    bad_cohort = [
        {
            "ticker": "9999.T",
            "symbol": "9999",
            "company_name": "Bad Lot Co.",
            "target_usd": 1000.0,
            "ref_price_jpy": 500.0,
            "tranche1_qty": 150,  # Invalid: not a multiple of 100
            "tranche1_price_jpy": 500.0,
            "tranche2_rungs": [],
            "algorithm": "None"
        }
    ]
    with pytest.raises(ValueError, match="multiple of 100 shares"):
        build_staged_order_plan(bad_cohort)


def test_log_attributed_order(tmp_path, monkeypatch):
    """Test persistence to attributed orders ledger."""
    dummy_file = tmp_path / "test_orders.json"
    monkeypatch.setattr("desk.japan_stager.ATTRIBUTED_ORDERS_FILE", dummy_file)

    sample_order = {
        "timestamp_utc": "2026-08-20T23:55:00Z",
        "order_id": 99991,
        "ticker": "5697.T",
        "symbol": "5697",
        "company_name": "Sanyu Co., Ltd.",
        "tranche": "Tranche 1",
        "action": "BUY",
        "quantity": 700,
        "limit_price_jpy": 823.0,
        "currency": "JPY",
        "tif": "GTC",
        "order_status": "PreSubmitted"
    }

    log_attributed_order(sample_order)
    assert dummy_file.exists()
    loaded = json.loads(dummy_file.read_text())
    assert len(loaded) == 1
    assert loaded[0]["order_id"] == 99991
