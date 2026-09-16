"""Live validation: free Sentinel-2 buildout connector on real parcels.

    python3 -m verticals.buyside_dd.validate_sentinel2_buildout

Sites chosen to map onto our verticals:
  - CFD housing buildout (muni land-secured)  : Ontario Ranch / New Model Colony, CA
  - Facility buildout (buyside DD)             : Hyundai Metaplant, Ellabell GA
  - Stable developed control (negative)        : established Phoenix residential
"""
from __future__ import annotations

from verticals.buyside_dd.connectors.base import ConnectorRequest
from verticals.buyside_dd.connectors.sentinel2_buildout import Sentinel2BuildoutConnector

BASELINE = "2020-01-01T00:00:00Z/2021-06-30T23:59:59Z"
RECENT = "2025-06-01T00:00:00Z/2026-06-15T23:59:59Z"

SITES = [
    {"name": "Teravalis/Douglas Ranch new MPC (AZ) — desert→master-planned community", "lat": 33.545, "lon": -112.62,
     "radius_km": 0.7, "expect": "BUILDOUT"},
    {"name": "Hyundai Metaplant facility (Ellabell GA) — timber→plant", "lat": 32.158, "lon": -81.430,
     "radius_km": 0.8, "expect": "BUILDOUT"},
    {"name": "Established Phoenix residential (control)", "lat": 33.452, "lon": -112.045,
     "radius_km": 0.6, "expect": "STABLE"},
]


def run(site: dict) -> None:
    conn = Sentinel2BuildoutConnector()
    req = ConnectorRequest(extra={"lat": site["lat"], "lon": site["lon"], "radius_km": site["radius_km"],
                                  "baseline": BASELINE, "recent": RECENT, "cloud_max": 20})
    res = conn.query(req)
    print(f"\n── {site['name']}")
    print(f"   (lat {site['lat']}, lon {site['lon']}, r={site['radius_km']}km; expect {site['expect']})")
    if not res.success:
        print(f"   FAILED: {res.error_kind} — {res.error_detail}")
        return
    by = {o.attribute: o for o in res.observations}
    bs, rs = by["baseline_scene"].value, by["recent_scene"].value
    ndbi, ndvi = by["ndbi_delta"], by["ndvi_delta"]
    built = by["construction_activity"]
    print(f"   baseline scene {bs['date']} ({bs['cloud_pct']:.0f}% cloud)   "
          f"recent scene {rs['date']} ({rs['cloud_pct']:.0f}% cloud)")
    print(f"   NDBI built-up : {ndbi.extra['baseline_ndbi']:+.3f} -> {ndbi.extra['recent_ndbi']:+.3f}   "
          f"Δ {ndbi.value:+.3f}")
    print(f"   NDVI green    : {ndvi.extra['baseline_ndvi']:+.3f} -> {ndvi.extra['recent_ndvi']:+.3f}   "
          f"Δ {ndvi.value:+.3f}")
    verdict = "BUILDOUT DETECTED" if built.value else "no significant buildout (stable)"
    corr = " (corroborated by vegetation loss)" if built.extra.get("corroborated_by_ndvi_drop") else ""
    print(f"   => {verdict}{corr}   [confidence {built.confidence}]")


def main():
    print("SENTINEL-2 BUILDOUT CONNECTOR — live validation (free, no auth)")
    for s in SITES:
        run(s)
    print("\ndone.")


if __name__ == "__main__":
    main()
