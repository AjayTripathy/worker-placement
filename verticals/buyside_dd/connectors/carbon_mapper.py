"""Carbon Mapper (Planet Tanager-1 + EMIT + airborne) methane/CO2 super-emitter connector.

WHY THIS EXISTS — satellite ground-truth as a verification channel.
Our detectors verify paper claims against documentary M-sources (deeds, permits,
EDGAR, OSHA). Those confirm a facility was *registered* or *permitted*; none of
them confirm a facility is *physically emitting right now*. Carbon Mapper's public
plume catalog closes that gap: a quantified methane/CO2 plume at a parcel is an
INDEPENDENT, instrument-measured observation that the site is operating — and, on
the honesty side, a direct refutation when an issuer/operator markets "clean" or
"within limits" while a 10,000 kg/hr plume sits over the asset.

The plume detections come from Planet's Tanager-1 hyperspectral satellite ("tan"),
NASA/JPL's EMIT ("emi"), and the Global Airborne Observatory / AVIRIS aircraft —
i.e. this is genuinely Planet-lineage data, free for non-commercial use via the
public Data Platform API (no token for the annotated catalog).

Endpoint (public, GET, no auth):
  https://api.carbonmapper.org/api/v1/catalog/plumes/annotated
  ?bbox=minLon&bbox=minLat&bbox=maxLon&bbox=maxLat
  &plume_gas=CH4 &emission_min=<kg/hr> &datetime=<RFC3339 range> &sort=emissions_desc

Quirk handled here: the annotated list nulls `latitude`/`longitude`/`datetime`, but
the `plume_id` encodes instrument + acquisition timestamp
(`tan20250815t183402...` -> Tanager, 2025-08-15 18:34:02), so we recover both from
the id. Location is already constrained by the bbox we query.

Inputs (via ConnectorRequest):
  - extra={"lat":.., "lon":.., "radius_km":1.0}  OR  extra={"bbox":[minLon,minLat,maxLon,maxLat]}
  - address (US) — geocoded to lat/lon via the free Census geocoder when no coords given
  - extra optional: {"gas":"CH4"|"CO2", "emission_min_kg_hr":0, "since":"YYYY-MM-DD"}

Returns observations keyed for the `environmental_status` attribute so it
co-dispatches with EPA Envirofacts and corroborates (or contradicts) it:
  - methane_super_emitter_present : bool   (the load-bearing verification datum)
  - methane_plume_count           : int
  - methane_max_emission_kg_hr    : float
  - methane_plume[i]              : per-plume record {plume_id, emission_kg_hr, gas, instrument, acq_date, quality}
"""

from __future__ import annotations

# Knowledge-graph dispatch contract (see knowledge_graph/dispatch.py) — added 2026-07-29 gap-close.
APPLIES_TO = {
    "kind": 'm_source',
    "sic_codes": [],
    "sic_prefixes": ['10', '12', '13', '28', '29', '46', '49'],
    "issuer_features": ['physical_plant_operations', 'methane_emitting_operations', 'environmental_claims'],
    "asset_classes": ['corporate_ipo_dd'],
    "applies_universally": False,
    "summary": 'Satellite methane/CO2 super-emitter plumes vs stated environmental claims. Energy/mining/chem/utilities.',
}

import math
import re
from datetime import datetime, timezone
from typing import ClassVar, Optional

from .base import (
    BaseConnector, ConnectorObservation, ConnectorRequest, ConnectorResult,
    ErrorKind, safe_get,
)

_API = "https://api.carbonmapper.org/api/v1/catalog/plumes/annotated"
_GEOCODER = ("https://geocoding.geo.census.gov/geocoder/locations/onelineaddress"
             "?address={addr}&benchmark=Public_AR_Current&format=json")
_DASHBOARD = "https://data.carbonmapper.org/"

# instrument-prefix -> human label (which platform measured the plume)
_INSTRUMENT = {
    "tan": "Tanager-1 (Planet)", "emi": "EMIT (NASA/JPL)", "ang": "AVIRIS-NG",
    "av3": "AVIRIS-3", "gao": "Global Airborne Observatory", "ssc": "satellite",
}
# annotated `plume_id`: {instr}{YYYYMMDD}t{HHMMSS}...   e.g. tan20250815t183402c38s4001-A
_PID_RE = re.compile(r"^([a-zA-Z]+)(\d{8})t(\d{6})")
# emission floor (kg/hr) above which a CH4 detection is a "super-emitter" for our purposes.
# Carbon Mapper's facility-scale detection sensitivity is ~100s kg/hr; 1000 is a
# conservative, unambiguous super-emitter threshold.
_SUPER_EMITTER_KG_HR = 1000.0
_QUALITY_CONF = {"good": 1.0, "questionable": 0.6, "bad": 0.3, None: 0.8}


