"""DOE/NREL Alternative Fueling Stations Locator."""

from __future__ import annotations

APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": [],
    "issuer_features": ["alt_fuel_infrastructure_claim"],
    "asset_classes": ["public_equity_forensics"],
    "applies_universally": False,
    "kind": "m_source",
    "summary": "DOE/NREL alternative-fueling-station locator; verifies claimed fueling-network buildout.",
}

import httpx

HEADERS = {"User-Agent": "Signal OS Research backtest@signalos.local"}


def query_alt_fuel_stations(fuel_type: str, cutoff_date: str, name_filter: str | None = None) -> dict:
    """List stations of a fuel type that were open or last-confirmed before cutoff.

    fuel_type: NREL code, e.g. 'HY' for hydrogen, 'ELEC' for EV charging.
    name_filter: case-insensitive substring; if any value of the station record
        contains it the station is added to a `matching_stations` bucket.
    """
    url = "https://developer.nrel.gov/api/alt-fuel-stations/v1.json"
    params = {"api_key": "DEMO_KEY", "fuel_type": fuel_type, "status": "all", "limit": "all"}
    try:
        with httpx.Client(timeout=30, headers=HEADERS) as c:
            r = c.get(url, params=params)
            r.raise_for_status()
            data = r.json()
    except Exception as e:
        return {"error": f"nrel_api_failed: {e}"}

    pre_cutoff = []
    for s in data.get("fuel_stations", []):
        d = s.get("open_date") or s.get("date_last_confirmed") or ""
        if d and d <= cutoff_date:
            pre_cutoff.append({
                "station_name": s.get("station_name"),
                "operator": s.get("ev_network") or s.get("station_name"),
                "status": s.get("status_code"),
                "open_date": s.get("open_date"),
                "city": s.get("city"),
                "state": s.get("state"),
            })

    out = {
        "fuel_type": fuel_type,
        "total_stations_pre_cutoff": len(pre_cutoff),
        "sample_of_other_operators": list({s["operator"] for s in pre_cutoff if s["operator"]})[:20],
    }
    if name_filter:
        nf = name_filter.lower()
        matching = [s for s in pre_cutoff if any(nf in (str(v) or "").lower() for v in s.values())]
        out["name_filter"] = name_filter
        out["matching_stations_count"] = len(matching)
        out["matching_stations"] = matching
    return out
