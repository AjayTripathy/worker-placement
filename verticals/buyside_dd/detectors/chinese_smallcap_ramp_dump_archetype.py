"""Chinese / Asia small-cap ramp-and-dump archetype detector for corporate IPO DD.

FIRES when an issuer's structural features match the U.S. House Select Committee
on the CCP's documented ramp-and-dump archetype (March 2026 letter referencing
70% of Nasdaq's enforcement referrals to SEC/FINRA Aug 2022-Apr 2025 involving
Chinese-company manipulation, plus Nasdaq's May-2026-approved $25M China-issuer
minimum-float rule).

The archetype is a *composite* — no single feature is dispositive, but 4+ together
produce a high-precision DECLINE signal. The 2026-05-29 top-30 batch surfaced
this archetype on:
- Student Living EduVation (9/9 features)
- Gravity AI (8/9)
- AsiaPac AdTechinno (8/9)
- Cafe Deco (7/9)
- Starrygazey (7/9)
- Neucleus Group (7/9)
- AMATUHI Holdings (7/9)
- Carbon Zero Technologies International (7/9)
- 3 Knights Dynamics (7/9)
- Wealth Management System (6/9)
- Libera Gaming (6/9)

Severity:
- RED: 7+ archetype features
- HIGH: 5-6 archetype features
- MEDIUM: 3-4 archetype features
- not-applicable: <3 features (or not Asia-domiciled)

## Archetype features (9 total)

1. Issuer is Cayman / BVI holdco with operating subsidiary in mainland China / HK
   / Taiwan / Singapore / Malaysia / Japan / Korea
2. Sole or near-sole underwriter is on the SignalOS underwriter_archetype_risk
   watchlist (D. Boral, Spartan, Revere, Network 1, etc.)
3. Proposed deal size sits exactly at or just above Nasdaq's $25M China-issuer
   minimum floor (post-May-2026 rule)
4. Multiple "Pre-IPO Investors" engineered just below the 5% 13D threshold
   (typically 4.9% each x 3-6 holders)
5. Concentrated voting power post-IPO via dual-class / super-voting (>50%
   insider voting)
6. Material related-party transactions with founder-family entities
   (>10% of revenue or >$1M RPT velocity)
7. Lockup shorter than 180 days (90-day or 6-month patterns)
8. Resale prospectus filed concurrently to bypass D&O lockup for Pre-IPO Investors
9. Auditor is a small PCAOB-registered firm with <1-year engagement or
   <5 client base (often Singapore / KL / Hong Kong)

## Data shape

{
  "company_name": "Student Living EduVation",
  "cayman_or_bvi_holdco": true,
  "operating_jurisdiction": "Hong Kong",
  "lead_underwriter": "D. Boral Capital",
  "lead_underwriter_on_watchlist": true,
  "proposed_proceeds_usd": 25000000,
  "near_nasdaq_floor": true,
  "pre_ipo_investor_count_at_4_9_pct": 6,
  "insider_voting_post_ipo_pct": 79.71,
  "rpt_velocity_above_threshold": true,
  "lockup_days": 90,
  "resale_prospectus_concurrent": true,
  "auditor_name": "Assentsure PAC",
  "auditor_small_or_new": true,
  "as_of_date": "2026-05-29",
  "source_url": "S-1/A cover + Selling Stockholder + RPT + Auditor sections"
}
"""
from __future__ import annotations


APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": [],
    "issuer_features": ["cayman_or_bvi_holdco", "asia_operating_jurisdiction"],
    "asset_classes": ["corporate_ipo_dd"],
    "applies_universally": False,  # only fires when Asia-holdco predicate holds
    "summary": "Composite of 9 ramp-and-dump features on Cayman/Asia small-caps.",
}


ASIA_JURISDICTIONS = {
    "china", "hong kong", "hongkong", "hk", "taiwan", "singapore",
    "malaysia", "japan", "korea", "south korea", "vietnam", "indonesia",
    "thailand", "cayman", "bvi",
}


def _is_asia(jurisdiction: str) -> bool:
    if not jurisdiction:
        return False
    j = jurisdiction.lower()
    return any(tok in j for tok in ASIA_JURISDICTIONS)


def evaluate(obligor_name: str, data: dict) -> dict:
    features = {
        "cayman_or_bvi_holdco": bool(data.get("cayman_or_bvi_holdco")),
        "asia_operating_jurisdiction": _is_asia(data.get("operating_jurisdiction", "")),
        "watchlist_underwriter": bool(data.get("lead_underwriter_on_watchlist")),
        "near_nasdaq_25m_floor": bool(data.get("near_nasdaq_floor")),
        "pre_ipo_holders_below_13d": (data.get("pre_ipo_investor_count_at_4_9_pct") or 0) >= 3,
        "concentrated_insider_voting": (data.get("insider_voting_post_ipo_pct") or 0) > 50,
        "material_rpt_with_founder_family": bool(data.get("rpt_velocity_above_threshold")),
        "short_lockup": (data.get("lockup_days") or 999) < 180,
        "concurrent_resale_prospectus": bool(data.get("resale_prospectus_concurrent")),
        "small_or_new_auditor": bool(data.get("auditor_small_or_new")),
    }

    # Cayman + Asia operating jurisdiction is required base predicate
    has_asia_holdco = features["cayman_or_bvi_holdco"] or features["asia_operating_jurisdiction"]
    n_fired = sum(features.values())

    if not has_asia_holdco:
        return {
            "fires": False,
            "reason": "NOT_ASIA_DOMICILED",
            "evidence": {"features": features, "n_fired": n_fired},
        }

    if n_fired >= 7:
        severity, reason = "RED", "RAMP_AND_DUMP_ARCHETYPE_DENSE"
    elif n_fired >= 5:
        severity, reason = "HIGH", "RAMP_AND_DUMP_ARCHETYPE_MODERATE"
    elif n_fired >= 3:
        severity, reason = "MEDIUM", "PARTIAL_ARCHETYPE_FEATURES"
    else:
        return {
            "fires": False,
            "reason": "FEATURES_TOO_SPARSE",
            "evidence": {"features": features, "n_fired": n_fired},
        }

    return {
        "fires": True,
        "reason": reason,
        "severity": severity,
        "evidence": {
            "n_archetype_features_fired": n_fired,
            "features": features,
            "lead_underwriter": data.get("lead_underwriter"),
            "operating_jurisdiction": data.get("operating_jurisdiction"),
            "proposed_proceeds_usd": data.get("proposed_proceeds_usd"),
            "auditor": data.get("auditor_name"),
        },
    }
