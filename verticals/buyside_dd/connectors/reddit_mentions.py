"""reddit_mentions — social-attention ingestion for the conditioning layer / social-thesis engine.

Returns per-ticker Reddit mention volume + velocity + crowd lean across finance subreddits, to
feed discovery_state (attention sub-layer) and the social-thesis triage.

SOURCE: ApeWisdom (https://apewisdom.io/api/v1.0/filter/<filter>) — a free, no-auth API that
already aggregates Reddit mention counts per ticker with a 24h-ago count (velocity) and upvotes.
This sidesteps Reddit's public-.json 403 wall (Reddit hard-blocks datacenter IPs without OAuth).
Tickers come pre-resolved by ApeWisdom; we still cross-check against the SEC ticker universe.
UPGRADE PATH: direct Reddit OAuth (set REDDIT_CLIENT_ID/REDDIT_CLIENT_SECRET) for raw post/comment
text + custom sentiment — stubbed in _reddit_oauth(), not required for the standing feed.
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
    "summary": 'Retail social attention (Reddit). Any public ticker.',
}

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import requests

_APE = "https://apewisdom.io/api/v1.0/filter/{flt}/page/{page}"
_SEC_TICKERS = "https://www.sec.gov/files/company_tickers.json"
_CACHE = Path(__file__).resolve().parent.parent / "outputs" / "_ticker_universe.json"

# ApeWisdom filters (subreddit aggregates). 'all-stocks' = broad finance aggregate.
DEFAULT_FILTERS = ["all-stocks", "wallstreetbets"]

# ETFs / indices / leveraged products — surfaced by WSB but NOT honesty-detector targets
# (no issuer to diligence). Excluded from the candidate universe (SPEC §2 refinement).
EXCLUDE_ETF = {
    "SPY", "QQQ", "IWM", "DIA", "VOO", "VTI", "VXX", "UVXY", "VIXY", "SVXY", "SQQQ", "TQQQ",
    "SOXL", "SOXS", "SPXL", "SPXS", "SPXU", "UPRO", "TZA", "TNA", "LABU", "LABD", "ARKK", "ARKG",
    "XLF", "XLE", "XLK", "XLV", "XLI", "XLP", "XLU", "XLY", "XLB", "XLRE", "XLC", "SMH", "SOXX",
    "GLD", "SLV", "GDX", "USO", "UNG", "TLT", "IEF", "HYG", "LQD", "EEM", "FXI", "KWEB", "EWZ",
    "VEA", "VWO", "BITO", "BITX", "IBIT", "GBTC", "ETHE", "KRE", "XBI", "JEPI", "JEPQ", "SCHD",
    "VGT", "VYM", "RSP", "MAGS", "BIL", "SGOV", "USFR", "VT", "ITOT", "QYLD", "FNGU", "BOIL",
}


def _ticker_universe() -> set[str]:
    """Valid US tickers from SEC company_tickers.json (cached 7d). Plain UA — SEC's WAF blocks
    browser-fingerprint-looking requests, so DON'T send Sec-Ch-Ua here."""
    try:
        if _CACHE.exists() and (time.time() - _CACHE.stat().st_mtime) < 7 * 86400:
            return set(json.loads(_CACHE.read_text()))
    except Exception:
        pass
    try:
        r = requests.get(_SEC_TICKERS, headers={"User-Agent": "SignalOS Research admin@signalos.io"},
                         timeout=30)
        if r.status_code == 200:
            tickers = {row["ticker"].upper() for row in r.json().values() if row.get("ticker")}
            _CACHE.parent.mkdir(parents=True, exist_ok=True)
            _CACHE.write_text(json.dumps(sorted(tickers)))
            return tickers
    except Exception:
        pass
    try:
        return set(json.loads(_CACHE.read_text()))
    except Exception:
        return set()


def _fetch_filter(flt: str, pages: int = 2) -> list[dict]:
    out = []
    for page in range(1, pages + 1):
        try:
            r = requests.get(_APE.format(flt=flt, page=page),
                             headers={"User-Agent": "Mozilla/5.0 (SignalOS research)"}, timeout=20)
            if r.status_code != 200:
                break
            res = r.json().get("results", [])
            if not res:
                break
            out.extend(res)
            time.sleep(0.4)
        except Exception:
            break
    return out


def _reddit_oauth():  # upgrade-path stub (raw text + custom sentiment)
    import os
    cid, sec = os.environ.get("REDDIT_CLIENT_ID"), os.environ.get("REDDIT_CLIENT_SECRET")
    if not (cid and sec):
        return None
    raise NotImplementedError("Reddit OAuth path not wired — ApeWisdom is the active source.")


