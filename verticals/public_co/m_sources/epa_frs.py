"""EPA Facility Registry Service (FRS) — every regulated US facility.

Real factories register with EPA because they handle regulated substances
(emissions, hazardous waste, water discharge). FRS is the federal index of
those facilities. A claimed factory that doesn't appear here either isn't
real or isn't yet at industrial scale.

Endpoint: https://frs-public.epa.gov/ords/frs_public2/frs_rest_services.get_facilities

Stronger discriminator than NHTSA address (which holds corporate HQ, not
factory locations).
"""

from __future__ import annotations

APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": [],
    "issuer_features": ["industrial_facility_claim"],
    "asset_classes": ["public_equity_forensics"],
    "applies_universally": False,
    "kind": "m_source",
    "summary": "EPA Facility Registry lookup; a claimed factory absent from FRS isn't real or isn't industrial-scale.",
}

import urllib.parse

import httpx

HEADERS = {"User-Agent": "Signal OS Research backtest@signalos.local"}


def query_facilities(facility_name: str, state_abbr: str, city_filter: str | None = None) -> dict:
    """Look up FRS facilities by name + state, optionally filter by city."""
    qs = urllib.parse.urlencode({
        "facility_name": facility_name,
        "state_abbr": state_abbr,
        "output": "JSON",
    })
    url = f"https://frs-public.epa.gov/ords/frs_public2/frs_rest_services.get_facilities?{qs}"
    try:
        with httpx.Client(timeout=30, headers=HEADERS) as c:
            r = c.get(url)
            if r.status_code != 200:
                return {"error": f"status_{r.status_code}"}
            data = r.json()
    except Exception as e:
        return {"error": str(e)}

    results = data.get("Results", {}) or {}
    facilities_raw = results.get("FRSFacility", []) or []
    if isinstance(facilities_raw, dict):
        facilities_raw = [facilities_raw]

    facilities = []
    for f in facilities_raw:
        rec = {
            "registry_id": f.get("RegistryId"),
            "facility_name": f.get("FacilityName"),
            "address": f.get("LocationAddress"),
            "city": f.get("CityName"),
            "county": f.get("CountyName"),
            "state": f.get("StateAbbr"),
            "zip": f.get("ZipCode"),
            "lat": f.get("Latitude83"),
            "lon": f.get("Longitude83"),
        }
        if city_filter and (rec["city"] or "").upper() != city_filter.upper():
            continue
        facilities.append(rec)

    error = results.get("Error", {})
    return {
        "search_name": facility_name,
        "state_abbr": state_abbr,
        "city_filter": city_filter,
        "n_facilities": len(facilities),
        "facilities": facilities,
        "epa_error": error.get("ErrorMessage") if isinstance(error, dict) else None,
    }
