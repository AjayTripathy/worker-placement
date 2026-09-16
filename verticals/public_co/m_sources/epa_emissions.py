"""
EPA operational-capacity connector — FRS + TRI + GHGRP, with location audit.

Tests whether a company's named facilities operate at the physical scale
implied by its commercial claims, by probing three EPA registries:

  - FRS (Facility Registry Service): the master index of every EPA-permitted
    facility in the US. Any facility with a Title V air permit, RCRA hazmat
    permit, NPDES water discharge, TRI/GHGRP reporting, or a Superfund/
    brownfield record appears here. A real industrial site almost always
    has at least one of these permits.

  - TRI (Toxic Release Inventory): facilities that manufacture, process,
    or use TRI-listed chemicals above thresholds (10k or 25k lbs/yr).
    Industrial-chemistry manufacturing usually crosses these thresholds.

  - GHGRP (Greenhouse Gas Reporting Program): facilities emitting >25kt
    CO2e/yr. Heavy manufacturing, power generation, and industrial gas
    production cross this.

What v2 adds over v1:
  - FRS as the primary "is the company permitted at all" probe — broader
    than TRI/GHGRP because it picks up ANY EPA-permitted facility, not
    just industrial-chemical or large-emitter sites.
  - Facility-type heuristic: distinguishes PRODUCTION-named facilities
    from OFFICE/WAREHOUSE/INNOVATION sites.
  - Location audit: caller passes claimed_locations=[{"city": "WOODBINE",
    "state": "GA"}, ...], connector probes each and reports whether the
    company has any FRS-registered facility there. Catches the
    "EPA knows the company, but doesn't know the claimed plant" pattern.

The strongest divergence signal is CLAIMED_LOCATION_GAP: the focal
company has SOME EPA footprint (so we know they're not invisible to
EPA), but at the specific locations they market as production
facilities, no company-affiliated permit exists.

Usage:
    query_facility_emissions(
        company_name="Plug Power",
        claimed_locations=[
            {"city": "WOODBINE",   "state": "GA"},
            {"city": "CHARLESTON", "state": "TN"},
            {"city": "KINGSLAND",  "state": "GA"},
        ],
    )

API: data.epa.gov/efservice/  (Envirofacts JSON-REST)
Auth: none
Cost: free
"""

from __future__ import annotations

APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": [],
    "issuer_features": ["facility_scale_claim", "industrial_facility_claim"],
    "asset_classes": ["public_equity_forensics"],
    "applies_universally": False,
    "kind": "m_source",
    "summary": "EPA FRS+TRI+GHGRP probe: does a claimed industrial facility operate at permitted physical scale?",
}

import urllib.parse
from collections import defaultdict

import httpx

HEADERS = {"User-Agent": "Signal OS Research backtest@signalos.local"}
BASE = "https://data.epa.gov/efservice"


# Order matters: PRODUCTION wins over R&D wins over OFFICE.
_PRODUCTION_KEYWORDS = [
    "PLANT", "FACTORY", "MANUFACTURING", "MFG", "PRODUCTION",
    "REFINERY", "MILL", "GIGAFACTORY", "FOUNDRY", "SMELTER",
]
_RD_KEYWORDS = [
    "R&D", "RESEARCH", "LABORATORY", " LAB ", "DEVELOPMENT",
    "INNOVATION CENTER", "INNOVATION CTR",
]
_OFFICE_KEYWORDS = [
    "OFFICE", "HQ", "HEADQUARTERS", "WAREHOUSE", "DISTRIBUTION",
    "CORPORATE", " HQ", " OFFICE",
]


def _classify_facility_type(name: str) -> str:
    n = f" {(name or '').upper()} "
    if any(k in n for k in _PRODUCTION_KEYWORDS):
        return "PRODUCTION"
    if any(k in n for k in _RD_KEYWORDS):
        return "R&D"
    if any(k in n for k in _OFFICE_KEYWORDS):
        return "OFFICE_OR_WAREHOUSE"
    return "UNCLASSIFIED"


def _get(path: str) -> list | None:
    """Envirofacts JSON-REST GET. Returns list or None on error."""
    url = f"{BASE}/{path}"
    try:
        r = httpx.get(url, headers=HEADERS, timeout=30, follow_redirects=True)
        if r.status_code != 200:
            return None
        return r.json()
    except Exception:
        return None


