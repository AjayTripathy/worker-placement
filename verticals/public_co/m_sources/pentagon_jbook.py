"""APPLIES_TO declared at module level (see below).

Pentagon J-Book program-funding M-source.

WHY THIS EXISTS
The canonical YSS / IONQ short-thesis pattern is: company derives ~90% of
revenue from a specific Pentagon program; that program is zeroed out in
the next FY budget; the company doesn't disclose the change publicly.
`usaspending` catches rear-view federal awards but cannot see *forward*
budget allocations. The Pentagon's annual J-Books (RDT&E, Procurement,
O&M, etc.) publish per-Program-Element funding tables with multi-year
projections. When a small-cap's named program goes from funded to $0 for
two consecutive J-Books, the customer base is disappearing on a timeline
visible to anyone reading the budget docs — months before the company
acknowledges it in earnings.

DATA SOURCE
J-Books are PDFs released ~annually by each service comptroller:
  - https://www.saffm.hq.af.mil/Budget/  (Air Force / Space Force)
  - https://www.asafm.army.mil/Budget-Materials/  (Army)
  - https://www.secnav.navy.mil/fmc/fmb/Pages/Fiscal-Year-2027.aspx  (Navy)
  - https://comptroller.defense.gov/Budget-Materials/  (OSD aggregate)

V1 IMPLEMENTATION
Programs are stored as hand-extracted JSON in
`data/_jbook_data/programs.json`. The connector matches by program name,
synonyms, PE number, or primary-contractor name and returns the funding
trajectory + a status enum.

Extending: see `data/_jbook_data/README.md`. Eventually
`scripts/ingest_jbook.py` will automate the PDF → JSON extraction; for
now extension is manual.

STATUS ENUM (signal field)
  FUNDED_GROWING         — Y-over-Y funding increasing
  FUNDED_STEADY          — Y-over-Y funding ~stable
  FUNDED_SHRINKING       — funded but declining
  UNFUNDED_THIS_YEAR     — single-year gap (could be CR timing)
  UNFUNDED_TWO_PLUS_YEARS — sustained de-funding (canonical YSS/IONQ signal)
  TERMINATED             — program explicitly killed in J-Book narrative
  NOT_FOUND              — program not in our corpus; UNVERIFIABLE downstream
"""
from __future__ import annotations

APPLIES_TO = {
    "sic_codes": [3812, 3721, 3728, 3669, 7370, 7371, 7372, 7373, 8731, 3674, 3825, 3845],
    "sic_prefixes": ["372", "381", "382", "366", "367", "873"],
    "issuer_features": [
        "mentions_dod_program",
        "mentions_dod_customer",
        "mentions_darpa",
        "mentions_navy",
        "mentions_army",
        "mentions_air_force",
        "mentions_space_force",
        "mentions_nro",
        "government_customer_concentration_above_5pct",
        "primary_contractor_to_dod_prime",
    ],
    "asset_classes": ["corporate_ipo_dd", "public_co_defense", "public_co_space", "public_co_quantum"],
    "applies_universally": False,
    "kind": "m_source",
    "summary": "Pentagon J-Book per-program funding trajectory — surfaces YSS/IONQ short-thesis pattern (R/M gap).",
    "verification_question": "If the issuer says program X is a material revenue contributor (R), does X appear funded with growing/steady multi-year forward allocation in the latest Pentagon J-Book (M)?",
}

import json
import re
from pathlib import Path
from typing import Any, Optional

HERE = Path(__file__).parent.parent / "data" / "_jbook_data"
DEFAULT_JSON = HERE / "programs.json"

_CACHE: Optional[dict] = None


def _load(json_path: Optional[Path] = None) -> dict:
    """Load + cache the J-Book program corpus."""
    global _CACHE
    if _CACHE is not None:
        return _CACHE
    p = Path(json_path) if json_path else DEFAULT_JSON
    if not p.exists():
        return {"programs": [], "_meta": {"error": f"corpus not found at {p}"}}
    _CACHE = json.loads(p.read_text())
    return _CACHE


