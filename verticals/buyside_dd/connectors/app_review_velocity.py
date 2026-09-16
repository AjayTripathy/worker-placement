"""app_review_velocity — APP-STORE REVIEW VELOCITY + cohort quality for any issuer whose
product reaches customers as a consumer app.

Sibling of consumer_product_heat / consumer_product_reviews in the consumer lane (principal
directive 2026-08-16: "build an app store review velocity tool and wire it into the SignalOS
brain so it can be called in the future for places with apps"). Retail reviews catch a CPG
brand rotting; this catches the app-distributed business — brokers, fintechs, marketplaces,
insurers, social — where the app IS the storefront and review cadence is a free, dated,
public proxy for the customer-acquisition funnel.

WHAT DISCRIMINATES (same doctrine as the retail sibling — direction and velocity, not stars):
  (a) REVIEW VELOCITY — dated reviews/day from the App Store RSS feed. Unlike Walmart, the
      App Store exposes HUNDREDS of dated reviews, so run 1 gives a true trailing-7d/30d rate,
      no snapshot wait.
  (b) RECENT-COHORT RATING minus LIFETIME RATING — the fresh cohort leads the slow lifetime
      mean by months. Two independent estimates: visible cohort (RSS, run 1) and EXACT
      ((R1*N1 − R0*N0)/(N1 − N0)) once two lookup snapshots ≥3d apart exist.
  (c) ONE-STAR SHARE of the recent cohort vs the visible baseline — complaint mix shifts
      before the mean does.

THE MAUDE LESSON, ENCODED (frontrun_maude_velocity pilot, KILLED 2026-07): a velocity spike
measures PROMPTING, not sentiment. In-app review prompts, a version release, or a support-flow
change manufacture review waves the way regulatory-reporting changes manufacture MAUDE spikes.
So every velocity observation carries version_release_recent (currentVersionReleaseDate inside
the window) and the interpretation rule: a spike coincident with a release is an ARTIFACT
CANDIDATE until the cohort rating confirms direction; a velocity COLLAPSE has no such excuse
and is the cleaner signal (absence-is-observation). Marketing claims of growing MAU alongside
collapsing review cadence = a divergence worth a bench's time.

SOURCES / REACHABILITY:
  - iTunes Search/Lookup API — open JSON, no key. Lifetime userRatingCount + averageUserRating
    + currentVersionReleaseDate. US storefront by default (extra.country to override).
  - iTunes customer-reviews RSS — open JSON, no key. ~50 dated reviews/page, up to 10 pages,
    mostRecent order. US storefront; the velocity is a US-ONLY rate and the output says so.
  - Google Play store page — no API. Parsed from the page's ld+json aggregateRating (rating +
    count only, undated) via browser-fingerprint headers, r.jina.ai proxy fallback. Play gives
    NO dated stream, so Play velocity is snapshot-delta only. DEGRADED-LOUD when walled.

RESOLUTION DISCIPLINE (muni-matcher lesson): ticker → app is resolved via iTunes search with
seller/track token matching; AMBIGUITY RETURNS UNRESOLVED with the candidate list — never a
silent pick. extra.itunes_id / extra.play_pkg override resolution; resolved ids are cached in
data/app_review_velocity/resolution_cache.json and validated on every use (seller drift flags).
"""

from __future__ import annotations

# Knowledge-graph dispatch contract (see knowledge_graph/dispatch.py). Keyed on the
# verification attribute — customer-funnel trajectory of an app-distributed product —
# NOT the issuer's birth sector (brokers, insurers, social, fintech all qualify).
APPLIES_TO = {
    "kind": 'm_source',
    "sic_codes": [],
    "sic_prefixes": ['737', '6199', '6211', '6311', '6411', '7372', '7389'],
    "issuer_features": ['consumer_app', 'mobile_app_channel', 'app_distributed_product',
                        'consumer_brand', 'dtc_brand', 'platform_or_marketplace_kpi',
                        'dau_mau_marketed', 'subscriber_growth_claim'],
    "asset_classes": ['public_equity', 'corporate_ipo_dd'],
    "applies_universally": False,
    "summary": ('App-store review velocity (dated reviews/day, App Store RSS) + recent-cohort-vs-'
                'lifetime rating delta + Play aggregate snapshots, for issuers whose product is a '
                'consumer app. Version-release spikes flagged as prompt artifacts (MAUDE lesson).'),
    "verification_question": ("Is this issuer's app acquiring raters faster or slower than before, "
                              "and is the fresh cohort rating it better or worse than the lifetime "
                              "average — net of review-prompt/version artifacts?"),
}