def _frs_lookup(company_name: str, state: str | None = None) -> list[dict]:
    """Find FRS facilities whose primary_name contains the company name."""
    encoded = urllib.parse.quote(company_name.upper())
    if state:
        path = f"FRS_FACILITY_SITE/state_code/{state.upper()}/primary_name/CONTAINING/{encoded}/JSON"
    else:
        path = f"FRS_FACILITY_SITE/primary_name/CONTAINING/{encoded}/JSON"
    rows = _get(path) or []
    needle = company_name.lower()
    return [r for r in rows if needle in (r.get("primary_name") or "").lower()]


def _frs_at_location(city: str, state: str) -> list[dict]:
    """List FRS facilities at a city+state. Used for reverse-lookup audit."""
    path = f"FRS_FACILITY_SITE/state_code/{state.upper()}/city_name/{city.upper()}/JSON"
    return _get(path) or []


def _tri_lookup(company_name: str, state: str | None = None) -> list[dict]:
    """Find TRI facilities whose name contains company_name."""
    encoded = urllib.parse.quote(company_name.upper())
    path = f"tri_facility/facility_name/CONTAINING/{encoded}/JSON"
    rows = _get(path) or []
    needle = company_name.lower()
    filtered = [r for r in rows if needle in (r.get("facility_name") or "").lower()]
    if state:
        filtered = [r for r in filtered if (r.get("state_abbr") or "") == state.upper()]
    return filtered


def _tri_annual_reports(tri_facility_id: str) -> list[dict]:
    """Get all TRI_REPORTING_FORM records for a facility."""
    path = f"TRI_REPORTING_FORM/tri_facility_id/{tri_facility_id}/JSON"
    return _get(path) or []


def _ghgrp_lookup(company_name: str, state: str | None = None) -> list[dict]:
    """Find GHGRP facilities whose name contains company_name."""
    encoded = urllib.parse.quote(company_name.upper())
    path = f"PUB_DIM_FACILITY/facility_name/CONTAINING/{encoded}/JSON"
    rows = _get(path) or []
    needle = company_name.lower()
    filtered = [r for r in rows if needle in (r.get("facility_name") or "").lower()]
    if state:
        filtered = [r for r in filtered if (r.get("state") or "") == state.upper()]
    return filtered


def _ghgrp_emissions(facility_id: int | str) -> list[dict]:
    """Get GHG emission records for a GHGRP facility_id."""
    path = f"pub_facts_sector_ghg_emission/facility_id/{facility_id}/JSON"
    return _get(path) or []


def _audit_claimed_location(company_name: str, city: str, state: str) -> dict:
    """For a claimed plant location, check whether the company has any FRS
    facility there, and surface the other industrial neighbors."""
    facs = _frs_at_location(city, state)
    needle = company_name.lower()
    company_at_location = [
        f for f in facs
        if needle in (f.get("primary_name") or "").lower()
    ]
    # Top 8 neighbors for context (truncate field set)
    neighbors = [
        {
            "name":    f.get("primary_name"),
            "address": f.get("location_address"),
        }
        for f in facs[:8]
        if needle not in (f.get("primary_name") or "").lower()
    ]
    return {
        "city":                       city.upper(),
        "state":                      state.upper(),
        "n_frs_facilities_at_loc":    len(facs),
        "company_present_at_loc":     bool(company_at_location),
        "company_facilities_at_loc":  [
            {"name": f.get("primary_name"), "address": f.get("location_address")}
            for f in company_at_location
        ],
        "industrial_neighbors":       neighbors,
    }


