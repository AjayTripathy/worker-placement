"""restaurant_ratings — verify a physical operating location exists, is operational, and
its public rating/review velocity, for any deal that asserts brick-and-mortar units
(restaurant / retail / clinic / franchise rosters).

WHY THIS EXISTS: the Cheba/Evergreen DD (2026-06) marketed 24 operating restaurants by
address; the pipeline had NO connector to verify a storefront exists and is OPERATIONAL,
so it sat unverified until asked by hand. This closes that recall-floor gap — any claim of
the form "operator runs N units at these addresses" now auto-dispatches a per-address check.

PROVIDERS (in priority order):
  1. Google Places API (New) — AUTHORITATIVE. business_status (OPERATIONAL / CLOSED_PERMANENTLY /
     CLOSED_TEMPORARILY), rating, userRatingCount, matched name+address. Needs a key in
     env GOOGLE_PLACES_API_KEY or file ~/.google_places_key (chmod 600). Free $200/mo credit.
  2. OSM Nominatim — NO KEY. Confirms the address resolves to real coordinates (existence)
     and returns the matched OSM category. No ratings/operating-status → those come back
     UNVERIFIABLE_NO_KEY. This is real existence verification even without the paid key.

Returns observations: location_operating_status, location_rating, location_review_count,
location_match (matched name/address + distance), provider.
"""

from __future__ import annotations

# Knowledge-graph dispatch contract (see knowledge_graph/dispatch.py) — added 2026-07-29 gap-close.
APPLIES_TO = {
    "kind": 'm_source',
    "sic_codes": [],
    "sic_prefixes": ['58'],
    "issuer_features": ['multi_unit_retail_or_restaurant'],
    "asset_classes": ['corporate_ipo_dd'],
    "applies_universally": False,
    "summary": 'Verifies each marketed unit exists and is OPERATIONAL (Google Places + OSM).',
}

import json
import math
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import requests

from .base import (BaseConnector, ConnectorObservation, ConnectorRequest,
                   ConnectorResult, ErrorKind, safe_get)

_PLACES_URL = "https://places.googleapis.com/v1/places:searchText"
_NOMINATIM = "https://nominatim.openstreetmap.org/search"
_FIELD_MASK = ("places.displayName,places.formattedAddress,places.businessStatus,"
               "places.rating,places.userRatingCount,places.location,places.id")


def _places_key() -> Optional[str]:
    k = os.environ.get("GOOGLE_PLACES_API_KEY", "").strip()
    if k:
        return k
    f = Path.home() / ".google_places_key"
    try:
        if f.exists():
            return f.read_text().strip()
    except OSError:
        pass
    return None


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9 ]", " ", (s or "").lower())


def _street_number(addr: str) -> Optional[str]:
    m = re.match(r"\s*(\d+)", addr or "")
    return m.group(1) if m else None


def _zip5(addr: str) -> Optional[str]:
    m = re.search(r"\b(\d{5})(?:-\d{4})?\b", addr or "")
    return m.group(1) if m else None


def _haversine_m(a: tuple[float, float], b: tuple[float, float]) -> float:
    (lat1, lon1), (lat2, lon2) = a, b
    R = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))


def _address_matches(req_addr: str, got_addr: str) -> bool:
    """Loose match: same street number AND (same zip OR strong street-token overlap)."""
    rn, gn = _street_number(req_addr), _street_number(got_addr)
    if rn and gn and rn != gn:
        return False
    rz, gz = _zip5(req_addr), _zip5(got_addr)
    if rz and gz:
        return rz == gz
    rt = set(_norm(req_addr).split())
    gt = set(_norm(got_addr).split())
    return len(rt & gt) >= 3