import json
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

HERE = Path(__file__).resolve()
if str(HERE.parents[3]) not in sys.path:
    sys.path.insert(0, str(HERE.parents[3]))

import requests

from .base import (BaseConnector, ConnectorObservation, ConnectorRequest,
                   ConnectorResult, ErrorKind)
from .consumer_product_reviews import implied_cohort_rating

OUT_DIR = HERE.parent / "data" / "app_review_velocity"
OUT_DIR.mkdir(parents=True, exist_ok=True)
SNAPSHOTS = OUT_DIR / "snapshots.jsonl"
RESOLUTION_CACHE = OUT_DIR / "resolution_cache.json"

MIN_SNAPSHOT_GAP_DAYS = 3.0   # same rule as the retail sibling — hours apart measures nothing
MAX_RSS_PAGES = 10
COHORT_DELTA_MATERIAL = 0.25  # stars; app distributions are wider than retail's 0.15
MIN_COHORT_N = 15             # RSS gives volume; demand more than retail's 5 before calling it

# Standing names (book/queue holders with consumer apps). Resolution fills itunes ids on first
# run; play_pkg only where known-stable — a wrong pkg 404s LOUDLY and never silently scores.
TRACKED: dict[str, dict] = {
    "IBKR": {"query": "IBKR Mobile", "seller_hint": "Interactive Brokers", "play_pkg": "atws.app"},
    "RDDT": {"query": "Reddit", "seller_hint": "Reddit", "play_pkg": "com.reddit.frontpage"},
    "HOOD": {"query": "Robinhood", "seller_hint": "Robinhood", "play_pkg": "com.robinhood.android"},
    "SOFI": {"query": "SoFi", "seller_hint": "SoFi", "play_pkg": None},
    "LMND": {"query": "Lemonade Insurance", "seller_hint": "Lemonade", "play_pkg": None},
    "ETOR": {"query": "eToro", "seller_hint": "eToro", "play_pkg": None},
}

_UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
_HEADERS = {"User-Agent": _UA, "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8",
            "Sec-Fetch-Site": "cross-site", "Sec-Fetch-Mode": "navigate",
            "Sec-Ch-Ua": '"Chromium";v="126", "Google Chrome";v="126"'}
_JINA = "https://r.jina.ai/"


def _iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _tokens(s: str) -> set[str]:
    return set(re.sub(r"[^a-z0-9 ]", " ", (s or "").lower()).split())


# ─────────────────────────────────────────────────────────────────────────────
# iTunes: search / lookup / RSS
# ─────────────────────────────────────────────────────────────────────────────
def itunes_search(query: str, country: str = "us", limit: int = 10,
                  timeout: float = 20.0) -> list[dict]:
    r = requests.get("https://itunes.apple.com/search",
                     params={"term": query, "entity": "software", "country": country,
                             "limit": limit},
                     headers=_HEADERS, timeout=timeout)
    r.raise_for_status()
    return r.json().get("results", [])


def itunes_lookup(app_id: int, country: str = "us", timeout: float = 20.0) -> Optional[dict]:
    r = requests.get("https://itunes.apple.com/lookup",
                     params={"id": app_id, "country": country},
                     headers=_HEADERS, timeout=timeout)
    r.raise_for_status()
    res = r.json().get("results", [])
    return res[0] if res else None


def itunes_recent_reviews(app_id: int, country: str = "us", max_pages: int = MAX_RSS_PAGES,
                          timeout: float = 20.0, window_days: float = 30.0) -> dict:
    """Walk the mostRecent RSS until the oldest fetched review predates the window (or pages
    run out). Returns dated (ts, rating) rows + whether the window was fully covered — when
    pagination ran out first, any windowed count is a FLOOR and the caller must say so."""
    rows: list[tuple[datetime, int]] = []
    window_start = datetime.now(timezone.utc) - timedelta(days=window_days)
    covered = False
    pages_fetched = 0
    for page in range(1, max_pages + 1):
        url = (f"https://itunes.apple.com/{country}/rss/customerreviews/"
               f"id={app_id}/sortBy=mostRecent/page={page}/json")
        r = requests.get(url, headers=_HEADERS, timeout=timeout)
        if r.status_code != 200:
            break
        try:
            entries = r.json().get("feed", {}).get("entry", [])
        except (ValueError, AttributeError):
            break
        if isinstance(entries, dict):        # single-entry pages come back as a bare dict
            entries = [entries]
        page_rows = 0
        for e in entries:
            rating = e.get("im:rating", {}).get("label")
            updated = e.get("updated", {}).get("label")
            if not (rating and updated):     # the app's own metadata entry has neither
                continue
            try:
                ts = datetime.fromisoformat(updated.replace("Z", "+00:00"))
                rows.append((ts.astimezone(timezone.utc), int(rating)))
                page_rows += 1
            except (ValueError, TypeError):
                continue
        pages_fetched = page
        if page_rows == 0:
            break
        if rows and min(ts for ts, _ in rows) < window_start:
            covered = True
            break
        time.sleep(0.4)
    return {"rows": rows, "window_covered": covered, "pages_fetched": pages_fetched}


