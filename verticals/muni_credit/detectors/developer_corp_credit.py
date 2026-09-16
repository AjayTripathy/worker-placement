"""Master-developer corporate-credit deterioration detector for CA land-secured CFDs.

DISTINCT from `developer_bankruptcy.py`:
  - developer_bankruptcy.py fires ONLY on Ch 11 / Ch 9 / deeply-distressed ratings (CCC/Caa/D)
  - THIS detector fires on credit-quality DETERIORATION before bankruptcy:
    - sub-investment-grade rating (BB+/Ba1 or below), OR
    - downgrade in trailing 12 months, OR
    - negative outlook, OR
    - private-developer documented distress event (delinquency, foreclosure, lawsuit, exec turnover)

Why predictive: the 2008-2012 CFD distress wave was preceded by 12-24 months of
corporate-credit deterioration at the master developers (William Lyon BB→B,
Standard Pacific BB→CCC, Beazer BB→B, KB BB+→BB, etc.). Detecting the deterioration
PRE-bankruptcy is the diligence-replication value-add: an analyst at a $1B CA muni
shop would want this monitored quarterly.

DILIGENCE-REPLICATION framing (not alpha-seeking primary):
  - This is the "credit-rating sheet on every master developer" that the diligence
    file requires.
  - Refresh quarterly.
  - Cite source URL for every rating + rating action.
  - NEVER fabricate ratings — mark UNVERIFIABLE if unavailable.

Severity tiers:
  - HIGH:   sub-IG + recent downgrade (trailing 12mo) OR private developer with RED distress
  - MEDIUM: sub-IG stable (no recent downgrade) OR IG with negative outlook OR private STALE_RED
  - LOW:    IG with stable outlook + sub-IG with recent UPGRADE
  - INSUFFICIENT_DATA: no public rating + no distress documentation (private developer)

Data shape (per per-obligor JSON, under `developer_corp_credit` field):
  {
    "developer_name": "FivePoint Holdings",
    "is_public": true,
    "ticker": "FPH",
    "current_credit_rating": "B2",        # composite preferring Moody's > S&P > Fitch
    "rating_agency": "Moody's",
    "rating_outlook": "stable",
    "last_rating_action": "2025-09 upgraded B3->B2",
    "is_sub_ig": true,
    "recent_downgrade_12mo": false,
    "private_distress_event": null,        # only populated for private developers
    "_distress_severity": null,            # one of RED / STALE_RED / null
    "concentration_in_ca_cfd": 1,
    "as_of_date": "2026-05-28",
    "source_url": "https://...",
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
    "summary": "Master-developer corporate-credit deterioration detector for CA land-secured CFDs.",
}


# Sub-IG rating buckets per major agency
SUB_IG_MOODYS = {
    "Ba1", "Ba2", "Ba3", "B1", "B2", "B3",
    "Caa1", "Caa2", "Caa3", "Ca", "C",
}
SUB_IG_SP = {
    "BB+", "BB", "BB-", "B+", "B", "B-",
    "CCC+", "CCC", "CCC-", "CC", "C", "D",
}
SUB_IG_FITCH = SUB_IG_SP  # Fitch uses S&P-compatible scale

DISTRESSED_RATINGS = {
    "CCC+", "CCC", "CCC-", "CC", "C", "D",
    "Caa1", "Caa2", "Caa3", "Ca",
}


def _is_sub_ig(rating: str | None, agency: str | None) -> bool | None:
    if not rating:
        return None
    rating = rating.strip()
    if agency and agency.lower().startswith("moody"):
        return rating in SUB_IG_MOODYS
    # Default S&P/Fitch scale
    return rating in SUB_IG_SP


def _is_distressed(rating: str | None) -> bool:
    if not rating:
        return False
    return rating.strip() in DISTRESSED_RATINGS


def evaluate(obligor_name: str, data: dict) -> dict:
    """Evaluate developer-corp-credit detector against per-obligor data.

    `data` is the `developer_corp_credit` block passed by union_runner
    (which reads data.get(det_name, {})). If data is empty, falls back to
    INSUFFICIENT_DATA.
    """
    # union_runner passes the block directly as data — read fields here.
    # Fallback: if the runner ever passes the full per-CFD JSON, accept that too.
    if "developer_corp_credit" in data and isinstance(data["developer_corp_credit"], dict):
        dcc = data["developer_corp_credit"]
    else:
        dcc = data

    dev_name = dcc.get("developer_name")
    rating = dcc.get("current_credit_rating")
    agency = dcc.get("rating_agency")
    outlook = (dcc.get("rating_outlook") or "").strip().lower()
    last_action = dcc.get("last_rating_action") or ""
    is_public = dcc.get("is_public")
    is_sub_ig = dcc.get("is_sub_ig")
    if is_sub_ig is None:
        is_sub_ig = _is_sub_ig(rating, agency)
    recent_downgrade = dcc.get("recent_downgrade_12mo")
    if recent_downgrade is None:
        # Infer from last_rating_action text
        la = last_action.lower()
        recent_downgrade = ("downgrad" in la) and ("2025" in la or "2026" in la)

    private_event = dcc.get("private_distress_event")
    distress_severity = dcc.get("_distress_severity")

    # INSUFFICIENT_DATA: no developer or no signals at all
    if not dev_name and not rating and not private_event:
        return {
            "fires": False,
            "reason": "INSUFFICIENT_DATA",
            "evidence": {},
        }

    # Private developer with RED distress event (delinquency, foreclosure, lawsuit)
    if private_event and distress_severity == "RED":
        return {
            "fires": True,
            "reason": "PRIVATE_DEVELOPER_RED_DISTRESS",
            "severity": "HIGH",
            "evidence": {
                "developer_name": dev_name,
                "event": private_event,
                "event_date": dcc.get("_distress_event_date"),
                "source_url": dcc.get("source_url") or (dcc.get("source_urls") or [None])[0],
            },
        }

    # Private developer with stale red distress (multi-year-old, lingering)
    if private_event and distress_severity == "STALE_RED":
        return {
            "fires": True,
            "reason": "PRIVATE_DEVELOPER_STALE_DISTRESS",
            "severity": "MEDIUM",
            "evidence": {
                "developer_name": dev_name,
                "event": private_event,
                "event_date": dcc.get("_distress_event_date"),
            },
        }

    # Distressed rating (CCC/Caa/D) — duplicate with developer_bankruptcy.py
    # but kept here for completeness; severity HIGH
    if _is_distressed(rating):
        return {
            "fires": True,
            "reason": "DEVELOPER_DISTRESSED_RATING",
            "severity": "HIGH",
            "evidence": {
                "developer_name": dev_name,
                "rating": rating,
                "agency": agency,
            },
        }

    # Sub-IG + recent downgrade
    if is_sub_ig and recent_downgrade:
        return {
            "fires": True,
            "reason": "DEVELOPER_SUB_IG_RECENT_DOWNGRADE",
            "severity": "HIGH",
            "evidence": {
                "developer_name": dev_name,
                "rating": rating,
                "agency": agency,
                "last_rating_action": last_action,
            },
        }

    # Sub-IG with negative outlook
    if is_sub_ig and outlook == "negative":
        return {
            "fires": True,
            "reason": "DEVELOPER_SUB_IG_NEGATIVE_OUTLOOK",
            "severity": "HIGH",
            "evidence": {
                "developer_name": dev_name,
                "rating": rating,
                "outlook": outlook,
            },
        }

    # Sub-IG stable
    if is_sub_ig:
        return {
            "fires": True,
            "reason": "DEVELOPER_SUB_IG_STABLE",
            "severity": "MEDIUM",
            "evidence": {
                "developer_name": dev_name,
                "rating": rating,
                "agency": agency,
                "outlook": outlook or "stable",
            },
        }

    # IG with negative outlook
    if is_sub_ig is False and outlook == "negative":
        return {
            "fires": True,
            "reason": "DEVELOPER_IG_NEGATIVE_OUTLOOK",
            "severity": "LOW",
            "evidence": {
                "developer_name": dev_name,
                "rating": rating,
                "outlook": outlook,
            },
        }

    # IG stable or no rating concern
    return {
        "fires": False,
        "reason": "DEVELOPER_IG_STABLE_OR_UNRATED_CLEAN",
        "evidence": {
            "developer_name": dev_name,
            "rating": rating,
            "outlook": outlook,
            "is_public": is_public,
        },
    }
