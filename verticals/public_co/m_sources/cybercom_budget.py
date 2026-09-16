"""
USCYBERCOM + service-cyber-SAG budget aggregator.

WHY THIS EXISTS
Cyber Mission Force (CMF) and US Cyber Command (USCYBERCOM) funding does
not live in any single PE line. The 6,200-person CMF construct is
distributed across:
  - Army Cyber Activities - Cyberspace Operations  (Army OP-5 SAG 151)
  - Army Cyber Activities - Cybersecurity          (Army OP-5 SAG 152)
  - Marine Corps Cyberspace Activities             (USMC OP-5 SAG)
  - SOCOM Cyberspace Activities                    (SOCOM OP-5 SAG 1PLS)
  - Navy cyber SAGs                                (Navy OP-5 — see GAPS)
  - Air Force / Space Force cyber SAGs             (AF OP-5 — see GAPS)
  - USCYBERCOM unified appropriation               (post-FY24 — Combatant
                                                    Command Acquisition
                                                    Executive)

Pentagon J-Book queries by individual PE or program_name miss this
because no single record carries "CYBERCOM" or "Cyber Mission Force"
as the program name. This aggregator sums the service cyber SAGs and
adds the USCYBERCOM line where known, producing a trajectory + signal
analogous to pentagon_jbook.

CONTRACTOR ATTRIBUTION
OP-5 SAGs do not list primary contractors. A claim like "BAH supports
CYBERCOM" cannot be verified at the SAG-aggregate level — it requires
cross-reference with usaspending awards under CYBERCOM agency codes or
named cyber IDIQ vehicles (DEFENDER, JCC2, EITAAS-Cyber). This
aggregator returns the budget envelope; contractor-specific
verification is a join on the caller side.

GAPS
v1 covers the OP-5 SAGs ingested through 2026-05-23 (Army, USMC, SOCOM,
Reserves). Navy cyber SAGs are present in OMN_Book.pdf but the v3
parser didn't surface them by trigger; needs a Navy-specific cyber-SAG
re-pass. AF/SF cyber SAGs are blocked by the saffm.hq.af.mil DNS
outage.

SIGNAL ENUM
  FUNDED_GROWING        — aggregate Y-over-Y funding increasing ≥ 15%
  FUNDED_STEADY         — aggregate Y-over-Y stable (±15%)
  FUNDED_SHRINKING      — aggregate Y-over-Y declining ≥ 15%
  COVERAGE_PARTIAL      — < 3 services covered; signal not actionable
  NOT_FOUND             — no cyber SAGs in corpus
"""

from __future__ import annotations

APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": ["737", "366", "367", "873"],
    "issuer_features": ["mentions_dod_program", "mentions_dod_customer"],
    "asset_classes": ["public_equity_forensics"],
    "applies_universally": False,
    "kind": "m_source",
    "summary": "Aggregates USCYBERCOM/service-cyber SAG budget lines to verify cyber-program funding claims.",
}

import json
import re
from pathlib import Path
from typing import Any, Optional

from . import pentagon_jbook

# USCYBERCOM unified appropriation. Empty until ingested. Format mirrors
# OP-5 funding_history: {"FY2025": {"funded_M": ..., "note": "..."}}.
USCYBERCOM_DATA = Path(__file__).parent.parent / "data" / "_jbook_data" / "uscybercom_appropriation.json"

# OP-5 SAGs that constitute the service-level cyber budget envelope.
# Match against program_name (case-insensitive substring). Use specific
# names so we don't sweep in unrelated SAGs (e.g. "Cyber Information
# Operations" should match Army's Cyber Activities SAGs).
_CYBER_SAG_NAME_PATTERNS = (
    "Cyber Activities - Cyberspace Operations",
    "Cyber Activities - Cybersecurity",
    "Cyberspace Activities",
)