def resolve_itunes(query: str, seller_hint: str = "", country: str = "us") -> dict:
    """Ticker-name → app. Ambiguity → UNRESOLVED with candidates, never a silent pick."""
    try:
        results = itunes_search(query, country=country)
    except requests.RequestException as e:
        return {"status": "ERROR", "detail": f"itunes search failed: {e}"}
    if not results:
        return {"status": "NOT_FOUND", "detail": f"no software results for {query!r}"}
    q_tok, h_tok = _tokens(query), _tokens(seller_hint)
    scored = []
    for r0 in results:
        name_t = _tokens(r0.get("trackName", ""))
        seller_t = _tokens(r0.get("sellerName", "")) | _tokens(r0.get("artistName", ""))
        score = (2.0 * len(h_tok & seller_t) / max(len(h_tok), 1) if h_tok else 0.0) \
              + 1.0 * len(q_tok & name_t) / max(len(q_tok), 1)
        scored.append((score, r0))
    scored.sort(key=lambda x: -x[0])
    top_score, top = scored[0]
    runner = scored[1][0] if len(scored) > 1 else 0.0
    if top_score <= 0.5 or (runner > 0 and top_score / max(runner, 1e-9) < 1.3
                            and _tokens(scored[1][1].get("sellerName", "")) !=
                                _tokens(top.get("sellerName", ""))):
        return {"status": "UNRESOLVED",
                "detail": "ambiguous — refusing a silent pick",
                "candidates": [{"trackName": r0.get("trackName"),
                                "sellerName": r0.get("sellerName"),
                                "trackId": r0.get("trackId")} for _, r0 in scored[:5]]}
    return {"status": "RESOLVED", "itunes_id": top.get("trackId"),
            "trackName": top.get("trackName"), "sellerName": top.get("sellerName"),
            "score": round(top_score, 2)}


# ─────────────────────────────────────────────────────────────────────────────
# Google Play: ld+json aggregate only (no dated stream exists without batchexecute)
# ─────────────────────────────────────────────────────────────────────────────
def play_aggregate(pkg: str, timeout: float = 25.0) -> dict:
    url = f"https://play.google.com/store/apps/details?id={pkg}&hl=en_US&gl=US"
    html = None
    try:
        r = requests.get(url, headers=_HEADERS, timeout=timeout)
        if r.status_code == 200:
            html = r.text
        elif r.status_code == 404:
            return {"status": "NOT_FOUND", "detail": f"play pkg {pkg} 404 — wrong package id"}
    except requests.RequestException:
        pass
    if html is None:                       # bot-wall / egress issue → proxy fallback, labeled
        try:
            r = requests.get(_JINA + url, timeout=max(timeout, 60.0))
            if r.status_code == 200:
                html = r.text
        except requests.RequestException:
            pass
    if html is None:
        return {"status": "DEGRADED", "detail": "play page unreachable (direct + proxy)"}
    m = re.search(r'"aggregateRating"\s*:\s*{[^}]*"ratingValue"\s*:\s*"?([\d.]+)"?'
                  r'[^}]*"ratingCount"\s*:\s*"?(\d+)"?', html)
    if not m:
        m2 = re.search(r'([\d.]+)\s*star[\s\S]{0,300}?([\d.,]+[KM]?)\s*reviews', html)
        if not m2:
            return {"status": "PARSE_FAIL", "detail": "no aggregateRating in play page"}
        val, cnt = m2.group(1), m2.group(2).replace(",", "")
        mult = 1_000_000 if cnt.endswith("M") else 1_000 if cnt.endswith("K") else 1
        return {"status": "OK", "rating": float(val),
                "count": int(float(cnt.rstrip("KM")) * mult), "parse": "text"}
    name_m = re.search(r'"name"\s*:\s*"([^"]+)"', html)
    return {"status": "OK", "rating": float(m.group(1)), "count": int(m.group(2)),
            "app_name": name_m.group(1) if name_m else None, "parse": "ld+json"}


