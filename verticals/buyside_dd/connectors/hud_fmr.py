"""HUD Fair Market Rent (FMR) connector.

Resolves market rent caps for Section 8 voucher payments. Used to flag any
sponsor claim of "Section 8 viability" where the proposed rent exceeds FMR.

API: https://www.huduser.gov/hudapi/public/fmr  (free, requires bearer token)
Token: register at https://www.huduser.gov/portal/dataset/fmr-api.html, then
       export HUD_API_TOKEN=<token>

Resolution strategy for a property:
  1. If request.geographic_area is a 5-digit zip → lookup small-area FMR by zip
  2. Else require state + (county or city) → lookup statelist → countylist → fmr
"""

from __future__ import annotations

# Knowledge-graph dispatch contract (see knowledge_graph/dispatch.py) — added 2026-07-29 gap-close.
APPLIES_TO = {
    "kind": 'm_source',
    "sic_codes": [],
    "sic_prefixes": ['65'],
    "issuer_features": ['residential_rental_business'],
    "asset_classes": ['corporate_ipo_dd', 'real_assets'],
    "applies_universally": False,
    "summary": 'HUD Fair Market Rent benchmark for residential rent claims.',
}

import os
from typing import Optional

from .base import (
    BaseConnector,
    ConnectorRequest,
    ConnectorResult,
    ConnectorObservation,
    ErrorKind,
    safe_get,
)


HUD_BASE = "https://www.huduser.gov/hudapi/public/fmr"


class HudFmrConnector(BaseConnector):
    source_id = "hud_fmr"
    rate_limit_per_min = 60

    def query(self, request: ConnectorRequest) -> ConnectorResult:
        token = os.getenv("HUD_API_TOKEN")
        if not token:
            return self._fail(
                request, ErrorKind.AUTH,
                "HUD_API_TOKEN env var not set; register at huduser.gov/portal/dataset/fmr-api.html",
            )

        year = request.year or 2024
        sess = self._session()
        sess.headers["Authorization"] = f"Bearer {token}"

        entity_id, kind, detail = self._resolve_entity(sess, request)
        if entity_id is None:
            return self._fail(request, kind or ErrorKind.UNSUPPORTED, detail or "could not resolve entity")

        self._throttle()
        url = f"{HUD_BASE}/data/{entity_id}?year={year}"
        r, err_kind, err_detail = safe_get(sess, url)
        if r is None:
            return self._fail(request, err_kind, err_detail)
        try:
            data = r.json()
        except ValueError as e:
            return self._fail(request, ErrorKind.PARSE_FAIL, f"json: {e}", raw=r.text)

        try:
            payload = data.get("data", {})
            basic = payload.get("basicdata") or [payload.get("basicdata")]
            if isinstance(basic, list) and basic and isinstance(basic[0], dict):
                row = basic[0]
            elif isinstance(basic, dict):
                row = basic
            else:
                row = payload
            obs = []
            for br in (0, 1, 2, 3, 4):
                key = f"Efficiency" if br == 0 else f"One-Bedroom" if br == 1 else f"Two-Bedroom" if br == 2 else f"Three-Bedroom" if br == 3 else f"Four-Bedroom"
                v = row.get(key)
                if v is not None:
                    obs.append(ConnectorObservation(
                        attribute=f"hud_fmr_{br}br",
                        value=float(v),
                        value_unit="USD/month",
                        source_url=url,
                    ))
            obs.append(ConnectorObservation(
                attribute="hud_fmr_entity_id",
                value=entity_id,
                source_url=url,
            ))
            obs.append(ConnectorObservation(
                attribute="hud_fmr_year",
                value=year,
                source_url=url,
            ))
            return self._ok(request, obs, raw=r.text)
        except (KeyError, TypeError, ValueError) as e:
            return self._fail(request, ErrorKind.PARSE_FAIL, f"shape: {e}", raw=r.text)

    def _resolve_entity(
        self,
        sess,
        request: ConnectorRequest,
    ) -> tuple[Optional[str], Optional[ErrorKind], Optional[str]]:
        """Translate (state, city/county) → HUD entity ID. Cached per process."""
        # Direct entity ID provided
        eid = request.extra.get("hud_entity_id") if request.extra else None
        if eid:
            return eid, None, None

        state = request.state or (request.extra.get("state") if request.extra else None)
        if not state:
            return None, ErrorKind.UNSUPPORTED, "need state (2-letter) and county/city"

        # Get county list for state
        self._throttle()
        url = f"{HUD_BASE}/listCounties/{state}"
        r, ek, ed = safe_get(sess, url)
        if r is None:
            return None, ek, ed
        try:
            counties = r.json()
        except ValueError as e:
            return None, ErrorKind.PARSE_FAIL, f"json: {e}"

        target_city = (request.city or "").lower()
        target_county = (request.extra.get("county", "") if request.extra else "").lower()

        for c in counties:
            town_name = (c.get("town_name") or "").lower()
            county_name = (c.get("county_name") or "").lower()
            if target_county and target_county in county_name:
                return c.get("fips_code") or c.get("entityid"), None, None
            if target_city and (target_city in town_name or target_city in county_name):
                return c.get("fips_code") or c.get("entityid"), None, None

        return None, ErrorKind.NOT_FOUND, f"no FMR area match for state={state} city={target_city} county={target_county}"


if __name__ == "__main__":
    # Smoke test: Lawton OK 3BR FMR. Validates connector against real API.
    c = HudFmrConnector()
    req = ConnectorRequest(state="OK", city="Lawton", year=2024)
    result = c.query(req)
    print(f"success={result.success} error={result.error_kind}/{result.error_detail}")
    for o in result.observations:
        print(f"  {o.attribute} = {o.value} {o.value_unit or ''}")
