"""
Synthetic-control upgrade to scan_forest.py.

Methodology (matches West et al. 2020 PNAS approach):
  - For each project, compute a buffer-ring control area (5-30km outside AOI)
  - Mask both project and control to forest_2000 (canopy >=30%)
  - Compute annual deforestation rate (ha lost / ha forested) for both
  - Counterfactual deforestation = control rate × project forest area
  - Project benefit = counterfactual_loss - actual_project_loss
  - Compare to claim's implied avoided deforestation
"""
from __future__ import annotations

import json
import multiprocessing as mp
import os
import signal
import sys
import time
import traceback
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

# macOS fork() + Cocoa workaround: rasterio/Python load ObjC frameworks that
# refuse to be in a forked-after-thread state. Setting this env var disables
# the safety check and lets fork() proceed. (Required because our score-with-
# hard-timeout wrapper uses a watchdog thread alongside multiprocessing.fork.)
os.environ.setdefault("OBJC_DISABLE_INITIALIZE_FORK_SAFETY", "YES")

# Set GDAL HTTP timeouts BEFORE importing rasterio.
# These address the root cause of long Hansen tile-read hangs:
#   - LOWSPEED_TIME/LIMIT abort stalled streams (CPL_CURL_TIMEOUT alone doesn't
#     catch trickle-rate stalls — a connection at 100 B/s passes the per-request
#     timeout but never delivers data)
#   - CPL_VSIL_CURL_CHUNK_SIZE bumps HTTP range-request size from default 16KB
#     to 1MB, cutting round-trips ~64× for large windows on Amazonian tiles
#   - VSI_CACHE_SIZE bumped to 256MB so adjacent range reads hit cache
os.environ.setdefault("CPL_CURL_TIMEOUT", "30")
os.environ.setdefault("GDAL_HTTP_TIMEOUT", "30")
os.environ.setdefault("GDAL_HTTP_CONNECTTIMEOUT", "10")
os.environ.setdefault("GDAL_HTTP_LOWSPEED_TIME", "30")
os.environ.setdefault("GDAL_HTTP_LOWSPEED_LIMIT", "1000")  # bytes/sec — fail if <1KB/s for 30s
os.environ.setdefault("GDAL_HTTP_MAX_RETRY", "3")
os.environ.setdefault("GDAL_HTTP_RETRY_DELAY", "2")
os.environ.setdefault("CPL_VSIL_CURL_CHUNK_SIZE", "1048576")  # 1 MB
os.environ.setdefault("GDAL_DISABLE_READDIR_ON_OPEN", "EMPTY_DIR")
os.environ.setdefault("VSI_CACHE", "TRUE")
os.environ.setdefault("VSI_CACHE_SIZE", "268435456")  # 256MB

import httpx
import numpy as np
import rasterio
from rasterio.features import rasterize
from rasterio.windows import from_bounds
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import unary_union, transform
import pyproj

KML_NS = {"kml": "http://www.opengis.net/kml/2.2"}
HANSEN_BASE = "https://storage.googleapis.com/earthenginepartners-hansen/GFC-2023-v1.11/Hansen_GFC-2023-v1.11_"
PIX_HA_AT_LAT = lambda lat: 0.00025 * 111320 * 0.00025 * 111320 * np.cos(np.radians(lat)) / 10000
CARBON_STOCK_TCO2_HA = 165

DATA_DIR = Path(__file__).parent / "data"
KML_CACHE = DATA_DIR / "kml_cache"
KML_CACHE.mkdir(exist_ok=True, parents=True)


class TimeoutError(Exception): pass


def _timeout_handler(signum, frame):
    raise TimeoutError("project scoring timed out")


def hansen_tiles_for_bbox(min_lon, min_lat, max_lon, max_lat):
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


