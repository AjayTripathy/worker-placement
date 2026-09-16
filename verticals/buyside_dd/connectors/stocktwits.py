"""StockTwits attention connector — per-ticker retail message volume + bull/bear sentiment.

CONDITIONING LAYER (Attention sub-layer). This is a *no-edge* control source: it measures how
much retail chatter a name is already attracting, NOT whether the name is a good investment. Its
job is to let a divergence be filtered to UN-discovered names and to map signal-to-price latency.

Source: StockTwits public stream API, https://api.stocktwits.com/api/2/streams/symbol/<SYM>.json
- Free, no auth (low-volume public read). Returns up to 30 most-recent messages per call.
- Each message may carry entities.sentiment.basic == 'Bullish' | 'Bearish' (most are None).
- Lag: ~LIVE (the stream is the last ~30 posts, minutes-fresh).

What we extract (point-in-time honest):
  - message_count_30  : how many of the last-30 messages fall inside the asof window
  - msgs_per_day      : crude posting velocity over the window the 30 messages span
  - bull_count / bear_count / bull_bear_ratio over the messages that carry a label
  - newest/oldest message timestamps (so the caller sees the true freshness span)

LIMITS (disclosed): the public endpoint is a 30-message window, so for a very high-traffic name the
30 messages span only minutes and msgs_per_day saturates (a ceiling, read it as "very high"). Most
messages are unlabeled, so the bull/bear ratio is over the labeled subset only. A name with ZERO
messages / a 404 symbol is a genuine un-discovered signal, returned as success with count 0, not an
error.

Inputs (ConnectorRequest): entity_name carries the TICKER (e.g. 'RCAT'). Optional extra={'asof': 'YYYY-MM-DD'}
to window the messages (default = now).
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
    "summary": 'Retail message volume + bull/bear tilt. Any public ticker.',
}

from datetime import datetime, timezone, timedelta

from .base import BaseConnector, ConnectorObservation, ConnectorRequest, ConnectorResult, ErrorKind, safe_get

_API = "https://api.stocktwits.com/api/2/streams/symbol/{sym}.json"
# StockTwits blocks the default python-requests UA; present a normal browser UA.
_UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")


def _parse_ts(s: str) -> datetime | None:
    if not s:
        return None
    try:
        # StockTwits: '2026-06-24T19:01:33Z'
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None


class StockTwitsConnector(BaseConnector):
    source_id = "stocktwits"
    rate_limit_per_min = 30
    user_agent = _UA

    def query(self, request: ConnectorRequest) -> ConnectorResult:
        sym = (request.entity_name or "").strip().upper()
        if not sym:
            return self._fail(request, ErrorKind.UNSUPPORTED, "entity_name (ticker) required")
        asof = request.extra.get("asof")
        asof_dt = None
        if asof:
            try:
                # end of the asof DAY (inclusive). The public stream only ever returns the most
                # recent 30 messages, so a PAST asof can window them out; a TODAY/future asof must
                # NOT clip live messages whose UTC timestamp has rolled into the next calendar day
                # (a very high-velocity name like SPCX posts 30 messages within minutes, some past
                # midnight UTC). So: only apply the upper bound when asof is strictly in the past.
                day = datetime.fromisoformat(str(asof)).replace(tzinfo=timezone.utc)
                now = datetime.now(timezone.utc)
                # If the asof date is today (or later) in ANY of the local/UTC frames, the analyst
                # means "now" -> read the live stream, do NOT clip (UTC may already be a day ahead).
                if day.date() >= now.date() or day.date() >= (now - timedelta(hours=12)).date():
                    asof_dt = None
                else:
                    asof_dt = day + timedelta(days=1)   # past asof: end-of-day upper bound
            except ValueError:
                asof_dt = None

        sess = self._session()
        sess.headers["User-Agent"] = _UA
        url = _API.format(sym=sym)
        self._throttle()
        r, ek, ed = safe_get(sess, url, timeout=self.timeout_s)
        if r is None:
            if ek == ErrorKind.NOT_FOUND:
                # symbol not tracked on StockTwits == zero retail attention == un-discovered signal
                return self._ok(request, [
                    ConnectorObservation(attribute="message_count_30", value=0,
                                         source_url=url, confidence=1.0,
                                         extra={"note": "symbol not found on StockTwits = no retail stream = un-discovered"}),
                    ConnectorObservation(attribute="stocktwits_tracked", value=False, source_url=url),
                ], raw="404")
            return self._fail(request, ek, ed)
        try:
            data = r.json()
        except ValueError as e:
            return self._fail(request, ErrorKind.PARSE_FAIL, f"json: {e}", raw=r.text[:500])

        msgs = data.get("messages") or []
        # window to <= asof if requested
        windowed = []
        for m in msgs:
            ts = _parse_ts(m.get("created_at", ""))
            if asof_dt and ts and ts > asof_dt:
                continue
            windowed.append((m, ts))
        if not windowed:
            return self._ok(request, [
                ConnectorObservation(attribute="message_count_30", value=0, source_url=url,
                                     extra={"note": "tracked but no messages in asof window"}),
                ConnectorObservation(attribute="stocktwits_tracked", value=True, source_url=url),
            ], raw=r.text[:500])

        ts_list = [t for _, t in windowed if t]
        newest = max(ts_list) if ts_list else None
        oldest = min(ts_list) if ts_list else None
        span_days = max((newest - oldest).total_seconds() / 86400.0, 1e-6) if (newest and oldest) else None

        bull = bear = 0
        for m, _ in windowed:
            ent = (m.get("entities") or {}).get("sentiment") or {}
            b = (ent.get("basic") or "").lower()
            if b == "bullish":
                bull += 1
            elif b == "bearish":
                bear += 1
        labeled = bull + bear
        n = len(windowed)
        # msgs/day: if the 30-window spans <1 day it's a high-velocity ceiling
        msgs_per_day = (n / span_days) if span_days else None

        obs = [
            ConnectorObservation(attribute="message_count_30", value=n, source_url=url, confidence=1.0,
                                 extra={"caveat": "30-message public window; a high-traffic name saturates this ceiling"}),
            ConnectorObservation(attribute="msgs_per_day", value=round(msgs_per_day, 1) if msgs_per_day else None,
                                 source_url=url,
                                 extra={"window_days": round(span_days, 3) if span_days else None,
                                        "ceiling": bool(span_days and span_days < 1.0)}),
            ConnectorObservation(attribute="bull_count", value=bull, source_url=url),
            ConnectorObservation(attribute="bear_count", value=bear, source_url=url),
            ConnectorObservation(attribute="bull_bear_ratio",
                                 value=round(bull / bear, 2) if bear else (None if not bull else float("inf")),
                                 source_url=url, extra={"labeled_n": labeled}),
            ConnectorObservation(attribute="newest_message_utc", value=newest.isoformat() if newest else None, source_url=url),
            ConnectorObservation(attribute="oldest_message_utc", value=oldest.isoformat() if oldest else None, source_url=url),
            ConnectorObservation(attribute="stocktwits_tracked", value=True, source_url=url),
        ]
        return self._ok(request, obs, raw=r.text[:2048])


if __name__ == "__main__":
    for t in ["RCAT", "DXYZ", "SPCX"]:
        res = StockTwitsConnector().query(ConnectorRequest(entity_name=t))
        d = {o.attribute: o.value for o in res.observations}
        print(f"{t}: success={res.success} msgs={d.get('message_count_30')} "
              f"per_day={d.get('msgs_per_day')} bull/bear={d.get('bull_count')}/{d.get('bear_count')}")
