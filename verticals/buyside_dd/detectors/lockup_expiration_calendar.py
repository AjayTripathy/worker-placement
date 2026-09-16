"""Lockup expiration calendar detector for corporate IPO follow-on DD.

FIRES when a follow-on offering (or secondary share resale shelf) is filed
within a narrow window of a known insider lockup expiration — suggesting the
filing is structured to enable insider monetization rather than to raise
operating capital.

Severity:
- RED: follow-on filing within 30 days of lockup expiration AND >25% of float
       is secondary shares from insiders
- HIGH: follow-on within 90 days of lockup expiration AND material secondary
- MEDIUM: follow-on within 180 days of lockup, more primary than secondary

Live catch (2026-05-28 Firefly): IPO Aug 2025; first lockup expired 2026-02-03
(IPO lockup) + 2026-02-07 (SciTec resale shelf); follow-on filed 2026-05-26
(108 days after first expiration, in the "second window" pattern). 4M primary
+ 8M secondary + 11.1M SciTec resale shelf = ~13% of float as insider
monetization overhang.

## Data shape

{
  "company_name": "Firefly Aerospace",
  "ipo_date": "2025-08-07",
  "ipo_lockup_expiration_date": "2026-02-03",
  "additional_lockup_expirations": [
    {"date": "2026-02-07", "holder": "SciTec resale shelf"},
  ],
  "follow_on_filing_date": "2026-05-26",
  "follow_on_primary_shares": 4000000,
  "follow_on_secondary_shares": 8000000,
  "follow_on_resale_shelf_shares": 11100000,
  "current_float_shares": 100000000,

  # Mitigating factors (DETERMINISTIC SEVERITY DOWNGRADES). Default to
  # most-conservative (no mitigation) when unknown.
  "insider_public_hold_commitments_pct_of_insider_shares": 0.0,  # % of insider
                            # shares with publicly-stated extended hold commitments
  "insider_hold_commitment_additional_years": 0,                  # years of extension
  "as_of_date": "2026-05-28",
  "source_url": "Firefly S-1 Cover + Selling Stockholder Tables"
}
"""
from __future__ import annotations

from datetime import datetime

APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": [],
    "issuer_features": ["follow_on_offering"],
    "asset_classes": ["corporate_ipo_dd"],
    "applies_universally": True,  # cheap to evaluate; auto-bails if no lockup data
    "summary": "Follow-on filing within 90-180d of lockup expiration with material insider overhang.",
}


def _parse(s):
    try:
        return datetime.fromisoformat((s or "").replace("Z", ""))
    except Exception:
        return None


def evaluate(obligor_name: str, data: dict) -> dict:
    ipo_lockup = _parse(data.get("ipo_lockup_expiration_date"))
    filing = _parse(data.get("follow_on_filing_date"))

    if not ipo_lockup or not filing:
        return {"fires": False, "reason": "INSUFFICIENT_DATA", "evidence": {}}

    # Distance from filing to lockup (positive if filing AFTER lockup)
    days_after_lockup = (filing - ipo_lockup).days

    additional = data.get("additional_lockup_expirations") or []
    min_distance_days = abs(days_after_lockup)
    for add in additional:
        ad = _parse(add.get("date"))
        if ad:
            d = abs((filing - ad).days)
            min_distance_days = min(min_distance_days, d)

    secondary = data.get("follow_on_secondary_shares") or 0
    resale_shelf = data.get("follow_on_resale_shelf_shares") or 0
    primary = data.get("follow_on_primary_shares") or 0
    float_shares = data.get("current_float_shares") or 1
    insider_overhang_pct = ((secondary + resale_shelf) / float_shares) * 100

    # Mitigating factor: insider public hold commitments
    hold_pct = float(data.get("insider_public_hold_commitments_pct_of_insider_shares") or 0)
    hold_years = int(data.get("insider_hold_commitment_additional_years") or 0)
    has_meaningful_hold = hold_pct >= 50 and hold_years >= 1  # >=50% of insider shares, >=1 yr

    severity = None
    reason = None
    if min_distance_days <= 30 and insider_overhang_pct >= 25:
        severity, reason = "RED", "FOLLOW_ON_AT_LOCKUP_WITH_MAJOR_INSIDER_OVERHANG"
    elif min_distance_days <= 90 and insider_overhang_pct >= 10:
        severity, reason = "HIGH", "FOLLOW_ON_NEAR_LOCKUP_WITH_MATERIAL_OVERHANG"
    elif min_distance_days <= 180 and (secondary + resale_shelf) > primary:
        severity, reason = "MEDIUM", "FOLLOW_ON_WITHIN_LOCKUP_WINDOW_SECONDARY_DOMINATES"

    # Deterministic mitigating-factor downgrade: meaningful insider hold-commitment
    # drops severity one tier. Firefly case (no hold commitments) → severity unchanged.
    if severity and has_meaningful_hold:
        prior = severity
        severity = {"RED": "HIGH", "HIGH": "MEDIUM", "MEDIUM": "LOW"}.get(severity, severity)
        if severity != prior:
            reason += "__INSIDER_HOLD_COMMITMENTS_DOWNGRADED_ONE_TIER"

    if severity is None:
        return {
            "fires": False,
            "reason": "LOCKUP_TIMING_NOT_SUSPICIOUS",
            "evidence": {
                "days_from_lockup": min_distance_days,
                "insider_overhang_pct": insider_overhang_pct,
            },
        }

    return {
        "fires": True,
        "reason": reason,
        "severity": severity,
        "evidence": {
            "min_distance_to_lockup_days": min_distance_days,
            "insider_overhang_pct_of_float": insider_overhang_pct,
            "primary_shares": primary,
            "secondary_shares": secondary,
            "resale_shelf_shares": resale_shelf,
            "ipo_lockup_date": data.get("ipo_lockup_expiration_date"),
            "follow_on_filing_date": data.get("follow_on_filing_date"),
            "insider_hold_commitments_pct": hold_pct,
            "insider_hold_commitment_years": hold_years,
            "meaningful_hold_commitment_present": has_meaningful_hold,
        },
    }
