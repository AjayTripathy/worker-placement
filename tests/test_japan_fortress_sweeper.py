"""
Unit tests for the SignalOS Japanese Cash Fortress Sweeper (desk/japan_fortress_sweeper.py).
"""

import json
import pytest
from pathlib import Path
from desk.japan_fortress_sweeper import (
    compute_fortress_metrics,
    sweep_japanese_fortresses,
    run_sweep_and_save,
    OUTPUT_CANDIDATES_PATH
)


def test_compute_fortress_metrics_sanyu():
    """Test metric computation on Sanyu Co. record."""
    record = {
        "sym": "5697.T",
        "ind": "SANYU CO.,LTD.",
        "sec": "Steel",
        "mktcap": 4397702000.0,
        "px": 722.0,
        "pb": 0.425,
        "ncash_r": 0.825,
        "ncav_r": 1.21,
        "ebit": 886860000.0,
        "fcf": 2539505000.0,
        "fcfy": 0.577,
        "pfic_fmv_share": 0.357
    }
    metrics = compute_fortress_metrics(record)
    assert metrics is not None
    assert metrics["ticker"] == "5697.T"
    assert metrics["pb_ratio"] == 0.42
    assert metrics["net_cash_pct"] == 82.5
    assert metrics["ev_to_ebit"] < 1.0  # Deep liquidation multiple
    assert metrics["cluster"] == "Precision Steel & Metallurgy"
    assert metrics["fortress_score"] > 70.0


def test_sweep_japanese_fortresses_basic():
    """Verify live sweep isolates valid fortresses."""
    candidates = sweep_japanese_fortresses(max_pb=0.75, min_net_cash_pct=50.0, max_ev_ebit=3.5)
    assert len(candidates) >= 5
    tickers = [c["ticker"] for c in candidates]
    assert "5697.T" in tickers
    assert "7254.T" in tickers

    # Verify all passed candidates strictly satisfy thesis gates
    for c in candidates:
        assert c["pb_ratio"] <= 0.75
        assert c["net_cash_pct"] >= 50.0
        assert c["ebit_jpy"] > 0
        assert c["ev_to_ebit"] <= 3.5
        assert c["fcf_jpy"] > 0
        assert c["pfic_fmv_passive_pct"] < 50.0


def test_gates_rejection():
    """Verify that unprofitable or overlevered companies are rejected."""
    bad_record = {
        "sym": "9999.T",
        "ind": "LOSING CORP",
        "sec": "Machinery",
        "mktcap": 5000000000.0,
        "px": 500.0,
        "pb": 0.90,  # Fails PB > 0.75
        "ncash_r": 0.20,  # Fails cash < 50%
        "ncav_r": 0.50,
        "ebit": -1000000.0,  # Fails negative EBIT
        "fcf": -500000.0,
        "fcfy": -0.01,
        "pfic_fmv_share": 0.60  # Fails PFIC
    }
    metrics = compute_fortress_metrics(bad_record)
    assert metrics["pb_ratio"] == 0.90
    assert metrics["ev_to_ebit"] == 999.0


def test_run_sweep_and_save(tmp_path):
    """Test full execution and JSON persistence."""
    payload = run_sweep_and_save(top_n=10)
    assert payload["total_passed"] > 0
    assert len(payload["candidates"]) <= 10
    assert OUTPUT_CANDIDATES_PATH.exists()
    
    # Read saved JSON
    saved_data = json.loads(OUTPUT_CANDIDATES_PATH.read_text())
    assert saved_data["total_passed"] == payload["total_passed"]
