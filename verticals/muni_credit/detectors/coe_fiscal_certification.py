"""California County Office of Education (COE) fiscal certification detector
for K-12 school district GO bond obligors.

FIRES when the COE's quarterly AB 1200 fiscal certification on the district is
"Qualified" (Q) or "Negative" (N) for the current or any of the two trailing
interim reporting cycles.

Severity:
  RED    — any Negative in trailing 4 quarters (imminent fiscal emergency)
  HIGH   — two or more Qualified in trailing 4 quarters (back-to-back Q =
           pre-receivership trajectory) OR any active FCMAT fiscal-distress
           engagement OR state-receiver active
  MEDIUM — single Qualified in trailing 4 quarters

Why predictive: Under AB 1200 (Ed Code §42127.6 / §42131), every CA K-12
district files first interim (period ending Oct 31, due Dec 15) and second
interim (period ending Jan 31, due Mar 17) reports. The COE issues a
certification:
  Positive  — district will meet financial obligations current + 2 subsequent FY
  Qualified — district MAY NOT meet financial obligations in current or 2 subsequent FY
  Negative  — district WILL NOT meet financial obligations in current FY

Empirical lead time: Qualified status precedes state-receivership emergency
loan by 12-24 months (Sacramento City USD = Q on 2024-25 First Interim →
N on 2025-26 First Interim → BB- rating cut + $170M deficit by April 2026;
Oakland USD = chronic Q since 2023, FCMAT engagement, pre-receivership
trajectory; Vallejo City USD = Q for 5+ years before 2004 state takeover).

Public data: CDE Interim Status Reports (https://www.cde.ca.gov/fg/fi/ir/),
COE board agendas, FCMAT report archive (https://www.fcmat.org/fcmat-reports).

CRITICAL — interaction with `ca_k12_dedicated_tax_special_revenue` masking:
A Q/N certification reflects DISTRICT-LEVEL fiscal distress. For dedicated-tax
GO bonds with explicit pledged-special-revenue OS language, distress propagates
to the IDR but is capped at 5 notches above IDR per Fitch criteria. SCUSD case
(2026-04-28): IDR cut BB-, dedicated-tax GO held BBB+ (still IG). So a Q/N
fire on this detector should EXCLUDE only ULTGO older-series (no explicit
pledge), COPs, LRBs, certificate paper. Dedicated-tax GO with proper OS
language remains in BUY-ZONE — though severity influences pricing of the
descending-ladder play. This detector FIRES on the obligor; the bond-series
filter is applied downstream in the basket-construction layer.

Data shape:
  {
    "district_name": "River Delta Joint Unified",
    "coe": "Sacramento County Office of Education",
    "certifications_trailing_8q": [
      {"period": "2025-26-Q2", "status": "Qualified",
       "source_url": "https://www.cde.ca.gov/fg/fi/ir/second2526.asp"},
      {"period": "2025-26-Q1", "status": "Qualified",
       "source_url": "https://www.cde.ca.gov/fg/fi/ir/first2526.asp"},
      {"period": "2024-25-Q2", "status": "Positive",
       "source_url": "https://www.cde.ca.gov/fg/fi/ir/second2425.asp"},
      ...
    ],
    "fcmat_involvement_active": false,
    "fcmat_engagement_type": null,    # "FHRA" | "AB_139_audit" | "management_review" | null
    "state_receiver_active": false,
    "as_of_date": "2026-05-28",
    "confidence": "HIGH"
  }
"""
from __future__ import annotations

# Knowledge-graph dispatch contract (see knowledge_graph/dispatch.py). Added 2026-07-29
# to close the atlas gap; muni sector mapping mirrors detectors/dispatch_index.py.
APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": [],
    "issuer_features": ["k12_district_obligor"],
    "asset_classes": ["ca_k12_school_district_go", "ca_school_go_muni", "ca_k12_muni"],
    "applies_universally": False,
    "kind": "detector",
    "summary": "California County Office of Education (COE) fiscal certification detector",
}

VALID_STATUS = {"POSITIVE", "QUALIFIED", "NEGATIVE"}
SENTINEL_STRINGS = {"UNVERIFIABLE", "UNKNOWN", "N/A", "NONE", ""}
TRAILING_WINDOW_QUARTERS = 4


def _normalize_status(s):
    if s is None:
        return None
    if not isinstance(s, str):
        return None
    su = s.strip().upper()
    if su in SENTINEL_STRINGS:
        return None
    # Accept single-letter shorthand
    if su == "P":
        return "POSITIVE"
    if su == "Q":
        return "QUALIFIED"
    if su == "N":
        return "NEGATIVE"
    if su in VALID_STATUS:
        return su
    return None