def _parse_plume_id(pid: str) -> tuple[Optional[str], Optional[datetime]]:
    """Recover (instrument_label, acquisition_datetime_utc) from a plume_id."""
    if not pid:
        return None, None
    m = _PID_RE.match(pid)
    if not m:
        return None, None
    instr, ymd, hms = m.groups()
    label = _INSTRUMENT.get(instr.lower(), instr)
    try:
        dt = datetime.strptime(ymd + hms, "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
    except ValueError:
        dt = None
    return label, dt


def _bbox_from_point(lat: float, lon: float, radius_km: float) -> list[float]:
    dlat = radius_km / 111.0
    dlon = radius_km / (111.0 * max(0.05, math.cos(math.radians(lat))))
    return [lon - dlon, lat - dlat, lon + dlon, lat + dlat]


class CarbonMapperConnector(BaseConnector):
    """Resolve a location to recent satellite-measured methane/CO2 super-emitter plumes."""

    source_id = "carbon_mapper"
    rate_limit_per_min = 30
    user_agent = "SignalOS-BuysideDD/0.1 (research; carbon-mapper-connector)"

    def _geocode(self, address: str) -> Optional[tuple[float, float]]:
        s = self._session()
        url = _GEOCODER.format(addr=requests_quote(address))
        resp, ek, ed = safe_get(s, url, timeout=self.timeout_s)
        if resp is None:
            return None
        try:
            matches = resp.json().get("result", {}).get("addressMatches", [])
            if not matches:
                return None
            c = matches[0]["coordinates"]
            return float(c["y"]), float(c["x"])   # (lat, lon)
        except (ValueError, KeyError, IndexError, TypeError):
            return None

    def _resolve_bbox(self, request: ConnectorRequest) -> tuple[Optional[list[float]], Optional[str]]:
        x = request.extra or {}
        if x.get("bbox") and len(x["bbox"]) == 4:
            return [float(v) for v in x["bbox"]], None
        lat, lon = x.get("lat"), x.get("lon")
        radius = float(x.get("radius_km", 1.0))
        if lat is not None and lon is not None:
            return _bbox_from_point(float(lat), float(lon), radius), None
        if request.address:
            geo = self._geocode(request.address)
            if geo:
                return _bbox_from_point(geo[0], geo[1], radius), f"geocoded '{request.address}' -> {geo}"
            return None, f"could not geocode address '{request.address}'"
        return None, "need extra.lat+lon, extra.bbox, or a geocodable address"

    def query(self, request: ConnectorRequest) -> ConnectorResult:
        bbox, note = self._resolve_bbox(request)
        if bbox is None:
            return self._fail(request, ErrorKind.UNSUPPORTED, note or "no location")

        x = request.extra or {}
        gas = str(x.get("gas", "CH4")).upper()
        emin = int(x.get("emission_min_kg_hr", 0))
        params = [("bbox", bbox[0]), ("bbox", bbox[1]), ("bbox", bbox[2]), ("bbox", bbox[3]),
                  ("plume_gas", gas), ("emission_min", emin),
                  ("sort", "emissions_desc"), ("limit", 200), ("status", "published")]
        if x.get("since"):
            params.append(("datetime", f"{x['since']}T00:00:00Z/{self._now():%Y-%m-%dT%H:%M:%SZ}"))

        self._throttle()
        s = self._session()
        resp, ek, ed = safe_get(s, _API, timeout=self.timeout_s, params=params)
        if resp is None:
            return self._fail(request, ek or ErrorKind.UNKNOWN, ed or "request failed")
        try:
            payload = resp.json()
            items = payload.get("items", []) if isinstance(payload, dict) else []
        except ValueError as e:
            return self._fail(request, ErrorKind.PARSE_FAIL, f"json: {e}", raw=resp.text)

        plumes = []
        for p in items:
            pid = p.get("plume_id") or ""
            instr, acq = _parse_plume_id(pid)
            emission = p.get("emission_auto")
            plumes.append({
                "plume_id": pid,
                "gas": p.get("gas"),
                "emission_kg_hr": round(emission, 1) if isinstance(emission, (int, float)) else None,
                "emission_uncertainty_kg_hr": (round(p["emission_uncertainty_auto"], 1)
                                               if isinstance(p.get("emission_uncertainty_auto"), (int, float)) else None),
                "instrument": instr,
                "acq_date": acq.date().isoformat() if acq else None,
                "ipcc_sector": p.get("ipcc_sector"),
                "quality": p.get("quality"),
            })

        rates = [pl["emission_kg_hr"] for pl in plumes if pl["emission_kg_hr"] is not None]
        max_rate = max(rates) if rates else 0.0
        super_emitters = [pl for pl in plumes if (pl["emission_kg_hr"] or 0) >= _SUPER_EMITTER_KG_HR]
        present = bool(super_emitters)
        # observation-level confidence = best plume quality among super-emitters (or all)
        pool = super_emitters or plumes
        obs_conf = max((_QUALITY_CONF.get(pl["quality"], 0.8) for pl in pool), default=0.8) if pool else 0.9

        url = (f"{_DASHBOARD}?bbox={bbox[0]:.4f},{bbox[1]:.4f},{bbox[2]:.4f},{bbox[3]:.4f}")
        obs = [
            ConnectorObservation(
                attribute="methane_super_emitter_present",
                value=present, confidence=obs_conf, source_url=url,
                extra={"gas": gas, "threshold_kg_hr": _SUPER_EMITTER_KG_HR,
                       "n_super_emitters": len(super_emitters), "bbox": bbox,
                       "geocode_note": note},
            ),
            ConnectorObservation(
                attribute="methane_plume_count", value=len(plumes),
                confidence=0.95, source_url=url),
            ConnectorObservation(
                attribute="methane_max_emission_kg_hr", value=round(max_rate, 1),
                value_unit="kg/hr", confidence=obs_conf, source_url=url),
        ]
        # one observation per plume (cap at 10 strongest; list is emissions_desc-sorted)
        for i, pl in enumerate(plumes[:10]):
            acq = pl["acq_date"]
            odt = datetime.fromisoformat(acq).replace(tzinfo=timezone.utc) if acq else None
            obs.append(ConnectorObservation(
                attribute=f"methane_plume[{i}]", value=pl,
                observation_date=odt,
                confidence=_QUALITY_CONF.get(pl["quality"], 0.8),
                source_url=f"https://api.carbonmapper.org/api/v1/catalog/plume/{pl['plume_id']}"))
        return self._ok(request, obs, raw=resp.text)


def requests_quote(s: str) -> str:
    from urllib.parse import quote
    return quote(s)
