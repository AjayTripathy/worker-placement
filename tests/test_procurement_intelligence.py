"""
Unit and integration tests for the SignalOS Procurement Intelligence Stack.
"""

import datetime
import pytest
from verticals.public_co.m_sources.contract_mod_poller import (
    fetch_award_transactions,
    poll_contract_modifications
)
from verticals.public_co.m_sources.sam_opportunities import (
    query_sam_opportunities,
    parse_sole_source_justification
)
from verticals.public_co.m_sources.phemce_appropriations import (
    audit_phemce_stockpile_health,
    parse_congressional_budget_text,
    STATUTORY_SNS_SMALLPOX_TARGET_COURSES
)
from verticals.public_co.m_sources.fda_slep_telemetry import (
    model_stockpile_aging,
    BASELINE_SHELF_LIFE_YEARS
)
from desk.procurement_watch import run_procurement_sweep


def test_contract_mod_poller_live():
    """Test live USAspending query for SIGA master BARDA contract."""
    res = fetch_award_transactions("75A50118C00019", limit=5)
    assert res["award_id"] == "75A50118C00019"
    assert "transactions" in res
    assert isinstance(res["transactions"], list)
    assert len(res["transactions"]) > 0

    # Test modification delta detection
    poller_res = poll_contract_modifications("75A50118C00019", known_mod_numbers=["NON_EXISTENT_MOD"])
    assert poller_res["status"] == "OK"
    assert poller_res["cumulative_obligations"] > 0.0
    assert poller_res["has_new_mods"] is True


def test_sam_opportunities_parsing():
    """Test SAM.gov J&A sole-source parsing."""
    sample_notice = {
        "title": "Intent to Sole Source Smallpox Antiviral Procurement",
        "description": "BARDA intends to award a sole-source follow-on under FAR 6.302-1 Only One Responsible Source to SIGA Technologies.",
        "solicitationNumber": "75A50124R00001",
        "postedDate": "2026-08-01",
        "type": "Justification and Approval (J&A)",
        "department": "Department of Health and Human Services",
        "subTier": "Office of the Assistant Secretary for Preparedness and Response"
    }
    parsed = parse_sole_source_justification(sample_notice)
    assert parsed["is_sole_source"] is True
    assert "FAR 6.302-1" in parsed["far_authority"]
    assert parsed["solicitation_number"] == "75A50124R00001"


def test_phemce_appropriations_audit():
    """Test PHEMCE statutory stockpile health model."""
    audit = audit_phemce_stockpile_health(fiscal_year="FY2026", contractor_ticker="SIGA")
    assert audit["contractor_ticker"] == "SIGA"
    assert audit["statutory_sns_target_courses"] == STATUTORY_SNS_SMALLPOX_TARGET_COURSES
    assert audit["course_deficit"] >= 0
    assert audit["coverage_ratio"] > 0.0
    assert "HEALTHY" in audit["status"] or "TIGHT" in audit["status"]

    # Test text parsing
    sample_text = "The Committee provides $850.0 million for the Project BioShield Special Reserve Fund and $140.0 million for smallpox countermeasures to maintain 1.7 million courses."
    parsed = parse_congressional_budget_text(sample_text)
    assert parsed.get("parsed_srf_amount") == "850.0"
    assert parsed.get("parsed_smallpox_amount") == "140.0"
    assert parsed.get("parsed_course_count") == "1.7"


def test_fda_slep_telemetry():
    """Test FDA SLEP stockpile aging and replenishment window calculations."""
    custom_tranches = [
        {
            "tranche_id": "TEST-2020",
            "quantity_courses": 100_000,
            "format": "Oral Capsule",
            "current_expiry": (datetime.date.today() + datetime.timedelta(days=180)).isoformat(),
            "slep_status": "TEST"
        },
        {
            "tranche_id": "TEST-2025",
            "quantity_courses": 200_000,
            "format": "Oral Capsule",
            "current_expiry": (datetime.date.today() + datetime.timedelta(days=1000)).isoformat(),
            "slep_status": "TEST"
        }
    ]
    res = model_stockpile_aging(lead_time_months=9, tranches=custom_tranches)
    assert res["total_stockpile_courses_tracked"] == 300_000
    assert res["courses_expiring_within_12m"] == 100_000
    assert res["courses_in_active_reorder_window"] == 100_000
    assert res["telemetry_verdict"] == "REORDER_CYCLE_APPROACHING"


def test_procurement_watch_sweep():
    """Test dry-run sweep of desk procurement watcher."""
    alerts = run_procurement_sweep(dry_run=True)
    assert isinstance(alerts, list)
