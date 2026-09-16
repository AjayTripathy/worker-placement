"""
phemce_appropriations — Congressional Budget & PHEMCE Statutory Stockpile Parser.

Models and audits:
  - HHS/ASPR Project BioShield Special Reserve Fund (SRF) appropriations.
  - Strategic National Stockpile (SNS) operations & countermeasure procurement line items.
  - PHEMCE Statutory Stockpile Target: Mandate to maintain 1.70 million courses of smallpox antivirals.

Primary use: Evaluating the macro budgetary health and procurement runway for biodefense
contractors (e.g. SIGA Technologies / TPOXX) ahead of federal budget enactments.
"""

from __future__ import annotations

import datetime
import re
from typing import Any, Dict, List, Optional


# Statutory Baseline: PHEMCE Multi-Year Budget (MYB) Target for Smallpox Antiviral Courses
STATUTORY_SNS_SMALLPOX_TARGET_COURSES = 1_700_000

# Historical & Modeled HHS/ASPR Budget Line Items (in Millions USD)
BUDGET_RECORDS = {
    "FY2024": {
        "project_bioshield_srf_budget_m": 820.0,
        "sns_procurement_budget_m": 965.0,
        "barda_advanced_rd_budget_m": 1015.0,
        "smallpox_specific_allocation_m": 125.0,
        "estimated_active_courses_held": 1_650_000,
        "appropriation_status": "ENACTED"
    },
    "FY2025": {
        "project_bioshield_srf_budget_m": 835.0,
        "sns_procurement_budget_m": 980.0,
        "barda_advanced_rd_budget_m": 1040.0,
        "smallpox_specific_allocation_m": 130.0,
        "estimated_active_courses_held": 1_680_000,
        "appropriation_status": "ENACTED"
    },
    "FY2026": {
        "project_bioshield_srf_budget_m": 850.0,
        "sns_procurement_budget_m": 1000.0,
        "barda_advanced_rd_budget_m": 1075.0,
        "smallpox_specific_allocation_m": 140.0,
        "estimated_active_courses_held": 1_620_000,
        "appropriation_status": "PRESIDENT_REQUEST_PENDING_MARKUP"
    }
}


def audit_phemce_stockpile_health(
    fiscal_year: str = "FY2026",
    contractor_ticker: str = "SIGA",
    avg_cost_per_course_usd: float = 350.0
) -> Dict[str, Any]:
    """
    Audit the health of the biodefense contractor's statutory mandate against Congressional
    appropriations and the PHEMCE Strategic National Stockpile target.
    """
    record = BUDGET_RECORDS.get(fiscal_year, BUDGET_RECORDS["FY2026"])
    active_courses = record["estimated_active_courses_held"]
    target_courses = STATUTORY_SNS_SMALLPOX_TARGET_COURSES
    course_deficit = max(0, target_courses - active_courses)
    replenishment_funding_needed_m = (course_deficit * avg_cost_per_course_usd) / 1_000_000.0
    
    srf_budget = record["project_bioshield_srf_budget_m"]
    smallpox_alloc = record["smallpox_specific_allocation_m"]
    
    # Coverage score: Ratio of available smallpox allocation to replenishment funding needed
    coverage_ratio = (smallpox_alloc / replenishment_funding_needed_m) if replenishment_funding_needed_m > 0 else 2.0
    
    status = "HEALTHY / FULLY FUNDED"
    if coverage_ratio < 0.8:
        status = "APPROPRIATION_DEFICIT_RISK"
    elif coverage_ratio < 1.0:
        status = "TIGHT / GATED"

    return {
        "fiscal_year": fiscal_year,
        "contractor_ticker": contractor_ticker,
        "status": status,
        "statutory_sns_target_courses": target_courses,
        "estimated_active_courses_held": active_courses,
        "course_deficit": course_deficit,
        "replenishment_funding_needed_m": round(replenishment_funding_needed_m, 2),
        "project_bioshield_srf_total_m": srf_budget,
        "smallpox_specific_allocation_m": smallpox_alloc,
        "coverage_ratio": round(coverage_ratio, 2),
        "appropriation_status": record["appropriation_status"],
        "mandate_legitimacy": "Statutory under Homeland Security Act of 2002 & Project BioShield Act of 2004",
        "audit_timestamp": datetime.datetime.utcnow().isoformat() + "Z"
    }


def parse_congressional_budget_text(text: str) -> Dict[str, Any]:
    """
    Extract line-item dollar values and course counts from raw Congressional testimony
    or Committee Explanatory Statements.
    """
    res = {}
    # Match "$X million for [the] Project BioShield Special Reserve Fund" or "Special Reserve Fund ... $X"
    srf_match = re.search(r"\$([0-9,]+(?:\.[0-9]+)?)\s*(?:million|M)?\s*(?:for\s+(?:the\s+)?)?Project BioShield Special Reserve Fund", text, re.IGNORECASE)
    if not srf_match:
        srf_match = re.search(r"Special Reserve Fund[^\$]*\$([0-9,]+(?:\.[0-9]+)?)", text, re.IGNORECASE)
    if srf_match:
        res["parsed_srf_amount"] = srf_match.group(1)
        
    # Match "$X million for smallpox" or "smallpox ... $X"
    smallpox_match = re.search(r"\$([0-9,]+(?:\.[0-9]+)?)\s*(?:million|M)?\s*(?:for\s+)?smallpox", text, re.IGNORECASE)
    if not smallpox_match:
        smallpox_match = re.search(r"smallpox[^\$]*\$([0-9,]+(?:\.[0-9]+)?)", text, re.IGNORECASE)
    if smallpox_match:
        res["parsed_smallpox_amount"] = smallpox_match.group(1)
        
    courses_match = re.search(r"([0-9,]+(?:\.[0-9]+)?)\s*(?:million|M)?\s*courses", text, re.IGNORECASE)
    if courses_match:
        res["parsed_course_count"] = courses_match.group(1)
        
    return res
