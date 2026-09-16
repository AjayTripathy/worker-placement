"""USPTO patent search via PatentsView API.

Used for verifying inventor / IP claims (e.g. "Founder X invented Building System Y").

API: https://search.patentsview.org/api/v1/  (free; rate-limited)
Some PatentsView endpoints now require an API key. We pass it via env var
PATENTSVIEW_API_KEY when present; without one we fall back to anonymous which
works for low-volume queries.

Fallback: if PatentsView fails, scrape Google Patents (https://patents.google.com)
which has the same data without auth.
"""

from __future__ import annotations

# Knowledge-graph dispatch contract (see knowledge_graph/dispatch.py) — added 2026-07-29 gap-close.
APPLIES_TO = {
    "kind": 'm_source',
    "sic_codes": [],
    "sic_prefixes": [],
    "issuer_features": ['patent_portfolio_material', 'ip_licensing_business'],
    "asset_classes": ['corporate_ipo_dd'],
    "applies_universally": True,
    "summary": 'PatentsView patent search incl founder/inventor resolution. Universal-cheap; decisive on IP-heavy claims.',
}

import json
import os
from urllib.parse import quote_plus

from .base import (
    BaseConnector,
    ConnectorRequest,
    ConnectorResult,
    ConnectorObservation,
    ErrorKind,
    safe_get,
)


PATENTSVIEW_BASE = "https://search.patentsview.org/api/v1/patent"
GOOGLE_PATENTS = "https://patents.google.com/xhr/query"


class UsptoPatentsConnector(BaseConnector):
    source_id = "uspto_patents"
    rate_limit_per_min = 30

    def query(self, request: ConnectorRequest) -> ConnectorResult:
        target = request.person_name or request.entity_name
        if not target:
            return self._fail(request, ErrorKind.UNSUPPORTED, "need person_name (inventor) or entity_name (assignee)")

        # Try PatentsView first
        result = self._query_patentsview(request, target)
        if result.success:
            return result
        # Fall back to Google Patents
        return self._query_google_patents(request, target)

    def _query_patentsview(self, request: ConnectorRequest, target: str) -> ConnectorResult:
        key = os.getenv("PATENTSVIEW_API_KEY")
        if not key:
            # Without key, PatentsView returns empty body. Skip cleanly to fallback.
            return self._fail(request, ErrorKind.AUTH, "PATENTSVIEW_API_KEY not set; skipping primary path")

        # Split target into name parts if person; treat as assignee org if entity
        if request.person_name:
            parts = target.split()
            first = parts[0] if parts else ""
            last = parts[-1] if len(parts) > 1 else ""
            q = {"_and": [
                {"_text_phrase": {"inventors.inventor_name_first": first}} if first else {},
                {"_text_phrase": {"inventors.inventor_name_last": last}} if last else {},
            ]}
            q["_and"] = [c for c in q["_and"] if c]
        else:
            q = {"_text_phrase": {"assignees.assignee_organization": target}}

        fields = ["patent_id", "patent_title", "patent_date",
                  "inventors.inventor_name_first", "inventors.inventor_name_last",
                  "assignees.assignee_organization"]
        url = f"{PATENTSVIEW_BASE}?q={quote_plus(json.dumps(q))}&f={quote_plus(json.dumps(fields))}&o={quote_plus(json.dumps({'size': 25}))}"

        sess = self._session()
        sess.headers["X-Api-Key"] = key
        self._throttle()
        r, ek, ed = safe_get(sess, url)
        if r is None:
            return self._fail(request, ek, ed)
        try:
            data = r.json()
        except ValueError as e:
            return self._fail(request, ErrorKind.PARSE_FAIL, f"json: {e}", raw=r.text)

        patents = data.get("patents") or data.get("data", {}).get("patents", [])
        if not patents:
            return self._ok(request, [
                ConnectorObservation(attribute="patent_count", value=0, source_url=url),
            ], raw=r.text)

        obs = [ConnectorObservation(attribute="patent_count", value=len(patents), source_url=url)]
        for i, p in enumerate(patents[:10]):
            obs.append(ConnectorObservation(
                attribute=f"patent[{i}]",
                value={
                    "patent_id": p.get("patent_id"),
                    "title": p.get("patent_title"),
                    "date": p.get("patent_date"),
                    "inventors": [
                        f"{inv.get('inventor_name_first','')} {inv.get('inventor_name_last','')}".strip()
                        for inv in (p.get("inventors") or [])
                    ],
                    "assignees": [a.get("assignee_organization") for a in (p.get("assignees") or [])],
                },
                source_url=url,
            ))
        return self._ok(request, obs, raw=r.text)

    def _query_google_patents(self, request: ConnectorRequest, target: str) -> ConnectorResult:
        # Google Patents XHR endpoint expects URL-encoded query in 'url' param.
        # Format: url=inventor%3DName%2Bassignee%3DOrg
        if request.person_name:
            inner = f"inventor={quote_plus(target)}"
        else:
            inner = f"assignee={quote_plus(target)}"
        url = f"{GOOGLE_PATENTS}?url={quote_plus(inner)}&exp="
        sess = self._session()
        sess.headers["User-Agent"] = "Mozilla/5.0 (compatible; SignalOS/0.1)"
        self._throttle()
        r, ek, ed = safe_get(sess, url)
        if r is None:
            return self._fail(request, ek, f"google_patents fallback also failed: {ed}")

        # Detect Google's bot-detection / throttle page (HTML "Sorry..." response with 200 status)
        if r.text.lstrip().startswith("<html") or "<title>Sorry" in r.text[:500]:
            return self._fail(
                request,
                ErrorKind.RATE_LIMIT,
                "Google Patents throttled this IP. Set PATENTSVIEW_API_KEY (free at patentsview.org/apis/keyrequest.html) to use the primary path, or retry from a different IP.",
                raw=r.text[:500],
            )
        try:
            data = r.json()
        except ValueError:
            return self._fail(request, ErrorKind.PARSE_FAIL, "google_patents non-json", raw=r.text[:500])

        results_block = data.get("results", {})
        total = results_block.get("total_num_results", 0)
        clusters = results_block.get("cluster") or [{}]
        # First cluster has the actual results
        cluster_results = []
        for cluster in clusters:
            cluster_results.extend(cluster.get("result", []))
        if not cluster_results:
            return self._ok(request, [
                ConnectorObservation(attribute="patent_count", value=total, source_url=url),
            ], raw=r.text[:1000])

        obs = [ConnectorObservation(attribute="patent_count", value=total, source_url=url)]
        for i, hit in enumerate(cluster_results[:15]):
            p = hit.get("patent", {})
            obs.append(ConnectorObservation(
                attribute=f"patent[{i}]",
                value={
                    "patent_id": p.get("publication_number") or hit.get("id"),
                    "title": p.get("title"),
                    "snippet": p.get("snippet"),
                    "filing_date": p.get("filing_date"),
                    "grant_date": p.get("grant_date"),
                    "priority_date": p.get("priority_date"),
                    "assignee": p.get("assignee"),
                    "inventor": p.get("inventor"),
                },
                source_url=url,
            ))
        return self._ok(request, obs, raw=r.text[:2000])


if __name__ == "__main__":
    c = UsptoPatentsConnector()
    # Smoke: search for inventor 'Will Davis' (one of the AHC founders)
    r = c.query(ConnectorRequest(person_name="Will Davis"))
    print(f"success={r.success} error={r.error_kind}/{r.error_detail}")
    for o in r.observations[:5]:
        print(f"  {o.attribute} = {o.value}")
