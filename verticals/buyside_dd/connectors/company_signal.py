"""Lightweight company signal (Crunchbase substitute) via DDG snippet extraction.

Free triangulation source for: prior funding rounds, lead investors, founding
date, headcount range. Lower authority than SEC EDGAR but covers what EDGAR
doesn't (international rounds, secondary sales, news coverage of leadership).

Strategy: query DuckDuckGo Lite (no JS, no CF) with structured queries:
  - "{company} series A" / "{company} raised $"
  - "{company} crunchbase" / "{company} pitchbook"
  - "{company} site:linkedin.com/company"
Extract URLs + snippet text. Parse for funding amounts / dates / investor names
via regex.

Authority tier: 5 (snippet). Best used for corroboration when sec_edgar /
official sources are silent or partial.
"""

from __future__ import annotations

# Knowledge-graph dispatch contract (see knowledge_graph/dispatch.py) — added 2026-07-29 gap-close.
APPLIES_TO = {
    "kind": 'helper',
    "sic_codes": [],
    "sic_prefixes": [],
    "issuer_features": [],
    "asset_classes": ['corporate_ipo_dd'],
    "applies_universally": False,
    "summary": 'DDG-snippet company lookup plumbing (Crunchbase substitute) used by other connectors.',
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


DDG_LITE = "https://lite.duckduckgo.com/lite/"

# Regex to spot $X[M|K|B] amounts in snippets
DOLLAR_AMT = re.compile(r"\$([\d,.]+)\s*(million|billion|M|B|k|K)?", re.IGNORECASE)
ROUND_LABEL = re.compile(r"\b(seed|pre-seed|series\s+[a-z]|growth|crossover|ipo)\b", re.IGNORECASE)


class CompanySignalConnector(BaseConnector):
    source_id = "company_signal"
    rate_limit_per_min = 15

    def query(self, request: ConnectorRequest) -> ConnectorResult:
        if not request.entity_name:
            return self._fail(request, ErrorKind.UNSUPPORTED, "need entity_name")

        target = request.entity_name
        # Run 3 queries to triangulate
        queries = [
            f'"{target}" series funding round',
            f'"{target}" crunchbase',
            f'"{target}" raised million',
        ]
        all_snippets: list[dict] = []
        for q in queries:
            self._throttle()
            sess = self._session()
            sess.headers["User-Agent"] = "Mozilla/5.0 (compatible; SignalOS/0.1)"
            sess.headers["Accept"] = "text/html"
            try:
                r = sess.post(DDG_LITE, data={"q": q}, timeout=20)
            except Exception as e:
                continue
            if r.status_code >= 400:
                continue
            snippets = self._extract_snippets(r.text)
            for s in snippets:
                s["query"] = q
            all_snippets.extend(snippets)

        if not all_snippets:
            return self._fail(request, ErrorKind.NOT_FOUND, "no snippets returned for any query")

        # Aggregate signals
        funding_mentions = []
        round_mentions = []
        investor_mentions = set()
        urls_seen = set()

        for s in all_snippets:
            url = s.get("url", "")
            if url in urls_seen:
                continue
            urls_seen.add(url)
            text = s.get("text", "")
            for m in DOLLAR_AMT.finditer(text):
                amount, unit = m.group(1), (m.group(2) or "")
                funding_mentions.append({"raw": m.group(0), "url": url, "context": text[max(0,m.start()-40):m.end()+80]})
            for m in ROUND_LABEL.finditer(text):
                round_mentions.append({"label": m.group(0), "url": url})
            # Heuristic: capitalized words near "led by" or "from"
            for inv_match in re.finditer(r"(?:led by|from|investors?:?)\s+([A-Z][\w&\s,]+?)(?:\.|,|;)", text):
                investor_mentions.add(inv_match.group(1).strip())

        obs = []
        obs.append(ConnectorObservation(
            attribute="company_signal_url_count",
            value=len(urls_seen),
            source_url=DDG_LITE,
        ))
        obs.append(ConnectorObservation(
            attribute="company_signal_funding_mentions",
            value=funding_mentions[:10],
            source_url=DDG_LITE,
        ))
        obs.append(ConnectorObservation(
            attribute="company_signal_round_labels",
            value=list({r["label"].lower() for r in round_mentions}),
            source_url=DDG_LITE,
        ))
        obs.append(ConnectorObservation(
            attribute="company_signal_possible_investors",
            value=sorted(investor_mentions)[:15],
            source_url=DDG_LITE,
        ))
        obs.append(ConnectorObservation(
            attribute="company_signal_top_urls",
            value=list(urls_seen)[:8],
            source_url=DDG_LITE,
        ))
        return self._ok(request, obs)

    def _extract_snippets(self, html: str) -> list[dict]:
        """Parse DDG lite HTML — simple table format."""
        # DDG lite results are in <a class="result-link">title</a> followed by
        # a snippet td. We match link-snippet pairs liberally.
        results = []
        # Pattern for the result row: <a class="result-link" href="URL">TITLE</a> ... snippet text
        for m in re.finditer(
            r'<a[^>]*class="result-link"[^>]*href="([^"]+)"[^>]*>([^<]+)</a>'
            r'.*?<td[^>]*class="result-snippet"[^>]*>(.*?)</td>',
            html, re.DOTALL | re.IGNORECASE,
        ):
            url = m.group(1)
            title = re.sub(r"\s+", " ", m.group(2)).strip()
            snippet = re.sub(r"<[^>]+>", " ", m.group(3))
            snippet = re.sub(r"\s+", " ", snippet).strip()
            results.append({"url": url, "title": title, "text": f"{title}. {snippet}"})
        if not results:
            # Fallback: any link with text content as a degraded result
            for m in re.finditer(r'<a[^>]*href="(https?://[^"]+)"[^>]*>([^<]+)</a>', html):
                results.append({"url": m.group(1), "title": m.group(2).strip(), "text": m.group(2).strip()})
                if len(results) >= 10:
                    break
        return results


if __name__ == "__main__":
    c = CompanySignalConnector()
    r = c.query(ConnectorRequest(entity_name="American Housing Corporation"))
    print(f"success={r.success} error={r.error_kind}/{r.error_detail}")
    for o in r.observations[:8]:
        v = o.value
        if isinstance(v, list) and len(v) > 3:
            print(f"  {o.attribute} = (n={len(v)}) {v[:3]} ...")
        else:
            print(f"  {o.attribute} = {v}")