def _name_matches(prog: dict, query: str) -> bool:
    """Loose match against program_name + synonyms (case-insensitive substring)."""
    q = query.upper().strip()
    if not q:
        return False
    candidates = [prog.get("program_name", "")] + (prog.get("synonyms") or [])
    return any(q in (c or "").upper() or (c or "").upper() in q for c in candidates if c)


def _pe_matches(prog: dict, pe_query: str) -> bool:
    """Match Program Element number with permissive normalization.
    Strips 'PE' prefix, 'Project' prefix, whitespace, dashes, dots."""
    if not pe_query or not prog.get("pe_number"):
        return False
    def norm(s: str) -> str:
        s = (s or "").upper().strip()
        s = re.sub(r"^\s*(PE|PROJECT|PROJ)\s*[:.\-]?\s*", "", s)
        return re.sub(r"[^A-Z0-9]", "", s)
    return norm(pe_query) == norm(prog["pe_number"])


def _contractor_matches(prog: dict, contractor: str) -> bool:
    """Match against primary_contractors list."""
    if not contractor:
        return False
    c = contractor.upper().strip()
    return any(c in (pc or "").upper() or (pc or "").upper() in c
                for pc in (prog.get("primary_contractors") or []))


def _latest_funding_status(prog: dict, cutoff_year: Optional[int] = None) -> dict:
    """Derive {status, n_consecutive_unfunded, latest_funded_year, latest_funded_M}
    from a program's funding_history. cutoff_year limits to FYs at or before."""
    fh = prog.get("funding_history") or {}
    # Parse FY keys → year ints, ignore non-FY entries
    rows = []
    for k, v in fh.items():
        m = re.search(r"FY(\d{4})", k)
        if not m:
            # e.g. "FY2022-2024" — pick the latest year
            m2 = re.findall(r"\d{4}", k)
            if m2:
                year = max(int(y) for y in m2)
            else:
                continue
        else:
            year = int(m.group(1))
        if cutoff_year is not None and year > cutoff_year:
            continue
        funded = v.get("funded_M")
        rows.append((year, funded, v.get("note", "")))
    rows.sort()

    if not rows:
        return {"status": "NOT_FOUND_IN_TIMERANGE",
                "n_consecutive_unfunded": 0,
                "latest_funded_year": None,
                "latest_funded_M": None,
                "history_rows": []}

    # Find consecutive unfunded years at the tail (where funded_M == 0)
    n_consec_unfunded = 0
    for year, funded, _ in reversed(rows):
        if funded == 0:
            n_consec_unfunded += 1
        else:
            break

    # Find latest funded year
    latest_funded_year = None
    latest_funded_M = None
    for year, funded, _ in reversed(rows):
        if funded and funded > 0:
            latest_funded_year = year
            latest_funded_M = funded
            break

    # Status determination
    declared = prog.get("status")
    if declared == "TERMINATED":
        status = "TERMINATED"
    elif n_consec_unfunded >= 2:
        status = "UNFUNDED_TWO_PLUS_YEARS"
    elif n_consec_unfunded == 1:
        status = "UNFUNDED_THIS_YEAR"
    else:
        # Look at trajectory of funded years
        funded_rows = [(y, f) for y, f, _ in rows if f and f > 0]
        if len(funded_rows) >= 2:
            recent = funded_rows[-1][1]
            prior = funded_rows[-2][1]
            if recent > prior * 1.15:
                status = "FUNDED_GROWING"
            elif recent < prior * 0.85:
                status = "FUNDED_SHRINKING"
            else:
                status = "FUNDED_STEADY"
        elif funded_rows:
            status = "FUNDED_STEADY"
        else:
            status = "NOT_FOUND_IN_TIMERANGE"

    return {
        "status":                  status,
        "n_consecutive_unfunded":  n_consec_unfunded,
        "latest_funded_year":      latest_funded_year,
        "latest_funded_M":         latest_funded_M,
        "history_rows":            [{"fy": y, "funded_M": f, "note": n}
                                     for y, f, n in rows],
    }


