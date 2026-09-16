"""
DOL OFLC H-1B Labor Condition Application (LCA) Disclosure connector.

The Office of Foreign Labor Certification publishes every H-1B LCA
filing quarterly. The data covers:

  - Employer name + EIN (FEIN) + NAICS code
  - Worksite address (line1, city, state, zip)
  - **Number of workers requested at this worksite** (operational scope)
  - Job title + SOC code
  - Wage offer + prevailing wage + wage level (I-IV)
  - Decision date + period of employment

Why it's the highest-leverage gap closer in the taxonomy:
  - Free, structured, ~2M LCAs/year
  - Per-worksite-address — directly maps to claimed facility
  - Sub-20-employee operations that miss OSHA Form 300A often still
    file H-1B LCAs (immigration sponsorship doesn't have a headcount
    threshold)
  - Tech / drone / biotech / semi / SaaS are H-1B-dense — the four
    industries where OSHA Form 300A under-covers
  - SOC code + job title = direct evidence of what kind of work the
    company actually does at the named site

Schema of the slim CSV:
  case_status, decision_date, visa_class, job_title, soc_title,
  total_worker_positions, employer_name, employer_fein, naics_code,
  worksite_workers, worksite_address1, worksite_city, worksite_state,
  wage_from, wage_to, wage_unit

Data refresh: download per-quarter xlsx from
https://www.dol.gov/agencies/eta/foreign-labor/performance, then run
the slim-CSV extractor script (see scripts/extract_lca_slim.py for
the one-shot conversion). Mirror is gitignored under
verticals/public_co/data/_dol_data/.

Coverage gaps to remember:
  - LCA != actual hire. LCAs are PRE-FILED before petitioning USCIS.
    A high LCA count is corroboration of intent + ability to pay,
    not of confirmed headcount.
  - LCAs are required only for foreign-worker hiring. Companies with
    100% US-citizen workforces won't appear regardless of size.
  - Cap-exempt employers (universities, gov't, nonprofit research)
    file with different rules.
  - Multi-worksite LCAs report aggregate WORKSITE_WORKERS but assign
    them to a primary worksite.
"""

from __future__ import annotations

APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": [],
    "issuer_features": ["facility_scale_claim"],
    "asset_classes": ["public_equity_forensics"],
    "applies_universally": False,
    "kind": "m_source",
    "summary": "DOL H-1B LCA disclosures; per-worksite worker counts verify claimed operational scope.",
}

import csv
import re
from pathlib import Path
from typing import Any, Optional

HERE = Path(__file__).parent.parent / "data" / "_dol_data"
DEFAULT_CSV = HERE / "LCA_FY2024_Q4_slim.csv"

_CACHE: list[dict] | None = None


def _load(csv_path: Optional[Path] = None) -> list[dict]:
    """Load + cache slim LCA records. ~30MB, 600k rows."""
    global _CACHE
    if _CACHE is not None:
        return _CACHE
    p = Path(csv_path) if csv_path else DEFAULT_CSV
    if not p.exists():
        return []
    rows = []
    with open(p, newline="", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)
    _CACHE = rows
    return rows


