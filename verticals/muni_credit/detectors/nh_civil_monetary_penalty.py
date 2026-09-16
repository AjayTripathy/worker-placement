"""Nursing home Civil Monetary Penalty (CMP) detector.

FIRES when the facility has cumulative CMS civil monetary penalties > $500K
in the trailing 24 months, OR an active Denial of Payment for New Admissions
(DPNA) sanction.

Why predictive: large CMP penalties indicate sustained quality failures;
DPNA freezes new Medicare/Medicaid admissions, causing immediate census +
revenue decline.

Public data: CMS Nursing Home Compare enforcement actions dataset.

Data shape:
  {
    "cumulative_cmp_24mo_usd": 750000,
    "active_dpna": false,
    "n_cmps_24mo": 3,
    "as_of_date": "2024-12-31",
    "source_url": "..."
  }
"""
from __future__ import annotations

# Knowledge-graph dispatch contract (see knowledge_graph/dispatch.py). Added 2026-07-29
# to close the atlas gap; muni sector mapping mirrors detectors/dispatch_index.py.
APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": [],
    "issuer_features": ["nursing_home_obligor", "ccrc_obligor"],
    "asset_classes": ["ca_nh_muni", "ca_ccrc_muni", "ccrc_muni"],
    "applies_universally": False,
    "kind": "detector",
    "summary": "Nursing home Civil Monetary Penalty (CMP) detector.",
}

CMP_THRESHOLD_USD = 500_000


def evaluate(obligor_name: str, data: dict) -> dict:
    cmp_total = data.get("cumulative_cmp_24mo_usd")
    dpna = data.get("active_dpna")

    if cmp_total is None and dpna is None:
        return {"fires": False, "reason": "INSUFFICIENT_DATA", "evidence": {}}

    if dpna:
        return {
            "fires": True,
            "reason": "ACTIVE_DPNA",
            "severity": "HIGH",
            "evidence": {
                "cmp_total": cmp_total,
                "active_dpna": True,
                "as_of_date": data.get("as_of_date"),
            },
        }
    if cmp_total and cmp_total >= CMP_THRESHOLD_USD:
        return {
            "fires": True,
            "reason": "MATERIAL_CMP_HISTORY",
            "severity": "MEDIUM",
            "evidence": {
                "cmp_total_24mo": cmp_total,
                "threshold": CMP_THRESHOLD_USD,
                "n_cmps": data.get("n_cmps_24mo"),
            },
        }
    return {
        "fires": False,
        "reason": "NO_MATERIAL_PENALTIES",
        "evidence": {"cmp_total": cmp_total},
    }