def parse_kml_polygons(kml_path):
    raw = None
    try:
        with open(kml_path, "rb") as f:
            head = f.read(4)
        # Detect KMZ (zip) masquerading as .kml
        if head == b"PK\x03\x04":
            import zipfile
            with zipfile.ZipFile(kml_path) as zf:
                kml_member = next((n for n in zf.namelist() if n.lower().endswith(".kml")), None)
                if kml_member is None:
                    return []
                raw = zf.read(kml_member)
    except Exception:
        return []

    # Strip UTF-8 BOM if present — Verra KMLs sometimes ship with one and
    # ET.parse rejects them with "not well-formed (invalid token): line 1, column 2"
    if raw is None:
        try:
            with open(kml_path, "rb") as f:
                raw_check = f.read(3)
            if raw_check == b"\xef\xbb\xbf":
                with open(kml_path, "rb") as f:
                    raw = f.read()[3:]
        except Exception:
            pass
    elif raw[:3] == b"\xef\xbb\xbf":
        raw = raw[3:]

    try:
        if raw is not None:
            root = ET.fromstring(raw)
        else:
            tree = ET.parse(kml_path)
            root = tree.getroot()
    except ET.ParseError:
        # Many Verra KMLs declare `xsi:schemaLocation` on <Document> but forget
        # `xmlns:xsi` on the root <kml>, producing "unbound prefix" errors.
        # Inject the missing declaration and re-parse from string.
        try:
            if raw is None:
                with open(kml_path, "rb") as f:
                    raw = f.read()
            patched = raw.replace(
                b'xmlns="http://www.opengis.net/kml/2.2"',
                b'xmlns="http://www.opengis.net/kml/2.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"',
                1,
            )
            root = ET.fromstring(patched)
        except Exception:
            return []
    polys = []
    # Some Verra KMLs ship without the kml 2.2 namespace declaration on root.
    # Probe both namespaced and unnamespaced Polygon tags; use whichever matches.
    poly_iter = list(root.iter("{http://www.opengis.net/kml/2.2}Polygon"))
    if not poly_iter:
        poly_iter = list(root.iter("Polygon"))
    if not poly_iter:
        # Try with all namespaces stripped (rebuild via local-name match)
        poly_iter = [el for el in root.iter() if el.tag.split('}')[-1] == "Polygon"]

    def _find_coords(parent, container_local_name):
        """Find a <coordinates> descendant inside a <{container_local_name}>
        wrapper, namespace-agnostic. Returns the element or None."""
        for el in parent.iter():
            local = el.tag.split('}')[-1] if '}' in el.tag else el.tag
            if local == container_local_name:
                for c in el.iter():
                    cloc = c.tag.split('}')[-1] if '}' in c.tag else c.tag
                    if cloc == "coordinates":
                        return c
        return None

    def _find_all_coords(parent, container_local_name):
        out = []
        for el in parent.iter():
            local = el.tag.split('}')[-1] if '}' in el.tag else el.tag
            if local == container_local_name:
                for c in el.iter():
                    cloc = c.tag.split('}')[-1] if '}' in c.tag else c.tag
                    if cloc == "coordinates":
                        out.append(c)
        return out

    for poly_elem in poly_iter:
        outer = _find_coords(poly_elem, "outerBoundaryIs")
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
        for inner in _find_all_coords(poly_elem, "innerBoundaryIs"):
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

    # Fallback: if no Polygons found, treat closed LineStrings as polygon outer
    # rings. Some Verra KMLs (e.g. project 2568 Hainan Lingshui Mangrove) ship
    # only LineString boundaries — not technically a Polygon but unambiguously
    # represents the project AOI.
    if not polys:
        ls_iter = list(root.iter("{http://www.opengis.net/kml/2.2}LineString"))
        if not ls_iter:
            ls_iter = [el for el in root.iter() if (el.tag.split('}')[-1] if '}' in el.tag else el.tag) == "LineString"]
        for ls_elem in ls_iter:
            coords_el = None
            for c in ls_elem.iter():
                cloc = c.tag.split('}')[-1] if '}' in c.tag else c.tag
                if cloc == "coordinates":
                    coords_el = c
                    break
            if coords_el is None or not coords_el.text:
                continue
            coords = []
            for tup in coords_el.text.strip().split():
                parts = tup.split(",")
                if len(parts) >= 2:
                    try:
                        coords.append((float(parts[0]), float(parts[1])))
                    except ValueError:
                        continue
            if len(coords) < 4:
                continue
            # Close the ring if needed
            if coords[0] != coords[-1]:
                coords.append(coords[0])
            try:
                p = Polygon(coords)
                if p.is_valid and p.area > 0:
                    polys.append(p)
            except Exception:
                continue
    return polys