def query_lca_filings(
    employer_name: Optional[str] = None,
    fein: Optional[str] = None,
    naics_prefix: Optional[str] = None,
    city: Optional[str] = None,
    state: Optional[str] = None,
    address_substr: Optional[str] = None,
    soc_prefix: Optional[str] = None,
    only_certified: bool = True,
    csv_path: Optional[str] = None,
    match_mode: str = "word_boundary",
    max_results: int = 50,
    cutoff_date: Optional[str] = None,
) -> dict[str, Any]:
    """Search DOL H-1B LCA filings.

    Filters AND together. employer_name defaults to word-boundary
    matching (so 'AIRO' matches 'AIRO GROUP' but not 'CAIRO' or
    'KAIROS'). FEIN is exact-match if provided.

    Returns:
        {
          "n_filings":             int (total before truncation),
          "n_worker_positions":    int (sum of total_worker_positions),
          "n_worksite_workers":    int (sum of worksite_workers, more
                                        worksite-specific than total),
          "by_worksite":           list of {address, city, state, n_LCAs,
                                            n_workers, top_soc}
                                        sorted by n_workers desc,
          "by_naics":              {naics: count, ...},
          "by_soc_title":          {soc: count, ...},
          "matches":               list of records (up to max_results),
          "signal":                NO_LCA_FOOTPRINT | SMALL_SPONSOR |
                                    REGISTERED_H1B_SPONSOR,
        }

    Signal:
      - 0 filings + employer_name provided → NO_LCA_FOOTPRINT
      - n_worker_positions < 10 → SMALL_SPONSOR
      - n_worker_positions >= 10 → REGISTERED_H1B_SPONSOR
    """
    rows = _load(csv_path)
    if not rows:
        return {"error": "DOL H-1B LCA slim CSV not found; download "
                          "quarterly xlsx from dol.gov/agencies/eta/foreign-"
                          "labor/performance and run the slim extractor.",
                "n_filings": 0, "matches": [], "filters": {}}

    # Data-date envelope (independent of name filters): min/max
    # decision_date across the full file. Used to flag pre-cutoff
    # backtests that have no contemporaneous LCA data.
    decision_dates = [(r.get("decision_date") or "")[:10]
                       for r in rows if r.get("decision_date")]
    data_min = min(decision_dates) if decision_dates else None
    data_max = max(decision_dates) if decision_dates else None

    # If a cutoff_date is set, pre-filter rows to decision_date <= cutoff_date.
    # No rows in window → NO_DATA_AT_CUTOFF (cannot adjudicate).
    if cutoff_date:
        cd = str(cutoff_date)[:10]
        rows_in_window = [r for r in rows
                          if (r.get("decision_date") or "")[:10] <= cd
                          and (r.get("decision_date") or "")]
        if not rows_in_window:
            return {
                "n_filings":           0,
                "n_worker_positions":  0,
                "n_worksite_workers":  0,
                "by_worksite":         [],
                "by_naics":            {},
                "by_soc_title":        {},
                "matches":             [],
                "signal":              "NO_DATA_AT_CUTOFF",
                "match_mode":          match_mode,
                "filters": {"employer_name": employer_name, "fein": fein,
                            "naics_prefix": naics_prefix, "city": city,
                            "state": state, "address_substr": address_substr,
                            "soc_prefix": soc_prefix,
                            "cutoff_date": cutoff_date},
                "data_min_date":       data_min,
                "data_max_date":       data_max,
                "cutoff_date_applied": cd,
                "_note":               (f"DOL LCA file has no decisions on or "
                                        f"before {cd}; available date range "
                                        f"is {data_min} → {data_max}. Cannot "
                                        f"retroactively verify H-1B sponsorship "
                                        f"at this cutoff."),
            }
        rows = rows_in_window

    en = (employer_name or "").upper()
    fein_str = (fein or "").strip()
    np = (naics_prefix or "")
    cy = (city or "").upper()
    st = (state or "").upper()
    addr = (address_substr or "").upper()
    sp = (soc_prefix or "")

    # Employer-name matcher
    if en and match_mode == "word_boundary":
        pattern = re.compile(r"\b" + re.escape(en) + r"\b", re.IGNORECASE)
        def _name_ok(name: str) -> bool:
            return bool(pattern.search(name or ""))
    elif en and match_mode == "exact":
        def _name_ok(name: str) -> bool:
            return (name or "").upper() == en
    else:
        def _name_ok(name: str) -> bool:
            return en in (name or "").upper()

    matches: list[dict] = []
    for r in rows:
        if only_certified and (r.get("case_status") or "").upper() != "CERTIFIED":
            continue
        if en and not _name_ok(r.get("employer_name") or ""):
            continue
        if fein_str and (r.get("employer_fein") or "").strip() != fein_str:
            continue
        if np and not (r.get("naics_code") or "").startswith(np):
            continue
        if cy and cy != (r.get("worksite_city") or "").upper():
            continue
        if st and st != (r.get("worksite_state") or "").upper():
            continue
        if addr and addr not in (r.get("worksite_address1") or "").upper():
            continue
        if sp and not (r.get("soc_title") or "").startswith(sp):
            continue
        matches.append(r)

    n = len(matches)

    def _int(x):
        try: return int(x or 0)
        except (TypeError, ValueError): return 0
    n_total = sum(_int(r.get("total_worker_positions")) for r in matches)
    n_site  = sum(_int(r.get("worksite_workers")) for r in matches)

    # Per-worksite breakdown
    by_site: dict[tuple, dict] = {}
    for r in matches:
        key = (r.get("worksite_address1") or "?",
               r.get("worksite_city") or "?",
               r.get("worksite_state") or "?")
        s = by_site.setdefault(key, {"n_lcas": 0, "n_workers": 0,
                                     "soc_counts": {}})
        s["n_lcas"] += 1
        s["n_workers"] += _int(r.get("worksite_workers"))
        soc = r.get("soc_title") or "?"
        s["soc_counts"][soc] = s["soc_counts"].get(soc, 0) + 1
    by_site_list = []
    for (addr_, city_, state_), s in by_site.items():
        top_soc = (max(s["soc_counts"].items(), key=lambda x: x[1])[0]
                   if s["soc_counts"] else "?")
        by_site_list.append({
            "address":   addr_,
            "city":      city_,
            "state":     state_,
            "n_lcas":    s["n_lcas"],
            "n_workers": s["n_workers"],
            "top_soc":   top_soc,
        })
    by_site_list.sort(key=lambda x: -x["n_workers"])

    by_naics: dict[str, int] = {}
    by_soc:   dict[str, int] = {}
    for r in matches:
        nc = (r.get("naics_code") or "?")[:4]
        by_naics[nc] = by_naics.get(nc, 0) + 1
        soc = r.get("soc_title") or "?"
        by_soc[soc] = by_soc.get(soc, 0) + 1

    if n == 0 and employer_name:
        signal = "NO_LCA_FOOTPRINT"
    elif n_total < 10:
        signal = "SMALL_SPONSOR"
    else:
        signal = "REGISTERED_H1B_SPONSOR"

    slim = [{k: r.get(k) for k in
             ("case_status", "decision_date", "employer_name",
              "employer_fein", "naics_code", "worksite_address1",
              "worksite_city", "worksite_state", "worksite_workers",
              "total_worker_positions", "soc_title", "job_title",
              "wage_from", "wage_to")}
            for r in matches[:max_results]]

    return {
        "n_filings":          n,
        "n_worker_positions": n_total,
        "n_worksite_workers": n_site,
        "by_worksite":        by_site_list[:10],
        "by_naics":           dict(sorted(by_naics.items(), key=lambda x: -x[1])[:10]),
        "by_soc_title":       dict(sorted(by_soc.items(),   key=lambda x: -x[1])[:10]),
        "matches":            slim,
        "signal":             signal,
        "match_mode":         match_mode,
        "filters": {"employer_name": employer_name, "fein": fein,
                    "naics_prefix": naics_prefix, "city": city,
                    "state": state, "address_substr": address_substr,
                    "soc_prefix": soc_prefix,
                    "cutoff_date": cutoff_date},
        "data_min_date":      data_min,
        "data_max_date":      data_max,
    }
