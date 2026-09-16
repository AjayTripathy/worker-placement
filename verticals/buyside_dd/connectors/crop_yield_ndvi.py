"""Crop yield / condition connector — peak-season NDVI, YoY, as a revenue cross-check ($0).

WHY — the highest-value satellite use that has NO phone-data substitute and runs on
Planet's CHEAP daily product (and on free Sentinel-2): vegetation greenness over an
agricultural AOI at peak growing season is a well-established proxy for crop condition
and yield. Cross-checks the marketed number against the field: an ag/commodity/
fertilizer/crop-insurance issuer that guides "record yields / strong harvest" while
peak NDVI is DOWN year-over-year is a divergence worth a flag (Mode-B verification).

Signal — for an AOI and a peak-season window, take the lowest-cloud scene each year and
compute mean per-pixel NDVI = (NIR-Red)/(NIR+Red). Compare the current year to prior
year(s): ΔNDVI YoY and a condition-vs-prior classification. (Peak NDVI tracks biomass /
yield potential; season-integrated NDVI is the productization upgrade.)

Free tier: Sentinel-2 L2A 10 m (red/nir both 10 m -> clean per-pixel NDVI). Paid upgrade:
PlanetScope 3 m daily fills cloud gaps and resolves field-edge / small plots (planet_imagery).

Inputs (ConnectorRequest):
  - extra={"lat":..,"lon":..,"radius_km":1.0}  OR  extra={"bbox":[...]}  OR address (geocoded)
  - extra optional: {"current_year":2025, "n_prior":3,
                     "peak_start_md":"07-10", "peak_end_md":"08-25", "cloud_max":20}
"""

from __future__ import annotations

# Knowledge-graph dispatch contract (see knowledge_graph/dispatch.py) — added 2026-07-29 gap-close.
APPLIES_TO = {
    "kind": 'm_source',
    "sic_codes": [],
    "sic_prefixes": ['01', '02', '07', '20'],
    "issuer_features": ['agricultural_exposure'],
    "asset_classes": ['corporate_ipo_dd'],
    "applies_universally": False,
    "summary": 'Peak-season NDVI crop-condition read as a revenue cross-check for ag-exposed issuers.',
}

from typing import Optional

import numpy as np

from . import _s2util as S2
from .base import BaseConnector, ConnectorObservation, ConnectorRequest, ConnectorResult, ErrorKind

# YoY NDVI move beyond this (absolute) is a material condition change worth surfacing.
_MATERIAL_DNDVI = 0.05