def buffer_ring_geometry(project_geom, inner_km=5, outer_km=30, avg_lat=0):
    """
    Compute a donut-shaped buffer around project_geom in lon/lat coordinates.
    Approximates km->degree using local lat-corrected conversion.

    For high-polygon-count AOIs (e.g. smallholder programs with thousands of
    small plots), `shapely.buffer()` on the full MultiPolygon is effectively
    O(n²) — a 4332-polygon project takes 129s. We fall back to buffering the
    convex hull instead. The project rasterize step still uses precise
    geometry; only the *buffer* ring is approximated. Trade-off: counterfactual
    represents broader regional context rather than per-plot neighborhood.
    """
    # 1 degree latitude ≈ 111.32 km; 1 degree longitude varies with cos(lat)
    lat_deg_per_km = 1 / 111.32
    lon_deg_per_km = 1 / (111.32 * np.cos(np.radians(avg_lat)))
    inner_deg = inner_km * (lat_deg_per_km + lon_deg_per_km) / 2
    outer_deg = outer_km * (lat_deg_per_km + lon_deg_per_km) / 2

    # Heuristic: count polygons in MultiPolygon
    if hasattr(project_geom, "geoms"):
        n_polys = sum(1 for _ in project_geom.geoms)
    else:
        n_polys = 1
    HIGH_POLY_THRESHOLD = 500

    base = project_geom.convex_hull if n_polys > HIGH_POLY_THRESHOLD else project_geom
    outer_buffer = base.buffer(outer_deg)
    inner_buffer = base.buffer(inner_deg)
    ring = outer_buffer.difference(inner_buffer)
    return ring


def download_kml(uri, pid):
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