# ─────────────────────────────────────────────────────────────────────────────
# Snapshots (exact cohort delta + Play velocity need history)
# ─────────────────────────────────────────────────────────────────────────────
def _load_snapshots() -> dict:
    hist: dict[str, list[dict]] = {}
    if SNAPSHOTS.exists():
        for line in SNAPSHOTS.read_text().splitlines():
            try:
                row = json.loads(line)
                hist.setdefault(row["key"], []).append(row)
            except (ValueError, KeyError):
                continue
    return hist


def _append_snapshot(row: dict) -> None:
    with open(SNAPSHOTS, "a") as f:
        f.write(json.dumps(row) + "\n")


def _days_between(a: str, b: str) -> Optional[float]:
    try:
        ta = datetime.fromisoformat(a.replace("Z", "+00:00"))
        tb = datetime.fromisoformat(b.replace("Z", "+00:00"))
        return abs((tb - ta).total_seconds()) / 86400.0
    except (ValueError, TypeError):
        return None


def _resolution_cache() -> dict:
    try:
        return json.loads(RESOLUTION_CACHE.read_text())
    except (OSError, ValueError):
        return {}


def _save_resolution(ticker: str, entry: dict) -> None:
    cache = _resolution_cache()
    cache[ticker] = {**entry, "cached": _iso()}
    RESOLUTION_CACHE.write_text(json.dumps(cache, indent=1))


