"""Pennsylvania Bureau of Corporations and Charitable Organizations search.

KNOWN ISSUE (as of 2026-05): file.dos.pa.gov sits behind Cloudflare bot
detection. Plain `requests` returns 403 with the JS challenge page. This
connector currently fails fast with an AUTH error pointing to that fact.

To make this work we need one of:
  - Playwright/Selenium with stealth headers (chromium driver in env)
  - cloudscraper (third-party CF-bypass library)
  - Route via a residential proxy (paid)
  - Switch to OpenCorporates (paid for volume) for PA coverage

For now, treat `state_corp_pa` as a stub that signals to the dispatcher this
attribute is currently unverifiable from this environment, so the dispatcher
can fall back to a snippet-based search or skip with `verifiability=LOW`.

Endpoint when accessible: https://file.dos.pa.gov/api/Records/businesssearch
"""

from __future__ import annotations

# Knowledge-graph dispatch contract (see knowledge_graph/dispatch.py) — added 2026-07-29 gap-close.
APPLIES_TO = {
    "kind": 'm_source',
    "sic_codes": [],
    "sic_prefixes": [],
    "issuer_features": ['entity_registration_verification'],
    "asset_classes": ['corporate_ipo_dd'],
    "applies_universally": False,
    "summary": 'PA corporate/charity registry search for entity resolution. Geographic: PA entities.',
}

import json

from .base import (
    BaseConnector,
    ConnectorRequest,
    ConnectorResult,
    ConnectorObservation,
    ErrorKind,
    safe_get,
)


PA_HOME = "https://file.dos.pa.gov/search/business"
PA_API = "https://file.dos.pa.gov/api/Records/businesssearch"


class StateCorpPaConnector(BaseConnector):
    source_id = "state_corp_pa"
    rate_limit_per_min = 20

    def query(self, request: ConnectorRequest) -> ConnectorResult:
        if not request.entity_name:
            return self._fail(request, ErrorKind.UNSUPPORTED, "need entity_name")

        sess = self._session()
        sess.headers["Accept"] = "application/json, text/plain, */*"
        sess.headers["Accept-Language"] = "en-US,en;q=0.9"

        # Prime cookies
        self._throttle()
        r0, ek, ed = safe_get(sess, PA_HOME)
        if r0 is None:
            return self._fail(request, ek, ed)

        # POST search
        payload = {
            "SEARCH_VALUE": request.entity_name,
            "STARTS_WITH_YN": "false",
            "ACTIVE_ONLY_YN": False,
        }
        try:
            self._throttle()
            r = sess.post(PA_API, json=payload, timeout=20)
        except Exception as e:
            return self._fail(request, ErrorKind.NETWORK, f"post: {e}")
        if r.status_code >= 400:
            return self._fail(request, ErrorKind.UNKNOWN, f"http {r.status_code}: {r.text[:200]}")
        try:
            data = r.json()
        except ValueError as e:
            return self._fail(request, ErrorKind.PARSE_FAIL, f"json: {e}", raw=r.text)

        rows = data.get("rows") or data.get("Rows") or []
        if not rows:
            return self._ok(request, [
                ConnectorObservation(attribute="pa_corp_match_count", value=0, source_url=PA_API),
            ], raw=r.text)

        obs = [ConnectorObservation(attribute="pa_corp_match_count", value=len(rows), source_url=PA_API)]
        for i, row in enumerate(rows[:20]):
            obs.append(ConnectorObservation(
                attribute=f"pa_corp_match[{i}]",
                value={
                    "name": row.get("ENTITY_NAME") or row.get("EntityName") or row.get("Name"),
                    "entity_number": row.get("ENTITY_NUMBER") or row.get("EntityNumber"),
                    "status": row.get("STATUS") or row.get("Status"),
                    "type": row.get("ENTITY_TYPE") or row.get("EntityType"),
                    "formation_date": row.get("CREATION_DATE") or row.get("CreationDate"),
                    "registered_office": row.get("REG_OFFICE_ADDR") or row.get("RegisteredOffice"),
                },
                source_url=PA_API,
            ))
        return self._ok(request, obs, raw=r.text)


if __name__ == "__main__":
    c = StateCorpPaConnector()
    req = ConnectorRequest(entity_name="FCRE2 LLC")
    result = c.query(req)
    print(f"success={result.success} error={result.error_kind}/{result.error_detail}")
    for o in result.observations[:5]:
        print(f"  {o.attribute} = {o.value}")