class RestaurantRatingsConnector(BaseConnector):
    source_id = "restaurant_ratings"
    rate_limit_per_min = 50  # Nominatim wants <=60/min + a real UA; Places is fine
    user_agent = "SignalOS-BuysideDD/0.1 (diligence research; contact signalos)"

    # ---- Google Places (authoritative) ----
    def _google(self, name: str, address: str, key: str) -> tuple[Optional[dict], Optional[str]]:
        body = {"textQuery": f"{name} {address}".strip()}
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": key,
            "X-Goog-FieldMask": _FIELD_MASK,
        }
        try:
            r = requests.post(_PLACES_URL, headers=headers, json=body, timeout=self.timeout_s)
        except requests.exceptions.RequestException as e:
            return None, f"places_request: {e}"
        if r.status_code in (401, 403):
            return None, f"places_auth_{r.status_code}: {r.text[:160]}"
        if r.status_code != 200:
            return None, f"places_http_{r.status_code}: {r.text[:160]}"
        places = (r.json() or {}).get("places", []) or []
        if not places:
            return {"_empty": True}, None
        # pick the first place whose address matches the requested one, else the top hit
        chosen = None
        for p in places:
            if _address_matches(address, p.get("formattedAddress", "")):
                chosen = p
                break
        chosen = chosen or places[0]
        return {
            "name": (chosen.get("displayName") or {}).get("text"),
            "address": chosen.get("formattedAddress"),
            "business_status": chosen.get("businessStatus"),
            "rating": chosen.get("rating"),
            "review_count": chosen.get("userRatingCount"),
            "location": chosen.get("location"),
            "place_id": chosen.get("id"),
            "address_matched": _address_matches(address, chosen.get("formattedAddress", "")),
        }, None

    # ---- OSM Nominatim (no-key existence) ----
    def _nominatim(self, name: str, address: str) -> tuple[Optional[dict], Optional[str]]:
        s = requests.Session()
        s.headers.update({"User-Agent": self.user_agent})
        params = {"q": f"{name} {address}".strip(), "format": "jsonv2",
                  "addressdetails": 1, "limit": 1}
        r, err, detail = safe_get(s, _NOMINATIM, timeout=self.timeout_s, params=params)
        if err:  # retry on the address alone (name may not be in OSM)
            time.sleep(1.0)
            r, err, detail = safe_get(s, _NOMINATIM, timeout=self.timeout_s,
                                      params={"q": address, "format": "jsonv2", "limit": 1})
        if err or not r:
            return None, detail or "nominatim_error"
        arr = r.json() or []
        if not arr:
            # last resort: address-only geocode
            time.sleep(1.0)
            r2, err2, _ = safe_get(s, _NOMINATIM, timeout=self.timeout_s,
                                   params={"q": address, "format": "jsonv2", "limit": 1})
            arr = (r2.json() if (r2 and not err2) else []) or []
        if not arr:
            return {"_empty": True}, None
        hit = arr[0]
        return {
            "name": hit.get("name") or hit.get("display_name", "")[:60],
            "address": hit.get("display_name"),
            "category": f"{hit.get('category')}/{hit.get('type')}",
            "location": {"latitude": float(hit["lat"]), "longitude": float(hit["lon"])},
            "is_food_amenity": hit.get("category") in ("amenity",)
                               and hit.get("type") in ("fast_food", "restaurant", "cafe"),
        }, None

    def query(self, request: ConnectorRequest) -> ConnectorResult:
        address = request.address or request.extra.get("address")
        name = request.entity_name or request.extra.get("business_name") or ""
        if not address:
            return self._fail(request, ErrorKind.UNSUPPORTED,
                              "restaurant_ratings needs an address (request.address)")

        key = _places_key()
        obs: list[ConnectorObservation] = []
        now = self._now()

        if key:
            data, err = self._google(name, address, key)
            if err and "auth" in err:
                return self._fail(request, ErrorKind.AUTH, err)
            if err:
                return self._fail(request, ErrorKind.UNKNOWN, err)
            if data.get("_empty"):
                obs.append(ConnectorObservation(
                    attribute="location_operating_status", value="NOT_FOUND",
                    confidence=0.7, extra={"provider": "google_places", "query": f"{name} {address}"}))
                return self._ok(request, obs)
            status = data.get("business_status") or "UNKNOWN"
            obs.append(ConnectorObservation(
                attribute="location_operating_status", value=status,
                confidence=0.95 if data.get("address_matched") else 0.7,
                source_url=f"https://www.google.com/maps/place/?q=place_id:{data.get('place_id')}",
                extra={"provider": "google_places", "matched_name": data.get("name"),
                       "matched_address": data.get("address"),
                       "address_matched": data.get("address_matched")}))
            if data.get("rating") is not None:
                obs.append(ConnectorObservation(
                    attribute="location_rating", value=data["rating"], value_unit="stars_of_5",
                    extra={"provider": "google_places"}))
            if data.get("review_count") is not None:
                obs.append(ConnectorObservation(
                    attribute="location_review_count", value=data["review_count"],
                    extra={"provider": "google_places"}))
            return self._ok(request, obs)

        # ---- no key: existence-only via OSM ----
        data, err = self._nominatim(name, address)
        if err:
            return self._fail(request, ErrorKind.NETWORK, err)
        if data.get("_empty"):
            obs.append(ConnectorObservation(
                attribute="location_operating_status", value="ADDRESS_NOT_RESOLVED",
                confidence=0.5, extra={"provider": "osm_nominatim"}))
            return self._ok(request, obs)
        obs.append(ConnectorObservation(
            attribute="location_operating_status",
            value="ADDRESS_EXISTS_RATINGS_UNVERIFIABLE_NO_KEY",
            confidence=0.6,
            extra={"provider": "osm_nominatim", "matched": data.get("address"),
                   "category": data.get("category"),
                   "is_food_amenity": data.get("is_food_amenity"),
                   "hint": "set GOOGLE_PLACES_API_KEY or ~/.google_places_key for "
                           "business_status + rating + review_count"}))
        obs.append(ConnectorObservation(
            attribute="location_rating", value=None,
            extra={"provider": "none", "status": "UNVERIFIABLE_NO_KEY"}))
        return self._ok(request, obs)


