"""Live validation: crop-yield NDVI + oil-storage connectors (free Sentinel-2).

    python3 -m verticals.buyside_dd.validate_altdata
"""
from __future__ import annotations

from verticals.buyside_dd.connectors.base import ConnectorRequest
from verticals.buyside_dd.connectors.crop_yield_ndvi import CropYieldNdviConnector
from verticals.buyside_dd.connectors.oil_storage import OilStorageConnector

CROP_SITES = [
    {"name": "Iowa corn belt (central IA)", "lat": 42.03, "lon": -93.60, "radius_km": 1.5},
    {"name": "Illinois corn belt (Champaign Co)", "lat": 40.10, "lon": -88.20, "radius_km": 1.5},
]
OIL_SITES = [
    {"name": "Cushing OK — WTI delivery tank farms", "lat": 36.00, "lon": -96.77, "radius_km": 3.0},
]


def run_crop(site):
    c = CropYieldNdviConnector()
    res = c.query(ConnectorRequest(extra={"lat": site["lat"], "lon": site["lon"], "radius_km": site["radius_km"],
                                          "current_year": 2025, "n_prior": 4,
                                          "peak_start_md": "07-10", "peak_end_md": "08-25", "cloud_max": 25}))
    print(f"\n── CROP  {site['name']}  (r={site['radius_km']}km)")
    if not res.success:
        print(f"   FAILED: {res.error_kind} — {res.error_detail}"); return
    by = {o.attribute: o for o in res.observations}
    print("   peak-season mean NDVI by year:")
    for s in by["crop_ndvi_series"].value:
        print(f"      {s['year']}  {s['date']}  NDVI {s['mean_ndvi']:+.3f}  ({s['cloud_pct']:.0f}% cloud)")
    yoy = by["crop_ndvi_yoy_delta"].value
    vpa = by["crop_ndvi_vs_prior_avg"]
    print(f"   2025 vs 2024 ΔNDVI {yoy:+.3f}   |   2025 vs prior-avg {vpa.value:+.3f} "
          f"(prior avg {vpa.extra['prior_years_avg']:+.3f})")
    print(f"   => {by['crop_condition_vs_prior'].value}   [confidence {by['crop_ndvi_peak'].confidence}]")


def run_oil(site):
    c = OilStorageConnector()
    res = c.query(ConnectorRequest(extra={"lat": site["lat"], "lon": site["lon"], "radius_km": site["radius_km"],
                                          "cloud_max": 15}))
    print(f"\n── OIL  {site['name']}  (r={site['radius_km']}km)")
    if not res.success:
        print(f"   FAILED: {res.error_kind} — {res.error_detail}"); return
    by = {o.attribute: o for o in res.observations}
    print("   tank-farm shadow by period (sun-normalized 'norm' = inverse fill proxy):")
    for s in by["storage_series"].value:
        print(f"      {s['date']}  shadow {s['shadow_fraction']:.3f} -> norm {s['shadow_norm']:.3f}  "
              f"sun {s['sun_elev']:.0f}°  ({s['cloud']:.0f}% cloud)")
    inv = by["petroleum_storage_inventory"].value
    print(f"   => utilization proxy {inv['utilization_proxy_0to1']:.2f} (0=empty,1=full within window); "
          f"latest {inv['direction']}   [confidence {by['petroleum_storage_inventory'].confidence}]")
    print(f"      caveat: {by['petroleum_storage_inventory'].extra['caveat']}")


def main():
    print("ALT-DATA CONNECTORS — live validation (free Sentinel-2, no auth)")
    print("\n=== CROP YIELD / CONDITION (NDVI revenue cross-check) ===")
    for s in CROP_SITES:
        run_crop(s)
    print("\n=== PETROLEUM STORAGE (tank-farm shadow proxy) ===")
    for s in OIL_SITES:
        run_oil(s)
    print("\ndone.")


if __name__ == "__main__":
    main()