# ---------------------------------------------------------------------------
# Contractor cross-reference (reverse lookup: company -> J-Book programs)
# ---------------------------------------------------------------------------
_XWALK_PATH = Path(__file__).parent.parent / "data" / "_entity_resolution" / "ticker_pe_crosswalk.json"
_STOP = {"the", "of", "and", "for", "to", "a", "an", "system", "systems",
         "program", "programs", "support", "advanced", "joint", "new"}


def _load_crosswalk() -> dict:
    """The pre-built LLM ticker->PE crosswalk (data/_entity_resolution)."""
    try:
        d = json.loads(_XWALK_PATH.read_text())
        return d.get("tickers", d) if isinstance(d, dict) else {}
    except Exception:
        return {}


def _crosswalk_entry(xwalk: dict, key: str) -> Optional[dict]:
    if not key:
        return None
    ku = key.upper().strip()
    if ku in xwalk:
        return xwalk[ku]
    for e in xwalk.values():
        if (e.get("ticker") or "").upper() == ku or ku in (e.get("name") or "").upper():
            return e
    return None


def _program_by_pe(programs: list, pe: str) -> Optional[dict]:
    return next((p for p in programs if _pe_matches(p, pe)), None) if pe else None


def _name_in_text(program_name: str, text: str) -> Optional[str]:
    """Best-effort match of a J-Book program name in award-description text. Requires the
    FULL program name as a contiguous substring (high precision — scattered-token matching
    over-fired on generic names like 'Field Logistics'). Returns a confidence label or
    None: 'high' when the name carries a distinctive designator (MQ-25, F-35, a digit),
    'medium' for a specific multi-word phrase, else None (too generic to trust)."""
    pn = re.sub(r"\s+", " ", (program_name or "").strip().lower())
    t = re.sub(r"\s+", " ", (text or "").lower())
    if len(pn) < 5:
        return None
    distinctive = bool(re.search(r"\d|[a-z]+-[a-z0-9]", pn))   # MQ-25, F-35, B-21, has a number
    if distinctive:
        return "high" if re.search(r"\b" + re.escape(pn) + r"\b", t) else None
    # non-distinctive: require the full phrase contiguously AND >=2 specific tokens
    if pn in t:
        specific = [w for w in re.findall(r"[a-z0-9\-]{4,}", pn) if w not in _STOP]
        return "medium" if len(specific) >= 2 else None
    return None