# ─────────────────────────────────────────────────────────────────────────────
# Module-level helpers (batch verification + CLI self-test)
# ─────────────────────────────────────────────────────────────────────────────
def lookup(name: str, address: str) -> dict:
    """Convenience wrapper → flat dict {status, rating, review_count, provider, matched}."""
    c = RestaurantRatingsConnector()
    res = c.query(ConnectorRequest(entity_name=name, address=address))
    out = {"success": res.success, "error": res.error_detail}
    for o in res.observations:
        if o.attribute == "location_operating_status":
            out["status"] = o.value
            out["provider"] = o.extra.get("provider")
            out["matched"] = o.extra.get("matched_address") or o.extra.get("matched")
        elif o.attribute == "location_rating":
            out["rating"] = o.value
        elif o.attribute == "location_review_count":
            out["review_count"] = o.value
    return out


def verify_locations(rows: list[dict]) -> list[dict]:
    """rows: [{unit, name, address}, ...] → adds verification fields per row."""
    out = []
    for r in rows:
        v = lookup(r.get("name", "") or r.get("brand", ""), r["address"])
        out.append({**r, **v})
        time.sleep(1.1)  # Nominatim courtesy / Places pacing
    return out


# The 24 Cheba/Elevated units (deck p66) — built-in self-test fixture.
CHEBA_24 = [
    {"unit": "Cap Hill", "address": "638 E Colfax Ave, Denver, CO 80203"},
    {"unit": "Congress Park", "address": "745 Colorado Blvd, Denver, CO 80206"},
    {"unit": "Dillon", "address": "265 Dillon Ridge Rd, Silverthorne, CO 80498"},
    {"unit": "CSU", "address": "104 E Laurel St, Fort Collins, CO 80524"},
    {"unit": "Westside", "address": "925 S Taft Hill Rd, Fort Collins, CO 80521"},
    {"unit": "UNC", "address": "1645 8th Ave, Greeley, CO 80631"},
    {"unit": "Longmont-Downtown", "address": "635 Main St, Longmont, CO 80501"},
    {"unit": "Central Park", "address": "3990 Central Park Blvd, Denver, CO 80238"},
    {"unit": "Fillmore", "address": "3171 N Chestnut St, Colorado Springs, CO 80907"},
    {"unit": "Johnstown", "address": "4942 Thompson Pkwy, Johnstown, CO 80534"},
    {"unit": "Sloans Lake", "address": "4245 W Colfax Ave, Denver, CO 80204"},
    {"unit": "Boulder", "address": "1346 Pearl St, Boulder, CO 80302"},
    {"unit": "Centerplace", "address": "4239 Centerplace Dr, Greeley, CO 80634"},
    {"unit": "Powers", "address": "5697 Barnes Rd, Colorado Springs, CO 80917"},
    {"unit": "Aurora City Center", "address": "14505 E Alameda Ave, Aurora, CO 80012"},
    {"unit": "Interquest", "address": "1856 Democracy Point, Colorado Springs, CO 80908"},
    {"unit": "Englewood", "address": "5098 S Federal Blvd, Englewood, CO 80110"},
    {"unit": "DTC", "address": "7795 E Belleview Ave, Denver, CO 80111"},
    {"unit": "Sahara", "address": "2550 S Rainbow Blvd, Las Vegas, NV 89146"},
    {"unit": "Durango", "address": "7210 S Durango Dr, Las Vegas, NV 89113"},
    {"unit": "UNLV", "address": "4550 S Maryland Pkwy, Las Vegas, NV 89119"},
    {"unit": "Craig", "address": "345 W Craig Rd, North Las Vegas, NV 89032"},
    {"unit": "Stephanie", "address": "470 N Stephanie St, Henderson, NV 89014"},
    {"unit": "St Rose", "address": "3340 St Rose Pkwy, Henderson, NV 89052"},
]


if __name__ == "__main__":
    import sys
    brand = "Cheba Hut"
    print(f"[restaurant_ratings] key present: {bool(_places_key())} "
          f"({'Google Places — ratings+status' if _places_key() else 'OSM existence-only'})\n")
    rows = [{"unit": r["unit"], "name": brand, "address": r["address"]} for r in CHEBA_24]
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else len(rows)
    results = verify_locations(rows[:limit])
    for r in results:
        print(f"  {r['unit']:<20} {str(r.get('status','?'))[:42]:<42} "
              f"rating={r.get('rating')} n={r.get('review_count')} [{r.get('provider')}]")
    Path("outputs/cheba_addr_verify").mkdir(parents=True, exist_ok=True)
    json.dump(results, open("outputs/cheba_addr_verify/restaurant_ratings_run.json", "w"),
              indent=2, default=str)
    print(f"\n[wrote outputs/cheba_addr_verify/restaurant_ratings_run.json]")
