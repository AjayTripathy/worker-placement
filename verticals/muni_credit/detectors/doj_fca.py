"""DOJ False Claims Act / healthcare fraud settlement detector.

FIRES when the obligor has a DOJ FCA, Stark Law, or Anti-Kickback Statute
settlement > $25M in the trailing 24 months, OR is under a Corporate
Integrity Agreement (CIA).

Why predictive: large healthcare fraud settlements force operational changes
(compliance program overhaul, monitoring, reduced reimbursement from
penalized programs) that show up in financial results 6-18 months later.
CIA imposition is a structural overhead burden lasting 5 years.

Data shape:
  {
    "had_settlement": true,
    "settlement_amount_usd": 50000000,
    "settlement_date": "2023-09-15",
    "allegation": "Billing for medically unnecessary procedures",
    "cia_imposed": false,
    "source_url": "...",
    "confidence": "HIGH"
  }

Threshold: $25M settlement amount.
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
    "summary": "DOJ False Claims Act / healthcare fraud settlement detector.",
}

THRESHOLD_LARGE_USD = 25_000_000   # Standalone material settlement
THRESHOLD_RECIDIVIST_USD = 5_000_000  # If prior CIA in 5 yrs, smaller settlement still fires


def evaluate(obligor_name: str, data: dict) -> dict:
    had_settlement = data.get("had_settlement")
    amount = data.get("settlement_amount_usd")
    cia = data.get("cia_imposed", False)
    prior_cia_within_5yr = data.get("prior_cia_within_5yr", False)
    doj_intervened_complaint = data.get("doj_intervened_complaint", False)

    if had_settlement is None and not doj_intervened_complaint:
        return {"fires": False, "reason": "INSUFFICIENT_DATA", "evidence": {}}

    # DOJ-intervened pending complaint = high severity (recent Erlanger case)
    if doj_intervened_complaint:
        return {
            "fires": True,
            "reason": "DOJ_INTERVENED_PENDING_COMPLAINT",
            "severity": "HIGH",
            "evidence": {
                "estimated_exposure_usd": data.get("estimated_exposure_usd"),
                "allegation": data.get("allegation"),
                "intervention_date": data.get("intervention_date"),
            },
        }

    if not had_settlement:
        return {"fires": False, "reason": "NO_SETTLEMENT", "evidence": {}}

    if cia:
        return {
            "fires": True,
            "reason": "CIA_IMPOSED",
            "severity": "HIGH",
            "evidence": {
                "settlement_amount_usd": amount,
                "cia_imposed": True,
                "settlement_date": data.get("settlement_date"),
                "allegation": data.get("allegation"),
            },
        }
    if amount and amount >= THRESHOLD_LARGE_USD:
        return {
            "fires": True,
            "reason": "MATERIAL_FCA_SETTLEMENT",
            "severity": "MEDIUM",
            "evidence": {
                "settlement_amount_usd": amount,
                "threshold_usd": THRESHOLD_LARGE_USD,
                "settlement_date": data.get("settlement_date"),
                "allegation": data.get("allegation"),
            },
        }
    # Recidivism: smaller settlement still fires if there's a prior CIA history
    if prior_cia_within_5yr and amount and amount >= THRESHOLD_RECIDIVIST_USD:
        return {
            "fires": True,
            "reason": "FCA_RECIDIVIST",
            "severity": "HIGH",
            "evidence": {
                "settlement_amount_usd": amount,
                "prior_cia_within_5yr": True,
                "settlement_date": data.get("settlement_date"),
                "allegation": data.get("allegation"),
            },
        }
    return {
        "fires": False,
        "reason": "SETTLEMENT_BELOW_THRESHOLD",
        "evidence": {"amount_usd": amount},
    }