def score_project_synthetic_control(p, summary, inner_km=5, outer_km=30):
    """Score with synthetic-control buffer ring methodology."""
    pid = p["id"]
    result = {
        "id": pid,
        "name": p["name"],
        "subcat": p["subcat"],
        "country": p["country"],
        "claim_tco2_yr": p.get("est_annual_tco2"),
        "crediting_start_date": p.get("crediting_start_date"),
        "method": "synthetic_control_buffer_ring",
        "inner_km": inner_km,
        "outer_km": outer_km,
        "status": "started",
    }

    # Find KML
    kml_docs = [
        d for g in summary.get("documentGroups", []) for d in g.get("documents", [])
        if ".kml" in (d.get("documentName", "") or "").lower() or d.get("documentType") == "KML File"
    ]
    if not kml_docs:
        result["status"] = "no_kml"
        return result

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

    # Envelope-polygon filter (methodology note):
    # Some Verra KMLs include one or two giant rectangles representing the
    # project's regional/concession boundary alongside the actual planting or
    # protection sites. A single 10M+ ha polygon is implausible for a real
    # project AOI (Brazil's Amazonas state itself is 156M ha) — these are
    # almost certainly bbox envelopes. We drop polygons larger than 5M ha as
    # envelope artifacts and record the count in `envelopes_filtered` so the
    # methodology change is queryable downstream. The remaining sites then
    # pass area sanity checks normally. Only kicks in for multi-polygon AOIs;
    # a project consisting of a single very-large polygon is accepted as-is
    # so legitimate large-concession REDD+ projects aren't dropped.
    ENVELOPE_HA_THRESHOLD = 5_000_000
    n_envelopes = 0
    if len(polys) > 1:
        filtered = []
        for poly in polys:
            clat = poly.centroid.y
            poly_area_ha = poly.area * 111.32 * 111.32 * np.cos(np.radians(clat)) * 100
            if poly_area_ha > ENVELOPE_HA_THRESHOLD:
                n_envelopes += 1
                continue
            filtered.append(poly)
        if n_envelopes and filtered:
            polys = filtered
            result["envelopes_filtered"] = n_envelopes

    try:
        project_geom = unary_union(polys)
    except Exception as e:
        result["status"] = f"union_failed: {e}"
        return result

    min_lon, min_lat, max_lon, max_lat = project_geom.bounds
    avg_lat = (min_lat + max_lat) / 2
    aoi_area_km2 = project_geom.area * 111.32 * 111.32 * np.cos(np.radians(avg_lat))
    aoi_area_ha = aoi_area_km2 * 100
    if aoi_area_ha < 10 or aoi_area_ha > 10_000_000:
        result["status"] = f"implausible_area: {aoi_area_ha:.0f} ha"
        return result
    result["aoi_area_ha"] = aoi_area_ha
    result["n_polygons"] = len(polys)

    # Build buffer ring
    try:
        buffer_geom = buffer_ring_geometry(project_geom, inner_km=inner_km, outer_km=outer_km, avg_lat=avg_lat)
    except Exception as e:
        result["status"] = f"buffer_failed: {e}"
        return result

    if buffer_geom.is_empty:
        result["status"] = "buffer_empty"
        return result

    buf_min_lon, buf_min_lat, buf_max_lon, buf_max_lat = buffer_geom.bounds
    buffer_area_km2 = buffer_geom.area * 111.32 * 111.32 * np.cos(np.radians(avg_lat))
    buffer_area_ha = buffer_area_km2 * 100
    result["buffer_area_ha"] = buffer_area_ha

    # Determine tiles needed (project + buffer combined)
    combined_min_lon = min(min_lon, buf_min_lon)
    combined_min_lat = min(min_lat, buf_min_lat)
    combined_max_lon = max(max_lon, buf_max_lon)
    combined_max_lat = max(max_lat, buf_max_lat)
    tiles = hansen_tiles_for_bbox(combined_min_lon, combined_min_lat, combined_max_lon, combined_max_lat)
    if not tiles:
        result["status"] = "no_hansen_tiles"
        return result
    if len(tiles) > 6:
        result["status"] = f"too_many_tiles: {len(tiles)}"
        result["tiles"] = tiles
        return result
    result["tiles"] = tiles

    # Read tiles, mask to project AOI and buffer ring separately
    project_loss_by_year = defaultdict(float)
    buffer_loss_by_year = defaultdict(float)
    project_forest_2000_ha = 0.0
    buffer_forest_2000_ha = 0.0
    project_aoi_ha = 0.0
    buffer_aoi_ha = 0.0
    pix_ha = PIX_HA_AT_LAT(avg_lat)

    for tile_id in tiles:
        try:
            urls = {layer: f"/vsicurl/{HANSEN_BASE}{layer}_{tile_id}.tif"
                    for layer in ("lossyear", "treecover2000", "datamask")}

            with rasterio.open(urls["lossyear"]) as src:
                tb = src.bounds
                inter = (
                    max(combined_min_lon, tb.left),
                    max(combined_min_lat, tb.bottom),
                    min(combined_max_lon, tb.right),
                    min(combined_max_lat, tb.top),
                )
                if inter[0] >= inter[2] or inter[1] >= inter[3]:
                    continue
                window = from_bounds(*inter, src.transform).round_offsets().round_lengths()
                if window.width <= 0 or window.height <= 0:
                    continue
                transform_w = src.window_transform(window)
                shape = (int(window.height), int(window.width))
                lossyear = src.read(1, window=window)

            with rasterio.open(urls["treecover2000"]) as src:
                treecover = src.read(1, window=window)
            with rasterio.open(urls["datamask"]) as src:
                datamask = src.read(1, window=window)

            # Rasterize project mask AND buffer mask separately
            project_mask = rasterize([(project_geom, 1)], out_shape=shape, transform=transform_w, fill=0, dtype="uint8")
            buffer_mask = rasterize([(buffer_geom, 1)], out_shape=shape, transform=transform_w, fill=0, dtype="uint8")

            in_project = (project_mask == 1) & (datamask == 1)
            in_buffer = (buffer_mask == 1) & (datamask == 1)

            # Forest 2000 (canopy >= 30%)
            project_forest = (treecover >= 30) & in_project
            buffer_forest = (treecover >= 30) & in_buffer

            project_forest_2000_ha += float(project_forest.sum()) * pix_ha
            buffer_forest_2000_ha += float(buffer_forest.sum()) * pix_ha
            project_aoi_ha += float(in_project.sum()) * pix_ha
            buffer_aoi_ha += float(in_buffer.sum()) * pix_ha

            # Loss by year, only counting losses in pixels that were forested in 2000
            for yr_code in range(1, 24):
                pl = (lossyear == yr_code) & project_forest
                bl = (lossyear == yr_code) & buffer_forest
                project_loss_by_year[2000 + yr_code] += float(pl.sum()) * pix_ha
                buffer_loss_by_year[2000 + yr_code] += float(bl.sum()) * pix_ha

        except Exception as e:
            result["status"] = f"hansen_read_failed({tile_id}): {str(e)[:80]}"
            return result

    if project_aoi_ha == 0 or buffer_aoi_ha == 0:
        result["status"] = "empty_aoi_after_mask"
        return result

    if project_forest_2000_ha == 0 or buffer_forest_2000_ha == 0:
        result["status"] = "no_forest_in_aoi_2000"
        return result

    result["project_total_aoi_ha"] = project_aoi_ha
    result["project_forest_2000_ha"] = project_forest_2000_ha
    result["buffer_total_aoi_ha"] = buffer_aoi_ha
    result["buffer_forest_2000_ha"] = buffer_forest_2000_ha
    result["project_loss_by_year"] = dict(project_loss_by_year)
    result["buffer_loss_by_year"] = dict(buffer_loss_by_year)

    # Determine project period
    cs = (p.get("crediting_start_date") or "").strip()
    if not cs or len(cs) < 4:
        cs = (p.get("project_registration_date") or "").strip()
    if not cs or len(cs) < 4:
        split_year = 2014
    else:
        try:
            split_year = int(cs[:4])
            if split_year < 2002 or split_year > 2023:
                split_year = max(2002, min(2023, split_year))
        except ValueError:
            split_year = 2014
    result["split_year"] = split_year

    # Compute deforestation rates (ha lost / ha forested) per year, project period
    project_period_years = list(range(split_year, 2024))
    if not project_period_years:
        result["status"] = "split_outside_data"
        return result

    project_loss_period = sum(project_loss_by_year.get(y, 0) for y in project_period_years)
    buffer_loss_period = sum(buffer_loss_by_year.get(y, 0) for y in project_period_years)
    n_years = len(project_period_years)

    # Annual rate as fraction of starting forest
    project_rate = (project_loss_period / project_forest_2000_ha) / n_years if project_forest_2000_ha else 0
    buffer_rate = (buffer_loss_period / buffer_forest_2000_ha) / n_years if buffer_forest_2000_ha else 0

    result["project_annual_loss_rate"] = project_rate  # fraction of starting forest lost per year
    result["buffer_annual_loss_rate"] = buffer_rate
    result["project_mean_loss_ha_yr"] = project_loss_period / n_years
    result["buffer_mean_loss_ha_yr"] = buffer_loss_period / n_years

    # Counterfactual: if project area had behaved like buffer
    counterfactual_loss_ha_yr = buffer_rate * project_forest_2000_ha
    actual_loss_ha_yr = project_loss_period / n_years

    # Avoided deforestation per year (positive = project performed better than control)
    observed_avoided_ha_yr = counterfactual_loss_ha_yr - actual_loss_ha_yr
    result["counterfactual_loss_ha_yr"] = counterfactual_loss_ha_yr
    result["observed_avoided_ha_yr"] = observed_avoided_ha_yr

    # Compare to claim
    claim = p.get("est_annual_tco2") or 0
    if claim:
        implied_avoided_ha = claim / CARBON_STOCK_TCO2_HA
        ratio = observed_avoided_ha_yr / implied_avoided_ha if implied_avoided_ha else None
        result["implied_avoided_ha_yr"] = implied_avoided_ha
        result["ratio_observed_to_claimed"] = ratio
        # Severity based on synthetic-control output
        if ratio is None:
            sev = "no_score"
        elif ratio < 0:  # project area worse than control
            sev = "RED_FLAG_NEGATIVE"
        elif ratio < 0.25:
            sev = "SEVERE_UNDERDELIVERY"
        elif ratio < 0.75:
            sev = "MODERATE_UNDERDELIVERY"
        else:
            sev = "PASS"
        result["severity"] = sev
        # Divergence (normalized) as a feature for calibration
        result["divergence_normalized"] = max(min(1.0 - ratio, 2.0), -2.0) if ratio is not None else None

    result["status"] = "ok"
    return result


