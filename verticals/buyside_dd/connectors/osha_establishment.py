"""OSHA Establishment Search — verify a manufacturing facility exists.

Used to corroborate "we have a factory at X" claims. OSHA inspects workplaces;
an establishment with no inspection history doesn't disprove existence (small/
new facilities may not yet appear), but a hit is positive confirmation.

Endpoint: https://www.osha.gov/pls/imis/establishment.search
This is an HTML form, not a JSON API. We scrape it.

Alternative (bulk): DOL Enforcement Data has CSV downloads with all OSHA
inspections — better for batch but heavier setup.
"""

from __future__ import annotations

# Knowledge-graph dispatch contract (see knowledge_graph/dispatch.py) — added 2026-07-29 gap-close.
APPLIES_TO = {
    "kind": 'm_source',
    "sic_codes": [],
    "sic_prefixes": ['2', '3'],
    "issuer_features": ['physical_plant_operations', 'manufacturing_facility_claim'],
    "asset_classes": ['corporate_ipo_dd'],
    "applies_universally": False,
    "summary": 'OSHA establishment search: does the claimed factory exist as an inspected workplace.',
}

import re
from urllib.parse import urlencode

from .base import (
    BaseConnector,
    ConnectorRequest,
    ConnectorResult,
    ConnectorObservation,
    ErrorKind,
    safe_get,
)


OSHA_SEARCH = "https://www.osha.gov/pls/imis/establishment.search"


class OshaEstablishmentConnector(BaseConnector):
    source_id = "osha_establishment"
    rate_limit_per_min = 20
    timeout_s = 60.0  # OSHA establishment search is slow

    def query(self, request: ConnectorRequest) -> ConnectorResult:
        if not request.entity_name:
            return self._fail(request, ErrorKind.UNSUPPORTED, "need entity_name")

        params = {
            "establishment": request.entity_name,
            "State": (request.state or "All"),
            "officetype": "All",
            "Office": "All",
            "endDate": "",
            "startDate": "",
            "sic": "",
            "naics": "",
            "p_finduse": "establishment",
        }
        url = f"{OSHA_SEARCH}?{urlencode(params)}"
        sess = self._session()
        sess.headers["Accept"] = "text/html,application/xhtml+xml"
        sess.headers["User-Agent"] = "Mozilla/5.0 (compatible; SignalOS DD)"
        self._throttle()
        r, ek, ed = safe_get(sess, url, timeout=self.timeout_s)
        if r is None:
            return self._fail(request, ek, ed)

        html = r.text
        # OSHA result page: each establishment row contains a link to /pls/imis/establishment.inspection_detail?id=...
        # plus the establishment name and address in a table.
        rows = re.findall(
            r'<tr[^>]*>\s*<td[^>]*>\s*<a[^>]*href="([^"]+)"[^>]*>([^<]+)</a>\s*</td>\s*<td[^>]*>([^<]+)</td>\s*<td[^>]*>([^<]+)</td>\s*<td[^>]*>([^<]+)</td>',
            html, re.IGNORECASE,
        )
        obs = [ConnectorObservation(attribute="osha_establishment_count", value=len(rows), source_url=url)]
        for i, (link, name, addr, city, state) in enumerate(rows[:20]):
            obs.append(ConnectorObservation(
                attribute=f"osha_match[{i}]",
                value={
                    "name": name.strip(),
                    "address": addr.strip(),
                    "city": city.strip(),
                    "state": state.strip(),
                    "detail_url": "https://www.osha.gov" + link if link.startswith("/") else link,
                },
                source_url=url,
            ))
        # Detect "no results" page so we don't false-negative parse failures
        if not rows and "did not return any" in html.lower():
            return self._ok(request, [
                ConnectorObservation(attribute="osha_establishment_count", value=0, source_url=url),
            ], raw=html[:500])
        if not rows:
            # Could be parse failure or different layout; return what we have but flag
            return self._fail(request, ErrorKind.PARSE_FAIL,
                              "no rows matched; layout may have changed", raw=html[:1000])
        return self._ok(request, obs, raw=html[:2000])


if __name__ == "__main__":
    c = OshaEstablishmentConnector()
    r = c.query(ConnectorRequest(entity_name="American Housing Corporation", state="TX"))
    print(f"success={r.success} error={r.error_kind}/{r.error_detail}")
    for o in r.observations[:5]:
        print(f"  {o.attribute} = {o.value}")
