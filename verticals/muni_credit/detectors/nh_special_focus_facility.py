"""Nursing home Special Focus Facility (SFF) detector.

FIRES when the facility is on the CMS Special Focus Facility list — CMS's
designation for the worst-performing 5% of nursing homes nationally.

SFF facilities face:
  - More frequent CMS surveys (every 6 months vs 12-15 months)
  - Higher enforcement penalty exposure
  - Potential termination from Medicare/Medicaid if no improvement
  - Reputational damage affecting census

This is a textbook narrow detector — extremely small universe (~80 SFF
facilities + ~440 candidates nationally), very high precision.

Public data: CMS publishes the SFF list monthly.

Data shape:
  {
    "sff_status": "SFF" | "SFF_CANDIDATE" | "GRADUATED" | "NONE",
    "list_date": "2024-12-15",
    "source_url": "https://www.cms.gov/files/document/sfflist...",
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
    "summary": "Nursing home Special Focus Facility (SFF) detector.",
}


def evaluate(obligor_name: str, data: dict) -> dict:
    status = (data.get("sff_status") or "").upper()
    if not status:
        return {"fires": False, "reason": "INSUFFICIENT_DATA", "evidence": {}}
    if status == "SFF":
        return {
            "fires": True,
            "reason": "CMS_SFF_DESIGNATED",
            "severity": "HIGH",
            "evidence": {
                "sff_status": "SFF",
                "list_date": data.get("list_date"),
            },
        }
    if status == "SFF_CANDIDATE":
        return {
            "fires": True,
            "reason": "CMS_SFF_CANDIDATE",
            "severity": "MEDIUM",
            "evidence": {
                "sff_status": "SFF_CANDIDATE",
                "list_date": data.get("list_date"),
            },
        }
    return {
        "fires": False,
        "reason": "NOT_ON_SFF_LIST",
        "evidence": {"sff_status": status},
    }