def query_facility_emissions(
    company_name: str,
    state: str | None = None,
    claimed_locations: list[dict] | None = None,
) -> dict:
    """Probe FRS + TRI + GHGRP for a company's operational footprint, with
    optional reverse-lookup audit of claimed plant locations.

    Args:
      company_name:      focal company name (substring matched against FRS,
                         TRI, GHGRP facility/primary_name fields).
      state:             optional 2-letter state code to filter the
                         company-name searches.
      claimed_locations: optional list of {"city": "...", "state": "..."}
                         dicts. For each, the connector reports whether the
                         company has a registered facility there and lists
                         the other industrial neighbors.

    Signal precedence:
      INDUSTRIAL_SCALE_CONFIRMED           — in TRI or GHGRP
      CLAIMED_LOCATION_GAP                 — FRS knows the company elsewhere,
                                              but no company facility at any
                                              claimed location
      FRS_PERMITTED_NO_INDUSTRIAL_REPORTING — in FRS, not in TRI/GHGRP,
                                              and either no claimed_locations
                                              were given or the company is
                                              registered at all of them
      NO_EPA_FOOTPRINT                     — not in FRS at all
                                              (and not in TRI/GHGRP)
    """
    frs_facs   = _frs_lookup(company_name, state=state)
    tri_facs   = _tri_lookup(company_name, state=state)
    ghgrp_facs = _ghgrp_lookup(company_name, state=state)

    # FRS summary — classify each facility, count by type.
    frs_summary = []
    type_counts: dict[str, int] = defaultdict(int)
    for f in frs_facs[:25]:
        kind = _classify_facility_type(f.get("primary_name") or "")
        type_counts[kind] += 1
        frs_summary.append({
            "registry_id":   f.get("registry_id"),
            "primary_name":  f.get("primary_name"),
            "address":       f.get("location_address"),
            "city":          f.get("city_name"),
            "state":         f.get("state_code"),
            "zip":           f.get("postal_code"),
            "facility_type": kind,
        })

    tri_summary = []
    earliest = None
    latest = None
    for f in tri_facs[:10]:
        tid = f.get("tri_facility_id")
        reports = _tri_annual_reports(tid) if tid else []
        years = sorted({r.get("reporting_year") for r in reports if r.get("reporting_year")})
        chems = {r.get("tri_chem_id") for r in reports if r.get("tri_chem_id")}
        tri_summary.append({
            "tri_id":               tid,
            "facility_name":        f.get("facility_name"),
            "city":                 f.get("city_name"),
            "state":                f.get("state_abbr"),
            "years_reported":       years,
            "n_chemicals_reported": len(chems),
            "n_form_records":       len(reports),
        })
        if years:
            earliest = min(years) if earliest is None else min(earliest, min(years))
            latest = max(years) if latest is None else max(latest, max(years))

    ghgrp_summary = []
    for f in ghgrp_facs[:10]:
        fid = f.get("facility_id")
        emis = _ghgrp_emissions(fid) if fid else []
        years_e = sorted({e.get("year") for e in emis if e.get("year")})
        latest_y = max(years_e) if years_e else None
        latest_tco2e = (
            sum(e.get("co2e_emission", 0) or 0 for e in emis if e.get("year") == latest_y)
            if latest_y else None
        )
        ghgrp_summary.append({
            "ghgrp_id":       fid,
            "facility_name":  f.get("facility_name"),
            "city":           f.get("city"),
            "state":          f.get("state"),
            "years_reported": years_e,
            "latest_year":    latest_y,
            "latest_tCO2e":   round(latest_tco2e, 0) if latest_tco2e is not None else None,
        })

    # Location audit for any caller-supplied claimed_locations.
    location_audit: list[dict] = []
    if claimed_locations:
        for loc in claimed_locations:
            city = loc.get("city")
            st   = loc.get("state")
            if not city or not st:
                continue
            location_audit.append(_audit_claimed_location(company_name, city, st))

    in_frs   = bool(frs_summary)
    in_tri   = bool(tri_summary)
    in_ghgrp = bool(ghgrp_summary)

    # Signal precedence
    if in_tri or in_ghgrp:
        signal = "INDUSTRIAL_SCALE_CONFIRMED"
    elif in_frs and location_audit and not any(a["company_present_at_loc"] for a in location_audit):
        signal = "CLAIMED_LOCATION_GAP"
    elif in_frs:
        signal = "FRS_PERMITTED_NO_INDUSTRIAL_REPORTING"
    else:
        signal = "NO_EPA_FOOTPRINT"

    return {
        "company_name":  company_name,
        "state_filter":  state,
        "frs": {
            "facilities_found":   len(frs_facs),
            "facility_summary":   frs_summary,
            "type_counts":        dict(type_counts),
            "has_production":     type_counts.get("PRODUCTION", 0) > 0,
        },
        "tri": {
            "facilities_found": len(tri_facs),
            "facility_summary": tri_summary,
            "earliest_year":    earliest,
            "latest_year":      latest,
        },
        "ghgrp": {
            "facilities_found": len(ghgrp_facs),
            "facility_summary": ghgrp_summary,
        },
        "claimed_location_audit": location_audit,
        "operational_scale_signal": signal,
    }


if __name__ == "__main__":
    import json, sys
    name = sys.argv[1] if len(sys.argv) > 1 else "Plug Power"
    state = sys.argv[2] if len(sys.argv) > 2 else None
    # Demo claimed_locations for PLUG
    claimed = [
        {"city": "WOODBINE",   "state": "GA"},
        {"city": "KINGSLAND",  "state": "GA"},
        {"city": "CHARLESTON", "state": "TN"},
    ] if name.lower().startswith("plug") else None
    print(json.dumps(
        query_facility_emissions(name, state, claimed_locations=claimed),
        indent=2,
        default=str,
    ))
