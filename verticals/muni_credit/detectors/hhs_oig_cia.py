"""HHS-OIG Corporate Integrity Agreement (CIA) detector.

FIRES when the obligor has an active CIA imposed by HHS-OIG, typically
following a DOJ FCA settlement. CIAs are 5-year mandatory compliance
overhauls with independent review organizations, mandatory training,
and reporting requirements. They impose:
  - $2-10M/yr compliance program cost
  - 5-year window during which any compliance failure can trigger
    Medicare/Medicaid exclusion (essentially fatal — 50-70% of revenue)
  - Leadership/board distraction
  - Reputational overhang

Why predictive: empirically ~50% of obligors under active CIA get rating
action during the 5-year window vs ~15% base rate. The 5-year duration
makes this a structural rather than event-driven signal.

Data source: HHS-OIG publishes the active CIA list at
  https://oig.hhs.gov/compliance/corporate-integrity-agreements/cia-list/

Data shape:
  {
    "active_cia": true,
    "cia_signed_date": "2022-08-15",
    "cia_expiration_date": "2027-08-14",
    "cia_subject": "Excellence Medical Group (subsidiary of XYZ Health System)",
    "underlying_allegation": "...",
    "source_url": "..."
  }
"""
from __future__ import annotations

# Knowledge-graph dispatch contract (see knowledge_graph/dispatch.py). Added 2026-07-29
# to close the atlas gap; muni sector mapping mirrors detectors/dispatch_index.py.
APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": [],
    "issuer_features": ["hospital_obligor", "nursing_home_obligor", "ccrc_obligor"],
    "asset_classes": ["ca_hospital_muni", "healthcare_muni", "ca_chffa_hospital_conduit", "ca_nh_muni", "ca_ccrc_muni", "ccrc_muni"],
    "applies_universally": False,
    "kind": "detector",
    "summary": "HHS-OIG Corporate Integrity Agreement (CIA) detector.",
}

from datetime import datetime


def evaluate(obligor_name: str, data: dict) -> dict:
    active_cia = data.get("active_cia")
    if active_cia is None:
        return {"fires": False, "reason": "INSUFFICIENT_DATA", "evidence": {}}
    if not active_cia:
        return {"fires": False, "reason": "NO_ACTIVE_CIA", "evidence": {}}

    expiration = data.get("cia_expiration_date")
    as_of = data.get("as_of_date") or datetime.utcnow().strftime("%Y-%m-%d")

    # Check if CIA is still active
    if expiration:
        try:
            exp_d = datetime.fromisoformat(expiration[:10])
            asof_d = datetime.fromisoformat(as_of[:10])
            if asof_d > exp_d:
                return {
                    "fires": False,
                    "reason": "CIA_EXPIRED",
                    "evidence": {"expired_on": expiration},
                }
        except Exception:
            pass

    return {
        "fires": True,
        "reason": "ACTIVE_HHS_OIG_CIA",
        "severity": "HIGH",
        "evidence": {
            "signed": data.get("cia_signed_date"),
            "expiration": expiration,
            "subject": data.get("cia_subject"),
            "allegation": data.get("underlying_allegation"),
        },
    }
