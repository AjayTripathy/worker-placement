"""
DOE Office of Science Congressional Budget Justification M-source.

Companion to pentagon_jbook. Where pentagon_jbook reads DoD J-Books,
this reads DOE budget volumes. Same FY-trajectory-derived status enum
so downstream scoring is uniform.

WHY THIS EXISTS
Quantum / advanced-computing / fusion / isotope companies often derive
material revenue from DOE Office of Science programs (ASCR, BES, FES,
HEP, NP) and National Quantum Initiative (NQI) Centers — not from DoD
J-Book PEs. pentagon_jbook returns NOT_FOUND for those claims, masking
real forward-funding signal. This M-source closes that gap.

DATA SOURCE
DOE publishes annual Congressional Budget Justification volumes:
  https://www.energy.gov/cfo/articles/fy-2026-budget-justification
  https://science.osti.gov/budget

The Office of Science volume is the most-relevant for quantum / scientific
computing companies. Other volumes (NNSA, ARPA-E, EM, FE, NE, EERE) can
be added the same way via ingest_doe_budget.py.

V1 IMPLEMENTATION
Programs are LLM-extracted by ingest_doe_budget.py into
data/_doe_data/programs.json. Each entry has the same shape as
pentagon_jbook programs (program_id, program_name, pe_number,
funding_history{FY: {funded_M}}, primary_contractors). The status
enum is derived identically via _latest_funding_status.

STATUS ENUM (signal field)
Same as pentagon_jbook:
  FUNDED_GROWING | FUNDED_STEADY | FUNDED_SHRINKING |
  UNFUNDED_THIS_YEAR | UNFUNDED_TWO_PLUS_YEARS |
  TERMINATED | NOT_FOUND
"""
from __future__ import annotations

APPLIES_TO = {
    "sic_codes": [3674, 3825, 7370, 7371, 7372, 7373, 8731, 2911, 4911, 1311],
    "sic_prefixes": ["367", "382", "737", "873"],
    "issuer_features": [
        "mentions_doe_program",
        "mentions_office_of_science",
        "mentions_ascr",
        "mentions_bes",
        "mentions_fes",
        "mentions_hep",
        "mentions_nnsa",
        "mentions_arpa_e",
        "mentions_nqi",
        "mentions_quantum_initiative",
        "mentions_q_next",
        "mentions_qsa",
        "mentions_c2qa",
        "mentions_qsc",
        "mentions_sqms",
        "mentions_national_lab",
        "government_customer_concentration_above_5pct",
    ],
    "asset_classes": ["corporate_ipo_dd", "public_co_quantum", "public_co_nuclear", "public_co_defense"],
    "applies_universally": False,
    "kind": "m_source",
    "summary": "DOE Office of Science Congressional Budget Justification — forward funding for quantum / fusion / advanced-computing programs.",
    "verification_question": "If the issuer says DOE Office of Science program X / NQI center Y is a material revenue contributor (R), does it appear funded with growing/steady multi-year allocation in the latest DOE budget volume (M)?",
}

import json
import re
from pathlib import Path
from typing import Any, Optional

# Reuse the same status-derivation logic from pentagon_jbook
from .pentagon_jbook import _latest_funding_status

HERE = Path(__file__).parent.parent / "data" / "_doe_data"
DEFAULT_JSON = HERE / "programs.json"

_CACHE: Optional[dict] = None


def _load(p: Optional[Path] = None) -> dict:
    global _CACHE
    path = p or DEFAULT_JSON
    if _CACHE is not None and _CACHE.get("_path") == str(path):
        return _CACHE
    if not path.exists():
        _CACHE = {"_path": str(path), "_meta": {"error": f"no corpus at {path}"},
                   "programs": []}
        return _CACHE
    data = json.loads(path.read_text())
    data["_path"] = str(path)
    _CACHE = data
    return data


