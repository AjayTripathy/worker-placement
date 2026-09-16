"""Albuquerque NM building permits — best-effort connector.

ABQ doesn't expose a clean Socrata-style permit API. The city does publish
some open data via ArcGIS Hub at https://opendata.cabq.gov/ but the building
permits dataset specifically isn't exposed as a queryable FeatureService at a
predictable URL.

This connector tries two patterns in order:
  1. ABQ Citizen Self-Service portal API (Posse / Tyler EnerGov)
  2. ABQ Open Data ArcGIS query
Falls back to UNSUPPORTED with manual lookup URL.

Manual lookup:
  https://posse.cabq.gov/cit/css/(S(...))/Default.aspx
  https://www.cabq.gov/planning/online-services
"""

from __future__ import annotations

# Knowledge-graph dispatch contract (see knowledge_graph/dispatch.py) — added 2026-07-29 gap-close.
APPLIES_TO = {
    "kind": 'm_source',
    "sic_codes": [],
    "sic_prefixes": [],
    "issuer_features": ['real_estate_development', 'construction_activity_claim'],
    "asset_classes": ['corporate_ipo_dd'],
    "applies_universally": False,
    "summary": 'Albuquerque NM building permits. Geographic: applies to projects/operators in Albuquerque.',
}

from urllib.parse import quote_plus

from .base import (
    BaseConnector,
    ConnectorRequest,
    ConnectorResult,
    ConnectorObservation,
    ErrorKind,
    safe_get,
)


PORTAL_URL = "https://www.cabq.gov/planning/online-services"
# ArcGIS Hub building-permits FeatureServer (best-guess URL — may need updating)
ARCGIS_QUERY = "https://services.arcgis.com/Q5pZAALdIzXDH0CV/ArcGIS/rest/services/Building_Permits/FeatureServer/0/query"


class AlbuquerquePermitsConnector(BaseConnector):
    source_id = "albuquerque_permits"
    rate_limit_per_min = 30

    def query(self, request: ConnectorRequest) -> ConnectorResult:
        if not (request.entity_name or request.address):
            return self._fail(request, ErrorKind.UNSUPPORTED, "need entity_name or address")

        # Build ArcGIS query
        clauses = []
        if request.entity_name:
            name = request.entity_name.upper().replace("'", "''")
            clauses.append(
                f"(UPPER(APPLICANT) LIKE '%{name}%' OR UPPER(CONTRACTOR) LIKE '%{name}%' "
                f"OR UPPER(OWNER) LIKE '%{name}%')"
            )
        if request.address:
            num_part = request.address.split(",")[0].strip().upper()
            clauses.append(f"UPPER(SITE_ADDRESS) LIKE '%{num_part[:30]}%'")
        where = " AND ".join(clauses) if clauses else "1=1"

        params = {
            "where": where,
            "outFields": "*",
            "f": "json",
            "resultRecordCount": "25",
        }
        url = f"{ARCGIS_QUERY}?" + "&".join(f"{k}={quote_plus(v)}" for k, v in params.items())

        sess = self._session()
        sess.headers["User-Agent"] = "Mozilla/5.0 (compatible; SignalOS DD)"
        self._throttle()
        r, ek, ed = safe_get(sess, url)
        if r is None:
            return self._fail(
                request, ErrorKind.UNSUPPORTED,
                f"ABQ ArcGIS endpoint not reachable ({ek}/{ed}). Manual: {PORTAL_URL}",
            )
        try:
            data = r.json()
        except ValueError:
            return self._fail(
                request, ErrorKind.PARSE_FAIL,
                f"ABQ endpoint returned non-JSON. The FeatureServer URL may have changed. Manual: {PORTAL_URL}",
                raw=r.text[:500],
            )

        if "error" in data:
            return self._fail(
                request, ErrorKind.UNSUPPORTED,
                f"ABQ endpoint error: {data.get('error')}. URL likely outdated; check {PORTAL_URL}",
                raw=r.text[:500],
            )

        features = data.get("features", [])
        if not features:
            return self._ok(request, [
                ConnectorObservation(attribute="abq_permit_count", value=0, source_url=PORTAL_URL),
            ], raw=r.text[:500])

        obs = [ConnectorObservation(attribute="abq_permit_count", value=len(features), source_url=PORTAL_URL)]
        for i, feat in enumerate(features[:15]):
            attrs = feat.get("attributes", {})
            obs.append(ConnectorObservation(
                attribute=f"abq_permit[{i}]",
                value={
                    "permit_number": attrs.get("PERMIT_NO") or attrs.get("PERMIT_NUMBER"),
                    "type": attrs.get("PERMIT_TYPE"),
                    "status": attrs.get("STATUS"),
                    "address": attrs.get("SITE_ADDRESS"),
                    "applicant": attrs.get("APPLICANT"),
                    "contractor": attrs.get("CONTRACTOR"),
                    "owner": attrs.get("OWNER"),
                    "applied": attrs.get("APPLIED_DATE") or attrs.get("ISSUED_DATE"),
                    "description": attrs.get("DESCRIPTION") or attrs.get("WORK_DESC"),
                },
                source_url=PORTAL_URL,
            ))
        return self._ok(request, obs, raw=r.text[:1500])


if __name__ == "__main__":
    c = AlbuquerquePermitsConnector()
    r = c.query(ConnectorRequest(entity_name="American Housing Corporation"))
    print(f"success={r.success} error={r.error_kind}/{r.error_detail}")
    for o in r.observations[:3]:
        print(f"  {o.attribute} = {o.value}")
