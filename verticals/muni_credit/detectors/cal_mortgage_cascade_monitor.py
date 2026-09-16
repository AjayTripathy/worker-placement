"""Cal-Mortgage cascade monitor — CA NH/CCRC/small hospital muni only.

FIRES when the HCAI Cal-Mortgage Monthly Activity Report shows recent
bondholder claim payment activity (insurer paid claim on behalf of an insured
facility) AND the obligor under review is itself Cal-Mortgage insured. Claim
payment activity draws down the Health Facility Construction Loan Insurance
Fund (HFCLIF) reserves; multiple claims in a short window can erode insurer
capacity and re-mask risk on ALL other wrapped names simultaneously.

Why predictive: Cal-Mortgage is the dominant masking mechanism for CA NH /
CCRC / small hospital muni — wrapped bonds trade to State of California
AA- credit regardless of operator distress. That wrap is durable IF the
insurer pool is well-capitalized. When the insurer itself faces a claim
cascade (HFCLIF drawdowns, new pipeline defaults), the wrap weakens and
operator-credit signal starts leaking into spread.

This is a SECOND-ORDER detector. It does NOT replace operator-level detectors
(nh_cms_star_rating, ccrc_occupancy, going_concern, etc.) — it modulates
their interpretation. A wrapped name with operator distress + active insurer
cascade is materially worse than the same name in a quiet-claim regime.

Severity ladder:
  HIGH    if claim payment within trailing 6 months AND obligor is wrapped
  MEDIUM  if claim payment 6-18 months prior AND obligor is wrapped
  LOW     if claim payment >18 months prior AND obligor is wrapped
  NO_FIRE if obligor is not Cal-Mortgage insured (cascade is irrelevant
          — naked operator credit; let other detectors do their work)

Cascade sources are the HCAI Cal-Mortgage Monthly Activity Reports
(https://hcai.ca.gov/loans-bonds-grants/cal-mortgage-loan-insurance/) and
the biennial Actuarial Study. Claim payment events appear as:
  - New entries in the "OBLIGATIONS TO CAL-MORTGAGE: Anticipated Recoveries"
    table (loan was paid on behalf of bondholders, recovery is now pending).
  - Loan IDs in the "Summary of Defaulted Loans - Current or in Pipeline"
    case-reserve table (biennial actuarial study).
  - "Shortfall in Debt Service Reserve Funds" table entries.

Data shape:
  {
    "obligor_name": "Bethany Home Society",
    "cal_mortgage_status": "INSURED" | "NOT_INSURED" | "UNVERIFIABLE",
    "commitment_date": "2023-01-31",     # original Cal-Mortgage commitment
    "cascade_signal": {
        "claims_trailing_6mo": 0,
        "claims_trailing_18mo": 1,
        "claim_name": "St. Rose Hospital",
        "claim_amount_usd": 13957324,
        "claim_event_date": "2025-02-01",
        "source_url": "https://hcai.ca.gov/wp-content/uploads/2025/10/Monthly-Report-June-2025-Final-ADA-Compliant.pdf",
        "source_page": "Estimated HFCLIF Balance"
    },
    "as_of_date": "2026-05-28",
    "confidence": "HIGH"
  }

Notes on universe-level state: cascade_signal is essentially a SHARED state
across all wrapped names in the same as-of window — every wrapped name sees
the same insurer-pool drawdown. The detector still must be called per
obligor because (a) only wrapped names should fire and (b) the severity
attribution travels with the obligor's outcome record.
"""
from __future__ import annotations

# Knowledge-graph dispatch contract (see knowledge_graph/dispatch.py). Added 2026-07-29
# to close the atlas gap; muni sector mapping mirrors detectors/dispatch_index.py.
APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": [],
    "issuer_features": ["hospital_obligor", "nursing_home_obligor", "ccrc_obligor", "cal_mortgage_insured"],
    "asset_classes": ["ca_hospital_muni", "healthcare_muni", "ca_chffa_hospital_conduit", "ca_nh_muni", "ca_ccrc_muni", "ccrc_muni"],
    "applies_universally": False,
    "kind": "detector",
    "summary": "Cal-Mortgage cascade monitor — CA NH/CCRC/small hospital muni only.",
}

from datetime import date, datetime


def _parse_date(s):
    if isinstance(s, date):
        return s
    if not s:
        return None
    try:
        return datetime.strptime(s[:10], "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def _months_between(d_old, d_new):
    if d_old is None or d_new is None:
        return None
    return (d_new.year - d_old.year) * 12 + (d_new.month - d_old.month)


def evaluate(obligor_name: str, data: dict) -> dict:
    status = (data.get("cal_mortgage_status") or "").upper()
    if not status:
        return {"fires": False, "reason": "INSUFFICIENT_DATA", "evidence": {}}

    # Cascade only matters for wrapped names. A NOT_INSURED obligor is a
    # naked operator-credit play — other detectors handle it; this one
    # has nothing to add.
    if status == "NOT_INSURED":
        return {
            "fires": False,
            "reason": "NOT_CAL_MORTGAGE_INSURED",
            "evidence": {
                "cal_mortgage_status": "NOT_INSURED",
                "note": "Cascade detector inert; operator credit detectors apply naked.",
            },
        }

    if status == "UNVERIFIABLE":
        # Hostile-validator default: if we cannot verify insurance status from
        # the official statement, we cannot assert that the cascade signal
        # applies. Report but do not fire.
        return {
            "fires": False,
            "reason": "INSURANCE_STATUS_UNVERIFIABLE",
            "evidence": {
                "cal_mortgage_status": "UNVERIFIABLE",
                "note": "Cal-Mortgage status could not be confirmed from primary source.",
            },
        }

    if status != "INSURED":
        return {"fires": False, "reason": "UNKNOWN_STATUS", "evidence": {"status": status}}

    cascade = data.get("cascade_signal") or {}
    n_6mo = cascade.get("claims_trailing_6mo", 0) or 0
    n_18mo = cascade.get("claims_trailing_18mo", 0) or 0

    # No recent cascade activity → the wrap is doing its job; the framework
    # alpha is masked. The detector reports a NEGATIVE finding (informative
    # for downstream composition, not a fire).
    if n_6mo == 0 and n_18mo == 0:
        return {
            "fires": False,
            "reason": "WRAP_INTACT_NO_RECENT_CASCADE",
            "evidence": {
                "cal_mortgage_status": "INSURED",
                "commitment_date": data.get("commitment_date"),
                "claims_trailing_6mo": 0,
                "claims_trailing_18mo": 0,
                "as_of_date": data.get("as_of_date"),
            },
        }

    severity = "LOW"
    if n_6mo >= 1:
        severity = "HIGH"
    elif n_18mo >= 1:
        severity = "MEDIUM"

    return {
        "fires": True,
        "reason": "CAL_MORTGAGE_CASCADE_RECENT",
        "severity": severity,
        "evidence": {
            "cal_mortgage_status": "INSURED",
            "commitment_date": data.get("commitment_date"),
            "claims_trailing_6mo": n_6mo,
            "claims_trailing_18mo": n_18mo,
            "claim_name": cascade.get("claim_name"),
            "claim_amount_usd": cascade.get("claim_amount_usd"),
            "claim_event_date": cascade.get("claim_event_date"),
            "source_url": cascade.get("source_url"),
            "source_page": cascade.get("source_page"),
            "as_of_date": data.get("as_of_date"),
        },
    }
