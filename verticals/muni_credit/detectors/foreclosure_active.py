"""Land-secured (CFD) active-foreclosure detector.

FIRES when YFSR reports active bondholder-initiated foreclosure on CFD-
delinquent parcels in the last 24 months.

Why predictive: bondholder-initiated foreclosure is the lender-of-last-resort
signal. Comes 12-24 months AFTER first delinquency in CA's judicial-foreclosure
timeline — so this is LAGGING. Pair with delinquency_spike (leading) to confirm.

Public data: CDIAC YFSR fields `Total Number of Foreclosure Parcels` and
`Date Foreclosure Commenced`. RY 2023-24 saw 7 YFSRs report foreclosure
on 8 parcels — low absolute number, high precision.

Data shape:
  {
    "active_foreclosure_parcels": 12,
    "foreclosure_commenced_date": "2023-03-15",
    "foreclosure_resolved_date": null,
    "months_since_commenced": 26,
    "as_of_date": "2024-12-31",
    "source": "CDIAC YFSR RY2023-24",
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
    "summary": "Land-secured (CFD) active-foreclosure detector.",
}

LOOKBACK_MONTHS = 24


def evaluate(obligor_name: str, data: dict) -> dict:
    n_parcels = data.get("active_foreclosure_parcels")
    commenced = data.get("foreclosure_commenced_date")
    resolved = data.get("foreclosure_resolved_date")
    months_since = data.get("months_since_commenced")

    if n_parcels is None and commenced is None:
        return {"fires": False, "reason": "INSUFFICIENT_DATA", "evidence": {}}

    if not isinstance(n_parcels, int) or n_parcels <= 0:
        return {"fires": False, "reason": "NO_ACTIVE_FORECLOSURE", "evidence": {}}

    # If resolved already, don't fire
    if resolved:
        return {
            "fires": False,
            "reason": "FORECLOSURE_RESOLVED",
            "evidence": {"resolved_date": resolved, "n_parcels": n_parcels},
        }

    # If commenced more than 24mo ago without resolution, still firing but flag staleness
    if isinstance(months_since, (int, float)) and months_since > LOOKBACK_MONTHS:
        severity = "MEDIUM"
        reason = "FORECLOSURE_PROTRACTED"
    else:
        severity = "HIGH" if n_parcels >= 5 else "MEDIUM"
        reason = "FORECLOSURE_ACTIVE"

    return {
        "fires": True,
        "reason": reason,
        "severity": severity,
        "evidence": {
            "active_foreclosure_parcels": n_parcels,
            "foreclosure_commenced_date": commenced,
            "months_since_commenced": months_since,
        },
    }