# ─────────────────────────────────────────────────────────────────────────────
# The read
# ─────────────────────────────────────────────────────────────────────────────
def read_app(ticker: str, query: str = "", seller_hint: str = "",
             itunes_id: Optional[int] = None, play_pkg: Optional[str] = None,
             country: str = "us") -> dict:
    """One issuer → the full signal dict. Every failure is a labeled status, never a zero."""
    tracked = TRACKED.get(ticker, {})
    query = query or tracked.get("query", ticker)
    seller_hint = seller_hint or tracked.get("seller_hint", "")
    play_pkg = play_pkg or tracked.get("play_pkg")
    out: dict[str, Any] = {"ticker": ticker, "asof": _iso(), "country": country}

    # resolve (explicit id > cache > search)
    if itunes_id is None:
        cached = _resolution_cache().get(ticker)
        if cached and cached.get("itunes_id"):
            itunes_id = cached["itunes_id"]
            out["resolution"] = {**cached, "via": "cache"}
        else:
            res = resolve_itunes(query, seller_hint, country)
            out["resolution"] = res
            if res.get("status") != "RESOLVED":
                return out
            itunes_id = res["itunes_id"]
            _save_resolution(ticker, res)
    else:
        out["resolution"] = {"status": "RESOLVED", "itunes_id": itunes_id, "via": "explicit"}

    # lifetime aggregates + version date
    try:
        meta = itunes_lookup(itunes_id, country)
    except requests.RequestException as e:
        meta = None
        out["itunes_lookup"] = {"status": "ERROR", "detail": str(e)}
    if meta:
        # seller-drift check on cached resolutions — a sold/rebranded app must not score silently
        if seller_hint and not (_tokens(seller_hint) & _tokens(meta.get("sellerName", ""))):
            out["seller_drift_flag"] = (f"lookup seller {meta.get('sellerName')!r} no longer "
                                        f"matches hint {seller_hint!r} — verify before trusting")
        ver_date = meta.get("currentVersionReleaseDate")
        out["itunes_lookup"] = {
            "status": "OK", "trackName": meta.get("trackName"),
            "sellerName": meta.get("sellerName"),
            "lifetime_rating": meta.get("averageUserRating"),
            "lifetime_count": meta.get("userRatingCount"),
            "current_version": meta.get("version"),
            "current_version_date": ver_date,
        }

    # dated velocity from RSS
    try:
        rss = itunes_recent_reviews(itunes_id, country)
    except requests.RequestException as e:
        rss = {"rows": [], "window_covered": False, "pages_fetched": 0, "error": str(e)}
    rows = rss["rows"]
    now = datetime.now(timezone.utc)
    if rows:
        n7 = sum(1 for ts, _ in rows if ts >= now - timedelta(days=7))
        n30 = sum(1 for ts, _ in rows if ts >= now - timedelta(days=30))
        oldest = min(ts for ts, _ in rows)
        span_days = max((now - oldest).total_seconds() / 86400.0, 0.25)
        recent = [r for ts, r in rows if ts >= now - timedelta(days=30)] or [r for _, r in rows]
        cohort_avg = sum(recent) / len(recent)
        one_star = sum(1 for r in recent if r == 1) / len(recent)
        ver_recent = False
        vd = (out.get("itunes_lookup") or {}).get("current_version_date")
        if vd:
            try:
                ver_recent = (now - datetime.fromisoformat(vd.replace("Z", "+00:00"))
                              .astimezone(timezone.utc)).days <= 30
            except (ValueError, TypeError):
                ver_recent = False
        out["velocity"] = {
            "status": "OK",
            "reviews_7d": n7, "reviews_30d": n30,
            "per_day_7d": round(n7 / 7.0, 2), "per_day_30d": round(n30 / 30.0, 2),
            "window_covered": rss["window_covered"],
            "floor_note": (None if rss["window_covered"] else
                           f"RSS pagination exhausted at {rss['pages_fetched']} pages spanning "
                           f"{span_days:.1f}d — windowed counts are FLOORS; span rate "
                           f"{len(rows)/span_days:.1f}/day is the honest velocity"),
            "visible_cohort_avg": round(cohort_avg, 2),
            "visible_cohort_n": len(recent),
            "one_star_share": round(one_star, 3),
            "version_release_recent": ver_recent,
            "caveat": ("US storefront only; velocity measures PROMPTING as much as sentiment "
                       "(MAUDE lesson) — a spike coincident with version_release_recent=True is "
                       "an artifact candidate until the cohort rating confirms; a COLLAPSE has "
                       "no prompt excuse and is the cleaner signal. POPULATION WARNING "
                       "(calibrated 2026-08-16, first 6-name cross-section): visible_cohort_avg "
                       "is WRITTEN reviews only, a structurally angrier population than the "
                       "prompted-ratings-dominated lifetime mean — every tracked name reads "
                       "1.8-3.9 recent vs ~4.5+ lifetime. NEVER read visible-vs-lifetime as "
                       "deterioration. Valid comparisons: this cohort vs ITS OWN history "
                       "(velocity + rating over snapshots), name vs name within this channel, "
                       "and the EXACT cohort delta below (same-population arithmetic)."),
        }
    else:
        out["velocity"] = {"status": "EMPTY",
                           "detail": f"no dated RSS reviews ({rss.get('error', 'empty feed')})"}

    # Play aggregate (undated — snapshot fodder)
    if play_pkg:
        out["play"] = {**play_aggregate(play_pkg), "pkg": play_pkg}
    else:
        out["play"] = {"status": "NO_PKG", "detail": "no play package known — pass extra.play_pkg"}

    # snapshot + exact cohort delta
    key = f"{ticker}|{itunes_id}"
    hist = _load_snapshots().get(key, [])
    prev = next((h for h in reversed(hist)
                 if (_days_between(h.get("asof", ""), _iso()) or 0) >= MIN_SNAPSHOT_GAP_DAYS), None)
    lk = out.get("itunes_lookup") or {}
    snap = {"key": key, "asof": _iso(),
            "itunes_count": lk.get("lifetime_count"), "itunes_rating": lk.get("lifetime_rating"),
            "play_count": (out.get("play") or {}).get("count"),
            "play_rating": (out.get("play") or {}).get("rating")}
    _append_snapshot(snap)
    if prev and prev.get("itunes_count") and snap.get("itunes_count"):
        days = _days_between(prev["asof"], snap["asof"]) or 1.0
        dn = snap["itunes_count"] - prev["itunes_count"]
        cohort = implied_cohort_rating(prev.get("itunes_rating") or 0.0, prev["itunes_count"],
                                       snap.get("itunes_rating") or 0.0, snap["itunes_count"])
        out["exact_cohort"] = {
            "status": "OK", "baseline_asof": prev["asof"], "days": round(days, 1),
            "new_raters": dn, "raters_per_day": round(dn / days, 1),
            "cohort_rating": (round(cohort, 2) if cohort is not None and dn >= MIN_COHORT_N
                              else None),
            "delta_vs_lifetime": (round(cohort - (lk.get("lifetime_rating") or 0), 2)
                                  if cohort is not None and dn >= MIN_COHORT_N else None),
            "note": (None if dn >= MIN_COHORT_N else
                     f"only {dn} new raters since baseline — below MIN_COHORT_N={MIN_COHORT_N}, "
                     "cohort mean withheld as noise"),
        }
        if prev.get("play_count") and snap.get("play_count"):
            out["exact_cohort"]["play_raters_per_day"] = round(
                (snap["play_count"] - prev["play_count"]) / days, 1)
    else:
        out["exact_cohort"] = {"status": "BASELINE_ONLY",
                               "note": (f"{len(hist) + 1} snapshot(s) stored; exact cohort delta "
                                        f"needs a second ≥{MIN_SNAPSHOT_GAP_DAYS:.0f}d out — RSS "
                                        "visible cohort above is the run-1 signal")}
    return out


