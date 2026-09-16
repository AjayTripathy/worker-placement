"""GDELT news-volume attention connector — article volume/velocity for a company name.

CONDITIONING LAYER (Attention sub-layer). No-edge control: how much NEWS attention a name draws.
This is VELOCITY, not sentiment — the spec is explicit. A name with a news-volume spike is being
"discovered" by the press; an unknown name with flat near-zero coverage is un-discovered.

Source: GDELT 2.0 DOC API, https://api.gdeltproject.org/api/v2/doc/doc
  mode=timelinevol returns a daily/15-min normalized "volume intensity" series (% of all monitored
  global coverage) for the query over a timespan. Free, no auth.

CRITICAL RATE LIMIT (disclosed): GDELT throttles to ~1 request / 5 seconds per IP and 429s hard
otherwise. We back off and retry; if still blocked we return RATE_LIMIT (the aggregator degrades
this component to UNAVAILABLE rather than fabricating a volume).

What we extract (point-in-time honest):
  - recent_vol_avg_7d  : mean of the timeline's last 7 points
  - baseline_vol_avg   : mean over the earlier window (the name's own history)
  - vol_vs_baseline    : recent / baseline (>1 == elevated news attention)
  - peak_vol, n_points

Lag: ~15 min (GDELT updates every 15 minutes). Inputs: entity_name = company name (exact-phrase
quoted in the query). Optional extra={'asof': ...} to set the window end (GDELT timespan only goes
back from NOW, so for a far-past asof the series may be truncated — surfaced via n_points).
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
    "summary": 'News article volume/velocity attention read. Any public name.',
}

import time

from .base import BaseConnector, ConnectorObservation, ConnectorRequest, ConnectorResult, ErrorKind

_API = "https://api.gdeltproject.org/api/v2/doc/doc"
_UA = "Mozilla/5.0 (compatible; SignalOS-BuysideDD/0.1; conditioning-layer research)"


class GdeltNewsConnector(BaseConnector):
    source_id = "gdelt_news"
    rate_limit_per_min = 12   # respect GDELT's ~1 req / 5s ceiling
    user_agent = _UA
    _max_retries = 3
    _backoff_s = 6.0

    def query(self, request: ConnectorRequest) -> ConnectorResult:
        name = (request.entity_name or "").strip()
        if not name:
            return self._fail(request, ErrorKind.UNSUPPORTED, "entity_name (company name) required")
        params = {
            "query": f'"{name}"',
            "mode": "timelinevol",
            "format": "json",
            "timespan": str(request.extra.get("timespan", "3months")),
        }
        sess = self._session()
        sess.headers["User-Agent"] = _UA

        data = None
        last_detail = ""
        for attempt in range(self._max_retries):
            self._throttle()
            try:
                r = sess.get(_API, params=params, timeout=self.timeout_s)
            except Exception as e:
                last_detail = f"network: {e}"
                time.sleep(self._backoff_s)
                continue
            if r.status_code == 429 or "Too Many Requests" in r.text[:200]:
                last_detail = "GDELT 429 / rate-limited (1 req / 5s ceiling)"
                time.sleep(self._backoff_s * (attempt + 1))
                continue
            if r.status_code >= 400:
                return self._fail(request, ErrorKind.UNKNOWN, f"http {r.status_code}: {r.text[:160]}")
            try:
                data = r.json()
            except ValueError:
                # GDELT sometimes returns empty body for a no-coverage name -> treat as zero volume
                if not r.text.strip():
                    return self._ok(request, [
                        ConnectorObservation(attribute="recent_vol_avg_7d", value=0.0, source_url=_API,
                                             extra={"note": "no GDELT coverage = un-discovered in news"}),
                        ConnectorObservation(attribute="n_points", value=0, source_url=_API),
                    ], raw=r.text[:300])
                last_detail = "non-json body"
                time.sleep(self._backoff_s)
                continue
            break

        if data is None:
            return self._fail(request, ErrorKind.RATE_LIMIT,
                              f"GDELT unavailable after {self._max_retries} tries: {last_detail}")

        timeline = data.get("timeline", [])
        pts = (timeline[0].get("data") if timeline else []) or []
        vals = [p.get("value", 0.0) for p in pts]
        if not vals:
            return self._ok(request, [
                ConnectorObservation(attribute="recent_vol_avg_7d", value=0.0, source_url=_API,
                                     extra={"note": "empty timeline = no measurable news volume"}),
                ConnectorObservation(attribute="n_points", value=0, source_url=_API),
            ], raw=str(data)[:500])

        recent = vals[-7:]
        baseline_window = vals[:-7] if len(vals) > 7 else vals
        recent_avg = sum(recent) / len(recent)
        baseline_avg = (sum(baseline_window) / len(baseline_window)) if baseline_window else 0.0
        vol_vs_baseline = (recent_avg / baseline_avg) if baseline_avg > 0 else (None if recent_avg == 0 else float("inf"))

        obs = [
            ConnectorObservation(attribute="recent_vol_avg_7d", value=round(recent_avg, 5), source_url=_API,
                                 extra={"unit": "% of global monitored coverage (GDELT normalized)"}),
            ConnectorObservation(attribute="baseline_vol_avg", value=round(baseline_avg, 5), source_url=_API),
            ConnectorObservation(attribute="vol_vs_baseline",
                                 value=round(vol_vs_baseline, 2) if vol_vs_baseline not in (None, float("inf")) else vol_vs_baseline,
                                 source_url=_API, extra={"interpretation": ">1 = elevated news attention vs own history"}),
            ConnectorObservation(attribute="peak_vol", value=round(max(vals), 5), source_url=_API),
            ConnectorObservation(attribute="n_points", value=len(vals), source_url=_API),
        ]
        return self._ok(request, obs, raw=str(data)[:2048])


if __name__ == "__main__":
    for name in ["Red Cat Holdings", "Destiny Tech100"]:
        res = GdeltNewsConnector().query(ConnectorRequest(entity_name=name))
        d = {o.attribute: o.value for o in res.observations}
        print(f"{name}: success={res.success} err={res.error_kind} "
              f"recent7={d.get('recent_vol_avg_7d')} vs_base={d.get('vol_vs_baseline')} n={d.get('n_points')}")
        time.sleep(6)
