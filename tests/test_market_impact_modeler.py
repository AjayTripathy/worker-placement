"""
Unit tests for the SignalOS Market Impact & Execution Modeler (desk/market_impact_modeler.py).
"""

import pytest
import math
from desk.market_impact_modeler import (
    compute_market_impact,
    compute_capacity_thresholds,
    analyze_5697_t_capacity,
    GAMMA_PERM,
    ETA_TEMP
)


def test_compute_market_impact_basic():
    """Test basic Almgren-Chriss impact calculations."""
    res = compute_market_impact(
        target_shares=1000,
        spot_price=823.0,
        adv_shares=9110.0,
        daily_volatility=0.0191,
        participation_rate=0.10,
        half_spread_bps=12.5,
        fx_rate_to_usd=155.0
    )
    assert res["target_shares"] == 1000
    assert res["notional_local"] == 823000.0
    assert res["notional_usd"] == pytest.approx(5309.68, rel=1e-2)
    assert res["days_to_execute"] >= 1
    assert res["permanent_impact_bps"] > 0
    assert res["temporary_impact_bps"] > 0
    assert len(res["impact_regime"]) > 0
    assert "MODERATE" in res["impact_regime"] or "LOW" in res["impact_regime"]


def test_square_root_scaling():
    """Verify the square-root law of market impact: I(4Q) = 2 * I(Q)."""
    base_res = compute_market_impact(
        target_shares=1000,
        spot_price=100.0,
        adv_shares=10000.0,
        daily_volatility=0.02,
        participation_rate=0.10
    )
    quad_res = compute_market_impact(
        target_shares=4000,
        spot_price=100.0,
        adv_shares=10000.0,
        daily_volatility=0.02,
        participation_rate=0.10
    )
    # Permanent impact scales with sqrt(Q/V_total)
    assert quad_res["permanent_impact_bps"] == pytest.approx(base_res["permanent_impact_bps"], rel=1e-1)


def test_capacity_thresholds():
    """Verify institutional capacity threshold tiers."""
    thresholds = compute_capacity_thresholds(
        spot_price=823.0,
        adv_shares=9110.0,
        daily_volatility=0.0191,
        max_days=5,
        shares_outstanding=6_040_000
    )
    assert len(thresholds) == 5
    # Verify share counts increase across tiers
    shares = [t["max_shares"] for t in thresholds]
    assert shares == sorted(shares)
    assert thresholds[-1]["max_shares"] == 302000  # 5% of 6.04M shares
    assert "FIEA" in thresholds[-1]["tier_name"] or "5.0%" in thresholds[-1]["tier_name"]


def test_5697_t_audit():
    """Test 5697.T specific audit function."""
    audit = analyze_5697_t_capacity()
    assert audit["ticker"] == "5697.T"
    assert audit["spot_price_jpy"] == 823.0
    assert audit["adv_20d_shares"] == 9110.0
    assert len(audit["order_sizing_simulations"]) == 5
    assert "micro_slicing_schedule_1800shs" in audit

    # Check our starter size (1,800 shares)
    starter_sim = audit["order_sizing_simulations"][0]
    assert starter_sim["target_shares"] == 1800
    assert starter_sim["notional_usd"] < 10000.0
    assert starter_sim["total_slippage_bps"] < 60.0  # Very low impact


def test_micro_slicing_schedule():
    """Test micro-slicing schedule generation."""
    from desk.market_impact_modeler import generate_micro_slicing_schedule
    sched = generate_micro_slicing_schedule(
        target_shares=1800,
        spot_price=823.0,
        adv_shares=9110.0,
        lot_size=100
    )
    assert sched["target_shares"] == 1800
    assert sched["lot_size"] == 100
    assert sched["total_lots"] == 18
    assert "accumulate_distribute" in sched["algorithms"]
    assert "percentage_of_volume" in sched["algorithms"]
    assert "passive_liquidity_ladder" in sched["algorithms"]
    assert sched["algorithms"]["passive_liquidity_ladder"]["total_rungs"] == 5