def scan(filters: Optional[list[str]] = None, *, pages: int = 2,
         validate_against_sec: bool = True, exclude_etfs: bool = True) -> dict:
    """Scan ApeWisdom finance filters; return {asof, source, n_tickers, tickers:{T:{...}}}.

    Per ticker: mentions, mentions_24h_ago, velocity (mentions/24h_ago), rank, upvotes, name,
    filters (which subs), sentiment (if ApeWisdom supplies it), spike (bool). Ranked by mentions.
    exclude_etfs drops index/ETF/leveraged products (not honesty-detector targets).
    """
    filters = filters or DEFAULT_FILTERS
    universe = _ticker_universe() if validate_against_sec else set()
    agg: dict[str, dict] = {}
    for flt in filters:
        for row in _fetch_filter(flt, pages):
            t = (row.get("ticker") or "").upper()
            if not t:
                continue
            if exclude_etfs and t in EXCLUDE_ETF:
                continue
            if universe and t not in universe:
                continue  # drop crypto / non-US-equity tickers ApeWisdom also tracks
            m = int(row.get("mentions") or 0)
            m24 = int(row.get("mentions_24h_ago") or 0)
            a = agg.setdefault(t, {"mentions": 0, "mentions_24h_ago": 0, "upvotes": 0,
                                   "name": row.get("name"), "filters": [], "rank_best": 9999,
                                   "sentiment": row.get("sentiment")})
            # a ticker can appear in multiple filters; take the max mentions (avoid double count)
            a["mentions"] = max(a["mentions"], m)
            a["mentions_24h_ago"] = max(a["mentions_24h_ago"], m24)
            a["upvotes"] = max(a["upvotes"], int(row.get("upvotes") or 0))
            a["rank_best"] = min(a["rank_best"], int(row.get("rank") or 9999))
            if flt not in a["filters"]:
                a["filters"].append(flt)

    ranked = []
    for t, a in agg.items():
        m, m24 = a["mentions"], a["mentions_24h_ago"]
        a["velocity"] = round(m / m24, 2) if m24 else (float("inf") if m else 0.0)
        a["spike"] = bool(m24 and m >= max(2 * m24, m24 + 20))  # 2x or +20 absolute = fresh spike
        ranked.append((t, a))
    ranked.sort(key=lambda kv: kv[1]["mentions"], reverse=True)
    return {
        "asof": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "source": "apewisdom",
        "filters": filters,
        "universe_size": len(universe),
        "n_tickers": len(ranked),
        "tickers": dict(ranked),
    }


if __name__ == "__main__":
    res = scan()
    print(f"asof {res['asof']} | source={res['source']} | tickers={res['n_tickers']} "
          f"| universe={res['universe_size']}")
    print(f"{'TICKER':7}{'MENT':>6}{'24H':>6}{'VELOC':>7}{'SPIKE':>7}{'UPVOTE':>8}  NAME")
    for t, a in list(res["tickers"].items())[:25]:
        sp = "▲" if a["spike"] else ""
        print(f"{t:7}{a['mentions']:>6}{a['mentions_24h_ago']:>6}{a['velocity']:>7}{sp:>7}"
              f"{a['upvotes']:>8}  {(a['name'] or '')[:26]}")
    Path("outputs").mkdir(exist_ok=True)
    json.dump(res, open("outputs/reddit_scan_latest.json", "w"), indent=2, default=str)
    print("\n[wrote outputs/reddit_scan_latest.json]")


# ── Uniform-contract wrapper (bespoke-promotion 2026-08-08) ─────────────────────
from .base import BaseConnector, ConnectorObservation, ConnectorRequest, ConnectorResult, ErrorKind


class RedditMentionsConnector(BaseConnector):
    source_id = "reddit_mentions"

    def query(self, request: ConnectorRequest) -> ConnectorResult:
        x = request.extra or {}
        ticker = str(x.get("ticker") or request.entity_name or "").upper()
        if not ticker or " " in ticker:
            return self._fail(request, ErrorKind.UNSUPPORTED,
                              "reddit_mentions needs a TICKER (extra.ticker or entity_name)")
        res = scan(pages=int(x.get("pages", 2)))
        row = (res.get("tickers") or {}).get(ticker)
        if row is None:
            # absence from the top of the attention tape IS the observation
            return self._ok(request, [ConnectorObservation(
                attribute="reddit_attention", value="ABSENT-FROM-TOP",
                confidence=0.6,
                extra={"universe_size": res.get("universe_size"),
                       "note": "not in ApeWisdom top pages — low retail attention, "
                               "supports UNDISCOVERED (not proof)"})], raw=None)
        return self._ok(request, [
            ConnectorObservation(attribute="reddit_mentions", value=row.get("mentions"),
                                 extra={"mentions_24h_ago": row.get("mentions_24h_ago"),
                                        "velocity": row.get("velocity"),
                                        "rank": row.get("rank"), "spike": row.get("spike"),
                                        "upvotes": row.get("upvotes")}),
        ], raw=__import__('json').dumps(row, default=str))
