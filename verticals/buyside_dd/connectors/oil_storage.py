"""Petroleum storage inventory connector — floating-roof shadow proxy ($0 aggregate tier).

WHY — crude/product inventory at a tank farm is financially material, hard to fake, and
has NO phone-data substitute. Floating-roof tanks sink as they drain: an emptier tank
shows a larger interior shadow (roof low, inner wall casts a crescent); a full tank shows
the roof near the rim (small shadow, bright metal roof). Aggregate tank-farm shadow
fraction is therefore an INVERSE proxy for fill. Cross-checks a midstream/E&P/refiner's
reported storage utilization against the physical tanks (Mode-B), and complements EIA
weekly stocks with a per-site read.

RESOLUTION REALITY (honest): true PER-TANK volumetrics need ~0.5-3 m (PlanetScope/SkySat/
Maxar) where a tank is 20-100 px and the inner shadow is measurable. On FREE Sentinel-2
(10 m) a tank is only 5-10 px, so this connector delivers an AGGREGATE tank-farm
shadow/brightness index over time — directionally informative, not a calibrated barrel
count. The PAID escalation is planet_imagery (3 m) for per-tank shadow geometry. Sun
elevation (reported per scene) is the dominant confounder and is disclosed, not corrected,
on the free tier.

Inputs (ConnectorRequest):
  - extra={"lat":..,"lon":..,"radius_km":3.0}  OR  extra={"bbox":[...]}  OR address
  - extra optional: {"periods":["2023-06-01/2023-08-31", ...], "cloud_max":15}
"""

from __future__ import annotations

# Knowledge-graph dispatch contract (see knowledge_graph/dispatch.py) — added 2026-07-29 gap-close.
APPLIES_TO = {
    "kind": 'm_source',
    "sic_codes": [],
    "sic_prefixes": ['13', '29', '46', '51'],
    "issuer_features": ['commodity_storage_business', 'petroleum_exposure'],
    "asset_classes": ['corporate_ipo_dd'],
    "applies_universally": False,
    "summary": 'Floating-roof shadow petroleum-inventory proxy. Storage/refining/midstream issuers.',
}

import math
from typing import Optional

import numpy as np

from . import _s2util as S2
from .base import BaseConnector, ConnectorObservation, ConnectorRequest, ConnectorResult, ErrorKind

_DEFAULT_PERIODS = ["2023-04-01/2023-06-30", "2023-10-01/2023-12-31",
                    "2024-04-01/2024-06-30", "2024-10-01/2024-12-31",
                    "2025-04-01/2025-06-30", "2025-10-01/2025-12-31"]


