"""
Full Hansen GFC scan of all active VCS forest projects with KML AOIs.

Output: forest_scan_results.json - per-project divergence scores.

Methodology:
  1. Download KML from Verra
  2. Parse polygons, build unified AOI MultiPolygon
  3. Determine Hansen 10°x10° tiles needed
  4. Read lossyear, treecover2000, datamask windows via /vsicurl/
  5. Mask to AOI polygons
  6. Compute pre-project (years before crediting start) vs project-period mean annual loss
  7. Score divergence vs project's claim
"""
from __future__ import annotations

import json
import os
import signal
import sys
import time
import traceback
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

# Set GDAL HTTP timeouts BEFORE importing rasterio
os.environ.setdefault("CPL_CURL_TIMEOUT", "30")
os.environ.setdefault("GDAL_HTTP_TIMEOUT", "30")
os.environ.setdefault("GDAL_HTTP_CONNECTTIMEOUT", "10")
os.environ.setdefault("GDAL_HTTP_MAX_RETRY", "2")
os.environ.setdefault("GDAL_HTTP_RETRY_DELAY", "1")
os.environ.setdefault("VSI_CACHE", "TRUE")
os.environ.setdefault("VSI_CACHE_SIZE", "67108864")  # 64MB

import httpx
import numpy as np
import rasterio
from rasterio.features import rasterize
from rasterio.windows import from_bounds
from shapely.geometry import Polygon
from shapely.ops import unary_union


class TimeoutError(Exception): pass

def _timeout_handler(signum, frame):
    raise TimeoutError("project scoring timed out")

KML_NS = {"kml": "http://www.opengis.net/kml/2.2"}
HANSEN_BASE = "https://storage.googleapis.com/earthenginepartners-hansen/GFC-2023-v1.11/Hansen_GFC-2023-v1.11_"
PIX_HA_AT_LAT = lambda lat: 0.00025 * 111320 * 0.00025 * 111320 * np.cos(np.radians(lat)) / 10000
CARBON_STOCK_TCO2_HA = 165  # generic mid-tropical estimate

DATA_DIR = Path(__file__).parent / "data"
KML_CACHE = DATA_DIR / "kml_cache"
KML_CACHE.mkdir(exist_ok=True, parents=True)


def hansen_tiles_for_bbox(min_lon: float, min_lat: float, max_lon: float, max_lat: float) -> list[str]:
    """Return Hansen tile names overlapping the given bbox.

    Hansen tiles are 10°×10° named by top-left corner. e.g., 00N_010E covers lat 10S–0, lon 10E–20E.
    """
    tiles = []
    for top_lat in range(80, -60, -10):
        bottom_lat = top_lat - 10
        if bottom_lat >= max_lat or top_lat <= min_lat:
            continue
        for left_lon in range(-180, 180, 10):
            right_lon = left_lon + 10
            if right_lon <= min_lon or left_lon >= max_lon:
                continue
            lat_str = f"{abs(top_lat):02d}{'N' if top_lat >= 0 else 'S'}"
            lon_str = f"{abs(left_lon):03d}{'E' if left_lon >= 0 else 'W'}"
            tiles.append(f"{lat_str}_{lon_str}")
    return tiles


def parse_kml_polygons(kml_path: Path) -> list[Polygon]:
    """Extract all valid Polygon geometries from a KML file."""
    try:
        tree = ET.parse(kml_path)
    except ET.ParseError:
        return []
    root = tree.getroot()
    polys = []
    for poly_elem in root.iter("{http://www.opengis.net/kml/2.2}Polygon"):
        outer = poly_elem.find(".//kml:outerBoundaryIs/kml:LinearRing/kml:coordinates", KML_NS)
        if outer is None or not outer.text:
            continue
        outer_coords = []
        for tup in outer.text.strip().split():
            parts = tup.split(",")
            if len(parts) >= 2:
                try:
                    outer_coords.append((float(parts[0]), float(parts[1])))
                except ValueError:
                    continue
        if len(outer_coords) < 4:
            continue
        inner_coords = []
        for inner in poly_elem.findall(".//kml:innerBoundaryIs/kml:LinearRing/kml:coordinates", KML_NS):
            if not inner.text:
                continue
            cs = []
            for tup in inner.text.strip().split():
                parts = tup.split(",")
                if len(parts) >= 2:
                    try:
                        cs.append((float(parts[0]), float(parts[1])))
                    except ValueError:
                        continue
            if len(cs) >= 4:
                inner_coords.append(cs)
        try:
            p = Polygon(outer_coords, holes=inner_coords if inner_coords else None)
            if p.is_valid and p.area > 0:
                polys.append(p)
        except Exception:
            continue
    return polys


def download_kml(uri: str, pid: str) -> Path | None:
    """Download a KML from a Verra document URL with caching."""
    cache_path = KML_CACHE / f"{pid}.kml"
    if cache_path.exists() and cache_path.stat().st_size > 100:
        return cache_path
    try:
        with httpx.Client(timeout=60, follow_redirects=True, headers={"User-Agent": "Mozilla/5.0"}) as c:
            r = c.get(uri)
            if r.status_code == 200 and len(r.content) > 100:
                cache_path.write_bytes(r.content)
                return cache_path
    except Exception:
        return None
    return None