def query_by_contractor(contractor_name: str, *, ticker: Optional[str] = None,
                        cutoff_date: Optional[str] = None, live: bool = True,
                        json_path: Optional[str] = None) -> dict[str, Any]:
    """Reverse lookup: a company -> the J-Book programs it likely funds, with funding
    trajectory + its DoD award footprint. Bridges two ways:
      (1) the pre-built LLM ticker_pe_crosswalk (PE-level, high fidelity), and
      (2) a LIVE USAspending pull of the recipient's DoD contracts -> heuristic
          program-name match against the corpus, plus the $ obligated footprint.
    USAspending does not expose PE on awards, so (2) is best-effort; full PE mapping
    across the expanded corpus needs the LLM crosswalk re-run."""
    data = _load(Path(json_path) if json_path else None)
    programs = data.get("programs", [])
    cutoff_year = int(str(cutoff_date)[:4]) if cutoff_date else None
    matched: dict[str, dict] = {}

    def _add(prog, source, confidence, evidence=None):
        pid = prog.get("program_id")
        if pid in matched:
            matched[pid]["sources"].add(source)
            return
        st = _latest_funding_status(prog, cutoff_year=cutoff_year)
        matched[pid] = {
            "program_id": pid, "program_name": prog.get("program_name"),
            "pe_number": prog.get("pe_number"), "service": prog.get("service"),
            "status": st["status"], "latest_funded_year": st["latest_funded_year"],
            # NB: the PROGRAM's funding (the contractor is one of possibly many primes) —
            # NOT this contractor's award. Their award $ is dod_award_total_M at top level.
            "program_funded_M": st["latest_funded_M"],
            "match_confidence": confidence, "sources": {source}, "evidence": evidence,
        }

    # (1) pre-built crosswalk (LLM PE inference — treat as high confidence)
    entry = _crosswalk_entry(_load_crosswalk(), ticker or contractor_name)
    for pe in (entry or {}).get("matched_pes", []):
        pen = pe.get("pe_number") if isinstance(pe, dict) else pe
        prog = _program_by_pe(programs, pen)
        if prog:
            _add(prog, "crosswalk", "high", evidence="LLM PE crosswalk")

    # (2) live USAspending DoD footprint + description match
    usas = None
    if live:
        try:
            from . import usaspending
            usas = usaspending.query_dod_contracts(contractor_name)
        except Exception:
            usas = None
    if usas and not usas.get("error"):
        joined = " || ".join((a.get("Description") or "") for a in usas.get("top_awards", []))
        for prog in programs:
            conf = _name_in_text(prog.get("program_name", ""), joined)
            if conf:
                _add(prog, "usaspending_desc", conf, evidence="contract-description match")

    _rank = {"high": 2, "medium": 1, "low": 0}
    out = sorted(matched.values(),
                 key=lambda m: (_rank.get(m["match_confidence"], 0), m["program_funded_M"] or 0),
                 reverse=True)
    for m in out:
        m["sources"] = sorted(m["sources"])
    return {
        "contractor": contractor_name, "ticker": ticker,
        "dod_award_total_M": round((usas or {}).get("total_amount", 0) / 1e6, 2) if usas else None,
        "dod_n_awards": (usas or {}).get("n_awards") if usas else None,
        "dod_agencies": (usas or {}).get("agencies") if usas else None,
        "n_programs_matched": len(out),
        "programs": out,
        "signal": ("CONTRACTOR_PROGRAMS_FOUND" if out else
                   "DOD_PRESENCE_NO_PROGRAM_LINK" if (usas and usas.get("n_awards")) else
                   "NO_DOD_PRESENCE"),
        "_note": ("Reverse lookup via pre-built PE crosswalk + live USAspending award "
                  "matching (best-effort; USAspending omits PE, so program links are "
                  "name-heuristic unless present in the LLM crosswalk)."),
    }


