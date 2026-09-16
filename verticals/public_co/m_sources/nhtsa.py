"""NHTSA vPIC manufacturer registry."""

from __future__ import annotations

APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": ["371"],
    "issuer_features": ["vehicle_manufacturer_claim"],
    "asset_classes": ["public_equity_forensics"],
    "applies_universally": False,
    "kind": "m_source",
    "summary": "NHTSA vPIC manufacturer registry; verifies claimed vehicle-manufacturer status.",
}

import urllib.parse

import httpx

HEADERS = {"User-Agent": "Signal OS Research backtest@signalos.local"}


def query_manufacturer(name: str) -> dict:
    url = (
        f"https://vpic.nhtsa.dot.gov/api/vehicles/getmanufacturerdetails/"
        f"{urllib.parse.quote(name)}?format=json"
    )
    try:
        with httpx.Client(timeout=30, headers=HEADERS) as c:
            r = c.get(url)
            r.raise_for_status()
            data = r.json()
    except Exception as e:
        return {"error": str(e)}
    results = data.get("Results", [])
    rows = [r for r in results if name.lower() in (r.get("Mfr_Name") or "").lower()]
    return {
        "search_term": name,
        "n_manufacturers": len(rows),
        "manufacturers": [
            {
                "mfr_name": r.get("Mfr_Name"),
                "mfr_id": r.get("Mfr_ID"),
                "country": r.get("Country"),
                "address": r.get("Address"),
                "vehicle_types": [vt.get("Name") for vt in (r.get("VehicleTypes") or [])],
            }
            for r in rows[:5]
        ],
    }
