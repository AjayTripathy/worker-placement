"""Bozeman MT building permits — best-effort connector.

Bozeman's permitting runs through OpenGov (https://bozeman.opengov.com/), which
is a SaaS platform with a JS-heavy SPA and no documented public REST API. To
make this fully programmatic we'd need to either:
  (a) reverse-engineer the OpenGov XHR endpoints used by the citizen portal
  (b) request an API key from OpenGov directly (paid)
  (c) scrape the rendered HTML via Playwright/Selenium (heavy)

For v1 this connector tries the OpenGov public projects API pattern (which
sometimes works for Citizen-facing workflows). When it doesn't, it returns
UNSUPPORTED with the portal URL so the operator can do a manual lookup.

Manual lookup URL:
  https://bozeman.opengov.com/PORTAL/PROJECT/permitting
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
    "summary": 'Bozeman MT permits (Laserfiche). Geographic: Bozeman/Gallatin County projects.',
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


PORTAL_URL = "https://bozeman.opengov.com/PORTAL/PROJECT/permitting"
# Tenant ID would need to be discovered via inspecting the portal's bootstrap JS.
OPENGOV_API = "https://bozeman.opengov.com/api/v1/projects/search"


class BozemanPermitsConnector(BaseConnector):
    source_id = "bozeman_permits"
    rate_limit_per_min = 20

    def query(self, request: ConnectorRequest) -> ConnectorResult:
        if not (request.entity_name or request.address):
            return self._fail(request, ErrorKind.UNSUPPORTED, "need entity_name or address")

        # Try the OpenGov projects search API (best-guess endpoint)
        q = request.entity_name or request.address
        url = f"{OPENGOV_API}?q={quote_plus(q)}&page=1&perPage=20"
        sess = self._session()
        sess.headers["User-Agent"] = "Mozilla/5.0 (compatible; SignalOS DD)"
        self._throttle()
        r, ek, ed = safe_get(sess, url)
        if r is None or r.status_code >= 400:
            return self._fail(
                request,
                ErrorKind.UNSUPPORTED,
                f"Bozeman OpenGov API not available ({ek}/{ed if ed else 'no response'}). "
                f"Manual lookup at {PORTAL_URL}",
            )
        try:
            data = r.json()
        except ValueError:
            return self._fail(
                request, ErrorKind.PARSE_FAIL,
                f"non-JSON response; OpenGov endpoint shape may have changed. Manual: {PORTAL_URL}",
                raw=r.text[:500],
            )

        projects = data.get("projects") or data.get("data") or []
        if not projects:
            return self._ok(request, [
                ConnectorObservation(attribute="bozeman_permit_count", value=0, source_url=PORTAL_URL),
            ], raw=r.text[:500])

        obs = [ConnectorObservation(attribute="bozeman_permit_count", value=len(projects), source_url=PORTAL_URL)]
        for i, p in enumerate(projects[:15]):
            obs.append(ConnectorObservation(
                attribute=f"bozeman_permit[{i}]",
                value={
                    "project_id": p.get("id") or p.get("projectId"),
                    "title": p.get("name") or p.get("title"),
                    "type": p.get("type"),
                    "status": p.get("status"),
                    "applicant": p.get("applicantName") or p.get("applicant"),
                    "address": p.get("address"),
                    "filed": p.get("createdAt") or p.get("submittedAt"),
                },
                source_url=PORTAL_URL,
            ))
        return self._ok(request, obs, raw=r.text[:1500])


if __name__ == "__main__":
    c = BozemanPermitsConnector()
    r = c.query(ConnectorRequest(entity_name="American Housing Corporation"))
    print(f"success={r.success} error={r.error_kind}/{r.error_detail}")
    for o in r.observations[:3]:
        print(f"  {o.attribute} = {o.value}")
