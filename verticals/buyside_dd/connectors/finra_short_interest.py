"""FINRA short-interest positioning connector — bi-monthly reported short position by ticker.

CONDITIONING LAYER (Positioning sub-layer). No-edge control: the single most direct "how crowded
is the short already" gauge. A 25%-of-float short interest means the short divergence is largely
DISCOVERED (already priced, squeeze-prone); a sub-5% short interest on a name with a short thesis
means a genuine, un-discovered frontrun. This is exactly the control the spec wants.

Source: FINRA Query API (free, no auth),
  POST https://api.finra.org/data/group/otcMarket/name/consolidatedShortInterest
  Filter by symbolCode == <TICKER>. Returns the bi-monthly consolidated equity short-interest
  records: currentShortPositionQuantity, previousShortPositionQuantity, averageDailyVolumeQuantity,
  daysToCoverQuantity, settlementDate, changePercent.

IMPORTANT — what this feed does NOT give: shares-outstanding or float. So short-interest as a
% OF FLOAT cannot be computed from this source alone (a known gap; Phase 2 joins SEC shares-
outstanding to convert quantity -> %). What IS native here and IS a clean crowding metric:
  - days_to_cover (short qty / avg daily volume) — the squeeze-pressure proxy
  - short_qty level + its bi-monthly change
So we report days_to_cover as the primary positioning signal and the raw quantity + change; if the
caller supplies extra={'float_shares': N} or {'shares_outstanding': N} we ALSO compute si_pct.

LAG (disclosed, surfaced): FINRA settlement dates are bi-monthly and published with a ~1-2 WEEK
delay; the latest record is typically 1-3 weeks stale vs asof. asof_lag_days surfaces it; never
backfilled.

Inputs: entity_name = TICKER. extra={'asof': 'YYYY-MM-DD'} (picks the latest record <= asof),
optional extra={'float_shares' | 'shares_outstanding': int} to enable si_pct.
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
    "summary": 'Bi-monthly reported short positioning. Any public ticker.',
}

from datetime import datetime, timezone

from .base import BaseConnector, ConnectorObservation, ConnectorRequest, ConnectorResult, ErrorKind

_API = "https://api.finra.org/data/group/otcMarket/name/consolidatedShortInterest"
_UA = "SignalOS-BuysideDD/0.1 conditioning-layer research"
# FINRA crowding thresholds (days-to-cover, the native squeeze proxy)
_DTC_CROWDED = 5.0      # >=5 days to cover = meaningfully crowded short
_SI_PCT_CROWDED = 20.0  # spec's DISCOVERED_CROWDED short-interest threshold (needs float)


class FinraShortInterestConnector(BaseConnector):
    source_id = "finra_short_interest"
    rate_limit_per_min = 30
    user_agent = _UA

    def query(self, request: ConnectorRequest) -> ConnectorResult:
        sym = (request.entity_name or "").strip().upper()
        if not sym:
            return self._fail(request, ErrorKind.UNSUPPORTED, "entity_name (ticker) required")
        asof = request.extra.get("asof")
        try:
            asof_dt = datetime.fromisoformat(str(asof)).date() if asof else datetime.now(timezone.utc).date()
        except ValueError:
            asof_dt = datetime.now(timezone.utc).date()

        body = {"limit": 1000,
                "compareFilters": [{"compareType": "equal", "fieldName": "symbolCode", "fieldValue": sym}]}
        sess = self._session()
        sess.headers.update({"User-Agent": _UA, "Content-Type": "application/json",
                             "Accept": "application/json"})
        self._throttle()
        try:
            r = sess.post(_API, json=body, timeout=self.timeout_s)
        except Exception as e:
            return self._fail(request, ErrorKind.NETWORK, f"post: {e}")
        if r.status_code == 429:
            return self._fail(request, ErrorKind.RATE_LIMIT, "FINRA 429")
        if r.status_code >= 400:
            return self._fail(request, ErrorKind.UNKNOWN, f"http {r.status_code}: {r.text[:160]}")
        try:
            recs = r.json()
        except ValueError as e:
            return self._fail(request, ErrorKind.PARSE_FAIL, f"json: {e}", raw=r.text[:300])
        if not isinstance(recs, list) or not recs:
            return self._fail(request, ErrorKind.NOT_FOUND, f"no FINRA short-interest record for {sym}")

        # latest settlement <= asof
        def _d(rec):
            try:
                return datetime.strptime(rec.get("settlementDate", "")[:10], "%Y-%m-%d").date()
            except ValueError:
                return None
        dated = [(d, rec) for rec in recs if (d := _d(rec)) is not None]
        eligible = [(d, rec) for d, rec in dated if d <= asof_dt]
        if not eligible:
            return self._fail(request, ErrorKind.NOT_FOUND,
                              f"FINRA has records for {sym} but none on/before {asof_dt}")
        sdate, rec = max(eligible, key=lambda t: t[0])

        short_qty = rec.get("currentShortPositionQuantity")
        prev_qty = rec.get("previousShortPositionQuantity")
        adv = rec.get("averageDailyVolumeQuantity")
        dtc = rec.get("daysToCoverQuantity")
        change_pct = rec.get("changePercent")
        lag_days = (asof_dt - sdate).days

        # si_pct only if caller supplies a float / shares-outstanding (feed has neither)
        si_pct = None
        denom = request.extra.get("float_shares") or request.extra.get("shares_outstanding")
        if denom:
            try:
                si_pct = round(100.0 * short_qty / float(denom), 2)
            except (TypeError, ValueError, ZeroDivisionError):
                si_pct = None

        crowded = False
        if si_pct is not None and si_pct >= _SI_PCT_CROWDED:
            crowded = True
        elif dtc is not None and dtc >= _DTC_CROWDED:
            crowded = True

        obs = [
            ConnectorObservation(attribute="short_position_qty", value=short_qty, source_url=_API,
                                 extra={"settlement_date": str(sdate)}),
            ConnectorObservation(attribute="prev_short_position_qty", value=prev_qty, source_url=_API),
            ConnectorObservation(attribute="short_change_pct", value=change_pct, source_url=_API),
            ConnectorObservation(attribute="avg_daily_volume", value=adv, source_url=_API),
            ConnectorObservation(attribute="days_to_cover", value=dtc, source_url=_API,
                                 extra={"interpretation": "short_qty / ADV; >=5 = crowded short (native squeeze proxy)"}),
            ConnectorObservation(attribute="short_interest_pct", value=si_pct, source_url=_API,
                                 extra={"note": ("computed from caller-supplied float/shares" if si_pct is not None
                                                 else "UNAVAILABLE — FINRA feed has no float; supply extra.float_shares")}),
            ConnectorObservation(attribute="si_crowded", value=crowded, source_url=_API,
                                 extra={"dtc_threshold": _DTC_CROWDED, "si_pct_threshold": _SI_PCT_CROWDED}),
            ConnectorObservation(attribute="settlement_date", value=str(sdate), source_url=_API),
            ConnectorObservation(attribute="asof_lag_days", value=lag_days, source_url=_API,
                                 extra={"note": "FINRA SI is bi-monthly, ~1-2wk publish delay; never backfilled"}),
        ]
        return self._ok(request, obs, raw=str(rec)[:2048])


if __name__ == "__main__":
    for t in ["RCAT", "GME"]:
        res = FinraShortInterestConnector().query(ConnectorRequest(entity_name=t))
        d = {o.attribute: o.value for o in res.observations}
        print(f"{t}: success={res.success} err={res.error_kind} short_qty={d.get('short_position_qty')} "
              f"dtc={d.get('days_to_cover')} crowded={d.get('si_crowded')} lag={d.get('asof_lag_days')}")
