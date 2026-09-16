"""Mangrove-specific scoring — fixes the methodology breakdown that hung the V2 forest scan.

Why this exists:
  The V2 buffer-ring synthetic-control method (Hansen GFC + 5-30km buffer)
  fails for mangroves because:
    (a) Hansen v1.11 is calibrated for upland forest, not intertidal mangroves
    (b) A 5-30km buffer around a coastal project is mostly ocean — there's no
        valid matched-neighbor counterfactual
  This produces pathological tile-fetch patterns that hang the scanner
  (signal.alarm doesn't preempt rasterio C calls).

This methodology:
  1. Uses Global Mangrove Watch v3 (Bunting et al. 2018/2022) — purpose-built
     mangrove extent layers at ~25m resolution
  2. Computes mangrove EXTENT change between 2010 and 2020 within the project AOI
  3. Uses a coastline-following buffer (constrained to GMW mangrove biome — no ocean)
     as the synthetic control
  4. Uses mangrove-specific carbon stock (350 tCO2/ha biome midpoint per Donato et al. 2011)
     instead of the upland 165 tCO2/ha default

Run via: python3 score_mangrove.py [project_id]
Or imported and called from scan_forest_v2.main() dispatch.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import numpy as np

# Set GDAL HTTP timeouts BEFORE importing rasterio
os.environ.setdefault("CPL_CURL_TIMEOUT", "30")
os.environ.setdefault("GDAL_HTTP_TIMEOUT", "30")
os.environ.setdefault("GDAL_HTTP_MAX_RETRY", "2")

import rasterio
from rasterio.features import rasterize
from rasterio.windows import from_bounds
from shapely.geometry import Polygon, MultiPolygon, box
from shapely.ops import unary_union

# Import shared utilities from the forest scanner
sys.path.insert(0, str(Path(__file__).parent))
from scan_forest_v2 import parse_kml_polygons, KML_CACHE


HERE = Path(__file__).parent
DATA_DIR = HERE / "data"
GMW_DIR_2020 = DATA_DIR / "gmw" / "gmw_v3_2020"
GMW_DIR_2010 = DATA_DIR / "gmw" / "gmw_v3_2010"

# Carbon stock per hectare for mangrove biome (Donato et al. 2011, Nature Geoscience)
# Tropical mangroves: 600-1500 tC/ha → 2200-5500 tCO2/ha total
# Above-ground component only (relevant for canopy-loss): 100-200 tC/ha → 366-733 tCO2/ha
# We use 350 tCO2/ha as a conservative midpoint for above-ground carbon equivalent.
MANGROVE_CARBON_TCO2_HA = 350

# Pixel size at equator (degrees → meters → hectares)
GMW_RES_DEG = 0.000222222222222
def pix_to_ha_at_lat(lat_deg: float) -> float:
    m_per_deg_lat = 111_320
    m_per_deg_lon = 111_320 * np.cos(np.radians(lat_deg))
    pix_m2 = (GMW_RES_DEG * m_per_deg_lat) * (GMW_RES_DEG * m_per_deg_lon)
    return pix_m2 / 10_000


def gmw_tiles_for_bbox(min_lon: float, min_lat: float, max_lon: float, max_lat: float) -> list[str]:
    """List GMW tile filenames covering a bounding box.

    GMW v3 tile naming: GMW_NXXEYYY_2020_v3.tif where N/S = top-lat sign,
    E/W = left-lon sign. Tiles are 1×1 degree. Top-lat is the upper edge.
    """
    tiles = []
    # Mangroves are tropical/subtropical: 35N to 35S
    for top_lat in range(35, -36, -1):
        bottom_lat = top_lat - 1
        if bottom_lat >= max_lat or top_lat <= min_lat:
            continue
        for left_lon in range(-180, 180):
            right_lon = left_lon + 1
            if right_lon <= min_lon or left_lon >= max_lon:
                continue
            # GMW filename convention: N{lat:02d}W{lon:03d} (letter BEFORE number)
            # e.g., GMW_N13W017 covers (-17,12) to (-16,13).
            lat_s = f"{'N' if top_lat >= 0 else 'S'}{abs(top_lat):02d}"
            lon_s = f"{'E' if left_lon >= 0 else 'W'}{abs(left_lon):03d}"
            tiles.append(f"GMW_{lat_s}{lon_s}")
    return tiles


def read_mangrove_extent_in_polygon(polygon, year: int) -> tuple[float, float]:
    """Compute (mangrove_ha_in_polygon, total_polygon_ha) using GMW {year} tiles.

    Returns (mangrove_ha, polygon_area_ha). If polygon is in non-mangrove zone,
    returns (0, polygon_area_ha).
    """
    gmw_dir = GMW_DIR_2020 if year == 2020 else GMW_DIR_2010 if year == 2010 else None
    if gmw_dir is None:
        raise ValueError(f"No GMW data for year {year}; have 2010 and 2020 only")

    bounds = polygon.bounds  # (min_lon, min_lat, max_lon, max_lat)
    tiles = gmw_tiles_for_bbox(*bounds)

    total_mangrove_pix = 0
    total_aoi_pix = 0
    centroid_lat = polygon.centroid.y
    pix_to_ha = pix_to_ha_at_lat(centroid_lat)

    for tile_id in tiles:
        path = gmw_dir / f"{tile_id}_{year}_v3.tif"
        if not path.exists():
            # Tile may not exist for ocean-only or non-mangrove areas
            continue
        try:
            with rasterio.open(path) as src:
                # Compute window for the polygon's bbox intersected with the tile's bounds
                tile_bounds = src.bounds
                isect_min_lon = max(bounds[0], tile_bounds.left)
                isect_min_lat = max(bounds[1], tile_bounds.bottom)
                isect_max_lon = min(bounds[2], tile_bounds.right)
                isect_max_lat = min(bounds[3], tile_bounds.top)
                if isect_max_lon <= isect_min_lon or isect_max_lat <= isect_min_lat:
                    continue

                window = from_bounds(isect_min_lon, isect_min_lat, isect_max_lon, isect_max_lat, src.transform)
                arr = src.read(1, window=window)
                if arr.size == 0:
                    continue

                # Rasterize the polygon to the same window's transform
                window_transform = src.window_transform(window)
                # Clip polygon to window bounds for efficiency
                window_bbox = box(isect_min_lon, isect_min_lat, isect_max_lon, isect_max_lat)
                clipped = polygon.intersection(window_bbox)
                if clipped.is_empty:
                    continue
                shapes = [clipped] if not hasattr(clipped, "geoms") else list(clipped.geoms)
                shapes = [s for s in shapes if not s.is_empty]
                if not shapes:
                    continue
                aoi_mask = rasterize(
                    [(s, 1) for s in shapes],
                    out_shape=arr.shape,
                    transform=window_transform,
                    fill=0,
                    dtype="uint8",
                )
                in_aoi = (aoi_mask == 1)
                total_mangrove_pix += int(((arr == 1) & in_aoi).sum())
                total_aoi_pix += int(in_aoi.sum())
        except Exception as e:
            # Skip unreadable tiles
            continue

    return total_mangrove_pix * pix_to_ha, total_aoi_pix * pix_to_ha


def coastline_constrained_buffer(aoi, inner_km: float = 5, outer_km: float = 50):
    """Build a buffer ring around aoi, constrained roughly to a coastal band.

    For AOIs with many small polygons (e.g. 10k+ planting sites), buffering the
    full multi-polygon by 50km creates a huge union that's slow to rasterize.
    We use the convex hull of the AOI as the buffer base — captures the project's
    geographic extent without per-polygon buffering complexity. The resulting
    buffer is then masked to GMW mangrove biome at read time, so the effective
    buffer is mangrove-only — no ocean intersection, no inland intersection.
    """
    hull = aoi.convex_hull
    centroid = hull.centroid
    deg_per_km_lat = 1 / 110.574
    deg_per_km_lon = 1 / max(111.32 * np.cos(np.radians(centroid.y)), 1.0)
    deg_per_km = (deg_per_km_lat + deg_per_km_lon) / 2

    inner = hull.buffer(inner_km * deg_per_km)
    outer = hull.buffer(outer_km * deg_per_km)
    return outer.difference(inner)


def score_mangrove(project: dict, summary: dict) -> dict:
    """Mangrove-specific synthetic-control scoring.

    Returns same shape as score_project_synthetic_control() so downstream code
    (calibration, insurance output, satellite-direct report) works unchanged.
    """
    pid = project["id"]
    out = {
        "id": pid,
        "name": project.get("name"),
        "subcat": project.get("subcat"),
        "country": project.get("country"),
        "claim_tco2_yr": project.get("est_annual_tco2"),
        "method": "mangrove_v1_gmw",
        "inner_km": 5,
        "outer_km": 50,
    }

    # Parse KMLs. Cache filename pattern is just `{pid}.kml`.
    kml_path = KML_CACHE / f"{pid}.kml"
    if not kml_path.exists():
        out["status"] = "kml_not_cached"
        return out
    polygons = parse_kml_polygons(kml_path)
    if not polygons:
        out["status"] = "kml_parse_failed"
        return out

    # Filter envelope/bounding-box polygons. Some Verra mangrove KMLs include
    # one or two giant rectangles representing project regional boundaries
    # alongside thousands of small actual planting-site polygons. A real mangrove
    # project site is at most a few thousand ha; envelopes are millions.
    ENVELOPE_HA_THRESHOLD = 100_000
    filtered = []
    n_envelopes = 0
    for poly in polygons:
        clat = poly.centroid.y
        area_ha = poly.area * 111.32 * 111.32 * np.cos(np.radians(clat)) * 100
        if area_ha > ENVELOPE_HA_THRESHOLD:
            n_envelopes += 1
            continue
        filtered.append(poly)
    if n_envelopes:
        out["envelopes_filtered"] = n_envelopes
    if not filtered:
        out["status"] = "all_polygons_envelope_artifacts"
        return out
    polygons = filtered

    aoi = unary_union(polygons)
    if isinstance(aoi, Polygon):
        aoi = MultiPolygon([aoi])

    # Crude area sanity check
    centroid_lat = aoi.centroid.y
    aoi_area_ha = aoi.area * 111.32 * 111.32 * np.cos(np.radians(centroid_lat)) * 100
    out["aoi_area_ha"] = round(aoi_area_ha, 1)
    out["n_polygons"] = len(polygons)
    if aoi_area_ha < 1 or aoi_area_ha > 10_000_000:
        out["status"] = f"implausible_area: {aoi_area_ha:.0f} ha"
        return out

    # Mangrove extent in AOI (2010 and 2020)
    aoi_mangrove_2020_ha, aoi_total_ha = read_mangrove_extent_in_polygon(aoi, 2020)
    aoi_mangrove_2010_ha, _ = read_mangrove_extent_in_polygon(aoi, 2010)

    out["aoi_mangrove_2010_ha"] = round(aoi_mangrove_2010_ha, 1)
    out["aoi_mangrove_2020_ha"] = round(aoi_mangrove_2020_ha, 1)

    # Net change in AOI 2010→2020 (positive = restoration; negative = loss)
    aoi_net_change_ha = aoi_mangrove_2020_ha - aoi_mangrove_2010_ha
    out["aoi_net_change_ha_2010_2020"] = round(aoi_net_change_ha, 1)

    # Buffer ring (constrained to GMW mangrove biome via masking at read time)
    buffer_ring = coastline_constrained_buffer(aoi, inner_km=5, outer_km=50)
    if buffer_ring.is_empty:
        out["status"] = "buffer_empty"
        return out

    buffer_mangrove_2020_ha, _ = read_mangrove_extent_in_polygon(buffer_ring, 2020)
    buffer_mangrove_2010_ha, _ = read_mangrove_extent_in_polygon(buffer_ring, 2010)
    out["buffer_mangrove_2010_ha"] = round(buffer_mangrove_2010_ha, 1)
    out["buffer_mangrove_2020_ha"] = round(buffer_mangrove_2020_ha, 1)

    # Two-stage sanity check, in increasing severity:
    # 1. If neither AOI nor buffer has any mangrove, project simply isn't in
    #    mangrove biome — methodology doesn't apply, mark unverifiable.
    if (aoi_mangrove_2010_ha < 5 and aoi_mangrove_2020_ha < 5
            and buffer_mangrove_2010_ha < 10 and buffer_mangrove_2020_ha < 10):
        out["status"] = "not_in_mangrove_biome"
        return out

    # 2. If buffer has mangrove but AOI has zero → project's claimed AOI doesn't
    #    overlap with detected mangrove canopy at GMW resolution. For an ARR
    #    project this could mean (a) restoration plantings haven't reached
    #    GMW-detectable canopy, (b) project sites are in degraded land that
    #    never had mangrove, or (c) the claim is overstated. Surface as a
    #    severity finding rather than skipping.
    subcat = (project.get("subcat") or "").upper()
    is_arr = "ARR" in subcat or "WRC" in subcat
    if aoi_mangrove_2010_ha < 5 and aoi_mangrove_2020_ha < 5:
        out["status"] = "ok"  # we have a meaningful finding to report
        out["interpretation"] = (
            "Buffer has mangrove biome but AOI shows zero mangrove canopy at "
            f"GMW v3 25m resolution in both 2010 and 2020. For {'ARR' if is_arr else 'this'} "
            f"project, this indicates {'restoration has not produced detectable canopy' if is_arr else 'the project AOI may not actually be in mangrove biome'}."
        )
        out["severity"] = "RED_FLAG_NEGATIVE" if is_arr else "RED_FLAG_AOI_OUTSIDE_BIOME"
        out["ratio_observed_to_claimed"] = 0.0
        out["divergence_normalized"] = 1.0
        out["counterfactual_change_ha_yr"] = round((buffer_mangrove_2020_ha - buffer_mangrove_2010_ha) / 10, 2)
        out["observed_aoi_change_ha_yr"] = 0.0
        out["project_benefit_ha_yr"] = 0.0
        claim = project.get("est_annual_tco2") or 0
        out["implied_benefit_ha_yr"] = round(claim / MANGROVE_CARBON_TCO2_HA, 2) if claim else 0
        out["carbon_stock_tco2_ha"] = MANGROVE_CARBON_TCO2_HA
        return out

    buffer_net_change_ha = buffer_mangrove_2020_ha - buffer_mangrove_2010_ha
    out["buffer_net_change_ha_2010_2020"] = round(buffer_net_change_ha, 1)

    # Rates per ha of starting mangrove
    aoi_change_rate = aoi_net_change_ha / max(aoi_mangrove_2010_ha, 1)
    buffer_change_rate = buffer_net_change_ha / max(buffer_mangrove_2010_ha, 1)
    out["aoi_change_rate_per_ha_decade"] = round(aoi_change_rate, 4)
    out["buffer_change_rate_per_ha_decade"] = round(buffer_change_rate, 4)

    # Counterfactual: what would have happened in AOI without project = buffer rate × AOI 2010 area
    counterfactual_change_ha_decade = buffer_change_rate * aoi_mangrove_2010_ha
    counterfactual_change_ha_yr = counterfactual_change_ha_decade / 10
    aoi_change_ha_yr = aoi_net_change_ha / 10

    out["counterfactual_change_ha_yr"] = round(counterfactual_change_ha_yr, 2)
    out["observed_aoi_change_ha_yr"] = round(aoi_change_ha_yr, 2)

    # Project benefit = aoi_change - counterfactual_change
    # Positive = project did better than counterfactual (good)
    project_benefit_ha_yr = aoi_change_ha_yr - counterfactual_change_ha_yr
    out["project_benefit_ha_yr"] = round(project_benefit_ha_yr, 2)

    # Compare to claim
    claim_tco2_yr = project.get("est_annual_tco2") or 0
    implied_benefit_ha_yr = claim_tco2_yr / MANGROVE_CARBON_TCO2_HA if claim_tco2_yr else 0
    out["implied_benefit_ha_yr"] = round(implied_benefit_ha_yr, 2)
    out["carbon_stock_tco2_ha"] = MANGROVE_CARBON_TCO2_HA

    if implied_benefit_ha_yr > 0:
        ratio = project_benefit_ha_yr / implied_benefit_ha_yr
    else:
        ratio = None
    out["ratio_observed_to_claimed"] = round(ratio, 3) if ratio is not None else None

    # Severity tier (matches forest scoring conventions)
    if ratio is None:
        out["severity"] = "uncomputable"
    elif ratio < 0:
        out["severity"] = "RED_FLAG_NEGATIVE"
    elif ratio < 0.25:
        out["severity"] = "SEVERE_UNDERDELIVERY"
    elif ratio < 0.75:
        out["severity"] = "MODERATE_UNDERDELIVERY"
    else:
        out["severity"] = "PASS"
    out["divergence_normalized"] = round(max(min(1.0 - (ratio or 0), 2.0), -2.0), 3)

    out["status"] = "ok"
    return out


if __name__ == "__main__":
    # Smoke test against project 2834 — Sine Saloum/Casamance Mangroves, Senegal
    # (the project that hung the V2 forest scan)
    pid = sys.argv[1] if len(sys.argv) > 1 else "2834"

    with open(DATA_DIR / "forest_inventory.json") as f:
        inv = json.load(f)
    project = next((p for p in inv if str(p["id"]) == str(pid)), None)
    if not project:
        print(f"Project {pid} not in inventory", file=sys.stderr)
        sys.exit(1)

    sp = HERE / "rs_cache" / f"{pid}.json"
    if not sp.exists():
        print(f"No rs_cache summary for {pid} at {sp}", file=sys.stderr)
        sys.exit(1)
    with open(sp) as f:
        summary = json.load(f)

    print(f"Scoring mangrove project {pid}: {project['name'][:60]}", file=sys.stderr)
    print(f"  Country: {project.get('country')}", file=sys.stderr)
    print(f"  Claim: {project.get('est_annual_tco2'):,.0f} tCO2/yr" if project.get('est_annual_tco2') else "  Claim: unknown", file=sys.stderr)

    t0 = time.time()
    result = score_mangrove(project, summary)
    elapsed = time.time() - t0
    print(f"\nElapsed: {elapsed:.1f}s", file=sys.stderr)
    print(f"\nResult:")
    for k, v in result.items():
        print(f"  {k}: {v}")
