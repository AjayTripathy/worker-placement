"""
OSHA Form 300A Establishment-Specific Summary connector.

OSHA publishes annual CSV extracts of every establishment that filed a
Form 300A injury/illness summary. The 300A is required of any
establishment with >=20 employees in covered industries (most
manufacturing, mining, transportation, healthcare, etc.). The file
contains, per establishment:

  - establishment_name + company_name
  - street_address, city, state, zip
  - naics_code + industry_description
  - **annual_average_employees** (the operational scope proxy)
  - total_hours_worked (cross-check on headcount)

This is what catches scope inflation that EPA misses. A small-cap
claiming "500-person manufacturing facility" should appear in OSHA's
300A summary at the claimed address with ~500 average employees. If
the address has no 300A filing, or the 300A shows 12 employees, that's
a hard contradiction independent of any EPA chemistry threshold.

Coverage gaps:
  1. Establishments with <20 employees aren't required to file 300A
     (so 'no record' at a small claimed facility is uninformative)
  2. Some low-risk industries (offices, banking, software) exempt
  3. R&D-only sites without manufacturing activity may not file
  4. Annual data has typical 6-12 month publication lag

Data file (downloaded from osha.gov/Establishment-Specific-Injury-and-
Illness-Data) is treated as a local mirror. To refresh:

    curl -LO https://www.osha.gov/sites/default/files/ITA_300A_Summary_Data_2024_through_12-31-2025.csv
    mv ITA*.csv verticals/public_co/data/_osha_data/

Roughly 400k establishments per year. Loaded lazily on first query.
"""

from __future__ import annotations

APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": [],
    "issuer_features": ["facility_scale_claim"],
    "asset_classes": ["public_equity_forensics"],
    "applies_universally": False,
    "kind": "m_source",
    "summary": "OSHA 300A establishment summaries; injury-report employee counts verify claimed facility headcount.",
}

import csv
import re
from pathlib import Path
from typing import Any, Optional

HERE = Path(__file__).parent.parent / "data" / "_osha_data"
DEFAULT_CSV = HERE / "ITA_300A_Summary_Data_2024_through_12-31-2025.csv"

_CACHE: list[dict] | None = None


def _load(csv_path: Optional[Path] = None) -> list[dict]:
    """Load + cache OSHA 300A summary records. ~80MB, 400k rows."""
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