def _normalize(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").lower().strip())


def _name_matches(prog: dict, query: str) -> bool:
    q = _normalize(query)
    if not q:
        return False
    candidates = [prog.get("program_name", "")] + (prog.get("synonyms") or [])
    return any(q in _normalize(c) for c in candidates if c)


def _code_matches(prog: dict, code: str) -> bool:
    """Match by doe_program_code (stored in pe_number field)."""
    if not code:
        return False
    pe = prog.get("pe_number") or ""
    return _normalize(code) == _normalize(pe)


def _office_matches(prog: dict, office: str) -> bool:
    """Match by parent_office (stored in agency field)."""
    if not office:
        return False
    return _normalize(office) == _normalize(prog.get("agency") or "")


def _contractor_matches(prog: dict, contractor: str) -> bool:
    if not contractor:
        return False
    c = _normalize(contractor)
    if not c:
        return False
    for pc in (prog.get("primary_contractors") or []):
        if c in _normalize(pc) or _normalize(pc) in c:
            return True
    return False


def query_program_funding(
    program_name: Optional[str] = None,
    doe_program_code: Optional[str] = None,
    parent_office: Optional[str] = None,
    contractor_name: Optional[str] = None,
    qis_only: bool = False,
    cutoff_date: Optional[str] = None,
    json_path: Optional[str] = None,
) -> dict[str, Any]:
    """Look up DOE Office of Science program funding status.

    Args:
      program_name: e.g., "Quantum Information Science", "Advanced Scientific Computing Research"
      doe_program_code: e.g., "ASCR-QIS" (formal code if assigned)
      parent_office: filter by parent ("ASCR", "BES", "FES", "HEP", "NP", "BER")
      contractor_name: company name; returns programs where they appear as primary
      qis_only: if True, only return QIS-relevant programs (qis_relevant=true)
      cutoff_date: ISO YYYY-MM-DD; only consider funding through this year
      json_path: override default _doe_data/programs.json

    Returns:
      Same shape as pentagon_jbook.query_program_funding:
      {matched_programs, n_matches, primary_match, signal, cutoff_year, _note}
    """
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
        if qis_only and not prog.get("qis_relevant"):
            continue
        if program_name and _name_matches(prog, program_name):
            matches.append(prog); continue
        if doe_program_code and _code_matches(prog, doe_program_code):
            matches.append(prog); continue
        if parent_office and _office_matches(prog, parent_office):
            matches.append(prog); continue
        if contractor_name and _contractor_matches(prog, contractor_name):
            matches.append(prog); continue

    if not matches:
        return {
            "matched_programs": [],
            "n_matches":        0,
            "primary_match":    None,
            "signal":           "NOT_FOUND",
            "cutoff_year":      cutoff_year,
            "_note": (
                "No matching DOE program in the corpus. Either the program isn't "
                "in our extracted set yet (run scripts/ingest_doe_budget.py on more "
                "DOE volumes) or the query terms don't match any known name/synonym/"
                "office code."
            ),
        }

    primary = matches[0]
    primary_status = _latest_funding_status(primary, cutoff_year=cutoff_year)
    signal = primary_status["status"]

    priority = {
        "TERMINATED": 6, "UNFUNDED_TWO_PLUS_YEARS": 5,
        "UNFUNDED_THIS_YEAR": 4, "FUNDED_SHRINKING": 3,
        "FUNDED_STEADY": 2, "FUNDED_GROWING": 1,
        "NOT_FOUND_IN_TIMERANGE": 0,
    }
    if len(matches) > 1:
        ranked = sorted(matches, key=lambda p: -priority.get(
            _latest_funding_status(p, cutoff_year=cutoff_year)["status"], 0
        ))
        primary = ranked[0]
        primary_status = _latest_funding_status(primary, cutoff_year=cutoff_year)
        signal = primary_status["status"]

    compact = [{
        "program_id":       p.get("program_id"),
        "program_name":     p.get("program_name"),
        "doe_program_code": p.get("pe_number"),
        "parent_office":    p.get("agency"),
        "qis_relevant":     bool(p.get("qis_relevant")),
        "funding_history":  p.get("funding_history"),
        "primary_contractors": p.get("primary_contractors"),
        "documented_in":    p.get("documented_in"),
    } for p in matches]

    return {
        "matched_programs": compact,
        "n_matches":        len(matches),
        "primary_match":    compact[0] if compact else None,
        "primary_status":   primary_status,
        "signal":           signal if len(matches) == 1 else f"{signal} (primary of {len(matches)} matches)",
        "cutoff_year":      cutoff_year,
        "_note":            f"Matched {len(matches)} DOE program(s); "
                             f"primary: {primary.get('program_name','?')} "
                             f"({primary.get('agency','?')})",
    }
