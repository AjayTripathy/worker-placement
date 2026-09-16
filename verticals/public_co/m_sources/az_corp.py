"""Arizona Corporation Commission entity search.

Public JSON endpoint at https://ecorp.azcc.gov/api/Search.
"""

from __future__ import annotations

APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": [],
    "issuer_features": [],
    "asset_classes": ["public_equity_forensics"],
    "applies_universally": False,
    "kind": "m_source",
    "summary": "Arizona Corporation Commission entity search for entity-resolution of claimed AZ entities.",
}

import httpx

HEADERS = {
    "User-Agent": "Signal OS Research backtest@signalos.local",
    "Content-Type": "application/json",
}


def search(entity_name: str) -> dict:
    url = "https://ecorp.azcc.gov/api/Search"
    payload = {
        "EntityName": entity_name,
        "EntityNumber": "",
        "EntityType": "",
        "EntityStatus": "",
        "PageSize": 50,
        "PageNumber": 1,
    }
    try:
        with httpx.Client(timeout=30, headers=HEADERS) as c:
            r = c.post(url, json=payload)
            if r.status_code != 200:
                return {"error": f"status_{r.status_code}"}
            data = r.json()
    except Exception as e:
        return {"error": str(e)}

    entities = data.get("EntitySearchResults", []) if isinstance(data, dict) else data
    matched = []
    if isinstance(entities, list):
        for e in entities:
            name = e.get("EntityName") or ""
            if entity_name.lower() in name.lower():
                matched.append({
                    "name": name,
                    "type": e.get("EntityType"),
                    "status": e.get("EntityStatus"),
                    "formed_date": e.get("FormedDate") or e.get("DateOfFormation"),
                    "entity_number": e.get("EntityNumber"),
                })
    return {
        "search_term": entity_name,
        "n_entities_found": len(matched),
        "entities": matched,
    }