def query_establishments(
    company_name: Optional[str] = None,
    address_substr: Optional[str] = None,
    city: Optional[str] = None,
    state: Optional[str] = None,
    naics_prefix: Optional[str] = None,
    csv_path: Optional[str] = None,
    max_results: int = 50,
    match_mode: str = "word_boundary",
    cutoff_date: Optional[str] = None,
) -> dict[str, Any]:
    """Search OSHA Form 300A establishments by combination of filters.

    All filters AND together; any filter omitted is unconstrained.
    `company_name` matching: word-boundary by default — "AIRO" matches
    "AIRO Group" but NOT "Cairo", "Kairos", or "Airosol". Pass
    match_mode="substring" for the legacy behavior, or "exact" to
    require the company name to equal the full establishment_name or
    company_name field (case-insensitive).

    `address_substr` is always substring; city/state are exact
    (uppercase); naics_prefix matches leading digits.

    `cutoff_date` (ISO YYYY-MM-DD): if provided, only rows with
    `year_filing_for <= cutoff_year` are considered. The OSHA 300A
    file ships year-stamped; without this filter, a pre-cutoff
    backtest leaks post-cutoff registrations (e.g., NKLA's Coolidge
    plant didn't exist in 2020 but shows up in the 2024 file).

    Returns:
        {
          "n_matches":             int (total before truncation),
          "matches":               list of records (up to max_results),
          "total_employees":       sum of annual_average_employees,
          "naics_breakdown":       {naics: count, ...},
          "by_state":              {state: count, ...},
          "signal":                NO_OSHA_FOOTPRINT | SMALL_EMPLOYER |
                                    REGISTERED_EMPLOYER | NO_DATA_AT_CUTOFF,
          "match_mode":            echo of the mode used,
          "filters":               echo,
          "data_years":            sorted list of year_filing_for values
                                    in the underlying file (helps the
                                    scorer reason about coverage),
          "cutoff_year":           int or None,
        }

    Signal mapping:
      - cutoff_date provided AND no rows in file have year_filing_for
        <= cutoff_year → NO_DATA_AT_CUTOFF (we cannot adjudicate)
      - 0 matches AND company_name was provided → NO_OSHA_FOOTPRINT
        (no establishment with this name in 300A — either too small to
        file, in an exempt industry, or doesn't exist as claimed)
      - total_employees < 50 across all matches → SMALL_EMPLOYER
      - total_employees >= 50 → REGISTERED_EMPLOYER
    """
    rows = _load(csv_path)
    if not rows:
        return {"error": "OSHA 300A CSV not found; download from osha.gov "
                          "and place in verticals/public_co/data/_osha_data/",
                "n_matches": 0, "matches": [], "filters": {}}

    cutoff_year: Optional[int] = None
    if cutoff_date:
        try:
            cutoff_year = int(str(cutoff_date)[:4])
        except (ValueError, TypeError):
            cutoff_year = None

    # Years present in the loaded file (independent of name filters)
    data_years = sorted({(r.get("year_filing_for") or "").strip()
                         for r in rows if (r.get("year_filing_for") or "").strip()})

    # Pre-filter rows to cutoff window. If no rows pass, return
    # NO_DATA_AT_CUTOFF — the dataset has no data old enough to adjudicate.
    if cutoff_year is not None:
        rows_in_window = []
        for r in rows:
            y = (r.get("year_filing_for") or "").strip()
            if not y:
                continue
            try:
                if int(y) <= cutoff_year:
                    rows_in_window.append(r)
            except ValueError:
                continue
        if not rows_in_window:
            return {
                "n_matches":       0,
                "matches":         [],
                "total_employees": 0,
                "naics_breakdown": {},
                "by_state":        {},
                "signal":          "NO_DATA_AT_CUTOFF",
                "match_mode":      match_mode,
                "filters":         {"company_name": company_name,
                                     "address_substr": address_substr,
                                     "city": city, "state": state,
                                     "naics_prefix": naics_prefix,
                                     "cutoff_date": cutoff_date},
                "data_years":      data_years,
                "cutoff_year":     cutoff_year,
                "_note":           ("OSHA 300A file has no rows with "
                                    f"year_filing_for <= {cutoff_year}; "
                                    f"available years: {data_years}. "
                                    "Cannot retroactively verify operations "
                                    "at this cutoff."),
            }
        rows = rows_in_window

    cn = (company_name or "").upper()
    addr = (address_substr or "").upper()
    cy = (city or "").upper()
    st = (state or "").upper()
    naics_p = (naics_prefix or "")

    # Build the company-name matcher up front (compiled once).
    if cn and match_mode == "word_boundary":
        pattern = re.compile(r"\b" + re.escape(cn) + r"\b", re.IGNORECASE)
        def _name_match(est: str, co: str) -> bool:
            return bool(pattern.search(est) or pattern.search(co))
    elif cn and match_mode == "exact":
        def _name_match(est: str, co: str) -> bool:
            return est == cn or co == cn
    else:  # substring fallback
        def _name_match(est: str, co: str) -> bool:
            return cn in est or cn in co

    matches = []
    for r in rows:
        if cn:
            est = (r.get("establishment_name") or "").upper()
            co  = (r.get("company_name") or "").upper()
            if not _name_match(est, co):
                continue
        if addr and addr not in (r.get("street_address") or "").upper():
            continue
        if cy and cy != (r.get("city") or "").upper():
            continue
        if st and st != (r.get("state") or "").upper():
            continue
        if naics_p and not (r.get("naics_code") or "").startswith(naics_p):
            continue
        matches.append(r)

    n_total = len(matches)
    truncated = matches[:max_results]
    total_emp = 0
    for r in matches:
        try: total_emp += int(r.get("annual_average_employees") or 0)
        except (TypeError, ValueError): pass

    naics_brk: dict[str, int] = {}
    by_state:  dict[str, int] = {}
    for r in matches:
        nc = (r.get("naics_code") or "?")[:4]
        naics_brk[nc] = naics_brk.get(nc, 0) + 1
        s = r.get("state") or "?"
        by_state[s] = by_state.get(s, 0) + 1

    if n_total == 0 and company_name:
        signal = "NO_OSHA_FOOTPRINT"
    elif total_emp < 50:
        signal = "SMALL_EMPLOYER"
    else:
        signal = "REGISTERED_EMPLOYER"

    # Slim down the matches for the response
    slim = [{k: r.get(k) for k in
             ("establishment_name", "company_name", "street_address",
              "city", "state", "zip_code", "naics_code",
              "industry_description", "annual_average_employees",
              "total_hours_worked", "size")}
            for r in truncated]

    return {
        "n_matches":        n_total,
        "matches":          slim,
        "total_employees":  total_emp,
        "naics_breakdown":  dict(sorted(naics_brk.items(), key=lambda x: -x[1])[:10]),
        "by_state":         dict(sorted(by_state.items(),  key=lambda x: -x[1])[:10]),
        "signal":           signal,
        "match_mode":       match_mode,
        "filters": {"company_name": company_name, "address_substr": address_substr,
                    "city": city, "state": state, "naics_prefix": naics_prefix,
                    "cutoff_date": cutoff_date},
        "data_years":       data_years,
        "cutoff_year":      cutoff_year,
    }
