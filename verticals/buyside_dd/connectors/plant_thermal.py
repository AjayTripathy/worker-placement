"""plant_thermal — read a parcel's land-surface temperature from Landsat (free, via Microsoft
Planetary Computer) to detect/track an industrial FURNACE coming online. Built for the Stevanato
Fishers/Latina GLP-1 plant-ramp monitor (2026-06).

WHY: a glass melting furnace runs ~1500C continuously — an unfakeable production signal a generic
factory lacks. A fired furnace shows as a HOT PIXEL above the building's own roof temperature.
Metric = "furnace excess" = max(LST) - median(LST) over the parcel: a running furnace makes the
hottest pixel anomalously hot vs the bulk roof/ground; an idle/empty building is ~uniform (excess~0).
Track the excess over time = utilization ramp. Calibrate against a KNOWN-operating furnace (control).

SOURCE: MPC STAC `landsat-c2-l2`, asset `lwir11` (Level-2 Surface Temperature, Kelvin = DN*0.00341802
+ 149.0). Free; assets signed via MPC's /sign endpoint. CAVEAT: Landsat overpass ~10:30 local
(daytime) -> solar roof-heating confound; the max-minus-median excess controls for it (furnace heat
is ABOVE the roof's own solar temp), and the control-plant calibration anchors interpretation. Night
thermal (ECOSTRESS) is the upgrade (needs Earthdata).
"""

from __future__ import annotations

# Knowledge-graph dispatch contract (see knowledge_graph/dispatch.py) — added 2026-07-29 gap-close.
APPLIES_TO = {
    "kind": 'm_source',
    "sic_codes": [],
    "sic_prefixes": ['2', '3'],
    "issuer_features": ['physical_plant_operations', 'capacity_ramp_claim'],
    "asset_classes": ['corporate_ipo_dd'],
    "applies_universally": False,
    "summary": 'Landsat land-surface temperature of a plant parcel: utilization cross-check for manufacturers.',
}

import math
from typing import Optional

import requests

from .base import (BaseConnector, ConnectorObservation, ConnectorRequest,
                   ConnectorResult, ErrorKind)

_STAC = "https://planetarycomputer.microsoft.com/api/stac/v1/search"
_SIGN = "https://planetarycomputer.microsoft.com/api/sas/v1/sign"
_ST_SCALE, _ST_OFFSET = 0.00341802, 149.0   # Landsat C2 L2 ST_B10 -> Kelvin


def _rfc(d: str, end: bool) -> str:
    return d if "T" in d else d + ("T23:59:59Z" if end else "T00:00:00Z")


def _bbox(lat: float, lon: float, radius_km: float) -> list[float]:
    dlat = radius_km / 111.0
    dlon = radius_km / (111.0 * max(0.05, math.cos(math.radians(lat))))
    return [lon - dlon, lat - dlat, lon + dlon, lat + dlat]


def _sign(href: str) -> Optional[str]:
    try:
        r = requests.get(_SIGN, params={"href": href}, timeout=20)
        return r.json().get("href") if r.status_code == 200 else None
    except Exception:
        return None