def score_project(p: dict, summary: dict) -> dict:
    """Compute divergence score for one forest project."""
    pid = p["id"]
    result = {
        "id": pid,
        "name": p["name"],
        "subcat": p["subcat"],
        "country": p["country"],
        "claim_tco2_yr": p.get("est_annual_tco2"),
        "crediting_start_date": p.get("crediting_start_date"),
        "status": "started",
    }

    # Find best KML (prefer most recent)
    kml_docs = [
        d for g in summary.get("documentGroups", []) for d in g.get("documents", [])
        if ".kml" in (d.get("documentName", "") or "").lower() or d.get("documentType") == "KML File"
    ]
    if not kml_docs:
        result["status"] = "no_kml"
        return result

    # Sort by upload date (most recent first)
    kml_docs.sort(key=lambda d: d.get("uploadDate", ""), reverse=True)
    kml_path = None
    for doc in kml_docs[:3]:
        kml_path = download_kml(doc["uri"], pid)
        if kml_path:
            break
    if not kml_path:
        result["status"] = "kml_download_failed"
        return result

    polys = parse_kml_polygons(kml_path)
    if not polys:
        result["status"] = "kml_parse_failed"
        return result

    # Build union and bounds
    try:
        mp = unary_union(polys)
    except Exception as e:
        result["status"] = f"union_failed: {e}"
        return result

    min_lon, min_lat, max_lon, max_lat = mp.bounds

    # Skip if AOI is too tiny (<10 ha) or implausibly large (>10M ha)
    avg_lat = (min_lat + max_lat) / 2
    aoi_area_km2 = mp.area * 111.32 * 111.32 * np.cos(np.radians(avg_lat))
    aoi_area_ha = aoi_area_km2 * 100  # km² → ha
    if aoi_area_ha < 10 or aoi_area_ha > 10_000_000:
        result["status"] = f"implausible_area: {aoi_area_ha:.0f} ha"
        return result
    result["aoi_area_ha"] = aoi_area_ha
    result["n_polygons"] = len(polys)

    # Determine Hansen tiles
    tiles = hansen_tiles_for_bbox(min_lon, min_lat, max_lon, max_lat)
    if not tiles:
        result["status"] = "no_hansen_tiles"
        return result
    if len(tiles) > 6:
        # Too spread out to handle simply; flag and skip
        result["status"] = f"too_many_tiles: {len(tiles)}"
        result["tiles"] = tiles
        return result
    result["tiles"] = tiles

    # Read each tile's window for our AOI bbox, accumulating loss-by-year and forest-2000 area
    loss_by_year = defaultdict(float)
    forest_2000_ha = 0.0
    total_aoi_ha = 0.0
    pix_ha = PIX_HA_AT_LAT(avg_lat)

    for tile_id in tiles:
        try:
            urls = {layer: f"/vsicurl/{HANSEN_BASE}{layer}_{tile_id}.tif"
                    for layer in ("lossyear", "treecover2000", "datamask")}

            with rasterio.open(urls["lossyear"]) as src:
                # Intersect AOI bbox with tile bounds
                tb = src.bounds
                inter = (
                    max(min_lon, tb.left),
                    max(min_lat, tb.bottom),
                    min(max_lon, tb.right),
                    min(max_lat, tb.top),
                )
                if inter[0] >= inter[2] or inter[1] >= inter[3]:
                    continue
                window = from_bounds(*inter, src.transform).round_offsets().round_lengths()
                if window.width <= 0 or window.height <= 0:
                    continue
                transform = src.window_transform(window)
                shape = (int(window.height), int(window.width))
                lossyear = src.read(1, window=window)

            with rasterio.open(urls["treecover2000"]) as src:
                treecover = src.read(1, window=window)
            with rasterio.open(urls["datamask"]) as src:
                datamask = src.read(1, window=window)

            # Rasterize AOI polygons to this window
            aoi_mask = rasterize([(mp, 1)], out_shape=shape, transform=transform, fill=0, dtype="uint8")

            in_aoi = (aoi_mask == 1) & (datamask == 1)
            forest_2000 = (treecover >= 30) & in_aoi
            total_aoi_ha += float(in_aoi.sum()) * pix_ha
            forest_2000_ha += float(forest_2000.sum()) * pix_ha

            for yr_code in range(1, 24):
                loss_pix = (lossyear == yr_code) & in_aoi
                loss_by_year[2000 + yr_code] += float(loss_pix.sum()) * pix_ha

        except Exception as e:
            result["status"] = f"hansen_read_failed({tile_id}): {str(e)[:80]}"
            return result

    if total_aoi_ha == 0:
        result["status"] = "empty_aoi_after_mask"
        return result

    result["total_aoi_ha"] = total_aoi_ha
    result["forest_2000_ha"] = forest_2000_ha
    result["forest_fraction_2000"] = forest_2000_ha / total_aoi_ha if total_aoi_ha else 0
    result["loss_by_year"] = dict(loss_by_year)

    # Determine pre/post split using crediting start date
    cs = (p.get("crediting_start_date") or "").strip()
    if not cs or len(cs) < 4:
        # Try project registration date as fallback
        cs = (p.get("project_registration_date") or "").strip()
    if not cs or len(cs) < 4:
        # No date available - use 2014 as median split
        split_year = 2014
        result["split_year_source"] = "default_2014"
    else:
        try:
            split_year = int(cs[:4])
            if split_year < 2002 or split_year > 2023:
                split_year = max(2002, min(2023, split_year))
            result["split_year_source"] = f"crediting_start={cs[:10]}"
        except ValueError:
            split_year = 2014
            result["split_year_source"] = "default_2014_parse_failed"
    result["split_year"] = split_year

    pre_years = [y for y in range(2001, split_year)]
    post_years = [y for y in range(split_year, 2024)]
    if not pre_years or not post_years:
        result["status"] = "split_outside_data"
        return result

    pre_loss = sum(loss_by_year.get(y, 0) for y in pre_years) / len(pre_years)
    post_loss = sum(loss_by_year.get(y, 0) for y in post_years) / len(post_years)
    result["pre_loss_ha_yr"] = pre_loss
    result["post_loss_ha_yr"] = post_loss
    result["change_ha_yr"] = post_loss - pre_loss
    result["change_pct"] = (post_loss - pre_loss) / pre_loss * 100 if pre_loss else None

    # Compare to claim
    claim = p.get("est_annual_tco2") or 0
    if claim:
        implied_avoided_ha = claim / CARBON_STOCK_TCO2_HA
        observed_reduction_ha = pre_loss - post_loss
        ratio = observed_reduction_ha / implied_avoided_ha if implied_avoided_ha else None
        result["implied_avoided_ha_yr"] = implied_avoided_ha
        result["observed_reduction_ha_yr"] = observed_reduction_ha
        result["ratio_observed_to_claimed"] = ratio
        # Severity: ratio < 0 = MORE deforestation during project (red flag)
        # 0-25% = severe under-delivery
        # 25-75% = moderate under-delivery
        # >75% = within range
        if ratio is None:
            sev = "no_score"
        elif ratio < 0:
            sev = "RED_FLAG_NEGATIVE"
        elif ratio < 0.25:
            sev = "SEVERE_UNDERDELIVERY"
        elif ratio < 0.75:
            sev = "MODERATE_UNDERDELIVERY"
        else:
            sev = "PASS"
        result["severity"] = sev

    result["status"] = "ok"
    return result


