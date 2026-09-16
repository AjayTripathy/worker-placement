"""Texas Comptroller franchise tax entity search (free, JSON API).

Verifies TX-registered entities. Returns: legal name, taxpayer ID (11-digit
Comptroller# or 9-digit FEIN), mailing-address ZIP. The mailing ZIP is the
single most useful corroboration — sponsors often claim a HQ city in pitch
materials but their tax address tells a different story.

Endpoint discovered by reading the JS on https://mycpa.cpa.state.tx.us/coa/Index.html:
  apiUrl = "https://comptroller.texas.gov/data-search/franchise-tax";
  ajaxUrl = apiUrl + `?name=${encodeURIComponent(name)}`;

No auth, no rate limit documented (be polite — ~20/min).
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
    "summary": 'TX franchise-tax entity search for entity resolution. Geographic: TX entities.',
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


TX_API = "https://comptroller.texas.gov/data-search/franchise-tax"


class TxComptrollerCorpConnector(BaseConnector):
    source_id = "tx_comptroller_corp"
    rate_limit_per_min = 20

    def query(self, request: ConnectorRequest) -> ConnectorResult:
        name = request.entity_name
        taxpayer_id = (request.extra or {}).get("taxpayer_id")
        if not name and not taxpayer_id:
            return self._fail(request, ErrorKind.UNSUPPORTED, "need entity_name or extra.taxpayer_id")

        url = f"{TX_API}?{'taxpayerId=' + quote_plus(taxpayer_id) if taxpayer_id else 'name=' + quote_plus(name)}"
        sess = self._session()
        sess.headers["User-Agent"] = "Mozilla/5.0 (compatible; SignalOS DD)"
        self._throttle()
        r, ek, ed = safe_get(sess, url)
        if r is None:
            return self._fail(request, ek, ed)
        try:
            data = r.json()
        except ValueError as e:
            return self._fail(request, ErrorKind.PARSE_FAIL, f"json: {e}", raw=r.text[:500])

        if not data.get("success"):
            return self._fail(request, ErrorKind.PARSE_FAIL, f"api error: {data}", raw=r.text[:500])

        rows = data.get("data") or []
        obs = [ConnectorObservation(
            attribute="tx_corp_match_count",
            value=data.get("count", len(rows)),
            source_url=url,
        )]
        for i, row in enumerate(rows[:25]):
            obs.append(ConnectorObservation(
                attribute=f"tx_corp_match[{i}]",
                value={
                    "name": row.get("name"),
                    "taxpayer_id": row.get("taxpayerId"),
                    "mailing_zip": row.get("mailingAddressZip"),
                },
                source_url=url,
            ))
        return self._ok(request, obs, raw=r.text)


if __name__ == "__main__":
    c = TxComptrollerCorpConnector()
    r = c.query(ConnectorRequest(entity_name="American Housing Corporation"))
    print(f"success={r.success} error={r.error_kind}/{r.error_detail}")
    for o in r.observations[:5]:
        print(f"  {o.attribute} = {o.value}")