class CropYieldNdviConnector(BaseConnector):
    source_id = "crop_yield_ndvi"
    rate_limit_per_min = 30
    user_agent = "SignalOS-BuysideDD/0.1 (research; crop-ndvi)"

    def _resolve_bbox(self, request: ConnectorRequest):
        x = request.extra or {}
        if x.get("bbox") and len(x["bbox"]) == 4:
            return [float(v) for v in x["bbox"]], None
        if x.get("lat") is not None and x.get("lon") is not None:
            return S2.bbox_from_point(float(x["lat"]), float(x["lon"]), float(x.get("radius_km", 1.0))), None
        if request.address:
            geo = S2.geocode(self._session(), request.address, self.timeout_s)
            if geo:
                return S2.bbox_from_point(geo[0], geo[1], float(x.get("radius_km", 1.0))), f"geocoded '{request.address}'"
            return None, f"could not geocode '{request.address}'"
        return None, "need extra.lat+lon, extra.bbox, or a geocodable address"

    def _peak_ndvi(self, bbox, year: int, peak_start_md: str, peak_end_md: str, cloud_max: int) -> Optional[dict]:
        dt = f"{year}-{peak_start_md}T00:00:00Z/{year}-{peak_end_md}T23:59:59Z"
        scene, err = S2.best_scene(self._session(), bbox, dt, cloud_max, self.timeout_s)
        if scene is None:
            return None
        red = S2.read_window(S2.asset_href(scene, "red"), bbox)
        nir = S2.read_window(S2.asset_href(scene, "nir"), bbox)
        if red is None or nir is None:
            return None
        h, w = min(red.shape[0], nir.shape[0]), min(red.shape[1], nir.shape[1])
        red, nir = red[:h, :w], nir[:h, :w]
        denom = nir + red
        mask = denom > 0
        ndvi = np.where(mask, (nir - red) / np.where(mask, denom, 1), np.nan)
        veg = ndvi[mask & (ndvi > 0.2)]            # active vegetation pixels
        return {"year": year, "date": S2.scene_date(scene), "cloud": S2.scene_cloud(scene),
                "mean_ndvi": float(np.nanmean(ndvi)) if mask.any() else None,
                "veg_ndvi": float(veg.mean()) if veg.size else None,
                "veg_frac": float(veg.size / ndvi.size)}

    def query(self, request: ConnectorRequest) -> ConnectorResult:
        bbox, note = self._resolve_bbox(request)
        if bbox is None:
            return self._fail(request, ErrorKind.UNSUPPORTED, note or "no location")
        x = request.extra or {}
        cur = int(x.get("current_year", 2025))
        n_prior = int(x.get("n_prior", 3))
        ps, pe = x.get("peak_start_md", "07-10"), x.get("peak_end_md", "08-25")
        cloud_max = int(x.get("cloud_max", 20))

        self._throttle()
        series = []
        for yr in range(cur - n_prior, cur + 1):
            r = self._peak_ndvi(bbox, yr, ps, pe, cloud_max)
            if r:
                series.append(r)
        if not series or series[-1]["year"] != cur or series[-1]["mean_ndvi"] is None:
            return self._fail(request, ErrorKind.NOT_FOUND, "no usable current-year peak scene")

        cur_rec = series[-1]
        prior = [s for s in series[:-1] if s["mean_ndvi"] is not None]
        prior_mean = float(np.mean([s["mean_ndvi"] for s in prior])) if prior else None
        d_yoy = (cur_rec["mean_ndvi"] - series[-2]["mean_ndvi"]) if len(series) >= 2 and series[-2]["mean_ndvi"] is not None else None
        d_vs_prioravg = (cur_rec["mean_ndvi"] - prior_mean) if prior_mean is not None else None

        verdict = "in-line"
        ref = d_vs_prioravg if d_vs_prioravg is not None else d_yoy
        if ref is not None:
            if ref <= -_MATERIAL_DNDVI:
                verdict = "BELOW prior — weaker crop condition than the recent baseline"
            elif ref >= _MATERIAL_DNDVI:
                verdict = "ABOVE prior — stronger crop condition than the recent baseline"
        conf = round(max(0.4, 0.9 - (cur_rec["cloud"] or 0) / 100.0), 2)

        url = f"https://earth-search.aws.element84.com/v1 (S2 L2A peak NDVI, bbox {bbox})"
        obs = [
            ConnectorObservation(attribute="crop_condition_vs_prior", value=verdict, confidence=conf,
                                 source_url=url, extra={"geocode_note": note}),
            ConnectorObservation(attribute="crop_ndvi_peak", value=round(cur_rec["mean_ndvi"], 4),
                                 value_unit="NDVI", confidence=conf, source_url=url,
                                 extra={"year": cur, "date": cur_rec["date"], "cloud_pct": cur_rec["cloud"]}),
            ConnectorObservation(attribute="crop_ndvi_yoy_delta", value=round(d_yoy, 4) if d_yoy is not None else None,
                                 confidence=conf, source_url=url),
            ConnectorObservation(attribute="crop_ndvi_vs_prior_avg",
                                 value=round(d_vs_prioravg, 4) if d_vs_prioravg is not None else None,
                                 confidence=conf, source_url=url,
                                 extra={"prior_years_avg": round(prior_mean, 4) if prior_mean is not None else None}),
            ConnectorObservation(attribute="crop_ndvi_series",
                                 value=[{"year": s["year"], "date": s["date"], "mean_ndvi": round(s["mean_ndvi"], 4) if s["mean_ndvi"] is not None else None,
                                         "cloud_pct": s["cloud"]} for s in series],
                                 confidence=1.0, source_url=url),
        ]
        return self._ok(request, obs)