def _score_worker(p, summary, q):
    """Subprocess entry point — run scoring and put result on queue."""
    try:
        r = score_project_synthetic_control(p, summary)
    except Exception as e:
        r = {"id": str(p.get("id")), "status": f"score_exception: {str(e)[:120]}"}
    try:
        q.put(r)
    except Exception:
        pass


def score_with_hard_timeout(p, summary, timeout_s=180):
    """Run scoring in a subprocess with OS-level kill on timeout.

    signal.alarm doesn't preempt GDAL C extension code, so a hung Hansen tile
    read blocks the parent indefinitely. We fork a worker and use a watchdog
    thread that os.kill()s it via SIGKILL once the budget is exceeded —
    bypassing multiprocessing.Process.join() which doesn't reliably honour
    the timeout when the child is in an uninterruptible kernel call (state
    "U") on macOS Python 3.9.
    """
    import os as _os
    import threading as _threading

    pid_s = str(p.get("id"))
    ctx = mp.get_context("fork")
    q = ctx.Queue()
    proc = ctx.Process(target=_score_worker, args=(p, summary, q))
    proc.start()
    child_pid = proc.pid

    killed = {"by_watchdog": False}

    def _watchdog():
        time.sleep(timeout_s)
        if proc.is_alive():
            killed["by_watchdog"] = True
            try:
                _os.kill(child_pid, signal.SIGKILL)
            except ProcessLookupError:
                pass

    wd = _threading.Thread(target=_watchdog, daemon=True)
    wd.start()

    proc.join()  # blocks until child exits (watchdog will SIGKILL if needed)
    if killed["by_watchdog"]:
        # Drain any partial result the worker may have written before SIGKILL
        try:
            proc.close()
        except Exception:
            pass
        return {"id": pid_s, "status": f"hard_timeout_{timeout_s}s"}
    if not q.empty():
        try:
            return q.get_nowait()
        except Exception:
            pass
    return {"id": pid_s, "status": "subprocess_no_result"}


