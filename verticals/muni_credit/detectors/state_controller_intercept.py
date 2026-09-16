"""State Controller / RPTTF / LCFF apportionment-intercept activity detector.

FIRES when the trailing-12-month flow of state-mediated or county-mediated
apportionment to a CA muni obligor shows a modification, withholding, or
interruption event.

Why predictive: Multiple CA muni masking mechanisms rely on a state or
county officer (State Controller for CSFA LCFF; County Auditor-Controller
for RPTTF; State Controller for general aid apportionment) diverting
payments directly to a bond trustee or successor agency before the obligor
touches the funds. The masking layer is structural — but when a state or
county actor MODIFIES the apportionment (rejects a ROPS item, qualifies a
district as fiscally distressed, withholds an apportionment payment), that
modification is the canonical alarm signal that the intercept is not
operating routinely.

Severity:
  HIGH    — an actual interruption of payment to the obligor or to the
            bond trustee (DOF rejects ROPS bond-debt-service item; SCO
            withholds an entire LCFF apportionment; county auditor fails
            RPTTF distribution).
  MEDIUM  — a modification short of interruption (DOF approves ROPS with
            partial denial of non-debt items; CDE issues Qualified or
            Negative fiscal certification to a district under interim
            review; SCO publishes an audit finding with material
            findings).
  LOW     — routine reporting only.

Critical structural note (do not silently merge these channels):
  • CSFA charter LCFF intercept: STATE Controller diverts apportionment
    to bond trustee under Ed Code 17199.4 — this is a TRUE SCO intercept.
  • CA K-12 USD GO (dedicated-tax SB 222 special-revenue treatment):
    Property tax flows from COUNTY tax collector directly to bond
    trustee. State Controller has NO direct role in bond debt service.
    The relevant 'apportionment activity' channel for K-12 USD is the
    CDE Interim Status Report (Qualified / Negative certification),
    which signals operating-side fiscal distress that does NOT route to
    bondholder pledge but IS the upstream signal for IDR cut → 5-notch-
    ceiling compression on dedicated-tax-GO ratings.
  • Successor RDA RPTTF: COUNTY Auditor-Controller distributes RPTTF
    semi-annually per HSC §34183. DOF approves the ROPS each fiscal
    year. SCO does NOT directly pay these distributions — DOF approval
    + County distribution is the canonical channel. Use the
    'intercept_type' field to route the right channel.

Data shape:
  {
    "obligor_name": "...",
    "intercept_type": "lcff" | "rpttf" | "csfa_intercept" | "cde_interim" | "other",
    "trailing_12mo_distributions": [
      {
        "period": "ROPS 25-26",
        "amount_usd": 36497260,
        "approved": true,
        "approval_date": "2025-04-04",
        "source_url": "https://dof.ca.gov/.../Fontana_ROPS_25-26.pdf"
      }, ...
    ],
    "interruption_or_modification_events": [
      {
        "event_type": "QUALIFIED_CERTIFICATION" | "NEGATIVE_CERTIFICATION"
                      | "ROPS_ITEM_DENIED" | "ROPS_BOND_DEBT_DENIED"
                      | "APPORTIONMENT_WITHHELD" | "ADMIN_NOTE"
                      | "DOF_LITIGATION" | "ROPS_PPA_OFFSET",
        "date": "2026-03-02",
        "description": "...",
        "source_url": "..."
      }
    ],
    "as_of_date": "2026-05-28",
    "confidence": "HIGH"
  }

Returns:
  {
    "fires": bool,
    "reason": "...",
    "severity": "HIGH" | "MEDIUM" | "LOW",
    "evidence": {...}
  }
"""
from __future__ import annotations

# Knowledge-graph dispatch contract (see knowledge_graph/dispatch.py). Added 2026-07-29
# to close the atlas gap; muni sector mapping mirrors detectors/dispatch_index.py.
APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": [],
    "issuer_features": ["k12_district_obligor", "charter_school_obligor", "successor_agency_obligor"],
    "asset_classes": ["ca_k12_school_district_go", "ca_school_go_muni", "ca_k12_muni", "ca_charter_muni", "ca_charter_muni_csfa_issued", "ca_charter_pooled_jpa", "ca_rda_successor_muni", "ca_tax_allocation_bonds_post_dissolution"],
    "applies_universally": False,
    "kind": "detector",
    "summary": "State Controller / RPTTF / LCFF apportionment-intercept activity detector.",
}

from datetime import datetime, timedelta


