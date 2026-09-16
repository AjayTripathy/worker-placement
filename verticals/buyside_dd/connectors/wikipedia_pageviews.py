"""Wikipedia pageviews attention connector — daily pageviews of the company's article.

CONDITIONING LAYER (Attention sub-layer). No-edge control: how much public/research attention a
name draws, measured by daily views of its English-Wikipedia article. Clean, free, no auth — the
most reliable of the four attention sources.

Source: Wikimedia REST pageviews API,
  https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/all-agents/<title>/daily/<start>/<end>
Title resolution: en.wikipedia opensearch (action=opensearch) maps a company name -> canonical
article title. Many micro-caps have NO Wikipedia article at all — that is itself a strong
un-discovered signal, returned as success with views=0 and has_article=False (not an error).

What we extract (point-in-time honest):
  - recent_views_7d / recent_views_30d : pageview sums ending at asof
  - baseline_views_per_day             : median daily views over the trailing ~90d (the name's own history)
  - recent_vs_baseline                 : recent 7d-avg / baseline (>1 == elevated attention)
  - peak_day_views, has_article

Lag: ~1 day (Wikimedia publishes daily counts the next day). Inputs: entity_name = company name
(NOT ticker — Wikipedia indexes by company name). Optional extra={'wiki_title': ...} to override
title resolution, extra={'asof': 'YYYY-MM-DD'}.
"""

from __future__ import annotations

# Knowledge-graph dispatch contract (see knowledge_graph/dispatch.py) — added 2026-07-29 gap-close.
APPLIES_TO = {
    "kind": 'm_source',
    "sic_codes": [],
    "sic_prefixes": [],
    "issuer_features": [],
    "asset_classes": ['public_equity', 'corporate_ipo_dd'],
    "applies_universally": True,
    "summary": 'Wikipedia pageview attention read. Any public name with an article.',
}

import statistics
from datetime import datetime, timedelta, timezone
from urllib.parse import quote

from .base import BaseConnector, ConnectorObservation, ConnectorRequest, ConnectorResult, ErrorKind, safe_get

_OPENSEARCH = "https://en.wikipedia.org/w/api.php"
_PV = ("https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/"
       "en.wikipedia/all-access/all-agents/{title}/daily/{start}/{end}")
_UA = "SignalOS-BuysideDD/0.1 (conditioning-layer; research; +signalos)"


def _resolve_title(sess, name: str) -> str | None:
    params = {"action": "opensearch", "search": name, "limit": 1, "namespace": 0, "format": "json"}
    try:
        r = sess.get(_OPENSEARCH, params=params, timeout=15)
        if r.status_code != 200:
            return None
        data = r.json()
        # opensearch returns [query, [titles], [descs], [urls]]
        titles = data[1] if len(data) > 1 else []
        return titles[0] if titles else None
    except Exception:
        return None


class WikipediaPageviewsConnector(BaseConnector):
    source_id = "wikipedia_pageviews"
    rate_limit_per_min = 60
    user_agent = _UA

    def query(self, request: ConnectorRequest) -> ConnectorResult:
        name = (request.entity_name or "").strip()
        if not name:
            return self._fail(request, ErrorKind.UNSUPPORTED, "entity_name (company name) required")
        asof = request.extra.get("asof")
        try:
            end_dt = datetime.fromisoformat(str(asof)) if asof else datetime.now(timezone.utc)
        except ValueError:
            end_dt = datetime.now(timezone.utc)
        # Wikimedia counts lag ~1 day; back off the end so we don't query a not-yet-published day.
        end_dt = end_dt - timedelta(days=1)
        start_dt = end_dt - timedelta(days=90)

        sess = self._session()
        sess.headers["User-Agent"] = _UA

        title = request.extra.get("wiki_title") or _resolve_title(sess, name)
        if not title:
            return self._ok(request, [
                ConnectorObservation(attribute="has_article", value=False, source_url=_OPENSEARCH,
                                     extra={"note": "no en.wikipedia article = un-discovered signal"}),
                ConnectorObservation(attribute="recent_views_7d", value=0, source_url=_OPENSEARCH),
            ], raw="no title")

        url = _PV.format(title=quote(title.replace(" ", "_"), safe=""),
                         start=start_dt.strftime("%Y%m%d"), end=end_dt.strftime("%Y%m%d"))
        self._throttle()
        r, ek, ed = safe_get(sess, url, timeout=self.timeout_s)
        if r is None:
            if ek == ErrorKind.NOT_FOUND:
                # title resolved but no pageview series (very new / never-viewed article)
                return self._ok(request, [
                    ConnectorObservation(attribute="has_article", value=True, source_url=url),
                    ConnectorObservation(attribute="recent_views_7d", value=0, source_url=url,
                                         extra={"note": "article exists but no pageview data in window"}),
                    ConnectorObservation(attribute="wiki_title", value=title, source_url=url),
                ], raw="404 pv")
            return self._fail(request, ek, ed)
        try:
            items = r.json().get("items", [])
        except ValueError as e:
            return self._fail(request, ErrorKind.PARSE_FAIL, f"json: {e}", raw=r.text[:500])

        series = [(it["timestamp"][:8], it["views"]) for it in items]
        if not series:
            return self._ok(request, [
                ConnectorObservation(attribute="has_article", value=True, source_url=url),
                ConnectorObservation(attribute="recent_views_7d", value=0, source_url=url),
                ConnectorObservation(attribute="wiki_title", value=title, source_url=url),
            ], raw=r.text[:500])

        views = [v for _, v in series]
        recent_7 = sum(views[-7:])
        recent_30 = sum(views[-30:])
        baseline = statistics.median(views[:-7]) if len(views) > 7 else statistics.median(views)
        recent_avg = recent_7 / 7.0
        recent_vs_baseline = (recent_avg / baseline) if baseline > 0 else (None if recent_avg == 0 else float("inf"))
        peak = max(views)

        obs = [
            ConnectorObservation(attribute="has_article", value=True, source_url=url),
            ConnectorObservation(attribute="wiki_title", value=title, source_url=url),
            ConnectorObservation(attribute="recent_views_7d", value=recent_7, source_url=url),
            ConnectorObservation(attribute="recent_views_30d", value=recent_30, source_url=url),
            ConnectorObservation(attribute="baseline_views_per_day", value=round(baseline, 1), source_url=url,
                                 extra={"window": "trailing ~90d median"}),
            ConnectorObservation(attribute="recent_vs_baseline",
                                 value=round(recent_vs_baseline, 2) if recent_vs_baseline not in (None, float("inf")) else recent_vs_baseline,
                                 source_url=url, extra={"interpretation": ">1 = elevated vs own history"}),
            ConnectorObservation(attribute="peak_day_views", value=peak, source_url=url),
            ConnectorObservation(attribute="series_days", value=len(series), source_url=url),
        ]
        return self._ok(request, obs, raw=r.text[:2048])


if __name__ == "__main__":
    for name in ["Red Cat Holdings", "Destiny Tech100", "Tesla, Inc."]:
        res = WikipediaPageviewsConnector().query(ConnectorRequest(entity_name=name))
        d = {o.attribute: o.value for o in res.observations}
        print(f"{name}: success={res.success} has_article={d.get('has_article')} "
              f"7d={d.get('recent_views_7d')} base/day={d.get('baseline_views_per_day')} "
              f"vs_base={d.get('recent_vs_baseline')}")
