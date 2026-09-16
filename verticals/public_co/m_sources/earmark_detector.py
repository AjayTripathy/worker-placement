"""
Earmark / political-add detector.

WHY THIS EXISTS
The IONQ short thesis hinges on a specific kind of program funding: not
merit-based Pentagon award but "backdoor earmark" — line items Congress
adds without DoD requesting them, secured by friendly lawmakers. This
type of funding is *fragile*: it survives only as long as the sponsoring
lawmakers retain committee/majority status. When the political backers
lose power, the earmark goes away.

Pentagon J-Books tell you whether a program is FUNDED today (forward
view). usaspending tells you what's been awarded (rear view). Neither
distinguishes "merit-based PE that DoD requested" from "congressional
add that's at risk if sponsors lose power." This connector answers that
question.

CANONICAL CASES
- IONQ AFRL Quantum Networking ($51M FY22-FY24): never requested by
  Pentagon; entirely a congressional add. Sponsors lost majority after
  Nov 2024 election. FY25/FY26: zeroed out. EARMARK_AT_RISK → EARMARK_SUNSET.
- Qubitekk Quantum Networking: similar earmark structure but CA-aligned
  sponsors (Padilla) still in office, just in minority. Earmark was
  renewed in FY26 at lower amount. ROUTINE_EARMARK (current).

SIGNAL ENUM
  NOT_EARMARK              — not in earmark corpus
  ROUTINE_EARMARK          — earmark active; sponsors still in power
  EARMARK_AT_RISK          — earmark active in latest year but sponsors
                              transitioning out (lost majority, retired, etc.)
  EARMARK_SUNSET           — earmark previously active; sponsors lost
                              power; program no longer in current FY
  AMBIGUOUS                — earmark history partial; can't determine

DATA
- data/_earmark_data/earmarks.json — known earmarks linked to programs
- data/_earmark_data/lawmakers.json — lawmaker term/committee/power history

EXTENDING
Add new earmarks by parsing House/Senate Appropriations Defense
Subcommittee committee reports. See scripts/ingest_committee_report.py
for the parser (best-effort; report formats vary).
"""

from __future__ import annotations

APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": ["372", "381", "366", "367", "873"],
    "issuer_features": ["mentions_dod_program", "congressional_earmark_dependence"],
    "asset_classes": ["public_equity_forensics"],
    "applies_universally": False,
    "kind": "detector",
    "summary": "Distinguishes merit-based program funding from fragile congressional earmarks (political-add detection).",
}

import json
import re
from pathlib import Path
from typing import Any, Optional


HERE = Path(__file__).parent.parent / "data" / "_earmark_data"
EARMARKS_JSON = HERE / "earmarks.json"
LAWMAKERS_JSON = HERE / "lawmakers.json"

_EARMARKS_CACHE: Optional[dict] = None
_LAWMAKERS_CACHE: Optional[dict] = None


def _load_earmarks() -> dict:
    global _EARMARKS_CACHE
    if _EARMARKS_CACHE is None:
        _EARMARKS_CACHE = (json.loads(EARMARKS_JSON.read_text())
                           if EARMARKS_JSON.exists()
                           else {"earmarks": []})
    return _EARMARKS_CACHE


def _load_lawmakers() -> dict:
    global _LAWMAKERS_CACHE
    if _LAWMAKERS_CACHE is None:
        _LAWMAKERS_CACHE = (json.loads(LAWMAKERS_JSON.read_text())
                            if LAWMAKERS_JSON.exists()
                            else {"lawmakers": []})
    return _LAWMAKERS_CACHE


def _lookup_lawmaker(lawmaker_id: str) -> Optional[dict]:
    data = _load_lawmakers()
    for lw in data.get("lawmakers", []):
        if lw.get("lawmaker_id") == lawmaker_id:
            return lw
    return None


def _earmark_name_matches(em: dict, query: str) -> bool:
    """Match earmark by program_name or program_id (substring, case-insensitive)."""
    q = query.upper().strip()
    if not q:
        return False
    candidates = [em.get("program_name", ""), em.get("program_id", ""),
                  em.get("earmark_id", "")]
    return any(q in (c or "").upper() or (c or "").upper() in q for c in candidates if c)


def _earmark_pe_matches(em: dict, pe_query: str) -> bool:
    if not pe_query or not em.get("pe_number"):
        return False
    def norm(s: str) -> str:
        s = (s or "").upper().strip()
        s = re.sub(r"^\s*PE\s+", "", s)
        return re.sub(r"[^A-Z0-9]", "", s)
    return norm(pe_query) == norm(em["pe_number"])


def _earmark_program_id_matches(em: dict, program_id: str) -> bool:
    return (em.get("program_id") or "").lower() == (program_id or "").lower()


def _classify_signal(em: dict) -> str:
    """Determine the earmark's current signal from its history + sponsor status."""
    history = em.get("annual_history") or {}
    sponsors_in_power = em.get("sponsors_currently_in_power", None)
    active_now = em.get("active_in_current_fy", None)
    active_recent = em.get("active_in_most_recent_year", None)

    if not history:
        return "AMBIGUOUS"

    # If the latest year(s) are zero AND sponsors out of power → SUNSET
    sorted_years = sorted(history.keys())
    if sorted_years:
        latest = history[sorted_years[-1]]
        latest_add = latest.get("add_M") or latest.get("enacted_M") or 0
        if latest_add == 0:
            if sponsors_in_power is False:
                return "EARMARK_SUNSET"
            return "EARMARK_AT_RISK"  # zero this year, sponsors still around

    # Earmark active in current FY
    if active_now or active_recent:
        if sponsors_in_power is False:
            return "EARMARK_AT_RISK"
        if sponsors_in_power is True:
            return "ROUTINE_EARMARK"
        return "AMBIGUOUS"

    return "AMBIGUOUS"