# Event taxonomy — interruption-class events trigger HIGH severity, all others MEDIUM
INTERRUPTION_EVENTS = {
    "ROPS_BOND_DEBT_DENIED",        # DOF rejects a bond-debt-service line item
    "APPORTIONMENT_WITHHELD",       # SCO withholds an entire apportionment payment
    "NEGATIVE_CERTIFICATION",       # CDE: district will not meet financial obligations
    "TRUSTEE_PAYMENT_INTERRUPTED",  # Bond trustee receipt interrupted
}

MODIFICATION_EVENTS = {
    "QUALIFIED_CERTIFICATION",      # CDE: district may not meet financial obligations
    "ROPS_ITEM_DENIED",             # DOF rejects a non-bond ROPS item
    "ROPS_PPA_OFFSET",              # Prior-period adjustment reducing RPTTF
    "DOF_LITIGATION",               # ROPS item under active litigation
    "ADMIN_NOTE",                   # DOF/SCO non-binding admin note (admin cost too high, etc.)
    "SCO_AUDIT_FINDING",            # SCO published material audit finding
}


def _in_trailing_12_months(date_str: str, as_of: str) -> bool:
    """Return True iff date_str within trailing 365 days of as_of."""
    if not date_str:
        return False
    try:
        d = datetime.fromisoformat(date_str[:10])
        ref = datetime.fromisoformat(as_of[:10])
    except Exception:
        return False
    return timedelta(days=0) <= (ref - d) <= timedelta(days=365)


def evaluate(obligor_name: str, data: dict) -> dict:
    intercept_type = (data.get("intercept_type") or "other").lower()
    events = data.get("interruption_or_modification_events") or []
    distributions = data.get("trailing_12mo_distributions") or []
    as_of = data.get("as_of_date") or datetime.utcnow().strftime("%Y-%m-%d")
    confidence = (data.get("confidence") or "").upper()

    if not events and not distributions:
        return {"fires": False, "reason": "INSUFFICIENT_DATA",
                "evidence": {"intercept_type": intercept_type}}

    # Refuse to fire on LOW-confidence inputs (mirrors late_filing.py guard)
    if confidence in ("LOW", "") and not events:
        return {"fires": False, "reason": "INSUFFICIENT_DATA",
                "evidence": {"confidence": confidence, "note": "no events with sufficient confidence"}}

    # Filter events to trailing 12 months
    recent_events = [
        e for e in events
        if _in_trailing_12_months(e.get("date"), as_of)
    ]

    if not recent_events:
        # No events in trailing 12mo and (presumably) clean distributions
        approved_count = sum(1 for d in distributions if d.get("approved"))
        denied_count = sum(1 for d in distributions if d.get("approved") is False)
        if denied_count > 0:
            return {
                "fires": True,
                "reason": "DISTRIBUTION_DENIED",
                "severity": "HIGH",
                "evidence": {
                    "intercept_type": intercept_type,
                    "denied_count": denied_count,
                    "distributions": distributions,
                },
            }
        return {
            "fires": False,
            "reason": "ROUTINE_APPROVED",
            "severity": "LOW",
            "evidence": {
                "intercept_type": intercept_type,
                "approved_count": approved_count,
                "n_distributions": len(distributions),
            },
        }

    interruptions = [e for e in recent_events if e.get("event_type") in INTERRUPTION_EVENTS]
    modifications = [e for e in recent_events if e.get("event_type") in MODIFICATION_EVENTS]
    # Anything not classified — treat conservatively as modification to avoid silent NOOP
    other = [e for e in recent_events
             if e.get("event_type") not in INTERRUPTION_EVENTS
             and e.get("event_type") not in MODIFICATION_EVENTS]

    # Admin notes alone do not fire — too noisy across the universe (most ROPS letters carry them)
    binding_mods = [m for m in modifications if m.get("event_type") != "ADMIN_NOTE"]

    if interruptions:
        return {
            "fires": True,
            "reason": interruptions[0].get("event_type", "INTERRUPTION"),
            "severity": "HIGH",
            "evidence": {
                "intercept_type": intercept_type,
                "n_interruptions": len(interruptions),
                "events": interruptions,
            },
        }

    if binding_mods:
        return {
            "fires": True,
            "reason": binding_mods[0].get("event_type", "MODIFICATION"),
            "severity": "MEDIUM",
            "evidence": {
                "intercept_type": intercept_type,
                "n_modifications": len(binding_mods),
                "events": binding_mods,
            },
        }

    # Only admin notes or unclassified — informational, do not fire
    return {
        "fires": False,
        "reason": "ROUTINE_WITH_ADMIN_NOTES",
        "severity": "LOW",
        "evidence": {
            "intercept_type": intercept_type,
            "admin_notes": modifications,
            "other_events": other,
        },
    }
