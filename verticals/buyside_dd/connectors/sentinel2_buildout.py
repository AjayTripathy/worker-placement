"""Sentinel-2 optical buildout / construction-activity connector ($0, no auth).

WHY — the general "is this parcel physically being built / active?" sensor.
Carbon Mapper (carbon_mapper.py) only sees EMITTING assets (O&G, landfill). This
connector is the universal optical complement: it measures whether a parcel went
from bare ground/vegetation to BUILT between two dates — the physical ground-truth
behind a CFD/land-secured "buildout on schedule" claim or a buyside "facility under
construction / operating" claim.

FREE TIER (this module): ESA Sentinel-2 L2A (10-20 m), via the public Element84
Earth Search STAC API + the open `sentinel-cogs` AWS bucket. No account, no key.
Coarser than Planet (10 m vs 3 m / 50 cm) but $0 and global. The PAID ESCALATION
TIER is PlanetImageryConnector (planet_imagery.py) — same BaseConnector interface,
PlanetScope/SkySat resolution, behind a commercial license (see TECH_DEBT TD-1).

SIGNAL — over a parcel window at a baseline date vs a recent date:
  NDVI  = (NIR-Red)/(NIR+Red)     vegetation greenness
  NDBI  = (SWIR16-NIR)/(SWIR16+NIR)  built-up / bare index
A buildout reads as NDBI UP and NDVI DOWN (vegetation/soil -> roofs/pavement).
We report the deltas and a classification; absence of change is also a real datum
(stalled buildout = a land-secured red flag).

Inputs (ConnectorRequest):
  - extra={"lat":..,"lon":..,"radius_km":0.3}  OR  extra={"bbox":[minLon,minLat,maxLon,maxLat]}
  - address (US) -> geocoded via the free Census geocoder
  - extra optional: {"baseline":"2021-01-01/2021-06-30", "recent":"2025-09-01/2026-06-15", "cloud_max":20}
"""

from __future__ import annotations

# Knowledge-graph dispatch contract (see knowledge_graph/dispatch.py) — added 2026-07-29 gap-close.
APPLIES_TO = {
    "kind": 'm_source',
    "sic_codes": [],
    "sic_prefixes": ['15', '16', '17', '65', '70'],
    "issuer_features": ['construction_activity_claim', 'physical_plant_operations', 'real_estate_development'],
    "asset_classes": ['corporate_ipo_dd'],
    "applies_universally": False,
    "summary": 'Free Sentinel-2 NDBI/NDVI parcel change: is claimed construction actually happening.',
}

import math
from datetime import datetime, timezone
from typing import ClassVar, Optional
from urllib.parse import quote

import numpy as np
import rasterio
from rasterio.warp import transform_bounds
from rasterio.windows import from_bounds

from .base import (
    BaseConnector, ConnectorObservation, ConnectorRequest, ConnectorResult,
    ErrorKind, safe_get,
)

_STAC = "https://earth-search.aws.element84.com/v1/search"
_COLLECTION = "sentinel-2-l2a"
_GEOCODER = ("https://geocoding.geo.census.gov/geocoder/locations/onelineaddress"
             "?address={addr}&benchmark=Public_AR_Current&format=json")
_GDAL_ENV = dict(AWS_NO_SIGN_REQUEST="YES", GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR",
                 GDAL_HTTP_TIMEOUT="30", GDAL_HTTP_MAX_RETRY="2", VSI_CACHE="TRUE")
# NDBI rises and NDVI falls when ground is built up. Thresholds tuned conservatively.
_NDBI_BUILDOUT = 0.06     # >= this rise in built-up index => construction signal
_NDVI_DROP = 0.05         # >= this fall in greenness corroborates


def _https(href: str) -> str:
    if href.startswith("s3://sentinel-cogs/"):
        return "https://sentinel-cogs.s3.us-west-2.amazonaws.com/" + href[len("s3://sentinel-cogs/"):]
    return href


