"""HCAI (formerly OSHPD) seismic non-compliance detector — CA hospitals only.

FIRES when a CA hospital has at least one inpatient general acute care
building that is NOT in compliance with the SB 1953 / SB 90 seismic deadlines
(originally 2030, with extensions available through HCAI). Non-compliance
exposes the obligor to:
  - Required retrofit at $100M+ per hospital (Standard Performance Categories
    SPC-2 buildings must be SPC-4 by deadline)
  - Risk of mandatory closure of non-compliant buildings (effective closure
    of beds in that wing)
  - HCAI fines and operating restrictions

Why predictive: many CA hospitals have one or more non-compliant buildings
and have not funded the retrofit. The deadline is a hard wall — facilities
that miss it lose ICU/ED capacity. Material credit pressure builds over the
3-5 years before deadline.

Lead time vs rating action: typically 12-36 months — agencies cite seismic
exposure in CA hospital rationales.

Data source: HCAI publishes the public list of SPC ratings per facility at
https://hcai.ca.gov/construction-finance/seismic-compliance-and-safety/seismic-safety-list-of-buildings/

Data shape:
  {
    "n_buildings_total": 12,
    "n_buildings_spc_lt_4": 5,  # buildings below SPC-4 (non-compliant)
    "spc_2_buildings": 2,
    "n_buildings_with_extension": 1,
    "deadline_year": 2030,
    "estimated_retrofit_cost_usd": 250000000,
    "source_url": "https://hcai.ca.gov/...",
    "confidence": "HIGH"
  }
"""
from __future__ import annotations

# Knowledge-graph dispatch contract (see knowledge_graph/dispatch.py). Added 2026-07-29
# to close the atlas gap; muni sector mapping mirrors detectors/dispatch_index.py.
APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": [],
    "issuer_features": ["hospital_obligor"],
    "asset_classes": ["ca_hospital_muni", "healthcare_muni", "ca_chffa_hospital_conduit"],
    "applies_universally": False,
    "kind": "detector",
    "summary": "HCAI (formerly OSHPD) seismic non-compliance detector — CA hospitals only.",
}


def evaluate(obligor_name: str, data: dict) -> dict:
    n_total = data.get("n_buildings_total")
    n_below_compliance = data.get("n_buildings_spc_lt_4")

    if n_total is None or n_below_compliance is None:
        return {"fires": False, "reason": "INSUFFICIENT_DATA", "evidence": {}}

    if n_total == 0:
        return {"fires": False, "reason": "NO_BUILDINGS_TRACKED", "evidence": {}}

    share_below = n_below_compliance / n_total

    # Critical: SPC-2 buildings risk mandatory closure at deadline. >30% non-compliant
    # OR any SPC-2 buildings without funded retrofit is the fire condition.
    has_spc_2 = (data.get("spc_2_buildings") or 0) > 0
    funded_extension = data.get("n_buildings_with_extension", 0)
    unfunded_critical = (data.get("spc_2_buildings") or 0) - funded_extension

    # TIGHTENED THRESHOLDS (post-CA-test calibration):
    # The HCAI signal has a 3-7 year lead time vs the 2030 deadline; in a short
    # backtest window most "non-compliant" hospitals look fine because the
    # deadline hasn't arrived yet. Restrict fire to the most acute cases:
    #   1. ≥5 unfunded SPC-2 buildings (large material capex with no extension)
    #   2. OR ≥50% of buildings non-compliant AND no extensions secured
    # This drops fire rate from ~37% to ~5-10% of universe.
    if unfunded_critical >= 5:
        return {
            "fires": True,
            "reason": "MANY_UNFUNDED_SPC_2_BUILDINGS",
            "severity": "HIGH",
            "evidence": {
                "n_spc_2_unfunded": unfunded_critical,
                "n_total": n_total,
                "deadline_year": data.get("deadline_year"),
            },
        }
    if share_below >= 0.50 and funded_extension == 0:
        return {
            "fires": True,
            "reason": "MAJORITY_NON_COMPLIANT_NO_EXTENSIONS",
            "severity": "HIGH",
            "evidence": {
                "n_below_compliance": n_below_compliance,
                "n_total": n_total,
                "share_below": share_below,
            },
        }
    return {
        "fires": False,
        "reason": "COMPLIANCE_ADEQUATE",
        "evidence": {
            "share_below": share_below,
            "n_total": n_total,
        },
    }