def thermal_series(lat: float, lon: float, *, radius_km: float = 0.4,
                   start: str = "2023-01-01", end: str = "2026-06-15",
                   cloud_max: int = 30, max_scenes: int = 60) -> list[dict]:
    """Per-scene furnace-excess time series over the parcel. Returns
    [{date, max_C, median_C, excess_C, n_px}], oldest->newest."""
    import numpy as np
    import rasterio
    from rasterio.warp import transform_bounds
    from rasterio.windows import from_bounds

    bbox = _bbox(lat, lon, radius_km)
    body = {"collections": ["landsat-c2-l2"], "bbox": bbox,
            "datetime": f"{_rfc(start, False)}/{_rfc(end, True)}",
            "query": {"eo:cloud_cover": {"lt": cloud_max},
                      "platform": {"in": ["landsat-8", "landsat-9"]}},
            "limit": max_scenes, "sortby": [{"field": "properties.datetime", "direction": "asc"}]}
    try:
        feats = requests.post(_STAC, json=body, timeout=40).json().get("features", [])
    except Exception:
        return []
    out = []
    for f in feats:
        href = (f.get("assets", {}).get("lwir11", {}) or {}).get("href")
        if not href:
            continue
        signed = _sign(href)
        if not signed:
            continue
        try:
            with rasterio.open(signed) as ds:
                l, b, rt, t = transform_bounds("EPSG:4326", ds.crs, *bbox)
                win = from_bounds(l, b, rt, t, ds.transform)
                arr = ds.read(1, window=win).astype("float64")
            arr = arr[arr > 0]                       # drop fill
            if arr.size < 4:
                continue
            kelvin = arr * _ST_SCALE + _ST_OFFSET
            celsius = kelvin - 273.15
            celsius = celsius[(celsius > -40) & (celsius < 200)]
            if celsius.size < 4:
                continue
            mx, med = float(np.max(celsius)), float(np.median(celsius))
            out.append({"date": f["properties"]["datetime"][:10],
                        "max_C": round(mx, 1), "median_C": round(med, 1),
                        "excess_C": round(mx - med, 1), "n_px": int(celsius.size)})
        except Exception:
            continue
    return out


def _trend(series: list[dict]) -> Optional[float]:
    """Slope of excess_C over time (deg-C per year) via simple least squares on ordinal dates."""
    import datetime as _dt
    if len(series) < 4:
        return None
    xs = [_dt.date.fromisoformat(s["date"]).toordinal() for s in series]
    ys = [s["excess_C"] for s in series]
    n = len(xs); mx = sum(xs) / n; my = sum(ys) / n
    den = sum((x - mx) ** 2 for x in xs)
    if den == 0:
        return None
    slope = sum((xs[i] - mx) * (ys[i] - my) for i in range(n)) / den
    return round(slope * 365.25, 2)   # per year


class PlantThermalConnector(BaseConnector):
    source_id = "plant_thermal"

    def query(self, request: ConnectorRequest) -> ConnectorResult:
        x = request.extra or {}
        lat, lon = x.get("lat"), x.get("lon")
        if lat is None or lon is None:
            return self._fail(request, ErrorKind.UNSUPPORTED, "plant_thermal needs extra.lat + extra.lon")
        series = thermal_series(float(lat), float(lon),
                                radius_km=float(x.get("radius_km", 0.4)),
                                start=x.get("start", "2023-01-01"),
                                end=x.get("end", "2026-06-15"),
                                cloud_max=int(x.get("cloud_max", 30)))
        if not series:
            return self._fail(request, ErrorKind.NOT_FOUND, "no Landsat thermal scenes resolved")
        recent = series[-6:]
        recent_excess = sum(s["excess_C"] for s in recent) / len(recent)
        early = series[:6]
        early_excess = sum(s["excess_C"] for s in early) / len(early)
        return self._ok(request, [
            ConnectorObservation(attribute="furnace_excess_C", value=round(recent_excess, 1),
                                 confidence=0.6,
                                 extra={"interpretation": "max-minus-median LST over parcel; high/rising "
                                        "= furnace fired & utilization climbing",
                                        "recent_mean": round(recent_excess, 1),
                                        "early_mean": round(early_excess, 1),
                                        "n_scenes": len(series)}),
            ConnectorObservation(attribute="furnace_excess_trend_C_per_yr", value=_trend(series),
                                 confidence=0.5, extra={"sign>0": "ramping"}),
            ConnectorObservation(attribute="thermal_series", value=series[-12:],
                                 extra={"full_n": len(series)}),
        ])


if __name__ == "__main__":
    import sys, json
    lat, lon = float(sys.argv[1]), float(sys.argv[2])
    s = thermal_series(lat, lon, start=sys.argv[3] if len(sys.argv) > 3 else "2023-01-01")
    print(f"{len(s)} scenes")
    for r in s:
        print(f"  {r['date']}  max {r['max_C']:5.1f}C  med {r['median_C']:5.1f}C  "
              f"excess {r['excess_C']:5.1f}C  ({r['n_px']}px)")
    if s:
        print("trend (excess C/yr):", _trend(s))
