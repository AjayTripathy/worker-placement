"""Land-secured (CFD) issuer-administration / late-YFSR-filing detector.

FIRES when CFD has 3+ missing CDIAC YFSR filings (severity HIGH) or 1-2
missing (severity MEDIUM, secondary signal).

Why predictive: YFSR is mandatory under SB 165. Folsom CFD 2014-1 had 5
missing reports in RY 2023-24 — extreme administrative breakdown that
correlates with deeper governance issues. Distinct from the SEC-style
late_filing detector (which targets bond-disclosure documents) — this
targets CDIAC compliance specifically.

Public data: CDIAC RY annual summary report Figure 13.

Calibration: 34 of 1,829 CFDs missed at least one filing in RY 2023-24
(1.86%). The severity scales with miss count, and 1-miss alone is noisy
(could be admin oversight); 3+ misses is reliable distress signal.

Data shape:
  {
    "filings_due_not_received": 3,
    "filings_on_time": false,
    "last_filing_date": "2021-10-30",
    "as_of_date": "2024-12-31",
    "source": "CDIAC RY2023-24 Figure 13",
    "confidence": "HIGH"
  }
"""
from __future__ import annotations

# Knowledge-graph dispatch contract (see knowledge_graph/dispatch.py). Added 2026-07-29
# to close the atlas gap; muni sector mapping mirrors detectors/dispatch_index.py.
APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": [],
    "issuer_features": ["land_secured_district"],
    "asset_classes": ["ca_mello_roos_cfd", "ca_cfd_muni", "ca_1915_act_assessment_bonds"],
    "applies_universally": False,
    "kind": "detector",
    "summary": "Land-secured (CFD) issuer-administration / late-YFSR-filing detector.",
}

MISS_HIGH_THRESHOLD = 3
MISS_MEDIUM_THRESHOLD = 1


def evaluate(obligor_name: str, data: dict) -> dict:
    n_missed = data.get("filings_due_not_received")
    on_time = data.get("filings_on_time")

    if n_missed is None and on_time is None:
        return {"fires": False, "reason": "INSUFFICIENT_DATA", "evidence": {}}

    if not isinstance(n_missed, int):
        if on_time is True:
            n_missed = 0
        else:
            return {"fires": False, "reason": "INSUFFICIENT_DATA", "evidence": {}}

    if n_missed >= MISS_HIGH_THRESHOLD:
        return {
            "fires": True,
            "reason": "ADMINISTRATIVE_BREAKDOWN",
            "severity": "HIGH",
            "evidence": {
                "filings_due_not_received": n_missed,
                "last_filing_date": data.get("last_filing_date"),
            },
        }
    if n_missed >= MISS_MEDIUM_THRESHOLD:
        return {
            "fires": True,
            "reason": "LATE_YFSR_FILING",
            "severity": "MEDIUM",
            "evidence": {
                "filings_due_not_received": n_missed,
                "last_filing_date": data.get("last_filing_date"),
            },
        }
    return {
        "fires": False,
        "reason": "FILINGS_CURRENT",
        "evidence": {"filings_due_not_received": n_missed},
    }
