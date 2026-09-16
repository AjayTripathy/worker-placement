"""Land-secured (CFD) value-to-lien (V/L) ratio detector.

FIRES when V/L < 3.0 (industry yellow-flag, also LA City CFD policy minimum at
issuance). Severity HIGH at V/L < 2.0; severity RED at V/L < 1.0 (lien exceeds
property value — Diablo Grande at 0.14 is the canonical example).

Why predictive: V/L collapse means underlying parcel equity has eroded below
the bond claim. Bondholder recovery in foreclosure is bounded by AV;
sub-1x V/L = guaranteed principal impairment in workout.

Public data: CDIAC Yearly Fiscal Status Report (YFSR), mandatory for all CFDs
under SB 165 / Mello-Roos Act. Fields: `Assessed Value` + `Principal Outstanding`.

Data shape:
  {
    "assessed_value_usd": 5309345,
    "principal_outstanding_usd": 38660000,
    "overlapping_debt_usd": null,  # optional; if known, V/L denom = principal + overlapping
    "value_to_lien_ratio": 0.14,   # if pre-computed
    "as_of_date": "2024-06-30",
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
    "summary": "Land-secured (CFD) value-to-lien (V/L) ratio detector.",
}

VL_YELLOW = 3.0
VL_HIGH_SEVERITY = 2.0
VL_RED_SEVERITY = 1.0


def evaluate(obligor_name: str, data: dict) -> dict:
    vl = data.get("value_to_lien_ratio")
    av = data.get("assessed_value_usd")
    par = data.get("principal_outstanding_usd")
    overlapping = data.get("overlapping_debt_usd") or 0
    if not isinstance(overlapping, (int, float)):
        overlapping = 0

    # Filter UNVERIFIABLE sentinel strings — treat as missing
    if not isinstance(vl, (int, float)):
        vl = None
    if not isinstance(av, (int, float)):
        av = None
    if not isinstance(par, (int, float)):
        par = None

    if vl is None and av is not None and par:
        vl = av / (par + overlapping)

    if vl is None:
        return {"fires": False, "reason": "INSUFFICIENT_DATA", "evidence": {}}

    if vl < VL_RED_SEVERITY:
        severity = "RED"
    elif vl < VL_HIGH_SEVERITY:
        severity = "HIGH"
    elif vl < VL_YELLOW:
        severity = "MEDIUM"
    else:
        return {
            "fires": False,
            "reason": "V_L_ABOVE_3X",
            "evidence": {"value_to_lien_ratio": round(vl, 2)},
        }

    return {
        "fires": True,
        "reason": "VALUE_TO_LIEN_COLLAPSE",
        "severity": severity,
        "evidence": {
            "value_to_lien_ratio": round(vl, 2),
            "assessed_value_usd": av,
            "principal_outstanding_usd": par,
            "overlapping_debt_usd": overlapping,
            "threshold_yellow": VL_YELLOW,
            "as_of_date": data.get("as_of_date"),
        },
    }