def _summarize_sponsors(em: dict) -> dict:
    """Compute aggregate sponsor power status across all sponsoring lawmakers."""
    sponsors = em.get("sponsoring_lawmakers") or []
    resolved = []
    n_in_power = 0
    n_lost_power = 0
    losses_at = []
    for s in sponsors:
        lw_id = s.get("lawmaker_id")
        lw = _lookup_lawmaker(lw_id) if lw_id else None
        entry = {
            "lawmaker_id":   lw_id,
            "rationale":     s.get("rationale"),
            "name":          (lw or {}).get("name") if lw else None,
            "party":         (lw or {}).get("party") if lw else None,
            "state":         (lw or {}).get("state") if lw else None,
            "chamber":       (lw or {}).get("chamber") if lw else None,
            "in_power":      (lw or {}).get("currently_in_power") if lw else None,
            "lost_power_at": (lw or {}).get("lost_power_at") if lw else None,
            "lost_power_reason": (lw or {}).get("lost_power_reason") if lw else None,
        }
        resolved.append(entry)
        if entry["in_power"] is True:
            n_in_power += 1
        elif entry["in_power"] is False:
            n_lost_power += 1
            if entry["lost_power_at"]:
                losses_at.append(entry["lost_power_at"])
    return {
        "n_sponsors":         len(sponsors),
        "n_in_power":         n_in_power,
        "n_lost_power":       n_lost_power,
        "all_lost_power":     bool(sponsors) and n_in_power == 0,
        "most_recent_loss":   max(losses_at) if losses_at else None,
        "sponsors_resolved":  resolved,
    }


def query_earmark_status(
    program_name: Optional[str] = None,
    pe_number: Optional[str] = None,
    program_id: Optional[str] = None,
    cutoff_date: Optional[str] = None,
) -> dict[str, Any]:
    """Look up earmark / political-add status for a Pentagon program.

    Args:
      program_name: program name or any partial match against
                    earmark.program_name / program_id / earmark_id
      pe_number:    PE number with or without 'PE ' prefix
      program_id:   exact program_id (the canonical ID used to link
                    earmarks.json ↔ pentagon_jbook programs.json)
      cutoff_date:  ISO YYYY-MM-DD; only consider history through this FY

    Returns:
      {
        "n_matched_earmarks":  int,
        "matched_earmarks":    list of full entries,
        "primary_match":       earmark + sponsor analysis + derived signal,
        "signal":              NOT_EARMARK | ROUTINE_EARMARK | EARMARK_AT_RISK
                                | EARMARK_SUNSET | AMBIGUOUS,
        "cutoff_date":         echo,
      }

    Scorer mapping:
      EARMARK_SUNSET     → SEVERE  (program is gone AND political backers gone)
      EARMARK_AT_RISK    → SEVERE  (program live now but sponsors out → future de-funding likely)
      ROUTINE_EARMARK    → MODERATE (still active, but earmark-funded is forward-fragile)
      AMBIGUOUS          → UNVERIFIABLE
      NOT_EARMARK        → PASS (or UNVERIFIABLE if claim implies political risk)
    """
    data = _load_earmarks()
    matches: list[dict] = []
    for em in data.get("earmarks", []):
        if program_id and _earmark_program_id_matches(em, program_id):
            matches.append(em); continue
        if program_name and _earmark_name_matches(em, program_name):
            matches.append(em); continue
        if pe_number and _earmark_pe_matches(em, pe_number):
            matches.append(em); continue

    if not matches:
        return {
            "n_matched_earmarks": 0,
            "matched_earmarks":   [],
            "primary_match":      None,
            "signal":              "NOT_EARMARK",
            "cutoff_date":         cutoff_date,
            "_note": (
                "No earmark matched the query. Either the program is funded "
                "via regular Pentagon request (not an earmark) OR this "
                "program's earmark isn't in our corpus yet. Extend "
                "data/_earmark_data/earmarks.json or run "
                "scripts/ingest_committee_report.py on a relevant Approps "
                "committee report."
            ),
        }

    primary = matches[0]
    sponsors_info = _summarize_sponsors(primary)
    signal = _classify_signal(primary)

    return {
        "n_matched_earmarks": len(matches),
        "matched_earmarks":   matches,
        "primary_match":      {
            "earmark_id":    primary.get("earmark_id"),
            "program_id":    primary.get("program_id"),
            "program_name":  primary.get("program_name"),
            "agency":        primary.get("agency"),
            "earmark_type":  primary.get("earmark_type"),
            "annual_history": primary.get("annual_history"),
            "sponsors":      sponsors_info,
            "active_now":    primary.get("active_in_current_fy"),
            "active_recent": primary.get("active_in_most_recent_year"),
            "signal":        signal,
        },
        "signal":      signal,
        "cutoff_date": cutoff_date,
    }


if __name__ == "__main__":
    import sys
    q = sys.argv[1] if len(sys.argv) > 1 else "AFRL Quantum Networking"
    print(json.dumps(query_earmark_status(program_name=q), indent=2, default=str))
