"""Land-secured (CFD) developer-bankruptcy / issuer-Ch9 detector.

FIRES when (a) the top property owner / master developer has filed Ch 11, OR
(b) the CFD issuer itself has filed Ch 9, OR (c) the top property owner is
publicly distressed (sub-IG with deteriorating ratings or recent delisting).

Why predictive: direct credit-chain trace. The 2008-2012 CFD distress wave
was driven by Lennar / Pulte / KB Home-tier failures (and many regional
builders) dragging their CFDs down. Ch 9 for the issuer itself is the
strongest possible exclude signal (Diablo Grande CFD 1, Nov 2025).

Public data: CDA top-taxpayer list + Moody's/S&P/Bloomberg corp credit.
Court PACER for Ch 11/9 filings.

CAVEAT — entity resolution: CDA-listed developer is often an LLC ("Castle &
Cooke Mortgage LLC"); parent public-co credit needs separate lookup. Worth
the work for top 20 housing CFDs only.

Data shape:
  {
    "developer_name": "FivePoint Holdings",
    "developer_in_chapter_11": false,
    "issuer_in_chapter_9": false,
    "issuer_ch9_date": null,
    "developer_credit_rating": "B3",
    "developer_rating_outlook": "stable",
    "developer_recent_distress_event": null,
    "as_of_date": "2024-12-31",
    "source": "CDA + Moody's",
    "confidence": "HIGH (when fires)"
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
    "summary": "Land-secured (CFD) developer-bankruptcy / issuer-Ch9 detector.",
}

DISTRESSED_RATINGS = {"CCC+", "CCC", "CCC-", "CC", "C", "D",
                       "Caa1", "Caa2", "Caa3", "Ca", "C"}


def evaluate(obligor_name: str, data: dict) -> dict:
    dev_ch11 = data.get("developer_in_chapter_11")
    issuer_ch9 = data.get("issuer_in_chapter_9")
    rating = (data.get("developer_credit_rating") or "").strip()
    distress_event = data.get("developer_recent_distress_event")

    if dev_ch11 is None and issuer_ch9 is None and not rating and not distress_event:
        return {"fires": False, "reason": "INSUFFICIENT_DATA", "evidence": {}}

    if issuer_ch9:
        return {
            "fires": True,
            "reason": "ISSUER_CHAPTER_9",
            "severity": "RED",
            "evidence": {
                "issuer_ch9_date": data.get("issuer_ch9_date"),
            },
        }
    if dev_ch11:
        return {
            "fires": True,
            "reason": "DEVELOPER_CHAPTER_11",
            "severity": "RED",
            "evidence": {
                "developer_name": data.get("developer_name"),
            },
        }
    if rating in DISTRESSED_RATINGS:
        return {
            "fires": True,
            "reason": "DEVELOPER_DISTRESSED_RATING",
            "severity": "HIGH",
            "evidence": {
                "developer_name": data.get("developer_name"),
                "developer_credit_rating": rating,
            },
        }
    if distress_event:
        return {
            "fires": True,
            "reason": "DEVELOPER_RECENT_DISTRESS_EVENT",
            "severity": "MEDIUM",
            "evidence": {
                "developer_name": data.get("developer_name"),
                "event": distress_event,
            },
        }
    return {
        "fires": False,
        "reason": "DEVELOPER_HEALTHY",
        "evidence": {
            "developer_name": data.get("developer_name"),
            "developer_credit_rating": rating,
        },
    }
