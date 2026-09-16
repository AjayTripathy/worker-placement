"""
BLS Quarterly Census of Employment and Wages (QCEW) connector.

QCEW publishes county+NAICS quarterly establishment and employment
counts. Use it as a PLAUSIBILITY DENOMINATOR for company claims about
facility scope in specific geographies.

Example:
  Company X claims "500-person Aircraft Manufacturing facility in
  Maricopa County AZ" (NAICS 336411, FIPS 04013).
  → QCEW shows Maricopa County NAICS 336411 has ~6,500 total
    employees across ~10 establishments.
  → Company X's 500-person facility would be ~8% of county-wide
    aerospace mfg employment with 1/10th the establishment share.
    Plausible — flag depends on company's reported headcount + revenue.

API endpoint:
  https://data.bls.gov/cew/data/api/{year}/{qtr}/area/{fips5}.csv

Returns CSV with one row per (NAICS × ownership × aggregation_level)
within the queried FIPS area. Free, public, no key.

Coverage gaps:
  - 2-quarter publication lag (Q2 of YYYY available ~Q4 of YYYY)
  - State + federal employees included; private-sector ownership
    code is '5' (private). Public-sector dominant counties (e.g. WA
    DC, military bases) will show big federal employment.
  - Suppressed (D-flagged) when single employer dominates a cell.
"""

from __future__ import annotations

APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": [],
    "issuer_features": ["facility_scale_claim"],
    "asset_classes": ["public_equity_forensics"],
    "applies_universally": False,
    "kind": "m_source",
    "summary": "BLS QCEW county+NAICS employment as a plausibility denominator for claimed facility scale in a geography.",
}

import csv
from io import StringIO
from typing import Any, Optional

import httpx

HEADERS = {"User-Agent": "Signal OS Research backtest@signalos.local"}

# Aggregation levels (agglvl_code) at the county tier — see
# https://www.bls.gov/cew/classifications/aggregation/agg-level-titles.htm
# Observed in practice (06083 county-level CSV):
#   75 -> NAICS 3-digit (e.g. "336" Transportation Eq Mfg)
#   76 -> NAICS 4-digit (e.g. "3344" Semiconductor Mfg)
#   77 -> NAICS 5-digit
#   78 -> NAICS 6-digit (e.g. "336411" Aircraft Mfg)
COUNTY_AGGLVL = {
    6: 78,
    5: 77,
    4: 76,
    3: 75,
}


# Quick FIPS lookup for major counties we expect to query a lot.
# Use the FIPS field directly if you have it; this map is convenience-
# only for the most-common ticker-claim addresses.
FIPS_BY_COUNTY: dict[tuple[str, str], str] = {
    ("AZ", "Maricopa"):       "04013",
    ("CA", "Santa Barbara"):  "06083",
    ("CA", "San Diego"):      "06073",
    ("CA", "San Francisco"):  "06075",
    ("CA", "Alameda"):        "06001",
    ("CA", "Los Angeles"):    "06037",
    ("CA", "Santa Clara"):    "06085",
    ("MA", "Middlesex"):      "25017",
    ("MA", "Suffolk"):        "25025",
    ("NJ", "Bergen"):         "34003",
    ("NJ", "Middlesex"):      "34023",
    ("NY", "New York"):       "36061",
    ("NY", "Kings"):           "36047",
    ("PA", "Montgomery"):     "42091",
    ("PA", "Philadelphia"):   "42101",
    ("TX", "Harris"):         "48201",
    ("TX", "Dallas"):         "48113",
    ("TX", "Travis"):          "48453",
    ("WA", "King"):            "53033",
    ("WA", "Benton"):          "53005",  # Hanford/Richland
    ("FL", "Miami-Dade"):     "12086",
    ("FL", "St. Lucie"):      "12111",
}


def lookup_fips(state: str, county: str) -> Optional[str]:
    """Convenience: lookup FIPS from state+county. Returns None if
    not in the convenience map (caller should provide FIPS directly)."""
    return FIPS_BY_COUNTY.get((state.upper(), county.title()))


def query_county_naics(
    fips5: str,
    year: int,
    qtr: int,
    naics_prefix: Optional[str] = None,
    ownership: str = "5",  # 5 = Private; 0 = Total
    naics_digits: int = 6,
) -> dict[str, Any]:
    """Query county-NAICS quarterly employment denominator.

    fips5: 5-digit FIPS (state+county), e.g. '04013' for Maricopa
    year, qtr: e.g. 2024, 4
    naics_prefix: filter to NAICS codes starting with this prefix
                  (e.g. '336' for transportation equipment mfg)
    ownership: '5' (private), '0' (total), '1' (federal), '2' (state),
               '3' (local), '8' (private + state + local)
    naics_digits: aggregation level (2, 3, 4, 5, 6)

    Returns:
      {
        "fips5":           str,
        "year":            int, "qtr": int,
        "matches":         list of {naics_code, naics_title?,
                            qtrly_estabs, avg_employees, total_wages,
                            avg_weekly_wage},
        "total_estabs":    sum of qtrly_estabs across matches,
        "total_employees": sum of avg(month1+2+3) across matches,
        "top_employers":   list sorted by avg_employees desc,
      }
    """
    url = f"https://data.bls.gov/cew/data/api/{year}/{qtr}/area/{fips5}.csv"
    try:
        with httpx.Client(headers=HEADERS, timeout=30) as c:
            r = c.get(url)
            if r.status_code != 200:
                return {"error": f"bls_status_{r.status_code}", "matches": []}
            csv_text = r.text
    except httpx.HTTPError as e:
        return {"error": f"bls_http: {e}", "matches": []}

    target_agglvl = str(COUNTY_AGGLVL.get(int(naics_digits), 76))
    matches = []
    reader = csv.DictReader(StringIO(csv_text))
    for row in reader:
        if row.get("own_code") != ownership:
            continue
        if row.get("agglvl_code") != target_agglvl:
            continue
        nc = row.get("industry_code", "")
        if naics_prefix and not nc.startswith(naics_prefix):
            continue
        try:
            estabs = int(row.get("qtrly_estabs") or 0)
            m1 = int(row.get("month1_emplvl") or 0)
            m2 = int(row.get("month2_emplvl") or 0)
            m3 = int(row.get("month3_emplvl") or 0)
            avg_emp = (m1 + m2 + m3) // 3 if (m1 or m2 or m3) else 0
            wages = int(row.get("total_qtrly_wages") or 0)
            wkly = int(row.get("avg_wkly_wage") or 0)
        except (TypeError, ValueError):
            continue
        matches.append({
            "naics_code":      nc,
            "qtrly_estabs":    estabs,
            "avg_employees":   avg_emp,
            "total_wages":     wages,
            "avg_weekly_wage": wkly,
        })

    matches.sort(key=lambda r: -r["avg_employees"])
    total_estabs = sum(m["qtrly_estabs"] for m in matches)
    total_emp    = sum(m["avg_employees"] for m in matches)

    return {
        "fips5":           fips5,
        "year":            year,
        "qtr":             qtr,
        "naics_prefix":    naics_prefix,
        "naics_digits":    naics_digits,
        "ownership":       ownership,
        "matches":         matches[:20],
        "total_estabs":    total_estabs,
        "total_employees": total_emp,
        "n_naics_cells":   len(matches),
    }