def _bbox_from_point(lat: float, lon: float, radius_km: float) -> list[float]:
    dlat = radius_km / 111.0
    dlon = radius_km / (111.0 * max(0.05, math.cos(math.radians(lat))))
    return [lon - dlon, lat - dlat, lon + dlon, lat + dlat]


class Sentinel2BuildoutConnector(BaseConnector):
    source_id = "sentinel2_buildout"
    rate_limit_per_min = 30
    user_agent = "SignalOS-BuysideDD/0.1 (research; sentinel2-buildout)"

    def _geocode(self, address: str) -> Optional[tuple[float, float]]:
        resp, ek, ed = safe_get(self._session(), _GEOCODER.format(addr=quote(address)), timeout=self.timeout_s)
        if resp is None:
            return None
        try:
            m = resp.json()["result"]["addressMatches"]
            return (float(m[0]["coordinates"]["y"]), float(m[0]["coordinates"]["x"])) if m else None
        except (ValueError, KeyError, IndexError, TypeError):
            return None

    def _resolve_bbox(self, request: ConnectorRequest) -> tuple[Optional[list[float]], Optional[str]]:
        x = request.extra or {}
        if x.get("bbox") and len(x["bbox"]) == 4:
            return [float(v) for v in x["bbox"]], None
        if x.get("lat") is not None and x.get("lon") is not None:
            return _bbox_from_point(float(x["lat"]), float(x["lon"]), float(x.get("radius_km", 0.3))), None
        if request.address:
            geo = self._geocode(request.address)
            if geo:
                return _bbox_from_point(geo[0], geo[1], float(x.get("radius_km", 0.3))), f"geocoded '{request.address}'"
            return None, f"could not geocode '{request.address}'"
        return None, "need extra.lat+lon, extra.bbox, or a geocodable address"

    @staticmethod
    def _rfc3339(dt_range: str) -> str:
        """Element84 STAC now requires RFC3339 datetimes (rejects bare YYYY-MM-DD as of 2026).
        Convert 'YYYY-MM-DD/YYYY-MM-DD' -> 'YYYY-MM-DDT00:00:00Z/YYYY-MM-DDT23:59:59Z'."""
        def one(d: str, end: bool) -> str:
            d = d.strip()
            if "T" in d:
                return d
            return d + ("T23:59:59Z" if end else "T00:00:00Z")
        if "/" in dt_range:
            a, b = dt_range.split("/", 1)
            return f"{one(a, False)}/{one(b, True)}"
        return one(dt_range, False)

    def _best_scene(self, bbox: list[float], dt_range: str, cloud_max: int) -> tuple[Optional[dict], Optional[str]]:
        body = {"collections": [_COLLECTION], "bbox": bbox, "datetime": self._rfc3339(dt_range),
                "query": {"eo:cloud_cover": {"lt": cloud_max}}, "limit": 30,
                "sortby": [{"field": "properties.eo:cloud_cover", "direction": "asc"}]}
        s = self._session()
        try:
            r = s.post(_STAC, json=body, timeout=self.timeout_s)
        except Exception as e:
            return None, f"stac post: {e}"
        if r.status_code >= 400:
            return None, f"stac http {r.status_code}"
        feats = r.json().get("features", [])
        return (feats[0], None) if feats else (None, f"no scene < {cloud_max}% cloud in {dt_range}")

    def _mean_index(self, scene: dict, bbox: list[float]) -> Optional[dict]:
        """Read Red/NIR/SWIR16 over the parcel window; return mean NDVI, NDBI, and band means."""
        a = scene.get("assets", {})
        try:
            red_h, nir_h, swir_h = _https(a["red"]["href"]), _https(a["nir"]["href"]), _https(a["swir16"]["href"])
        except KeyError:
            return None

        def band_mean(href: str) -> Optional[float]:
            with rasterio.Env(**_GDAL_ENV):
                with rasterio.open(href) as ds:
                    l, b, rt, t = transform_bounds("EPSG:4326", ds.crs, bbox[0], bbox[1], bbox[2], bbox[3])
                    win = from_bounds(l, b, rt, t, ds.transform)
                    arr = ds.read(1, window=win).astype("float64")
            if arr.size == 0:
                return None
            arr = arr[arr > 0]          # drop fill/nodata (0)
            return float(arr.mean()) if arr.size else None

        red, nir, swir = band_mean(red_h), band_mean(nir_h), band_mean(swir_h)
        if red is None or nir is None or swir is None:
            return None
        ndvi = (nir - red) / (nir + red) if (nir + red) else None
        ndbi = (swir - nir) / (swir + nir) if (swir + nir) else None
        return {"ndvi": ndvi, "ndbi": ndbi, "red": red, "nir": nir, "swir16": swir,
                "date": (scene.get("properties", {}).get("datetime") or "")[:10],
                "cloud": scene.get("properties", {}).get("eo:cloud_cover")}

    def query(self, request: ConnectorRequest) -> ConnectorResult:
        bbox, note = self._resolve_bbox(request)
        if bbox is None:
            return self._fail(request, ErrorKind.UNSUPPORTED, note or "no location")
        x = request.extra or {}
        cloud_max = int(x.get("cloud_max", 20))
        base_range = x.get("baseline", "2021-01-01/2021-09-30")
        recent_range = x.get("recent", "2025-06-01/2026-06-15")

        self._throttle()
        base_scene, e1 = self._best_scene(bbox, base_range, cloud_max)
        recent_scene, e2 = self._best_scene(bbox, recent_range, cloud_max)
        if base_scene is None or recent_scene is None:
            return self._fail(request, ErrorKind.NOT_FOUND, f"scene gap: baseline={e1}; recent={e2}")

        base = self._mean_index(base_scene, bbox)
        recent = self._mean_index(recent_scene, bbox)
        if base is None or recent is None:
            return self._fail(request, ErrorKind.PARSE_FAIL, "could not read COG window for one scene")

        d_ndbi = recent["ndbi"] - base["ndbi"]
        d_ndvi = recent["ndvi"] - base["ndvi"]
        buildout = (d_ndbi >= _NDBI_BUILDOUT)
        corroborated = buildout and (d_ndvi <= -_NDVI_DROP)
        # confidence discounts for cloud; both scenes already < cloud_max
        conf = round(max(0.4, 0.9 - (max(base["cloud"] or 0, recent["cloud"] or 0) / 100.0)), 2)

        url = f"https://earth-search.aws.element84.com/v1 (S2 L2A, bbox {bbox})"
        obs = [
            ConnectorObservation(
                attribute="construction_activity", value=buildout, confidence=conf, source_url=url,
                extra={"corroborated_by_ndvi_drop": corroborated,
                       "baseline_date": base["date"], "recent_date": recent["date"]}),
            ConnectorObservation(attribute="ndbi_delta", value=round(d_ndbi, 4),
                                 confidence=conf, source_url=url,
                                 extra={"baseline_ndbi": round(base["ndbi"], 4), "recent_ndbi": round(recent["ndbi"], 4)}),
            ConnectorObservation(attribute="ndvi_delta", value=round(d_ndvi, 4),
                                 confidence=conf, source_url=url,
                                 extra={"baseline_ndvi": round(base["ndvi"], 4), "recent_ndvi": round(recent["ndvi"], 4)}),
            ConnectorObservation(attribute="baseline_scene",
                                 value={"date": base["date"], "cloud_pct": base["cloud"]}, confidence=1.0, source_url=url),
            ConnectorObservation(attribute="recent_scene",
                                 value={"date": recent["date"], "cloud_pct": recent["cloud"]}, confidence=1.0, source_url=url),
        ]
        return self._ok(request, obs)
