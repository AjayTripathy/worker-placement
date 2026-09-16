"""Google Trends attention connector — search interest for a company name.

CONDITIONING LAYER (Attention sub-layer). No-edge control: retail search interest is a leading
attention signal (people Google a name before/while they pile in). Conceptually the strongest
retail-attention source — but operationally the WEAKEST because Google Trends has no official API.

REALITY CHECK (disclosed, NOT corrected): the unofficial Trends endpoints (`/trends/api/explore`
+ `/trends/api/widgetdata/multiline`) hard-429 datacenter / cloud IPs almost immediately, and the
common `pytrends` wrapper hits the same wall. This connector implements the real 2-step token flow
(explore -> widget token -> multiline) with backoff, but on a research/cloud IP it will usually
return RATE_LIMIT and the aggregator must degrade this component to UNAVAILABLE — never fabricate a
search-interest number. It works opportunistically from a residential IP / with a proxy.

What it extracts when it DOES work (point-in-time honest):
  - recent_interest_7d : mean of the last 7 interest points (0-100 Google-relative scale)
  - baseline_interest  : mean of the earlier window (own history)
  - interest_vs_baseline, peak_interest

Lag: ~1 day. Inputs: entity_name = search term (company name). extra={'geo': 'US', 'timeframe': 'today 3-m'}.
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
    "summary": 'Search-interest attention read. Any public name.',
}

import json
import time

from .base import BaseConnector, ConnectorObservation, ConnectorRequest, ConnectorResult, ErrorKind

_EXPLORE = "https://trends.google.com/trends/api/explore"
_MULTILINE = "https://trends.google.com/trends/api/widgetdata/multiline"
_UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
# Google's XSSI guard prefix. NB (bug fixed 2026-08-15): explore returns ")]}'\n" but multiline
# returns ")]}',\n" — a char-set lstrip that omits the COMMA stops there and every multiline parse
# fell through to PARSE_FAIL. Keep the comma in the strip set.
_XSSI = ")]}',\n "


def _dejson(text: str):
    return json.loads(text.lstrip(_XSSI))


class GoogleTrendsConnector(BaseConnector):
    source_id = "google_trends"
    rate_limit_per_min = 6
    user_agent = _UA
    _backoff_s = 4.0
    _max_retries = 2

    # ── shared series fetch (reused by consumer_product_heat — do NOT fork this flow) ──
    def fetch_series(self, term: str, geo: str = "US",
                     timeframe: str = "today 3-m") -> dict:
        """The 2-step token flow -> the RAW weekly/daily interest series.

        Returns {"status": "OK"|"RATE_LIMIT"|"PARSE_FAIL"|"NETWORK"|"EMPTY",
                 "points": [{"date": "Aug 10, 2025", "ts": 1754784000, "value": 32}, ...],
                 "term", "geo", "timeframe", "note"}.
        NEVER fabricates a number: a blocked fetch returns status != OK and points == [].
        """
        term = (term or "").strip()
        if not term:
            return {"status": "UNSUPPORTED", "points": [], "note": "empty term"}
        sess = self._session()
        sess.headers.update({"User-Agent": _UA, "Accept-Language": "en-US,en;q=0.9",
                             "Referer": "https://trends.google.com/trends/explore"})
        try:
            sess.get("https://trends.google.com/?geo=US", timeout=15)  # NID cookie
        except Exception:
            pass
        explore_req = {"comparisonItem": [{"keyword": term, "geo": geo, "time": timeframe}],
                       "category": 0, "property": ""}
        widget, note = None, ""
        for attempt in range(self._max_retries):
            self._throttle()
            try:
                r = sess.get(_EXPLORE, params={"hl": "en-US", "tz": "240",
                                               "req": json.dumps(explore_req)}, timeout=self.timeout_s)
            except Exception as e:
                note = f"network: {e}"
                time.sleep(self._backoff_s)
                continue
            if r.status_code == 429:
                note = "explore 429 (datacenter-IP block / rate budget spent)"
                time.sleep(self._backoff_s * (attempt + 1))
                continue
            if r.status_code >= 400:
                return {"status": "NETWORK", "points": [], "note": f"explore http {r.status_code}"}
            try:
                meta = _dejson(r.text)
            except ValueError:
                note = "explore non-json (interstitial block page)"
                time.sleep(self._backoff_s)
                continue
            widget = next((w for w in meta.get("widgets", []) if w.get("id") == "TIMESERIES"), None)
            break
        if widget is None:
            return {"status": "RATE_LIMIT", "points": [], "term": term,
                    "note": note or "no TIMESERIES widget (blocked)"}
        self._throttle()
        try:
            r2 = sess.get(_MULTILINE, params={"hl": "en-US", "tz": "240",
                                              "req": json.dumps(widget["request"]),
                                              "token": widget["token"]}, timeout=self.timeout_s)
        except Exception as e:
            return {"status": "NETWORK", "points": [], "term": term, "note": f"multiline: {e}"}
        if r2.status_code == 429:
            return {"status": "RATE_LIMIT", "points": [], "term": term, "note": "multiline 429"}
        try:
            series = _dejson(r2.text).get("default", {}).get("timelineData", [])
        except ValueError:
            return {"status": "PARSE_FAIL", "points": [], "term": term, "note": "multiline non-json"}
        pts = [{"ts": int(p.get("time", 0)), "date": p.get("formattedAxisTime"),
                "value": (p.get("value") or [0])[0]} for p in series]
        return {"status": "OK" if pts else "EMPTY", "points": pts, "term": term,
                "geo": geo, "timeframe": timeframe, "source": "google_trends_widget_json"}

    def query(self, request: ConnectorRequest) -> ConnectorResult:
        term = (request.entity_name or "").strip()
        if not term:
            return self._fail(request, ErrorKind.UNSUPPORTED, "entity_name (search term) required")
        geo = request.extra.get("geo", "US")
        timeframe = request.extra.get("timeframe", "today 3-m")

        sess = self._session()
        sess.headers.update({"User-Agent": _UA, "Accept-Language": "en-US,en;q=0.9",
                             "Referer": "https://trends.google.com/trends/explore"})
        # Step 0: get the NID cookie Google requires.
        try:
            sess.get("https://trends.google.com/?geo=US", timeout=15)
        except Exception:
            pass

        explore_req = {"comparisonItem": [{"keyword": term, "geo": geo, "time": timeframe}],
                       "category": 0, "property": ""}
        widget = None
        for attempt in range(self._max_retries):
            self._throttle()
            try:
                r = sess.get(_EXPLORE, params={"hl": "en-US", "tz": "240",
                                               "req": json.dumps(explore_req)}, timeout=self.timeout_s)
            except Exception as e:
                time.sleep(self._backoff_s)
                last = f"network: {e}"
                continue
            if r.status_code == 429:
                last = "Google Trends 429 (datacenter IP hard-block)"
                time.sleep(self._backoff_s * (attempt + 1))
                continue
            if r.status_code >= 400:
                return self._fail(request, ErrorKind.UNKNOWN, f"explore http {r.status_code}")
            # Response is JSON prefixed with ")]}',\n"
            try:
                meta = _dejson(r.text)
            except ValueError:
                last = "explore non-json (likely an interstitial block page)"
                time.sleep(self._backoff_s)
                continue
            for w in meta.get("widgets", []):
                if w.get("id") == "TIMESERIES":
                    widget = w
                    break
            break
        else:
            return self._fail(request, ErrorKind.RATE_LIMIT,
                              "Google Trends explore blocked after retries (expected on cloud IP); component UNAVAILABLE")

        if widget is None:
            return self._fail(request, ErrorKind.RATE_LIMIT,
                              "Google Trends did not return a TIMESERIES widget (rate-limited / blocked); component UNAVAILABLE")

        # Step 2: fetch the multiline series with the widget token.
        self._throttle()
        try:
            r2 = sess.get(_MULTILINE, params={"hl": "en-US", "tz": "240",
                                              "req": json.dumps(widget["request"]),
                                              "token": widget["token"]}, timeout=self.timeout_s)
        except Exception as e:
            return self._fail(request, ErrorKind.NETWORK, f"multiline: {e}")
        if r2.status_code == 429:
            return self._fail(request, ErrorKind.RATE_LIMIT, "Google Trends multiline 429; component UNAVAILABLE")
        try:
            series = _dejson(r2.text).get("default", {}).get("timelineData", [])
        except ValueError:
            return self._fail(request, ErrorKind.PARSE_FAIL, "multiline non-json", raw=r2.text[:300])

        vals = [pt.get("value", [0])[0] for pt in series]
        if not vals:
            return self._ok(request, [
                ConnectorObservation(attribute="recent_interest_7d", value=0, source_url=_MULTILINE,
                                     extra={"note": "no search interest series"}),
            ], raw=r2.text[:300])

        recent = vals[-7:]
        base_window = vals[:-7] if len(vals) > 7 else vals
        recent_avg = sum(recent) / len(recent)
        baseline = (sum(base_window) / len(base_window)) if base_window else 0.0
        vs_base = (recent_avg / baseline) if baseline > 0 else (None if recent_avg == 0 else float("inf"))

        obs = [
            ConnectorObservation(attribute="recent_interest_7d", value=round(recent_avg, 1), source_url=_MULTILINE,
                                 extra={"scale": "0-100 Google-relative"}),
            ConnectorObservation(attribute="baseline_interest", value=round(baseline, 1), source_url=_MULTILINE),
            ConnectorObservation(attribute="interest_vs_baseline",
                                 value=round(vs_base, 2) if vs_base not in (None, float("inf")) else vs_base,
                                 source_url=_MULTILINE),
            ConnectorObservation(attribute="peak_interest", value=max(vals), source_url=_MULTILINE),
            ConnectorObservation(attribute="n_points", value=len(vals), source_url=_MULTILINE),
        ]
        return self._ok(request, obs, raw=r2.text[:2048])


if __name__ == "__main__":
    res = GoogleTrendsConnector().query(ConnectorRequest(entity_name="Red Cat Holdings"))
    print(f"success={res.success} err={res.error_kind} detail={res.error_detail}")
    for o in res.observations:
        print(f"  {o.attribute} = {o.value}")