def query_program_funding(
    program_name: Optional[str] = None,
    pe_number: Optional[str] = None,
    contractor_name: Optional[str] = None,
    cutoff_date: Optional[str] = None,
    json_path: Optional[str] = None,
) -> dict[str, Any]:
    """Look up Pentagon J-Book funding status for a named program.

    Args:
      program_name: e.g., "Tranche 3 Transport Layer", "AFRL Quantum Networking"
      pe_number: e.g., "1206410SF" or "PE 1203636SF"
      contractor_name: company name; returns all programs they're a primary contractor on
      cutoff_date: ISO YYYY-MM-DD; only consider funding through this year
                   (rear-view enforcement for historical backtests)
      json_path: override default _jbook_data/programs.json

    Returns:
      {
        "matched_programs":    list of compact program records,
        "n_matches":           int,
        "primary_match":       most-relevant record (first match) with status,
        "signal":              FUNDED_GROWING | FUNDED_STEADY | FUNDED_SHRINKING |
                                UNFUNDED_THIS_YEAR | UNFUNDED_TWO_PLUS_YEARS |
                                TERMINATED | NOT_FOUND | MULTIPLE_PROGRAMS,
        "cutoff_year":         int or None,
        "_note":               human explainer,
      }

    Signal mapping for the deterministic scorer:
      FUNDED_GROWING        → PASS
      FUNDED_STEADY         → PASS
      FUNDED_SHRINKING      → MODERATE_UNDERDELIVERY
      UNFUNDED_THIS_YEAR    → MODERATE_UNDERDELIVERY (could be CR timing)
      UNFUNDED_TWO_PLUS_YEARS → SEVERE_UNDERDELIVERY (canonical YSS/IONQ signal)
      TERMINATED            → RED_FLAG_NEGATIVE
      NOT_FOUND             → UNVERIFIABLE
    """
    # A pure contractor query is a REVERSE lookup (company -> its programs) — route it
    # to the cross-reference (crosswalk + live USAspending), since auto-ingested entries
    # have no primary_contractors to match against directly.
    if contractor_name and not program_name and not pe_number:
        return query_by_contractor(contractor_name, cutoff_date=cutoff_date, json_path=json_path)

    data = _load(Path(json_path) if json_path else None)
    if "error" in (data.get("_meta") or {}):
        return {"error": data["_meta"]["error"],
                "n_matches": 0, "matched_programs": [],
                "signal": "NOT_FOUND"}

    cutoff_year: Optional[int] = None
    if cutoff_date:
        try:
            cutoff_year = int(str(cutoff_date)[:4])
        except (ValueError, TypeError):
            cutoff_year = None

    matches = []
    for prog in data.get("programs", []):
        if program_name and _name_matches(prog, program_name):
            matches.append(prog)
            continue
        if pe_number and _pe_matches(prog, pe_number):
            matches.append(prog)
            continue
        if contractor_name and _contractor_matches(prog, contractor_name):
            matches.append(prog)
            continue

    if not matches:
        return {
            "matched_programs": [],
            "n_matches":        0,
            "primary_match":    None,
            "signal":           "NOT_FOUND",
            "cutoff_year":      cutoff_year,
            "_note": (
                "No matching program in the J-Book corpus. Either the program is not "
                "in our hand-extracted set yet (extend data/_jbook_data/programs.json) "
                "or the query terms don't match any known name/synonym/PE number."
            ),
        }

    # Build compact summaries with derived status
    primary = matches[0]
    primary_status = _latest_funding_status(primary, cutoff_year=cutoff_year)
    signal = primary_status["status"]

    # If multiple programs match, prefer the one whose status is most actionable
    # (UNFUNDED_TWO_PLUS_YEARS > UNFUNDED_THIS_YEAR > SHRINKING > others)
    priority = {
        "TERMINATED": 6, "UNFUNDED_TWO_PLUS_YEARS": 5,
        "UNFUNDED_THIS_YEAR": 4, "FUNDED_SHRINKING": 3,
        "FUNDED_STEADY": 2, "FUNDED_GROWING": 1,
        "NOT_FOUND_IN_TIMERANGE": 0,
    }
    if len(matches) > 1:
        ranked = sorted(matches, key=lambda p: -priority.get(
            _latest_funding_status(p, cutoff_year=cutoff_year).get("status", ""), 0
        ))
        primary = ranked[0]
        primary_status = _latest_funding_status(primary, cutoff_year=cutoff_year)
        signal = primary_status["status"]

    compact = lambda p: {
        "program_id":          p.get("program_id"),
        "program_name":        p.get("program_name"),
        "pe_number":           p.get("pe_number"),
        "agency":              p.get("agency"),
        "service":             p.get("service"),
        "primary_contractors": p.get("primary_contractors"),
        "earmark_secured":     p.get("earmark_secured", False),
        "sole_source":         p.get("sole_source", False),
        "replacement_program": p.get("replacement_program"),
        "replacement_sole_source": p.get("replacement_sole_source"),
        "status_declared":     p.get("status"),
    }

    return {
        "matched_programs": [compact(p) for p in matches],
        "n_matches":        len(matches),
        "primary_match":    {**compact(primary), **primary_status},
        "signal":           signal,
        "cutoff_year":      cutoff_year,
        "_note":            primary.get("description", ""),
    }


if __name__ == "__main__":
    import sys
    q = sys.argv[1] if len(sys.argv) > 1 else "Tranche 3 Transport Layer"
    print(json.dumps(query_program_funding(program_name=q), indent=2, default=str))