def main():
    with open(DATA_DIR / "forest_inventory.json") as f:
        inv = json.load(f)
    targets = [p for p in inv if p.get("has_summary") and p.get("n_kml_docs", 0) > 0]

    # Optional: filter to top-N by claim size if requested
    limit_arg = next((a for a in sys.argv if a.startswith("--limit=")), None)
    if limit_arg:
        n = int(limit_arg.split("=")[1])
        targets.sort(key=lambda p: -(p.get("est_annual_tco2") or 0))
        targets = targets[:n]
        print(f"Limited to top {n} by claim size", file=sys.stderr)

    print(f"Targets: {len(targets)}", file=sys.stderr)

    out_path = DATA_DIR / "forest_scan_results_v2.json"
    results = []
    if out_path.exists() and "--restart" not in sys.argv:
        with open(out_path) as f:
            results = json.load(f)
    done_ids = {r["id"] for r in results}
    print(f"Already done: {len(done_ids)}", file=sys.stderr)

    rs_cache = Path(__file__).parent / "rs_cache"

    # Skip-list for projects known to hang the scoring (mostly mangroves where
    # the buffer-ring methodology breaks down because the buffer is mostly
    # ocean and the tile-read pattern is pathological). Recorded as a status
    # so they appear in results without consuming compute.
    KNOWN_PATHOLOGICAL = {
        # Mangrove / coastal projects — buffer-ring methodology breaks down (buffer
        # is mostly ocean → tile-read patterns hang GDAL). These are routed through
        # scan_mangrove.py which uses GMW v3 + convex-hull buffer instead.
        "2834",  # Sine Saloum/Casamance Mangrove (Senegal)
        "2792",  # Restoration of Degraded Mangroves (Myanmar)
        "2088",  # Mangrove Restoration and Sustainable Development (Myanmar)
        "1764",  # Reforestation of degraded mangrove lands (Myanmar)
        "1493",  # Mangrove restoration / coastal greenbelt (Indonesia)
        "1318",  # Livelihoods' mangrove restoration grouped (Senegal)
        "1463",  # India Sundarbans Mangrove Restoration
        "3868",  # Fangchenggang Mangrove afforestation (China)
        "3230",  # Abu Ali Island Mangrove (Saudi Arabia)
        "2568",  # Hainan Lingshui Mangrove Blue Carbon (China)
        "2343",  # Zhanjiang Mangrove Afforestation (China)
    }
    PATHOLOGICAL_KEYWORDS = ("mangrove", "mangroves")  # heuristic flag for review

    t_start = time.time()
    n_processed = 0
    for i, p in enumerate(targets):
        pid = str(p["id"])
        if pid in done_ids:
            continue
        if pid in KNOWN_PATHOLOGICAL:
            r = {"id": pid, "status": "skipped_pathological", "elapsed_s": 0.0}
            results.append(r)
            done_ids.add(pid)
            n_processed += 1
            print(f"  [{i+1}/{len(targets)}] {pid:>5}    0.0s  skipped_pathological      {p['name'][:50]}", file=sys.stderr, flush=True)
            with open(out_path, "w") as f:
                json.dump(results, f, indent=2)
            continue
        sp = rs_cache / f"{pid}.json"
        if not sp.exists():
            continue
        with open(sp) as f:
            summary = json.load(f)

        # Heuristic warning for mangrove projects (worth reviewing before scoring)
        name_lower = (p.get("name") or "").lower()
        if any(k in name_lower for k in PATHOLOGICAL_KEYWORDS):
            print(f"  [{i+1}/{len(targets)}] {pid:>5}  WARN: mangrove project — methodology may not apply", file=sys.stderr, flush=True)

        t0 = time.time()
        # Hard subprocess-based timeout: signal.alarm doesn't preempt GDAL C
        # extension code, so we run scoring in a fork()'d subprocess that we
        # can SIGKILL if it exceeds the wall-clock budget.
        r = score_with_hard_timeout(p, summary, timeout_s=180)
        elapsed = time.time() - t0
        r["elapsed_s"] = round(elapsed, 1)
        results.append(r)
        n_processed += 1
        sev = r.get("severity", r.get("status", "?"))[:25]
        print(f"  [{i+1}/{len(targets)}] {pid:>5}  {elapsed:>5.1f}s  {sev:<25}  {p['name'][:50]}", file=sys.stderr, flush=True)

        # Save every result (was: every 5). Loses at most 1 result on crash now.
        # Trade-off: more disk writes, but 1MB JSON dump every ~10s is fine.
        with open(out_path, "w") as f:
            json.dump(results, f, indent=2)

    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nTotal time: {(time.time()-t_start)/60:.1f} min, processed {n_processed} new", file=sys.stderr)
    print(f"Saved {len(results)} results to {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
