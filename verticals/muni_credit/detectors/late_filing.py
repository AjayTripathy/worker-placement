"""Late continuing disclosure filing detector.

FIRES when current date > 270 days post-FYE without the annual audited
financial statement being filed on MSRB EMMA.

Why predictive: SEC Rule 15c2-12 and the obligor's continuing disclosure
agreement (CDA) require annual financial filings within a stated window
(typically 180 days post-FYE for non-state-or-local issuers; often 270 days
in practice with grace periods). Failure to file by 270 days indicates one
of three things: (1) governance breakdown, (2) auditor disagreement (qualified
opinion pending), (3) operational paralysis affecting financial close.

Information asymmetry: many investors don't check EMMA filing dates against
CDA deadlines. By the time the missing filing makes the trade press, the
obligor has often already been downgraded. Lead time vs rating action: ~3-12
months.

Data shape:
  {
    "fiscal_year_end": "2024-06-30",
    "latest_audited_fs_filed_date": "2025-09-15",  # or null if not filed
    "as_of_date": "2026-05-27"  # the date you're running the screen
  }
"""
from __future__ import annotations

# Knowledge-graph dispatch contract (see knowledge_graph/dispatch.py). Added 2026-07-29
# to close the atlas gap; muni sector mapping mirrors detectors/dispatch_index.py.
APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": [],
    "issuer_features": [],
    "asset_classes": ["all_muni"],
    "applies_universally": True,
    "kind": "detector",
    "summary": "Late continuing disclosure filing detector.",
}

from datetime import datetime, timedelta

LATE_THRESHOLD_DAYS = 270


def evaluate(obligor_name: str, data: dict) -> dict:
    fye = data.get("fiscal_year_end")
    latest_filed = data.get("latest_audited_fs_filed_date")
    as_of = data.get("as_of_date") or datetime.utcnow().strftime("%Y-%m-%d")
    confidence = (data.get("confidence") or "").upper()

    if not fye:
        return {"fires": False, "reason": "INSUFFICIENT_DATA", "evidence": {}}

    # Sentinel-string handling: agents sometimes write "UNVERIFIABLE", "UNKNOWN",
    # "N/A" etc. as the filed-date value. Treat these as None to avoid firing
    # MISSING_FILING on data we don't actually have.
    if isinstance(latest_filed, str) and latest_filed.strip().upper() in (
            "UNVERIFIABLE", "UNKNOWN", "N/A", "NONE", ""):
        latest_filed = None

    # CRITICAL data quality guard: if confidence is LOW or there's an explicit
    # _warning, we don't know whether the filing was made — refuse to fire on
    # MISSING_FILING. Only fire when we have HIGH/MEDIUM-confidence verified-missing.
    if not latest_filed:
        if confidence in ("LOW", "") or data.get("_warning"):
            return {"fires": False, "reason": "INSUFFICIENT_DATA",
                    "evidence": {"confidence": confidence, "note": "filing status not verifiable"}}

    try:
        fye_d = datetime.fromisoformat(fye[:10])
        as_of_d = datetime.fromisoformat(as_of[:10])
    except Exception:
        return {"fires": False, "reason": "INSUFFICIENT_DATA", "evidence": {}}

    days_since_fye = (as_of_d - fye_d).days
    if days_since_fye <= LATE_THRESHOLD_DAYS:
        return {
            "fires": False,
            "reason": "WITHIN_DEADLINE",
            "evidence": {"days_since_fye": days_since_fye},
        }

    # Past the deadline — check if filing is there
    if latest_filed:
        try:
            filed_d = datetime.fromisoformat(latest_filed[:10])
            days_to_file = (filed_d - fye_d).days
            if days_to_file <= LATE_THRESHOLD_DAYS:
                return {
                    "fires": False,
                    "reason": "FILED_ON_TIME",
                    "evidence": {
                        "days_since_fye": days_since_fye,
                        "days_to_file": days_to_file,
                    },
                }
            # Filed but late
            return {
                "fires": True,
                "reason": "FILED_LATE",
                "severity": "MEDIUM",
                "evidence": {
                    "days_to_file": days_to_file,
                    "threshold": LATE_THRESHOLD_DAYS,
                    "filed_date": latest_filed,
                },
            }
        except Exception:
            pass

    # Past deadline AND no filing found
    return {
        "fires": True,
        "reason": "MISSING_FILING",
        "severity": "HIGH",
        "evidence": {
            "days_since_fye": days_since_fye,
            "threshold": LATE_THRESHOLD_DAYS,
            "fye": fye,
        },
    }