def run(tickers: Optional[list] = None, verbose: bool = True) -> dict:
    out = {}
    for t in (tickers or list(TRACKED)):
        out[t] = read_app(t)
        if verbose:
            v, e = out[t].get("velocity", {}), out[t].get("exact_cohort", {})
            print(f"[{t}] vel={v.get('per_day_30d', '—')}/d cohort={v.get('visible_cohort_avg', '—')} "
                  f"1star={v.get('one_star_share', '—')} exact={e.get('status')}")
        time.sleep(1.0)
    return out


# ─────────────────────────────────────────────────────────────────────────────
# Connector wrapper (dispatch-callable)
# ─────────────────────────────────────────────────────────────────────────────
class AppReviewVelocityConnector(BaseConnector):
    source_id = "app_review_velocity"
    rate_limit_per_min = 20

    def query(self, request: ConnectorRequest) -> ConnectorResult:
        ticker = (request.extra.get("ticker") or request.entity_name or "").strip()
        if not ticker:
            return self._fail(request, ErrorKind.UNSUPPORTED,
                              "need extra.ticker or entity_name")
        data = read_app(ticker.upper(),
                        query=request.extra.get("app_query", "") or request.entity_name or "",
                        seller_hint=request.extra.get("seller_hint", ""),
                        itunes_id=request.extra.get("itunes_id"),
                        play_pkg=request.extra.get("play_pkg"),
                        country=request.extra.get("country", "us"))
        obs = []
        res = data.get("resolution", {})
        obs.append(ConnectorObservation(
            attribute="app_resolution", value=res.get("status"),
            confidence=1.0 if res.get("status") == "RESOLVED" else 0.0, extra=res))
        if res.get("status") != "RESOLVED":
            return self._ok(request, obs)
        v = data.get("velocity", {})
        if v.get("status") == "OK":
            obs.append(ConnectorObservation(
                attribute="app_review_velocity", value=v["per_day_30d"],
                value_unit="reviews/day (US, trailing 30d)",
                confidence=0.9 if v.get("window_covered") else 0.6, extra=v))
            obs.append(ConnectorObservation(
                attribute="app_recent_cohort_rating", value=v["visible_cohort_avg"],
                value_unit="stars", confidence=0.8,
                extra={"n": v["visible_cohort_n"], "one_star_share": v["one_star_share"],
                       "version_release_recent": v["version_release_recent"]}))
        lk = data.get("itunes_lookup", {})
        if lk.get("status") == "OK":
            obs.append(ConnectorObservation(
                attribute="app_lifetime_rating", value=lk.get("lifetime_rating"),
                value_unit="stars", extra={"count": lk.get("lifetime_count"),
                                           "app": lk.get("trackName")}))
        ec = data.get("exact_cohort", {})
        if ec.get("status") == "OK":
            obs.append(ConnectorObservation(
                attribute="app_exact_cohort_delta", value=ec.get("delta_vs_lifetime"),
                value_unit="stars vs lifetime", confidence=0.95, extra=ec))
        pl = data.get("play", {})
        obs.append(ConnectorObservation(
            attribute="play_aggregate",
            value=pl.get("count") if pl.get("status") == "OK" else pl.get("status"),
            value_unit="lifetime raters" if pl.get("status") == "OK" else None,
            confidence=0.9 if pl.get("status") == "OK" else 0.0, extra=pl))
        return self._ok(request, obs, raw=json.dumps(data)[:2000])


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--run-tracked" in sys.argv or not args:
        result = run(args or None)
    else:
        result = {args[0]: read_app(args[0].upper(), query=" ".join(args[1:]))}
    print(json.dumps(result, indent=1, default=str))
