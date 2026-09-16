"""Compare per-polygon buffer vs convex-hull buffer on the same projects.

For projects that already have ok V2 results (per-polygon buffer), re-run
with convex-hull buffer and compare:
  - buffer_area_ha
  - buffer_forest_2000_ha
  - buffer_annual_loss_rate
  - ratio_observed_to_claimed
  - severity_tier

Usage: python3 compare_buffer_methods.py [project_id ...]
       python3 compare_buffer_methods.py     # auto-pick 5 high-poly successes
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import scan_forest_v2 as sfv2

DATA_DIR = Path(__file__).parent / "data"
RS_CACHE = Path(__file__).parent / "rs_cache"


def score_with_method(project, summary, force_convex_hull):
    """Run score_project_synthetic_control with a temporarily patched
    buffer_ring_geometry that either always uses convex hull or never does.
    """
    original = sfv2.buffer_ring_geometry

    def patched(project_geom, inner_km=5, outer_km=30, avg_lat=0):
        import numpy as np
        lat_deg_per_km = 1 / 111.32
        lon_deg_per_km = 1 / (111.32 * np.cos(np.radians(avg_lat)))
        inner_deg = inner_km * (lat_deg_per_km + lon_deg_per_km) / 2
        outer_deg = outer_km * (lat_deg_per_km + lon_deg_per_km) / 2
        base = project_geom.convex_hull if force_convex_hull else project_geom
        return base.buffer(outer_deg).difference(base.buffer(inner_deg))

    sfv2.buffer_ring_geometry = patched
    try:
        t0 = time.time()
        r = sfv2.score_project_synthetic_control(project, summary)
        elapsed = time.time() - t0
        r["_elapsed_s"] = elapsed
        return r
    finally:
        sfv2.buffer_ring_geometry = original


def main():
    with open(DATA_DIR / "forest_inventory.json") as f:
        inv = json.load(f)
    inv_by_id = {str(p["id"]): p for p in inv}

    with open(DATA_DIR / "forest_scan_results_v2.json") as f:
        existing = json.load(f)
    by_id = {str(r["id"]): r for r in existing}

    if len(sys.argv) > 1:
        pids = sys.argv[1:]
    else:
        # Pick 5 high-polygon successful records
        ok = [r for r in existing if r.get("severity") and r.get("n_polygons", 0) >= 1000]
        ok.sort(key=lambda r: r["n_polygons"])
        pids = [str(r["id"]) for r in ok[-5:]]

    print(f"\nComparing per-polygon vs convex-hull buffer on {len(pids)} projects\n")
    print(f"{'PID':<6} {'n_poly':>7}  {'method':<12}  {'buffer_area_ha':>15}  {'buf_loss/yr':>11}  {'ratio':>7}  {'severity':<22}  {'time':>6}")
    print("-" * 110)

    for pid in pids:
        p = inv_by_id.get(pid)
        if not p:
            print(f"{pid}: not in inventory")
            continue
        sp = RS_CACHE / f"{pid}.json"
        if not sp.exists():
            print(f"{pid}: no rs_cache")
            continue
        with open(sp) as f:
            summary = json.load(f)

        # Per-polygon (original methodology)
        r_orig = score_with_method(p, summary, force_convex_hull=False)
        r_hull = score_with_method(p, summary, force_convex_hull=True)

        for label, r in [("per-polygon", r_orig), ("convex-hull", r_hull)]:
            buf_area = r.get("buffer_area_ha", 0) or 0
            buf_loss = r.get("buffer_annual_loss_rate", 0) or 0
            ratio = r.get("ratio_observed_to_claimed")
            ratio_s = f"{ratio:.3f}" if ratio is not None else "—"
            sev = (r.get("severity") or r.get("status") or "?")[:22]
            elapsed = r.get("_elapsed_s", 0)
            print(f"{pid:<6} {r.get('n_polygons','?'):>7}  {label:<12}  {buf_area:>15,.0f}  {buf_loss:>11.5f}  {ratio_s:>7}  {sev:<22}  {elapsed:>5.1f}s")
        print()


if __name__ == "__main__":
    main()