class OilStorageConnector(BaseConnector):
    source_id = "oil_storage"
    rate_limit_per_min = 30
    user_agent = "SignalOS-BuysideDD/0.1 (research; oil-storage)"

    def _resolve_bbox(self, request: ConnectorRequest):
        x = request.extra or {}
        if x.get("bbox") and len(x["bbox"]) == 4:
            return [float(v) for v in x["bbox"]], None
        if x.get("lat") is not None and x.get("lon") is not None:
            return S2.bbox_from_point(float(x["lat"]), float(x["lon"]), float(x.get("radius_km", 3.0))), None
        if request.address:
            geo = S2.geocode(self._session(), request.address, self.timeout_s)
            if geo:
                return S2.bbox_from_point(geo[0], geo[1], float(x.get("radius_km", 3.0))), f"geocoded '{request.address}'"
            return None, f"could not geocode '{request.address}'"
        return None, "need extra.lat+lon, extra.bbox, or a geocodable address"

    def _shadow_index(self, bbox, dt_range: str, cloud_max: int) -> Optional[dict]:
        scene, err = S2.best_scene(self._session(), bbox, dt_range, cloud_max, self.timeout_s)
        if scene is None:
            return None
        bands = [S2.read_window(S2.asset_href(scene, b), bbox) for b in ("red", "green", "blue")]
        if any(b is None for b in bands):
            return None
        h = min(b.shape[0] for b in bands); w = min(b.shape[1] for b in bands)
        bright = np.mean([b[:h, :w] for b in bands], axis=0)
        bright = bright[bright > 0]
        if bright.size < 16:
            return None
        med = float(np.median(bright))
        shadow_frac = float((bright < 0.55 * med).mean())   # dark-pixel fraction (inverse fill proxy)
        sun = S2.sun_elevation(scene) or 45.0
        # shadow length ∝ 1/tan(sun_elev); multiply by tan() to remove the geometric sun-angle confound
        shadow_norm = round(shadow_frac * math.tan(math.radians(sun)), 4)
        return {"date": S2.scene_date(scene), "cloud": S2.scene_cloud(scene),
                "sun_elev": round(sun, 1), "mean_brightness": round(med, 1),
                "shadow_fraction": round(shadow_frac, 4), "shadow_norm": shadow_norm}

    def query(self, request: ConnectorRequest) -> ConnectorResult:
        bbox, note = self._resolve_bbox(request)
        if bbox is None:
            return self._fail(request, ErrorKind.UNSUPPORTED, note or "no location")
        x = request.extra or {}
        periods = x.get("periods", _DEFAULT_PERIODS)
        cloud_max = int(x.get("cloud_max", 15))

        self._throttle()
        series = []
        for p in periods:
            if "T" not in p:                       # normalize date-only ranges to RFC3339 (Element84 needs the time)
                a, b = p.split("/")
                p = f"{a}T00:00:00Z/{b}T23:59:59Z"
            r = self._shadow_index(bbox, p, cloud_max)
            if r:
                series.append(r)
        if len(series) < 2:
            return self._fail(request, ErrorKind.NOT_FOUND, f"only {len(series)} usable scene(s)")

        sf = [s["shadow_norm"] for s in series]            # sun-normalized; higher => emptier
        lo, hi = min(sf), max(sf)
        rng = (hi - lo) or 1.0
        latest = series[-1]
        # utilization proxy: higher fill => smaller (sun-normalized) shadow. Rank within observed range.
        util_proxy = round(1.0 - (latest["shadow_norm"] - lo) / rng, 3)
        direction = ("DRAWN DOWN vs window" if latest["shadow_norm"] > series[0]["shadow_norm"] + 0.01
                     else "FILLED vs window" if latest["shadow_norm"] < series[0]["shadow_norm"] - 0.01
                     else "flat vs window")
        conf = round(max(0.3, 0.7 - (latest["cloud"] or 0) / 100.0), 2)   # capped low: aggregate 10m proxy

        url = f"https://earth-search.aws.element84.com/v1 (S2 L2A tank-farm shadow, bbox {bbox})"
        obs = [
            ConnectorObservation(attribute="petroleum_storage_inventory",
                                 value={"utilization_proxy_0to1": util_proxy, "direction": direction,
                                        "latest_date": latest["date"], "tier": "aggregate_10m_proxy"},
                                 confidence=conf, source_url=url,
                                 extra={"caveat": "free Sentinel-2 10m aggregate shadow proxy, NOT a calibrated "
                                                  "barrel count. Sun-elevation confound IS normalized (×tan(elev)), "
                                                  "but the residual at 10m sits within noise — tanks are only 5-10px "
                                                  "so per-tank roof-shadow is sub-pixel. This is the case that "
                                                  "genuinely needs PlanetScope/SkySat 3m (planet_imagery, paid); "
                                                  "use within-season comparisons and treat as low-confidence.",
                                        "geocode_note": note}),
            ConnectorObservation(attribute="tank_shadow_fraction", value=latest["shadow_fraction"],
                                 confidence=conf, source_url=url,
                                 extra={"sun_elev_deg": latest["sun_elev"]}),
            ConnectorObservation(attribute="storage_series",
                                 value=series, confidence=1.0, source_url=url),
        ]
        return self._ok(request, obs)