def main():
    with open(DATA_DIR / "forest_inventory.json") as f:
        inv = json.load(f)
    targets = [p for p in inv if p.get("has_summary") and p.get("n_kml_docs", 0) > 0]
    print(f"Targets: {len(targets)}", file=sys.stderr)

    out_path = DATA_DIR / "forest_scan_results.json"
    results = []
    if out_path.exists():
        with open(out_path) as f:
            results = json.load(f)
    done_ids = {r["id"] for r in results}
    print(f"Already done: {len(done_ids)}", file=sys.stderr)

    rs_cache = DATA_DIR.parent.parent / "rs_cache"
    if not rs_cache.exists():
        rs_cache = Path("rs_cache")  # CWD fallback

    t_start = time.time()
    for i, p in enumerate(targets):
        pid = p["id"]
        if pid in done_ids:
            continue
        # Load summary from cache
        sp = rs_cache / f"{pid}.json"
        if not sp.exists():
            print(f"  [{i+1}/{len(targets)}] {pid}: no summary cache", file=sys.stderr)
            continue
        with open(sp) as f:
            summary = json.load(f)

        t0 = time.time()
        # Per-project hard timeout (90s)
        signal.signal(signal.SIGALRM, _timeout_handler)
        signal.alarm(90)
        try:
            r = score_project(p, summary)
        except TimeoutError:
            r = {"id": pid, "status": "timeout_90s"}
        except Exception as e:
            r = {"id": pid, "status": f"score_exception: {str(e)[:120]}", "tb": traceback.format_exc()[:500]}
        finally:
            signal.alarm(0)
        elapsed = time.time() - t0
        r["elapsed_s"] = round(elapsed, 1)
        results.append(r)
        sev = r.get("severity", r.get("status", "?"))[:25]
        print(f"  [{i+1}/{len(targets)}] {pid:>5}  {elapsed:>4.1f}s  {sev:<25}  {p['name'][:50]}", file=sys.stderr, flush=True)

        # Persist incrementally
        if (i + 1) % 5 == 0:
            with open(out_path, "w") as f:
                json.dump(results, f, indent=2)

    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nTotal time: {(time.time()-t_start)/60:.1f} min", file=sys.stderr)
    print(f"Saved {len(results)} results to {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