def evaluate(obligor_name: str, data: dict) -> dict:
    certs = data.get("certifications_trailing_8q") or []
    fcmat_active = data.get("fcmat_involvement_active")
    state_receiver = data.get("state_receiver_active")
    confidence = (data.get("confidence") or "").upper()

    # INSUFFICIENT_DATA: no certifications array AND no FCMAT/receiver booleans
    if not certs and fcmat_active is None and state_receiver is None:
        return {"fires": False, "reason": "INSUFFICIENT_DATA", "evidence": {}}

    # Sentinel handling on bool fields
    if isinstance(fcmat_active, str):
        fcmat_active = None if fcmat_active.strip().upper() in SENTINEL_STRINGS else fcmat_active
    if isinstance(state_receiver, str):
        state_receiver = None if state_receiver.strip().upper() in SENTINEL_STRINGS else state_receiver

    # Look at the trailing TRAILING_WINDOW_QUARTERS entries (assume sorted newest-first by caller)
    trailing = []
    for c in certs[:TRAILING_WINDOW_QUARTERS]:
        if not isinstance(c, dict):
            continue
        status_norm = _normalize_status(c.get("status"))
        if status_norm is None:
            continue
        trailing.append({
            "period": c.get("period"),
            "status": status_norm,
            "source_url": c.get("source_url"),
        })

    # Guard: if we have no usable certifications AND no boolean signals, refuse to fire
    if not trailing and not fcmat_active and not state_receiver:
        # Distinguish "we looked and they were all positive" from "no data"
        if certs and all(_normalize_status(c.get("status")) == "POSITIVE" for c in certs[:TRAILING_WINDOW_QUARTERS]):
            return {
                "fires": False,
                "reason": "ALL_POSITIVE_TRAILING_4Q",
                "evidence": {
                    "n_certs_reviewed": min(len(certs), TRAILING_WINDOW_QUARTERS),
                    "trailing_periods": [c.get("period") for c in certs[:TRAILING_WINDOW_QUARTERS]],
                },
            }
        return {"fires": False, "reason": "INSUFFICIENT_DATA",
                "evidence": {"confidence": confidence}}

    n_negative = sum(1 for c in trailing if c["status"] == "NEGATIVE")
    n_qualified = sum(1 for c in trailing if c["status"] == "QUALIFIED")
    n_positive = sum(1 for c in trailing if c["status"] == "POSITIVE")

    # State receivership = RED outright
    if state_receiver:
        return {
            "fires": True,
            "reason": "STATE_RECEIVER_ACTIVE",
            "severity": "RED",
            "evidence": {
                "state_receiver_active": True,
                "fcmat_involvement_active": fcmat_active,
                "trailing_certifications": trailing,
                "n_negative_trailing_4q": n_negative,
                "n_qualified_trailing_4q": n_qualified,
                "as_of_date": data.get("as_of_date"),
            },
        }

    # Any Negative in trailing window = RED
    if n_negative >= 1:
        return {
            "fires": True,
            "reason": "NEGATIVE_CERTIFICATION",
            "severity": "RED",
            "evidence": {
                "n_negative_trailing_4q": n_negative,
                "n_qualified_trailing_4q": n_qualified,
                "trailing_certifications": trailing,
                "fcmat_involvement_active": fcmat_active,
                "as_of_date": data.get("as_of_date"),
            },
        }

    # Two or more Qualifieds OR active FCMAT engagement = HIGH (pre-receivership trajectory)
    if n_qualified >= 2 or fcmat_active:
        return {
            "fires": True,
            "reason": "BACK_TO_BACK_QUALIFIED" if n_qualified >= 2 else "FCMAT_ACTIVE_ENGAGEMENT",
            "severity": "HIGH",
            "evidence": {
                "n_qualified_trailing_4q": n_qualified,
                "n_negative_trailing_4q": n_negative,
                "trailing_certifications": trailing,
                "fcmat_involvement_active": fcmat_active,
                "fcmat_engagement_type": data.get("fcmat_engagement_type"),
                "as_of_date": data.get("as_of_date"),
            },
        }

    # Single Qualified = MEDIUM
    if n_qualified >= 1:
        return {
            "fires": True,
            "reason": "SINGLE_QUALIFIED",
            "severity": "MEDIUM",
            "evidence": {
                "n_qualified_trailing_4q": n_qualified,
                "n_positive_trailing_4q": n_positive,
                "trailing_certifications": trailing,
                "as_of_date": data.get("as_of_date"),
            },
        }

    # All Positive (no Q, no N, no FCMAT, no receiver)
    return {
        "fires": False,
        "reason": "ALL_POSITIVE_TRAILING_4Q",
        "evidence": {
            "n_positive_trailing_4q": n_positive,
            "trailing_periods": [c["period"] for c in trailing],
            "as_of_date": data.get("as_of_date"),
        },
    }
