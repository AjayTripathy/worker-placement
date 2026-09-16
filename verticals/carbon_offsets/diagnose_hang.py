"""Instrument score_project_synthetic_control on a known-stuck project.

Records timing of every step:
  - KML download/parse + polygon union
  - Buffer ring build
  - Tile enumeration
  - Per-tile: rasterio.open() x3 bands, src.read() x3, rasterize() x2, mask
  - Per-tile-band per-byte stats (urlopen latency)

Usage: python3 diagnose_hang.py <project_id>
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

# Same env vars as scan_forest_v2 — diagnose under the same conditions
os.environ.setdefault("OBJC_DISABLE_INITIALIZE_FORK_SAFETY", "YES")
os.environ.setdefault("CPL_CURL_TIMEOUT", "30")
os.environ.setdefault("GDAL_HTTP_TIMEOUT", "30")
os.environ.setdefault("GDAL_HTTP_CONNECTTIMEOUT", "10")
os.environ.setdefault("GDAL_HTTP_LOWSPEED_TIME", "30")
os.environ.setdefault("GDAL_HTTP_LOWSPEED_LIMIT", "1000")
os.environ.setdefault("GDAL_HTTP_MAX_RETRY", "3")
os.environ.setdefault("GDAL_HTTP_RETRY_DELAY", "2")
os.environ.setdefault("CPL_VSIL_CURL_CHUNK_SIZE", "1048576")
os.environ.setdefault("VSI_CACHE", "TRUE")
os.environ.setdefault("VSI_CACHE_SIZE", "268435456")
os.environ.setdefault("CPL_DEBUG", "OFF")  # set to "ON" for verbose GDAL trace

import numpy as np
import rasterio
from rasterio.features import rasterize
from rasterio.windows import from_bounds
from shapely.ops import unary_union

sys.path.insert(0, str(Path(__file__).parent))
from scan_forest_v2 import (
    parse_kml_polygons, buffer_ring_geometry, hansen_tiles_for_bbox,
    download_kml, KML_CACHE, HANSEN_BASE, PIX_HA_AT_LAT,
)

DATA_DIR = Path(__file__).parent / "data"
RS_CACHE = Path(__file__).parent / "rs_cache"


class Stopwatch:
    def __init__(self):
        self.events = []
        self.t0 = time.time()
        self.last = self.t0

    def lap(self, label):
        now = time.time()
        delta = now - self.last
        total = now - self.t0
        self.events.append((label, delta, total))
        self.last = now
        print(f"  +{delta:>7.2f}s  (T+{total:>8.2f}s)  {label}", flush=True)


def diagnose(pid):
    sw = Stopwatch()
    print(f"\n=== Diagnosing project {pid} ===", flush=True)

    with open(DATA_DIR / "forest_inventory.json") as f:
        inv = json.load(f)
    p = next((x for x in inv if str(x["id"]) == str(pid)), None)
    if not p:
        print(f"Project {pid} not in inventory")
        return
    sw.lap(f"Loaded inventory; project = {p.get('name','?')[:60]}")

    sp = RS_CACHE / f"{pid}.json"
    with open(sp) as f:
        summary = json.load(f)
    sw.lap("Loaded rs_cache summary")

    # KML
    kml_docs = [
        d for g in summary.get("documentGroups", []) for d in g.get("documents", [])
        if ".kml" in (d.get("documentName", "") or "").lower() or d.get("documentType") == "KML File"
    ]
    kml_docs.sort(key=lambda d: d.get("uploadDate", ""), reverse=True)
    kml_path = None
    for doc in kml_docs[:3]:
        kml_path = download_kml(doc["uri"], pid)
        if kml_path:
            break
    sw.lap(f"Downloaded/cached KML: {kml_path}")

    polys = parse_kml_polygons(kml_path)
    sw.lap(f"Parsed KML: {len(polys)} polygons")

    project_geom = unary_union(polys)
    sw.lap(f"unary_union -> {project_geom.geom_type}, area_deg^2={project_geom.area:.4f}")

    min_lon, min_lat, max_lon, max_lat = project_geom.bounds
    avg_lat = (min_lat + max_lat) / 2
    aoi_area_ha = project_geom.area * 111.32 * 111.32 * np.cos(np.radians(avg_lat)) * 100
    print(f"  AOI bbox lat={min_lat:.3f}..{max_lat:.3f} lon={min_lon:.3f}..{max_lon:.3f}, area_ha={aoi_area_ha:,.0f}")

    buffer_geom = buffer_ring_geometry(project_geom, inner_km=5, outer_km=30, avg_lat=avg_lat)
    sw.lap(f"Built buffer ring: bounds={buffer_geom.bounds}")

    buf_min_lon, buf_min_lat, buf_max_lon, buf_max_lat = buffer_geom.bounds
    combined_min_lon = min(min_lon, buf_min_lon)
    combined_min_lat = min(min_lat, buf_min_lat)
    combined_max_lon = max(max_lon, buf_max_lon)
    combined_max_lat = max(max_lat, buf_max_lat)
    tiles = hansen_tiles_for_bbox(combined_min_lon, combined_min_lat, combined_max_lon, combined_max_lat)
    print(f"  Tiles to fetch: {tiles}")
    sw.lap(f"Determined {len(tiles)} tiles")

    pix_ha = PIX_HA_AT_LAT(avg_lat)

    for tile_id in tiles:
        print(f"\n  --- Tile {tile_id} ---")
        tile_sw = Stopwatch()
        urls = {layer: f"/vsicurl/{HANSEN_BASE}{layer}_{tile_id}.tif"
                for layer in ("lossyear", "treecover2000", "datamask")}

        # Open lossyear, read window
        try:
            with rasterio.open(urls["lossyear"]) as src:
                tile_sw.lap("rasterio.open(lossyear)")
                tb = src.bounds
                inter = (
                    max(combined_min_lon, tb.left),
                    max(combined_min_lat, tb.bottom),
                    min(combined_max_lon, tb.right),
                    min(combined_max_lat, tb.top),
                )
                if inter[0] >= inter[2] or inter[1] >= inter[3]:
                    print(f"  Tile doesn't intersect window — skip")
                    continue
                window = from_bounds(*inter, src.transform).round_offsets().round_lengths()
                print(f"  Window: width={window.width}, height={window.height} pixels")
                lossyear = src.read(1, window=window)
                tile_sw.lap(f"src.read(lossyear) -> shape={lossyear.shape}, dtype={lossyear.dtype}")
                shape = lossyear.shape
                transform_w = src.window_transform(window)

            with rasterio.open(urls["treecover2000"]) as src:
                tile_sw.lap("rasterio.open(treecover2000)")
                treecover = src.read(1, window=window)
                tile_sw.lap(f"src.read(treecover) -> shape={treecover.shape}")

            with rasterio.open(urls["datamask"]) as src:
                tile_sw.lap("rasterio.open(datamask)")
                datamask = src.read(1, window=window)
                tile_sw.lap(f"src.read(datamask) -> shape={datamask.shape}")

            project_mask = rasterize([(project_geom, 1)], out_shape=shape, transform=transform_w, fill=0, dtype="uint8")
            tile_sw.lap("rasterize(project_geom)")
            buffer_mask = rasterize([(buffer_geom, 1)], out_shape=shape, transform=transform_w, fill=0, dtype="uint8")
            tile_sw.lap("rasterize(buffer_geom)")

            in_project = (project_mask == 1) & (datamask == 1)
            in_buffer = (buffer_mask == 1) & (datamask == 1)
            project_forest = (treecover >= 30) & in_project
            buffer_forest = (treecover >= 30) & in_buffer
            tile_sw.lap("masks computed")

            project_aoi_pix = int(in_project.sum())
            buffer_aoi_pix = int(in_buffer.sum())
            print(f"  in_project={project_aoi_pix} pix, in_buffer={buffer_aoi_pix} pix")
        except Exception as e:
            print(f"  EXCEPTION: {type(e).__name__}: {str(e)[:200]}")

    sw.lap("\n=== Total elapsed ===")


if __name__ == "__main__":
    pid = sys.argv[1] if len(sys.argv) > 1 else "2709"
    diagnose(pid)
