"""FEMA National Risk Index hazard-exposure connector — natural-hazard ground truth per location.

WHAT. Resolves any physical referent (address / lat-lon / census tract / county) to FEMA's
National Risk Index scores for up to 18 natural hazards (wildfire, earthquake, riverine and
coastal flood, drought, heat wave, hurricane, tornado, ...) at CENSUS-TRACT granularity, with
tract building-value exposure. Tier-2 authority (government derived/aggregate — FEMA's published
risk model, not a primary record).

WHY IT'S IN THE ATLAS. Decks and official statements routinely carry hazard-shaped claims with a
physical referent — "insurance costs are stable", "the collateral pool is in low-risk areas",
"natural-disaster exposure is minimal", "wildfire risk is managed" — that previously had NO
dispatchable source. NRI converts them into checkable numbers. It also feeds the
insurance-withdrawal channel: insurers' exits track exactly these hazard designations, and
withdrawal drags property marketability and assessed value YEARS before any loss event — a slow,
under-watched signal (see knowledge graph: insurance_withdrawal_value_drag).

VALIDATED 2026-06-10 building the CA muni sleeve's wildfire overlay: the sleeve's seismic
diversification had silently CONCENTRATED wildfire exposure (Mendocino USD 91% of building value
in high-fire tracts). Hazards are checked jointly, not one at a time.

ENDPOINTS (all free, no auth):
  - FCC Area API: lat/lon -> census block FIPS -> tract FIPS
  - Census geocoder (BaseConnector._geocode pattern): address -> lat/lon
  - FEMA NRI ArcGIS service (official FEMA_NationalRiskIndex org): per-tract hazard fields.
    NOTE: OpenFEMA does NOT carry NRI and the old hazards.fema.gov static download path is dead;
    the ArcGIS feature service is the live programmatic source.
"""

from __future__ import annotations

# Knowledge-graph dispatch contract (see knowledge_graph/dispatch.py) — added 2026-07-29 gap-close.
APPLIES_TO = {
    "kind": 'm_source',
    "sic_codes": [],
    "sic_prefixes": [],
    "issuer_features": ['physical_plant_operations', 'real_estate_collateral'],
    "asset_classes": ['corporate_ipo_dd', 'real_assets'],
    "applies_universally": False,
    "summary": 'FEMA NRI natural-hazard exposure for physical footprints/collateral.',
}
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import urlencode

from .base import BaseConnector, ConnectorObservation, ConnectorRequest, ConnectorResult, ErrorKind, safe_get

_NRI = ("https://services.arcgis.com/XG15cJAlne2vxtgt/arcgis/rest/services/"
        "National_Risk_Index_Census_Tracts/FeatureServer/0/query")
_FCC = "https://geo.fcc.gov/api/census/area?lat={lat}&lon={lon}&format=json"
_GEOCODER = ("https://geocoding.geo.census.gov/geocoder/locations/onelineaddress"
             "?address={addr}&benchmark=Public_AR_Current&format=json")

# NRI hazard prefixes (field stems): {stem}_RISKS score 0-100, {stem}_RISKR rating, {stem}_EALS EAL score
HAZARDS = {
    "wildfire": "WFIR", "earthquake": "ERQK", "riverine_flood": "RFLD", "coastal_flood": "CFLD",
    "drought": "DRGT", "heat_wave": "HWAV", "hurricane": "HRCN", "tornado": "TRND",
    "strong_wind": "SWND", "winter_weather": "WNTW", "ice_storm": "ISTM", "hail": "HAIL",
    "lightning": "LTNG", "landslide": "LNDS", "avalanche": "AVLN", "cold_wave": "CWAV",
    "tsunami": "TSUN", "volcanic_activity": "VLCN",
}
HIGH_RATINGS = {"Relatively High", "Very High"}


