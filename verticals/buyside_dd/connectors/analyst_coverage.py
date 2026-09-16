"""analyst_coverage — INSTITUTIONAL-attention connector (Conditioning Layer, Phase 2).

THE GOAL (do not lose it): sell-side analyst density is the cheapest proxy for "is this name
institutionally WATCHED." A >$10B medtech with 20+ covering analysts and a press-released Class-I
recall is, by construction, discovered — the street has read the 8-K, modeled the recall, and set
price targets. A micro-cap with 0-1 analysts is genuinely off the institutional radar. This is the
analyst-coverage axis the gov-contract A/B already proved works as a conditioning variable.

WHAT WE RETURN (per ticker):
  - n_analysts            : number of covering analysts (numberOfAnalystOpinions)
  - recommendation_mean   : 1=Strong Buy ... 5=Strong Sell (consensus rating level)
  - recommendation_key    : 'strong_buy'..'strong_sell'
  - target_mean / spot / target_upside_pct : consensus price target vs price
  - rec_trend             : last ~4 monthly snapshots of strongBuy/buy/hold/sell/strongSell counts
  - revision_direction    : 'UPGRADING' | 'DOWNGRADING' | 'STABLE' (are analysts cutting or raising?)
  - market_cap            : for the cap_tier guard
  - coverage_level        : 'HEAVY' (>=15) | 'MODERATE' (5-14) | 'LIGHT' (1-4) | 'NONE' (0)
  - institutionally_watched : bool — n_analysts >= _WATCHED_FLOOR

SOURCE: yfinance (free; Yahoo Finance). numberOfAnalystOpinions + recommendationTrend. This is the
free feed the spec names. If yfinance returns nothing (delisted / blocked / micro-cap with no Yahoo
analyst record), we DEGRADE to a cap-tier + listing-age PROXY and SAY SO (proxy=True): a sub-$300M
name with no analyst record is treated as LIGHT/NONE coverage; we never invent an analyst count.

LAG: Yahoo's analyst aggregates refresh ~daily but individual revisions lag the actual broker note
by days. recommendationTrend periods are monthly buckets ('0m','-1m','-2m','-3m'). Surfaced.

Inputs: entity_name = TICKER. extra={'asof'} (informational; Yahoo serves current aggregates).
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
    "summary": 'Institutional-attention read: analyst count/coverage for the conditioning layer. Any public ticker.',
}

from typing import Any, Optional

from .base import BaseConnector, ConnectorObservation, ConnectorRequest, ConnectorResult, ErrorKind

_WATCHED_FLOOR = 8       # >=8 covering analysts == institutionally watched
_HEAVY = 15
_MODERATE = 5


def _coverage_level(n: Optional[int]) -> str:
    if n is None:
        return "UNKNOWN"
    if n >= _HEAVY:
        return "HEAVY"
    if n >= _MODERATE:
        return "MODERATE"
    if n >= 1:
        return "LIGHT"
    return "NONE"


def _net_bull(row: dict) -> Optional[float]:
    """A signed consensus score from a rec-trend row: (strongBuy*2 + buy) - (sell + strongSell*2),
    normalized by total. Higher = more bullish. Used to detect the QoQ revision direction."""
    sb, b = row.get("strongBuy") or 0, row.get("buy") or 0
    h = row.get("hold") or 0
    s, ss = row.get("sell") or 0, row.get("strongSell") or 0
    tot = sb + b + h + s + ss
    if tot == 0:
        return None
    return (2 * sb + b - s - 2 * ss) / tot


class AnalystCoverageConnector(BaseConnector):
    source_id = "analyst_coverage"
    rate_limit_per_min = 30
    user_agent = "SignalOS-BuysideDD/0.1 conditioning-layer analyst"

    def query(self, request: ConnectorRequest) -> ConnectorResult:
        sym = (request.entity_name or "").strip().upper()
        if not sym:
            return self._fail(request, ErrorKind.UNSUPPORTED, "entity_name (ticker) required")
        try:
            import yfinance as yf
        except Exception as e:  # noqa: BLE001
            return self._fail(request, ErrorKind.UNSUPPORTED, f"yfinance not importable: {e}")

        try:
            tk = yf.Ticker(sym)
            info = tk.info or {}
        except Exception as e:  # noqa: BLE001
            return self._fail(request, ErrorKind.NETWORK, f"yfinance .info failed for {sym}: {e}")

        n_analysts = info.get("numberOfAnalystOpinions")
        rec_mean = info.get("recommendationMean")
        rec_key = info.get("recommendationKey")
        target_mean = info.get("targetMeanPrice")
        spot = info.get("currentPrice") or info.get("regularMarketPrice")
        mcap = info.get("marketCap")
        avg_rating = info.get("averageAnalystRating")

        # recommendation trend (revision direction)
        rec_trend = None
        try:
            rt = tk.recommendations
            if rt is not None and len(rt):
                rec_trend = rt.to_dict("records")
        except Exception:  # noqa: BLE001
            rec_trend = None

        proxy = False
        proxy_note = None
        if not n_analysts:
            # DEGRADE to a cap-tier proxy and SAY SO. No fabricated analyst count.
            proxy = True
            if mcap is None:
                proxy_note = ("yfinance returned no analyst count AND no market cap; coverage UNKNOWN. "
                              "Not fabricated.")
                cov_proxy = "UNKNOWN"
            elif mcap >= 10e9:
                cov_proxy, proxy_note = "HEAVY", "no Yahoo analyst record but mcap>=$10B → large-caps are heavily covered (proxy)"
            elif mcap >= 2e9:
                cov_proxy, proxy_note = "MODERATE", "no Yahoo analyst record; mid-cap → moderate coverage (proxy)"
            elif mcap >= 300e6:
                cov_proxy, proxy_note = "LIGHT", "no Yahoo analyst record; small-cap → light coverage (proxy)"
            else:
                cov_proxy, proxy_note = "NONE", "no Yahoo analyst record; micro-cap → off institutional radar (proxy)"
            coverage_level = cov_proxy
            institutionally_watched = coverage_level in ("HEAVY", "MODERATE")
        else:
            coverage_level = _coverage_level(int(n_analysts))
            institutionally_watched = int(n_analysts) >= _WATCHED_FLOOR

        # revision direction from rec_trend: compare most-recent bucket to ~3 months prior
        revision_direction = None
        if rec_trend and len(rec_trend) >= 2:
            cur = _net_bull(rec_trend[0])
            prior = _net_bull(rec_trend[min(3, len(rec_trend) - 1)])
            if cur is not None and prior is not None:
                if cur - prior > 0.10:
                    revision_direction = "UPGRADING"
                elif cur - prior < -0.10:
                    revision_direction = "DOWNGRADING"
                else:
                    revision_direction = "STABLE"

        target_upside = None
        if target_mean and spot:
            try:
                target_upside = round(100.0 * (target_mean - spot) / spot, 1)
            except (TypeError, ZeroDivisionError):
                target_upside = None

        src = "yfinance / Yahoo Finance analyst aggregates"
        obs = [
            ConnectorObservation(attribute="n_analysts", value=(int(n_analysts) if n_analysts else None),
                                 source_url=src, extra={"proxy": proxy}),
            ConnectorObservation(attribute="coverage_level", value=coverage_level, source_url=src,
                                 extra={"thresholds": {"HEAVY": _HEAVY, "MODERATE": _MODERATE},
                                        "proxy": proxy, "proxy_note": proxy_note}),
            ConnectorObservation(attribute="institutionally_watched", value=institutionally_watched,
                                 source_url=src, extra={"watched_floor_analysts": _WATCHED_FLOOR}),
            ConnectorObservation(attribute="recommendation_mean", value=rec_mean, source_url=src,
                                 extra={"scale": "1=Strong Buy ... 5=Strong Sell", "avg_rating": avg_rating}),
            ConnectorObservation(attribute="recommendation_key", value=rec_key, source_url=src),
            ConnectorObservation(attribute="target_mean", value=target_mean, source_url=src),
            ConnectorObservation(attribute="spot", value=spot, source_url=src),
            ConnectorObservation(attribute="target_upside_pct", value=target_upside, source_url=src,
                                 extra={"interp": "consensus PT vs spot; large + still-bullish after a crash "
                                                  "= street has NOT capitulated = discovered/anchored"}),
            ConnectorObservation(attribute="revision_direction", value=revision_direction, source_url=src,
                                 extra={"note": "QoQ shift in net-bull consensus from recommendationTrend buckets"}),
            ConnectorObservation(attribute="rec_trend", value=rec_trend, source_url=src,
                                 extra={"buckets": "monthly: 0m / -1m / -2m / -3m"}),
            ConnectorObservation(attribute="market_cap", value=mcap, source_url=src),
        ]
        return self._ok(request, obs, raw=str({k: info.get(k) for k in
                        ("numberOfAnalystOpinions", "recommendationKey", "marketCap")})[:512])


if __name__ == "__main__":
    import sys, json
    t = sys.argv[1] if len(sys.argv) > 1 else "PODD"
    res = AnalystCoverageConnector().query(ConnectorRequest(entity_name=t))
    if not res.success:
        print(f"{t}: FAIL {res.error_kind} {res.error_detail}")
    else:
        d = {o.attribute: o.value for o in res.observations}
        print(f"{t}: n_analysts={d['n_analysts']} coverage={d['coverage_level']} "
              f"watched={d['institutionally_watched']} rec_mean={d['recommendation_mean']} "
              f"({d['recommendation_key']}) target_upside={d['target_upside_pct']}% "
              f"revision={d['revision_direction']} mcap={d['market_cap']}")
