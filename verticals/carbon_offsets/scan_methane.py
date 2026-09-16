"""
Carbon Mapper plume scan for all active VCS waste/methane projects in CM coverage.

Output: methane_scan_results.json - per-project capture-rate divergence scores.
"""
from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path

import httpx

DATA_DIR = Path(__file__).parent / "data"
RS_CACHE = Path(__file__).parent / "rs_cache"
CM_API = "https://api.carbonmapper.org/api/v1/stac/search"
# Carbon Mapper coverage bbox (approx, from STAC collection extent)
CM_BBOX = (-122.0, -34.85, 56.72, 48.45)
# Collections that publish point-source CH4 plumes
CM_COLLECTIONS = ["l4a-ch4-mfa-v1", "l4a-ch4-mfa-v3a", "l4a-ch4-mfa-jpl",
                  "l4a-ch4-mf-v1", "l4a-ch4-mfm-v1", "l4a-ch4-mfma-v1"]
# Sectors of interest:
#   1B = Fugitive emissions (oil/gas/coal)  - 1B1 solid fuels (coal), 1B2 oil & gas
#   3   = Agriculture (livestock manure)
#   6A  = Solid waste (landfills)
#   6B  = Wastewater
METHANE_SECTORS = {"1B", "1B1", "1B2", "3", "6", "6A", "6B"}
GWP_CH4 = 28


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlon / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def in_cm_coverage(lat: float, lon: float) -> bool:
    return (CM_BBOX[0] <= lon <= CM_BBOX[2]) and (CM_BBOX[1] <= lat <= CM_BBOX[3])


def fetch_plumes_near(lat: float, lon: float, buffer_deg: float = 0.2,
                      client: httpx.Client = None) -> list[dict]:
    bbox = [lon - buffer_deg, lat - buffer_deg, lon + buffer_deg, lat + buffer_deg]
    plumes = []
    own_client = client is None
    if own_client:
        client = httpx.Client(timeout=20, headers={"User-Agent": "Mozilla/5.0 SignalOS/1.0"})
    try:
        for coll in CM_COLLECTIONS:
            r = client.post(CM_API, json={"bbox": bbox, "collections": [coll], "limit": 100})
            if r.status_code != 200:
                continue
            for f in r.json().get("features", []):
                p = f["properties"]
                plat = p.get("cm:plume_latitude")
                plon = p.get("cm:plume_longitude")
                if plat is None or plon is None:
                    continue
                plumes.append({
                    "id": f["id"],
                    "collection": coll,
                    "datetime": p.get("datetime", "")[:10],
                    "plat": plat, "plon": plon,
                    "emission_kghr": p.get("cm:emission"),
                    "uncertainty_kghr": p.get("cm:emission_uncertainty"),
                    "sector": p.get("cm:plume:sector", "?"),
                    "instrument": (p.get("instruments") or ["?"])[0]
                                  if isinstance(p.get("instruments"), list) else "?",
                    "distance_km": haversine_km(lat, lon, plat, plon),
                })
    finally:
        if own_client:
            client.close()
    return plumes