class FemaNriHazardConnector(BaseConnector):
    """Resolve a location to FEMA NRI natural-hazard risk scores at census-tract level."""

    source_id = "fema_nri_hazard"
    rate_limit_per_min = 30
    user_agent = "SignalOS-BuysideDD/0.1 (research; fema-nri-connector)"

    def _geocode(self, address: str) -> Optional[tuple[float, float]]:
        s = self._session()
        from .carbon_mapper import requests_quote
        resp, ek, ed = safe_get(s, _GEOCODER.format(addr=requests_quote(address)), timeout=self.timeout_s)
        if resp is None:
            return None
        try:
            m = resp.json().get("result", {}).get("addressMatches", [])
            if not m:
                return None
            c = m[0]["coordinates"]
            return float(c["y"]), float(c["x"])
        except (ValueError, KeyError, IndexError, TypeError):
            return None

    def _tract_for_point(self, lat: float, lon: float) -> Optional[str]:
        resp, ek, ed = safe_get(self._session(), _FCC.format(lat=lat, lon=lon), timeout=self.timeout_s)
        if resp is None:
            return None
        try:
            blocks = resp.json().get("results", [])
            return blocks[0]["block_fips"][:11] if blocks else None
        except (ValueError, KeyError, IndexError, TypeError):
            return None

    def _resolve_tract(self, request: ConnectorRequest) -> tuple[Optional[str], list[str]]:
        x = request.extra or {}
        notes = []
        if x.get("tract_fips"):
            return str(x["tract_fips"]).zfill(11), notes
        lat, lon = x.get("lat"), x.get("lon")
        if lat is None and request.address:
            geo = self._geocode(request.address)
            if geo:
                lat, lon = geo
                notes.append(f"geocoded '{request.address}' -> ({lat:.4f},{lon:.4f})")
        if lat is not None and lon is not None:
            t = self._tract_for_point(float(lat), float(lon))
            if t:
                notes.append(f"FCC point->tract {t}")
                return t, notes
            notes.append("FCC point->tract lookup failed")
        return None, notes

    def query(self, request: ConnectorRequest) -> ConnectorResult:
        x = request.extra or {}
        wanted = x.get("hazards") or ["wildfire"]
        stems = {h: HAZARDS[h] for h in wanted if h in HAZARDS}
        if not stems:
            return self._result(request, False, [], ErrorKind.UNSUPPORTED,
                                f"unknown hazards {wanted}; choose from {sorted(HAZARDS)}")
        tract, notes = self._resolve_tract(request)
        if not tract:
            return self._result(request, False, [], ErrorKind.UNSUPPORTED,
                                "; ".join(notes) or "need extra.tract_fips, extra.lat+lon, or a geocodable address")
        fields = ["TRACTFIPS", "COUNTY", "STATEABBRV", "BUILDVALUE", "RISK_SCORE", "RISK_RATNG"]
        for st in stems.values():
            fields += [f"{st}_RISKS", f"{st}_RISKR", f"{st}_EALS"]
        q = urlencode({"where": f"TRACTFIPS='{tract}'", "outFields": ",".join(fields),
                       "returnGeometry": "false", "f": "json"})
        resp, ek, ed = safe_get(self._session(), _NRI + "?" + q, timeout=self.timeout_s)
        if resp is None:
            return self._result(request, False, [], ek or ErrorKind.NETWORK, ed)
        try:
            feats = resp.json().get("features", [])
        except ValueError:
            return self._result(request, False, [], ErrorKind.PARSE, "non-JSON NRI response",
                                raw=resp.text[:2000])
        if not feats:
            return self._result(request, False, [], ErrorKind.NO_DATA, f"tract {tract} not in NRI")
        a = feats[0]["attributes"]
        now = datetime.now(timezone.utc)
        obs = []
        for hz, st in stems.items():
            rating = a.get(f"{st}_RISKR") or "No Rating"
            score = a.get(f"{st}_RISKS")
            if rating == "No Rating" or score is None:
                score = 0.0                       # FEMA semantics: no modeled exposure, not missing
            obs.append(ConnectorObservation(
                attribute=f"{hz}_risk_score", value=round(float(score), 1),
                value_unit="nri_score_0_100", observation_date=now, confidence=0.85, source_url=_NRI,
                extra={"rating": rating, "is_high": rating in HIGH_RATINGS,
                     "eal_score": a.get(f"{st}_EALS"), "tract": tract,
                     "county": a.get("COUNTY"), "state": a.get("STATEABBRV"),
                     "tract_building_value_usd": a.get("BUILDVALUE"),
                     "notes": "; ".join(notes)}))
        obs.append(ConnectorObservation(
            attribute="composite_natural_hazard_risk", value=a.get("RISK_SCORE"),
            value_unit="nri_score_0_100", observation_date=now, confidence=0.85, source_url=_NRI,
            extra={"rating": a.get("RISK_RATNG"), "tract": tract}))
        return self._result(request, True, obs, raw=str(a)[:2000])

    def _result(self, request, success, obs, ek=None, ed=None, raw=None) -> ConnectorResult:
        return ConnectorResult(source_id=self.source_id, request=request,
                               queried_at=datetime.now(timezone.utc), success=success,
                               observations=obs, error_kind=ek, error_detail=ed,
                               raw_response_snippet=raw)
