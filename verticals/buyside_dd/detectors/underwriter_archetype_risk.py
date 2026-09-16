"""Underwriter archetype risk detector for corporate IPO DD.

FIRES when the lead / sole underwriter is on the SignalOS bad-actor watchlist:
firms with active FINRA AWC sanctions, U.S. House Select Committee on the CCP
investigations, or documented patterns of ramp-and-dump / pump-and-dump
facilitation on small-cap foreign IPOs.

The 2026 YTD top-30 IPO run surfaced this archetype repeatedly: 8 of 14 sub-
$100M DECLINE verdicts had underwriters from this watchlist. The pattern is
high-precision — underwriter quality alone correctly predicted DECLINE for
these names even before fundamental analysis.

Severity:
- RED: sole underwriter on watchlist (no syndicate diversification)
- HIGH: lead underwriter on watchlist with non-watchlist co-managers
- MEDIUM: watchlist underwriter in syndicate but not lead

The watchlist is sourced from public records:
- FINRA AWCs (Acceptance, Waiver, and Consent letters)
- U.S. House Select Committee on the CCP referrals
- SEC/PCAOB enforcement actions against underwriter or its parent
- Bloomberg / Renaissance Capital documented small-cap IPO performance

Live catches (2026-05-29 batch):
- D. Boral Capital: HSC-China probe (March 2026) — Student Living EduVation, Libera Gaming
- Spartan Capital Securities: FINRA fraud complaint (Dec 2024) — AMATUHI
- Revere Securities + Dominari Securities: HSC-China probe — Gravity AI
- Network 1 Financial Securities: FINRA AML/supervision AWC — 3 Knights Dynamics, Neucleus
- Maxim Group: consistent Donovan-Jones "sell" pattern — AsiaPac AdTechinno
- Pacific Century Securities: serially-renamed broker-dealer — Starrygazey
- Blue Diamond Securities: 6-name Asia micro-cap track record — Wealth Management System
- Ninth Eternity Securities: 13-amendment / 30-month registrations — Carbon Zero
- Boustead Securities: typical China/HK micro-cap shop (Libera initial U/W before D. Boral)

## Data shape

{
  "company_name": "Student Living EduVation",
  "lead_underwriter": "D. Boral Capital",
  "sole_underwriter": true,                  # if applicable
  "syndicate_members": ["D. Boral Capital"], # full list
  "as_of_date": "2026-05-29",
  "source_url": "S-1/A cover page"
}
"""
from __future__ import annotations

APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": [],
    "issuer_features": [],
    "asset_classes": ["corporate_ipo_dd"],
    "applies_universally": True,  # underwriter quality is universal IPO signal
    "summary": "Lead/sole underwriter on the FINRA/HSC-China/SEC-PCAOB watchlist.",
}

# Public-record-sourced watchlist as of 2026-05-29.
# Keys are case-insensitive substrings to allow loose matching ("D. Boral Capital LLC"
# matches "d. boral").
WATCHLIST = {
    "d. boral capital":         {"reason": "U.S. House Select Committee on the CCP probe March 2026 — facilitating ramp-and-dump on small-cap Chinese/HK IPOs", "tier": "RED"},
    "d boral":                  {"reason": "U.S. House Select Committee on the CCP probe March 2026", "tier": "RED"},
    "spartan capital":          {"reason": "FINRA fraud complaint Dec 2024 (CEO Lowry + ex-CCO Monchik named); ~$24M customer claims vs <$6M net capital", "tier": "RED"},
    "revere securities":        {"reason": "U.S. House Select Committee on the CCP probe March 2026", "tier": "RED"},
    "dominari securities":      {"reason": "Documented first-day-pump-then-fade pattern on small-cap APAC IPOs", "tier": "HIGH"},
    "network 1":                {"reason": "FINRA AWC AML/supervision failures specifically on small-cap Asia IPOs; last 6 issuer clients down 27-99%", "tier": "RED"},
    "maxim group":              {"reason": "Consistent independent-analyst (Donovan Jones) 'sell' on its China/HK micro-cap pipeline; same firm running ramp-and-dump archetypes", "tier": "HIGH"},
    "pacific century securities": {"reason": "Serially-renamed micro broker-dealer (fka Ambata / Vision Fuel / Gyre); prior F-1 cohort required 1:12-1:90 reverse splits", "tier": "RED"},
    "blue diamond securities":  {"reason": "Six known issuer clients are similar Asia micro-cap shells with insider cash-out structures", "tier": "HIGH"},
    "ninth eternity":           {"reason": "13-amendment / 30-month registration sequences typical; M2 Compliance filer agent", "tier": "HIGH"},
    "boustead securities":      {"reason": "Frequent original-then-replaced underwriter on China/HK micro-caps with ramp-and-dump features", "tier": "HIGH"},
    "rbw capital":              {"reason": "Listing-advisor + shareholder + placement-agent conflict pattern (First Breach 2026-05-27)", "tier": "MEDIUM"},
}


def _match_watchlist(name: str):
    if not name:
        return None
    n = name.lower()
    for key, info in WATCHLIST.items():
        if key in n:
            return key, info
    return None


def evaluate(obligor_name: str, data: dict) -> dict:
    lead = (data.get("lead_underwriter") or "").strip()
    sole = bool(data.get("sole_underwriter"))
    syndicate = data.get("syndicate_members") or ([lead] if lead else [])

    lead_match = _match_watchlist(lead)
    syndicate_matches = []
    for m in syndicate:
        h = _match_watchlist(m)
        if h:
            syndicate_matches.append((m, h))

    if not lead_match and not syndicate_matches:
        return {
            "fires": False,
            "reason": "NO_WATCHLIST_UNDERWRITER",
            "evidence": {"lead_underwriter": lead, "syndicate_size": len(syndicate)},
        }

    if lead_match and sole:
        severity = "RED"
        reason = "SOLE_UNDERWRITER_ON_WATCHLIST"
    elif lead_match:
        severity = lead_match[1]["tier"]
        reason = "LEAD_UNDERWRITER_ON_WATCHLIST"
    else:
        severity = "MEDIUM"
        reason = "SYNDICATE_MEMBER_ON_WATCHLIST_NOT_LEAD"

    matched_entries = ([("LEAD", lead, lead_match)] if lead_match else []) + \
                      [("SYNDICATE", m, h) for (m, h) in syndicate_matches]
    matched_names = [m for _, m, _ in matched_entries]
    matched_reasons = [h[1]["reason"] for _, _, h in matched_entries]

    return {
        "fires": True,
        "reason": reason,
        "severity": severity,
        "evidence": {
            "lead_underwriter": lead,
            "is_sole_underwriter": sole,
            "matched_underwriters": matched_names,
            "watchlist_reasons": matched_reasons,
            "syndicate_size": len(syndicate),
        },
    }