def score_methane_project(p: dict) -> dict:
    """Score one waste/methane project against Carbon Mapper plumes."""
    pid = p["resourceIdentifier"]
    result = {
        "id": pid,
        "name": p["resourceName"],
        "country": p["country"],
        "subcat": p.get("protocolSubCategories"),
        "category": p.get("protocolCategories"),
        "claim_tco2_yr": p.get("estAnnualEmissionReductions"),
        "status": "started",
    }

    sp = RS_CACHE / f"{pid}.json"
    if not sp.exists():
        # Try to fetch
        try:
            r = httpx.get(f"https://registry.verra.org/uiapi/resource/resourceSummary/{pid}",
                          timeout=20, headers={"User-Agent": "Mozilla/5.0"})
            if r.status_code == 200:
                sp.write_text(r.text)
        except Exception:
            pass

    if not sp.exists():
        result["status"] = "no_summary"
        return result

    with open(sp) as f:
        summary = json.load(f)
    loc = summary.get("location") or {}
    lat = loc.get("latitude")
    lon = loc.get("longitude")
    if lat is None or lon is None:
        result["status"] = "no_coords"
        return result
    result["lat"] = lat
    result["lon"] = lon

    if not in_cm_coverage(lat, lon):
        result["status"] = "outside_cm_coverage"
        return result

    plumes = fetch_plumes_near(lat, lon)
    nearby = [pl for pl in plumes if pl["distance_km"] <= 5]
    methane_nearby = [pl for pl in nearby if pl["sector"] in METHANE_SECTORS]
    result["plumes_5km_total"] = len(nearby)
    result["plumes_5km_methane_sector"] = len(methane_nearby)

    # Pick relevant plumes by project type
    cat = (p.get("protocolCategories") or "")
    if "Waste handling" in cat or "Energy industries" in cat:
        relevant_sectors = {"6A", "6", "6B"}
    elif "Fugitive emissions" in cat:
        relevant_sectors = {"1B", "1B1", "1B2"}
    elif "Livestock" in cat:
        relevant_sectors = {"3"}
    else:
        relevant_sectors = METHANE_SECTORS

    relevant = [pl for pl in nearby if pl["sector"] in relevant_sectors]
    result["plumes_5km_relevant_sector"] = len(relevant)

    # Per-detection emission summary
    rates = [pl["emission_kghr"] for pl in relevant if pl["emission_kghr"]]
    result["mean_obs_kghr"] = sum(rates) / len(rates) if rates else None
    result["median_obs_kghr"] = sorted(rates)[len(rates) // 2] if rates else None
    result["max_obs_kghr"] = max(rates) if rates else None
    result["n_observations"] = len(rates)
    result["plume_dates"] = sorted({pl["datetime"] for pl in relevant})

    # Convert claim to capture rate kg CH4/hr
    claim = p.get("estAnnualEmissionReductions") or 0
    if claim:
        capture_kghr = claim * 1000 / GWP_CH4 / 8760
        result["claim_capture_kghr"] = capture_kghr
        if rates:
            avg_obs = sum(rates) / len(rates)
            implied_capture_rate = capture_kghr / (capture_kghr + avg_obs) if (capture_kghr + avg_obs) > 0 else None
            result["implied_capture_rate"] = implied_capture_rate
            result["leakage_to_capture_ratio"] = avg_obs / capture_kghr if capture_kghr else None
            if implied_capture_rate is None:
                result["severity"] = "no_score"
            elif implied_capture_rate < 0.30:
                result["severity"] = "RED_FLAG_LOW_CAPTURE"
            elif implied_capture_rate < 0.50:
                result["severity"] = "SEVERE_LOW_CAPTURE"
            elif implied_capture_rate < 0.70:
                result["severity"] = "MODERATE_LOW_CAPTURE"
            else:
                result["severity"] = "PASS"
        else:
            result["severity"] = "no_observations"

    # Save sample plumes
    result["sample_plumes"] = [
        {"date": pl["datetime"], "kghr": pl["emission_kghr"], "sector": pl["sector"],
         "dist_km": round(pl["distance_km"], 2), "instrument": pl["instrument"]}
        for pl in sorted(relevant, key=lambda x: x["distance_km"])[:5]
    ]
    result["status"] = "ok"
    return result


def main():
    with open(DATA_DIR / "verra_projects.json") as f:
        projects = json.load(f)

    # Filter to methane-relevant active projects
    METHANE_KEYWORDS = ["Waste handling", "Fugitive emissions", "Livestock"]
    ACTIVE = {"Registered", "Late to verify", "Verification approval requested"}
    seen = set()
    targets = []
    for p in projects:
        pid = p.get("resourceIdentifier")
        if pid in seen:
            continue
        cat = p.get("protocolCategories") or ""
        if not any(k in cat for k in METHANE_KEYWORDS):
            continue
        if p.get("resourceStatus") not in ACTIVE:
            continue
        if (p.get("estAnnualEmissionReductions") or 0) < 5000:
            continue
        seen.add(pid)
        targets.append(p)

    targets.sort(key=lambda x: -(x.get("estAnnualEmissionReductions") or 0))
    print(f"Methane targets (active, >5k tCO2/yr): {len(targets)}", file=sys.stderr)

    out_path = DATA_DIR / "methane_scan_results.json"
    results = []
    if out_path.exists():
        with open(out_path) as f:
            results = json.load(f)
    done_ids = {r["id"] for r in results}
    print(f"Already done: {len(done_ids)}", file=sys.stderr)

    t_start = time.time()
    for i, p in enumerate(targets):
        pid = p["resourceIdentifier"]
        if pid in done_ids:
            continue
        t0 = time.time()
        try:
            r = score_methane_project(p)
        except Exception as e:
            r = {"id": pid, "status": f"score_exception: {str(e)[:120]}"}
        r["elapsed_s"] = round(time.time() - t0, 1)
        results.append(r)
        sev = r.get("severity", r.get("status", "?"))[:25]
        print(f"  [{i+1}/{len(targets)}] {pid:>5}  {r['elapsed_s']:>4.1f}s  {sev:<25}  {p['resourceName'][:50]}", file=sys.stderr)

        if (i + 1) % 20 == 0:
            with open(out_path, "w") as f:
                json.dump(results, f, indent=2)
        time.sleep(0.2)

    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nTotal time: {(time.time()-t_start)/60:.1f} min", file=sys.stderr)
    print(f"Saved {len(results)} results to {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
