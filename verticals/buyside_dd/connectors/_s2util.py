"""Shared Sentinel-2 helpers (free tier): Element84 STAC search + COG window reads.

Used by the optical alt-data connectors (crop_yield_ndvi, oil_storage). No auth:
Element84 Earth Search STAC for discovery, open `sentinel-cogs` AWS bucket for pixels.
"""
from __future__ import annotations

import math
from typing import Optional
from urllib.parse import quote

import numpy as np
import rasterio
from rasterio.warp import transform_bounds
from rasterio.windows import from_bounds

STAC = "https://earth-search.aws.element84.com/v1/search"
COLLECTION = "sentinel-2-l2a"
GEOCODER = ("https://geocoding.geo.census.gov/geocoder/locations/onelineaddress"
            "?address={addr}&benchmark=Public_AR_Current&format=json")
GDAL_ENV = dict(AWS_NO_SIGN_REQUEST="YES", GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR",
                GDAL_HTTP_TIMEOUT="30", GDAL_HTTP_MAX_RETRY="2", VSI_CACHE="TRUE")


def https(href: str) -> str:
    if href.startswith("s3://sentinel-cogs/"):
        return "https://sentinel-cogs.s3.us-west-2.amazonaws.com/" + href[len("s3://sentinel-cogs/"):]
    return href


def bbox_from_point(lat: float, lon: float, radius_km: float) -> list[float]:
    dlat = radius_km / 111.0
    dlon = radius_km / (111.0 * max(0.05, math.cos(math.radians(lat))))
    return [lon - dlon, lat - dlat, lon + dlon, lat + dlat]


def geocode(session, address: str, timeout: float = 20.0) -> Optional[tuple[float, float]]:
    try:
        r = session.get(GEOCODER.format(addr=quote(address)), timeout=timeout)
        m = r.json()["result"]["addressMatches"]
        return (float(m[0]["coordinates"]["y"]), float(m[0]["coordinates"]["x"])) if m else None
    except Exception:
        return None


def best_scene(session, bbox: list[float], dt_range: str, cloud_max: int, timeout: float = 25.0):
    """Lowest-cloud Sentinel-2 L2A scene intersecting bbox in the datetime range."""
    body = {"collections": [COLLECTION], "bbox": bbox, "datetime": dt_range,
            "query": {"eo:cloud_cover": {"lt": cloud_max}}, "limit": 30,
            "sortby": [{"field": "properties.eo:cloud_cover", "direction": "asc"}]}
    try:
        r = session.post(STAC, json=body, timeout=timeout)
    except Exception as e:
        return None, f"stac post: {e}"
    if r.status_code >= 400:
        return None, f"stac http {r.status_code}"
    feats = r.json().get("features", [])
    return (feats[0], None) if feats else (None, f"no scene < {cloud_max}% cloud in {dt_range}")


def read_window(href: str, bbox: list[float]) -> Optional[np.ndarray]:
    """Read the bbox (EPSG:4326) window from a COG band; returns the raw pixel array."""
    with rasterio.Env(**GDAL_ENV):
        with rasterio.open(https(href)) as ds:
            l, b, r, t = transform_bounds("EPSG:4326", ds.crs, bbox[0], bbox[1], bbox[2], bbox[3])
            win = from_bounds(l, b, r, t, ds.transform)
            arr = ds.read(1, window=win).astype("float64")
    return arr if arr.size else None


def asset_href(scene: dict, key: str) -> Optional[str]:
    a = scene.get("assets", {}).get(key)
    return a.get("href") if a else None


def scene_date(scene: dict) -> str:
    return (scene.get("properties", {}).get("datetime") or "")[:10]


def scene_cloud(scene: dict) -> float:
    return scene.get("properties", {}).get("eo:cloud_cover")


def sun_elevation(scene: dict) -> Optional[float]:
    p = scene.get("properties", {})
    if p.get("view:sun_elevation") is not None:
        return p["view:sun_elevation"]
    z = p.get("s2:mean_solar_zenith")
    return (90.0 - z) if z is not None else None