def _load_uscybercom() -> dict:
    """USCYBERCOM unified appropriation history. Empty by default."""
    if not USCYBERCOM_DATA.exists():
        return {}
    try:
        return json.loads(USCYBERCOM_DATA.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def _service_cyber_sags(cutoff_year: Optional[int] = None) -> list[dict]:
    """Return all OP-5 SAGs across services that match cyber-mission patterns."""
    data = pentagon_jbook._load()
    matches = []
    for prog in data.get("programs", []):
        if prog.get("exhibit_type") != "OP-5":
            continue
        name = prog.get("program_name") or ""
        if not any(pat.lower() in name.lower() for pat in _CYBER_SAG_NAME_PATTERNS):
            continue
        matches.append(prog)
    return matches


def query_cybercom_envelope(
    cutoff_date: Optional[str] = None,
    contractor_name: Optional[str] = None,
) -> dict[str, Any]:
    """Return aggregated CYBERCOM / cyber-SAG funding envelope.

    Args:
      cutoff_date: ISO YYYY-MM-DD; only consider funding through this FY
        (rear-view enforcement for historical backtests)
      contractor_name: optional company name; if provided, the response
        adds a `_contractor_note` flag — OP-5 SAGs don't carry contractor
        attribution, so any contractor-specific verification must be
        done by joining usaspending awards under CYBERCOM agency codes.

    Returns:
      {
        "envelope_by_fy":      dict mapping "FY2025" -> total $M across services,
        "by_service":          dict mapping service -> {program_name, funding_history},
        "uscybercom_unified":  dict — USCYBERCOM combatant-command appropriation
                                if available; {} otherwise,
        "services_covered":    list of service names with at least one cyber SAG,
        "n_sags":              int — number of cyber SAGs aggregated,
        "trajectory":          recent YoY % change (latest/prior - 1),
        "signal":              FUNDED_GROWING | FUNDED_STEADY | FUNDED_SHRINKING |
                                COVERAGE_PARTIAL | NOT_FOUND,
        "cutoff_year":         int or None,
        "_contractor_note":    string — when contractor_name given,
        "_gaps":               list of strings — known coverage gaps,
      }
    """
    cutoff_year = None
    if cutoff_date:
        try:
            cutoff_year = int(str(cutoff_date)[:4])
        except (ValueError, TypeError):
            cutoff_year = None

    sags = _service_cyber_sags(cutoff_year=cutoff_year)
    if not sags:
        return {
            "envelope_by_fy":     {},
            "by_service":         {},
            "uscybercom_unified": {},
            "services_covered":   [],
            "n_sags":             0,
            "trajectory":         None,
            "signal":             "NOT_FOUND",
            "cutoff_year":        cutoff_year,
            "_gaps":              ["No cyber SAGs in J-Book corpus"],
        }

    # Sum funding by FY across all matched SAGs
    envelope_by_fy: dict[str, float] = {}
    by_service: dict[str, list[dict]] = {}

    for prog in sags:
        svc = prog.get("service") or "UNKNOWN"
        by_service.setdefault(svc, []).append({
            "program_name":    prog.get("program_name"),
            "project":         prog.get("project"),
            "funding_history": prog.get("funding_history", {}),
        })
        for fy_key, v in (prog.get("funding_history") or {}).items():
            m = re.match(r"FY(\d{4})", fy_key)
            if not m:
                continue
            year = int(m.group(1))
            if cutoff_year is not None and year > cutoff_year:
                continue
            amount = v.get("funded_M") if isinstance(v, dict) else None
            if amount is None:
                continue
            envelope_by_fy[fy_key] = envelope_by_fy.get(fy_key, 0.0) + float(amount)

    # Add USCYBERCOM unified appropriation
    uscybercom = _load_uscybercom()
    uscybercom_history = uscybercom.get("funding_history") or {}
    for fy_key, v in uscybercom_history.items():
        m = re.match(r"FY(\d{4})", fy_key)
        if not m:
            continue
        year = int(m.group(1))
        if cutoff_year is not None and year > cutoff_year:
            continue
        amount = v.get("funded_M") if isinstance(v, dict) else None
        if amount is not None:
            envelope_by_fy[fy_key] = envelope_by_fy.get(fy_key, 0.0) + float(amount)

    # Coverage gaps — we expect 6 services in a complete envelope:
    # Army, ARMY-NG, ARMY-Reserve, NAVY, USMC, USCYBERCOM (+ AF/SF when DNS resolves)
    expected_services = {"ARMY", "NAVY", "USMC", "USCYBERCOM"}  # core 4
    present_services = set(by_service.keys())
    if uscybercom:
        present_services.add("USCYBERCOM")
    gaps = []
    for svc in expected_services - present_services:
        gaps.append(f"Missing: {svc} cyber budget")

    # Compute trajectory + signal
    fys = sorted(envelope_by_fy.keys())
    trajectory = None
    if len(fys) >= 2:
        prior = envelope_by_fy[fys[-2]]
        latest = envelope_by_fy[fys[-1]]
        if prior > 0:
            trajectory = (latest / prior) - 1

    if len(present_services) < 3:
        signal = "COVERAGE_PARTIAL"
    elif trajectory is None:
        signal = "FUNDED_STEADY"
    elif trajectory > 0.15:
        signal = "FUNDED_GROWING"
    elif trajectory < -0.15:
        signal = "FUNDED_SHRINKING"
    else:
        signal = "FUNDED_STEADY"

    result = {
        "envelope_by_fy":     envelope_by_fy,
        "by_service":         by_service,
        "uscybercom_unified": uscybercom,
        "services_covered":   sorted(present_services),
        "n_sags":             len(sags),
        "trajectory":         trajectory,
        "signal":             signal,
        "cutoff_year":        cutoff_year,
        "_gaps":              gaps,
    }

    if contractor_name:
        result["_contractor_note"] = (
            f"OP-5 SAGs do not carry contractor attribution. To verify "
            f"{contractor_name}-specific CYBERCOM exposure, cross-reference "
            f"usaspending awards under CYBERCOM agency codes (treasury "
            f"agency 097-9-7-097-00-200) or named cyber IDIQs (DEFENDER, "
            f"JCC2, EITAAS-Cyber). This aggregator returns the budget "
            f"envelope only."
        )

    return result
