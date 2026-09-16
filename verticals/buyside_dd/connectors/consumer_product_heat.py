"""consumer_product_heat — brand/product TREND VELOCITY for any consumer-products issuer.

THE LANE (principal directive 2026-08-15, "for consumer products like Suja we need a trending
heatmap and reviews"): the desk's consumer connectors were sector-LOCKED — beauty_virality and
beauty_velocity_poll only fire on SIC 284x cosmeceuticals, restaurant_ratings only on SIC 58 units.
A juice/CPG issuer (SUJA) fell between them and its court ran with `beauty_virality — NOT-FIRED
(juice/soda, no virality claim at issue)`. This module generalizes the SAME plumbing to the
verification ATTRIBUTE (is consumer demand for this brand accelerating or decaying?) rather than the
birth sector — the multi_venue/FVRR lesson written into the KG dispatch contract.

WHAT IT MEASURES (3 independent channels, unioned, each degradable ALONE):
  1. SEARCH  — Google Trends weekly interest for the brand's consumer-facing search terms.
               Reuses GoogleTrendsConnector.fetch_series (the 2-step token flow) — NOT forked.
               Source label: 'google_trends_widget_json' (unofficial widget endpoints; pytrends is
               NOT installed here and hits the same wall, so the widget flow is the live path).
  2. SOCIAL  — Reddit mention velocity via the reddit_mentions/ApeWisdom plumbing. Absence from the
               attention tape is itself an observation (absence-is-observation, per that module).
  3. RETAIL  — free retail-rank proxy: Amazon category Best-Sellers (via the r.jina.ai text proxy),
               best rank held by any of the brand's SKUs in the category top-N. FRAGILE by nature
               (proxy + static parse) — always labelled, never silently zero.

OUTPUT per brand: the search time series, an ACCELERATION flag (RISING / FLAT / DECAYING, recent
28d vs the trailing 90d baseline) and a 0-100 HEAT SCORE. The score renormalizes over the channels
that actually answered: a missing channel LOWERS CONFIDENCE, it never imputes a zero (the
no-zero-imputation invariant the forest/satellite connectors already carry).

DIRECTION > LEVEL. A brand can be small and accelerating (the interesting case) or huge and
decaying (the SUJA question). The heat score is a velocity read, not a size read.

RATE BUDGET (this is a scheduled watch — respect it): Google Trends ~6 req/min and hard-429s on a
cloud IP; Amazon best-sellers via r.jina.ai is ~5-8s/page. One bounded pass over the tracked list
per day is the design point. Nothing here is a per-tick poller.
"""

from __future__ import annotations

# Knowledge-graph dispatch contract (see knowledge_graph/dispatch.py).
# Keyed on the verification ATTRIBUTE (consumer-brand demand trajectory), not the birth sector:
# food/bev (20x), cosmetics/pharma-adjacent (28x), rubber/footwear (30/31), wholesale (51),
# food retail (54), apparel retail (56), misc retail incl. DTC (59).
APPLIES_TO = {
    "kind": 'm_source',
    "sic_codes": [],
    "sic_prefixes": ['20', '208', '209', '28', '284', '30', '31', '51', '54', '56', '59'],
    "issuer_features": ['consumer_brand', 'cpg_product', 'dtc_brand', 'consumer_virality_claim'],
    "asset_classes": ['public_equity', 'corporate_ipo_dd'],
    "applies_universally": False,
    "summary": 'Consumer brand/product trend velocity: search + social + retail-rank -> acceleration flag + 0-100 heat score.',
    "verification_question": "Is real-world demand for this issuer's consumer brands accelerating, flat, or decaying vs its own trailing 90 days?",
}

import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

HERE = Path(__file__).resolve()
if str(HERE.parents[3]) not in sys.path:
    sys.path.insert(0, str(HERE.parents[3]))  # signalos repo root

from .base import (BaseConnector, ConnectorObservation, ConnectorRequest,
                   ConnectorResult, ErrorKind)

OUT_DIR = HERE.parents[1] / "outputs" / "consumer_heat"
HEAT_JSON = OUT_DIR / "CONSUMER_HEAT.json"
TREND_LOG = OUT_DIR / "trend_history.jsonl"

_JINA = "https://r.jina.ai/"
_UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")

# ── the tracked consumer lane ────────────────────────────────────────────────────────────────
# ticker -> brands (search terms, first = primary), amazon best-seller category, retail search term.
# `control` marks names carried deliberately as controls (killed / luxury) so the heatmap can be
# read against something. Extend as the book adds consumer names; unknown tickers fall back to
# beauty_virality's registries (reuse, never a second brand map).
TRACKED: dict[str, dict] = {
    "SUJA": {"name": "Suja Life", "brands": ["Suja", "Suja juice", "Slice soda", "Vive Organic", "wellness shots"],
             "brand_tokens": ["suja", "vive organic"], "amazon_cat": "grocery", "retail_q": "suja", "sic": "2033",
             "note": "IPO 2026; core Suja juice + Emerging Brands (Slice healthy soda) launch"},
    "NATR": {"name": "Nature's Sunshine", "brands": ["Nature's Sunshine"],
             "brand_tokens": ["nature's sunshine", "natures sunshine"],
             "amazon_cat": "hpc", "retail_q": "natures sunshine", "sic": "2833"},
    "BKE":  {"name": "The Buckle", "brands": ["Buckle jeans", "BKE jeans"],
             "brand_tokens": ["buckle"], "amazon_cat": None, "retail_q": None, "sic": "5651",
             "note": "specialty retailer — its OWN SKUs are not on other retailers' shelves; review channel N/A by design"},
    "OLLI": {"name": "Ollie's Bargain Outlet", "brands": ["Ollie's Bargain Outlet"],
             "amazon_cat": None, "retail_q": None, "sic": "5331"},
    "COLM": {"name": "Columbia Sportswear", "brands": ["Columbia jacket", "Columbia Sportswear"],
             "brand_tokens": ["columbia"], "amazon_cat": "fashion", "retail_q": "columbia sportswear", "sic": "2300"},
    "ULTA": {"name": "Ulta Beauty", "brands": ["Ulta"], "amazon_cat": "beauty",
             "retail_q": None, "sic": "5912"},
    "FIZZ": {"name": "National Beverage (LaCroix)", "brands": ["LaCroix", "Shasta soda"],
             "brand_tokens": ["lacroix", "shasta"], "amazon_cat": "grocery", "retail_q": "lacroix", "sic": "2086"},
    "DPZ":  {"name": "Domino's Pizza", "brands": ["Dominos"], "amazon_cat": None,
             "retail_q": None, "sic": "5812"},
    "CMG":  {"name": "Chipotle", "brands": ["Chipotle"], "amazon_cat": None,
             "retail_q": None, "sic": "5812"},
    "NKE":  {"name": "Nike", "brands": ["Nike"], "brand_tokens": ["nike"], "amazon_cat": "fashion",
             "retail_q": "nike", "sic": "3021"},
    "LWAY": {"name": "Lifeway Foods", "brands": ["Lifeway kefir", "kefir"],
             "brand_tokens": ["lifeway"], "amazon_cat": "grocery", "retail_q": "lifeway kefir", "sic": "2026",
             "note": "courted 8/12"},
    "PLAY": {"name": "Dave & Buster's", "brands": ["Dave and Busters"], "amazon_cat": None,
             "retail_q": None, "sic": "5812", "control": "killed — negative control"},
    "BRBY": {"name": "Burberry", "brands": ["Burberry"], "brand_tokens": ["burberry"],
             "amazon_cat": "fashion", "retail_q": "burberry", "sic": "2300", "yf": "BRBY.L",
             "control": "luxury control (held)"},
}
# CPRT (Copart) is deliberately NOT in the lane: salvage-auto auctions are not a consumer brand —
# a heat read there would be a category error, so the lane refuses it rather than scoring noise.
EXCLUDED = {"CPRT": "not a consumer brand (salvage vehicle auctions) — out of lane by design"}

# generic product nouns that must NEVER become brand-match tokens (they'd match a competitor's SKU —
# the entity-resolution lesson: resolve the SUBJECT before you trust the hit).
_GENERIC_TOKENS = {"juice", "soda", "kefir", "jeans", "jacket", "shots", "drink", "water",
                   "beauty", "pizza", "sportswear", "life", "foods", "brands", "organic"}


def brand_tokens(ticker: str) -> list[str]:
    """Distinctive lowercase tokens that a SKU title must carry to count as THIS brand's.
    Explicit `brand_tokens` in TRACKED wins; otherwise derive from the brand strings, dropping
    generic product nouns."""
    ent = TRACKED.get(ticker.upper(), {})
    if ent.get("brand_tokens"):
        return [t.lower() for t in ent["brand_tokens"]]
    toks = []
    for b in ent.get("brands") or [ticker]:
        for w in re.split(r"[^A-Za-z0-9']+", b):
            w = w.lower().strip("'")
            if len(w) >= 4 and w not in _GENERIC_TOKENS and w not in toks:
                toks.append(w)
    return toks or [ticker.lower()]


# Amazon Best-Sellers category slugs actually reachable through the text proxy.
_AMZ_CAT_URL = {
    "grocery": "https://www.amazon.com/Best-Sellers-Grocery-Gourmet-Food/zgbs/grocery",
    "beauty": "https://www.amazon.com/Best-Sellers-Beauty/zgbs/beauty",
    "hpc": "https://www.amazon.com/Best-Sellers-Health-Personal-Care/zgbs/hpc",
    "fashion": "https://www.amazon.com/Best-Sellers-Clothing-Shoes-Jewelry/zgbs/fashion",
}

# ── channel weights (union of narrow reads; renormalized over the channels that ANSWERED) ──
CHANNEL_WEIGHT = {"search": 0.55, "social": 0.20, "retail": 0.25}
RISING_RATIO, DECAYING_RATIO = 1.12, 0.88   # recent-28d vs trailing-90d baseline
RECENT_WEEKS, BASELINE_WEEKS = 4, 13        # ~28d recent, ~90d trailing baseline


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


# ── pure scoring math (offline-testable; no network below this line) ────────────────────────
def trend_stats(points: list[dict], recent_weeks: int = RECENT_WEEKS,
                baseline_weeks: int = BASELINE_WEEKS) -> dict:
    """Acceleration read on a Google-Trends-shaped series.

    points: [{'value': int, 'date': str}, ...] oldest-first.
    Returns recent_avg, baseline_avg (the window BEFORE the recent one), ratio, direction,
    slope_pct_per_week over the recent window, peak, and last-vs-peak.
    Honest on short series: fewer than recent+2 points -> direction INSUFFICIENT_HISTORY.
    """
    vals = [float(p.get("value") or 0) for p in (points or [])]
    n = len(vals)
    out: dict[str, Any] = {"n_points": n, "recent_avg": None, "baseline_avg": None,
                           "ratio": None, "direction": "NO_DATA", "slope_pct_per_week": None,
                           "peak": max(vals) if vals else None,
                           "last_vs_peak": None}
    if n == 0:
        return out
    out["last_vs_peak"] = round(vals[-1] / max(vals), 3) if max(vals) > 0 else None
    # SEASONAL CONTROL. The recent-vs-trailing-90d read is calendar-confounded: run the whole lane
    # in August and every seasonal brand (jackets, back-to-school, summer beverages) prints DECAYING
    # off a peak-summer baseline. On a 12-month weekly series the FIRST points are ~the same weeks
    # one year ago, so recent-4w vs first-4w is a like-for-like YoY read on the same 0-100 scale.
    # The year-ago window is anchored on the point TIMESTAMPS, never on "the start of the series":
    # on a 5-year request the first points are 2021, and comparing to those would silently print a
    # 5-year change under a YoY label. With no timestamps we fall back to the 12m weekly assumption.
    ts = [p.get("ts") for p in (points or [])]
    yr_win = None
    if all(isinstance(t, int) and t > 0 for t in ts) and len(ts) >= recent_weeks + 4:
        span_days = (ts[-1] - ts[0]) / 86400.0
        if span_days >= 350:
            target = ts[-1] - 365 * 86400
            i = min(range(len(ts)), key=lambda k: abs(ts[k] - target))
            # window ENDING at the anchor when there is history before it, else the window STARTING
            # there (an exactly-12-month series has the anchor at index 0 and nothing before it)
            yr_win = (vals[i - recent_weeks + 1:i + 1] if i >= recent_weeks - 1
                      else vals[i:i + recent_weeks])
            out["yoy_anchor"] = (points[i] or {}).get("date") or ts[i]
    elif n >= 48:                      # 12-month weekly series with no usable timestamps
        yr_win = vals[:recent_weeks]
        out["yoy_anchor"] = "series start (~52w back, assumed weekly)"
    if yr_win:
        yr = sum(yr_win) / len(yr_win)
        rc = sum(vals[-recent_weeks:]) / recent_weeks
        out["yoy_base"] = round(yr, 1)
        out["yoy_ratio"] = round(rc / yr, 3) if yr > 0 else None
        if out["yoy_ratio"] is not None:
            out["yoy_direction"] = ("RISING" if out["yoy_ratio"] >= RISING_RATIO
                                    else "DECAYING" if out["yoy_ratio"] <= DECAYING_RATIO else "FLAT")
        out["yoy_note"] = ("recent window vs the same calendar window one year earlier (same series, "
                           "same scale) — the seasonally-controlled read; prefer it over `direction` "
                           "when the whole cohort moves together")
    if n < recent_weeks + 2:
        out["direction"] = "INSUFFICIENT_HISTORY"
        out["recent_avg"] = round(sum(vals) / n, 1)
        return out
    recent = vals[-recent_weeks:]
    base = vals[-(recent_weeks + baseline_weeks):-recent_weeks] or vals[:-recent_weeks]
    r = sum(recent) / len(recent)
    b = sum(base) / len(base)
    out["recent_avg"] = round(r, 1)
    out["baseline_avg"] = round(b, 1)
    if b > 0:
        ratio = r / b
        out["ratio"] = round(ratio, 3)
        out["direction"] = ("RISING" if ratio >= RISING_RATIO
                            else "DECAYING" if ratio <= DECAYING_RATIO else "FLAT")
    else:
        out["direction"] = "BASELINE_ZERO"
    # least-squares slope across the recent window, as % of the recent mean per week
    k = len(recent)
    xs = list(range(k))
    mx, my = sum(xs) / k, r
    denom = sum((x - mx) ** 2 for x in xs)
    if denom > 0 and r > 0:
        slope = sum((x - mx) * (y - my) for x, y in zip(xs, recent)) / denom
        out["slope_pct_per_week"] = round(100.0 * slope / r, 1)
    return out


def _clamp(x: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, x))


def _search_component(ts: dict) -> Optional[float]:
    """0-100 from the trend ratio, log-SYMMETRIC around 1.00 -> 50 (a doubling of search interest
    vs the trailing baseline ~= 95; a halving ~= 5). Symmetry matters: decay must be as legible as
    heat, or the heatmap only ever finds winners."""
    ratio = ts.get("ratio")
    if not ratio or ratio <= 0:
        return None
    import math
    return _clamp(50.0 + 45.0 * math.log(ratio) / math.log(2.0))


def _social_component(soc: dict) -> Optional[float]:
    """Reddit velocity (mentions vs 24h ago). ABSENT-FROM-TOP is a real read = 35 (quiet, not zero)."""
    if not soc:
        return None
    if soc.get("state") == "ABSENT":
        return 35.0
    v = soc.get("velocity")
    if v in (None, ""):
        return None
    try:
        v = float(v)
    except (TypeError, ValueError):
        return None
    import math
    if v <= 0:
        return 20.0
    return _clamp(50.0 + 45.0 * math.log(v) / math.log(3.0))


def _retail_component(ret: dict) -> Optional[float]:
    """Best Amazon category rank held by the brand: #1 -> 100, #100 -> ~25, absent -> 20 (present
    in the category page but unranked is different from 'we could not fetch' = None)."""
    if not ret or ret.get("status") != "OK":
        return None
    best = ret.get("best_rank")
    if best is None:
        return 20.0
    import math
    return _clamp(100.0 - 37.0 * math.log(max(1, int(best))) / math.log(10.0))


def heat_score(search_stats: Optional[dict], social: Optional[dict],
               retail: Optional[dict]) -> dict:
    """Union the channels that answered; renormalize weights over them. NEVER impute a missing
    channel as zero — a missing channel reduces `confidence` and is named in `degraded`."""
    comps = {"search": _search_component(search_stats or {}),
             "social": _social_component(social or {}),
             "retail": _retail_component(retail or {})}
    live = {k: v for k, v in comps.items() if v is not None}
    degraded = sorted(k for k, v in comps.items() if v is None)
    if not live:
        return {"score": None, "components": comps, "degraded": degraded, "confidence": 0.0,
                "note": "ALL CHANNELS DEGRADED — no heat read (not a zero score)"}
    wsum = sum(CHANNEL_WEIGHT[k] for k in live)
    score = sum(CHANNEL_WEIGHT[k] * v for k, v in live.items()) / wsum
    return {"score": round(score, 1), "components": {k: (round(v, 1) if v is not None else None)
                                                     for k, v in comps.items()},
            "degraded": degraded, "confidence": round(wsum, 2),
            "note": ("full-channel read" if not degraded
                     else "DEGRADED: " + ",".join(degraded) + " unavailable; score renormalized over the rest")}


# ── live channels ────────────────────────────────────────────────────────────────────────────
def search_trend(term: str, timeframe: str = "today 12-m", geo: str = "US") -> dict:
    """Google Trends weekly interest via the shared GoogleTrendsConnector flow (NOT forked)."""
    from .google_trends import GoogleTrendsConnector
    res = GoogleTrendsConnector().fetch_series(term, geo=geo, timeframe=timeframe)
    res["source"] = res.get("source", "google_trends_widget_json")
    res["source_label"] = ("google_trends (unofficial widget JSON endpoints; pytrends not installed)"
                           if res.get("status") == "OK" else
                           f"google_trends UNAVAILABLE [{res.get('status')}]: {res.get('note','')}")
    return res


def reddit_velocity(ticker: str) -> dict:
    """Reddit mention velocity through the existing reddit_mentions plumbing."""
    try:
        from .reddit_mentions import RedditMentionsConnector
        res = RedditMentionsConnector().query(ConnectorRequest(extra={"ticker": ticker, "pages": 2}))
    except Exception as e:                                   # degraded-loud, never silent
        return {"state": "ERROR", "note": f"reddit_mentions unavailable: {str(e)[:120]}"}
    if not res.success:
        return {"state": "ERROR", "note": res.error_detail}
    for o in res.observations:
        if o.attribute == "reddit_attention":
            return {"state": "ABSENT", "note": "not in the ApeWisdom top pages — low retail attention"}
        if o.attribute == "reddit_mentions":
            return {"state": "OK", "mentions": o.value, "mentions_24h_ago": o.extra.get("mentions_24h_ago"),
                    "velocity": o.extra.get("velocity"), "spike": o.extra.get("spike"),
                    "source": "apewisdom (via reddit_mentions)"}
    return {"state": "ERROR", "note": "no observation returned"}


_AMZ_ROW = re.compile(r"#(\d+)\s+\[!\[Image[^\]]*\]\([^)]*\)\]\([^)]*\)\[([^\]]{6,300})\]")


def amazon_rank_proxy(tokens: list[str], category: Optional[str],
                      timeout: float = 90.0) -> dict:
    """FREE retail-rank proxy: does any SKU carrying the brand hold a top-N Best-Sellers slot?

    Fetches the Amazon category Best-Sellers page through the r.jina.ai text proxy (Amazon hard-
    blocks direct datacenter GETs; the proxy returns a rendered-markdown snapshot). FRAGILE:
    proxy-cached, top-50 only, brand matched on title tokens. Labelled accordingly — a parse that
    finds nothing returns best_rank=None with status OK (absence IS the observation), while a
    fetch that fails returns status != OK so the score renormalizes it away.
    """
    if not category:
        return {"status": "NOT_APPLICABLE", "note": "no Amazon category mapped for this brand"}
    url = _AMZ_CAT_URL.get(category)
    if not url:
        return {"status": "NOT_APPLICABLE", "note": f"unknown category {category}"}
    import requests
    try:
        r = requests.get(_JINA + url, timeout=timeout)
    except Exception as e:
        return {"status": "FETCH_ERROR", "note": f"r.jina.ai: {str(e)[:120]}", "url": url}
    if r.status_code != 200:
        return {"status": f"HTTP_{r.status_code}", "note": "proxy/upstream blocked", "url": url}
    rows = []
    for rank, title in _AMZ_ROW.findall(r.text):
        rows.append((int(rank), re.sub(r"\s+", " ", title).strip()))
    if not rows:
        return {"status": "EMPTY_PARSE", "note": "best-seller rows not in the proxy snapshot",
                "url": url}
    toks = [t.lower() for t in tokens if t]
    hits = [{"rank": rk, "title": ti[:110]} for rk, ti in rows
            if any(tok in ti.lower() for tok in toks)]
    return {"status": "OK", "n_ranked_seen": len(rows), "best_rank": (min(h["rank"] for h in hits)
                                                                     if hits else None),
            "hits": hits[:5], "category": category, "url": url,
            "source": "amazon_best_sellers via r.jina.ai text proxy (FRAGILE, top-50, cached)"}


# ── store (MERGE, never clobber — the shared-store lesson) ───────────────────────────────────
def merge_heat_store(block_key: str, rows: dict, meta: Optional[dict] = None) -> Path:
    """Merge a per-ticker block into CONSUMER_HEAT.json. `block_key` is 'heat' or 'reviews'.
    Reads-modifies-writes so the two connectors never clobber each other's half."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    doc: dict = {}
    if HEAT_JSON.exists():
        try:
            doc = json.loads(HEAT_JSON.read_text())
        except Exception:
            doc = {}
    doc.setdefault("tickers", {})
    for tk, row in rows.items():
        doc["tickers"].setdefault(tk, {})[block_key] = row
    doc.setdefault("meta", {})[block_key] = {"asof": _now(), **(meta or {})}
    doc["asof"] = _now()
    HEAT_JSON.write_text(json.dumps(doc, indent=1, default=str))
    return HEAT_JSON


def _brands_for(ticker: str) -> dict:
    """Tracked-lane entry, else fall back to beauty_virality's registries (single brand map)."""
    tk = ticker.upper()
    if tk in TRACKED:
        return {"ticker": tk, **TRACKED[tk]}
    try:
        from .beauty_virality import BRAND_TO_VEHICLE, CONSUMER_BRAND_TO_VEHICLE
        for brand, v in {**CONSUMER_BRAND_TO_VEHICLE, **BRAND_TO_VEHICLE}.items():
            if (v.get("ticker") or "").upper() == tk:
                return {"ticker": tk, "name": v.get("name") or brand, "brands": [brand],
                        "amazon_cat": None, "retail_q": brand,
                        "note": "resolved from beauty_virality registry (no tracked-lane entry)"}
    except Exception:
        pass
    return {"ticker": tk, "name": tk, "brands": [tk], "amazon_cat": None, "retail_q": None,
            "note": "UNRESOLVED brand — ticker used as the search term (weak; add a TRACKED entry)"}


def read_brand(ticker: str, *, timeframe: str = "today 12-m", with_retail: bool = True,
               with_social: bool = True) -> dict:
    """One bounded heat read for one ticker: search + social + retail -> stats + heat score."""
    ent = _brands_for(ticker)
    if ticker.upper() in EXCLUDED:
        return {"ticker": ticker.upper(), "status": "OUT_OF_LANE", "note": EXCLUDED[ticker.upper()]}
    primary = (ent.get("brands") or [ticker])[0]
    series = search_trend(primary, timeframe=timeframe)
    stats = trend_stats(series.get("points") or [])
    social = reddit_velocity(ticker) if with_social else {"state": "SKIPPED"}
    retail = (amazon_rank_proxy(brand_tokens(ticker), ent.get("amazon_cat"))
              if with_retail else {"status": "SKIPPED"})
    hs = heat_score(stats, social, retail)
    row = {"ticker": ticker.upper(), "name": ent.get("name"), "brand_term": primary,
           "brands": ent.get("brands"), "control": ent.get("control"),
           "asof": _now(),
           "search": {"status": series.get("status"), "source": series.get("source_label"),
                      "timeframe": timeframe, **stats,
                      "series": [{"d": p.get("date"), "v": p.get("value")}
                                 for p in (series.get("points") or [])][-60:]},
           "social": social, "retail": retail,
           "heat_score": hs["score"], "heat_detail": hs,
           "direction": stats.get("direction")}
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(TREND_LOG, "a") as f:                       # append-only history for future deltas
        f.write(json.dumps({"asof": row["asof"], "ticker": row["ticker"],
                            "recent_avg": stats.get("recent_avg"), "ratio": stats.get("ratio"),
                            "direction": stats.get("direction"),
                            "yoy_ratio": stats.get("yoy_ratio"),
                            "heat": hs["score"]}) + "\n")
    return row


def run(tickers: Optional[list] = None, *, timeframe: str = "today 12-m",
        with_retail: bool = True, pause_s: float = 2.0, verbose: bool = True) -> dict:
    """Bounded pass over the lane. Writes the `heat` block of CONSUMER_HEAT.json."""
    tickers = [t.upper() for t in (tickers or list(TRACKED))]
    rows, degraded = {}, []
    for i, tk in enumerate(tickers):
        row = read_brand(tk, timeframe=timeframe, with_retail=with_retail)
        rows[tk] = row
        if row.get("heat_detail", {}).get("degraded"):
            degraded.append(f"{tk}:{'/'.join(row['heat_detail']['degraded'])}")
        if verbose:
            hd = row.get("heat_score")
            print(f"  {tk:6} {str(row.get('direction')):20} heat={hd if hd is not None else 'DEGRADED':>6} "
                  f"conf={row.get('heat_detail',{}).get('confidence')}  {row.get('name','')}")
        if i < len(tickers) - 1:
            time.sleep(pause_s)  # rate budget: Trends 429s fast
    p = merge_heat_store("heat", rows, {"n": len(rows), "timeframe": timeframe,
                                        "degraded": degraded,
                                        "channels": "google_trends + reddit(apewisdom) + amazon_bestsellers(r.jina.ai)"})
    if verbose:
        print(f"[consumer_product_heat] {len(rows)} brands -> {p}")
        if degraded:
            print(f"  DEGRADED (loud): {', '.join(degraded)}")
    return {"asof": _now(), "n": len(rows), "rows": rows, "degraded": degraded, "out": str(p)}


# ── uniform connector wrapper (dispatchable) ────────────────────────────────────────────────
class ConsumerProductHeatConnector(BaseConnector):
    source_id = "consumer_product_heat"
    rate_limit_per_min = 6          # Trends is the binding constraint

    def query(self, request: ConnectorRequest) -> ConnectorResult:
        x = request.extra or {}
        ticker = str(x.get("ticker") or request.entity_name or "").upper()
        if not ticker:
            return self._fail(request, ErrorKind.UNSUPPORTED,
                              "consumer_product_heat needs a TICKER (extra.ticker or entity_name)")
        if ticker in EXCLUDED:
            return self._fail(request, ErrorKind.UNSUPPORTED, EXCLUDED[ticker])
        row = read_brand(ticker, timeframe=x.get("timeframe", "today 12-m"),
                         with_retail=bool(x.get("with_retail", True)),
                         with_social=bool(x.get("with_social", True)))
        obs = [
            ConnectorObservation(attribute="consumer_trend_direction",
                                 value=row["search"].get("direction"),
                                 confidence=0.8 if row["search"].get("status") == "OK" else 0.3,
                                 extra={"ratio": row["search"].get("ratio"),
                                        "recent_avg": row["search"].get("recent_avg"),
                                        "baseline_avg": row["search"].get("baseline_avg"),
                                        "slope_pct_per_week": row["search"].get("slope_pct_per_week"),
                                        "yoy_ratio": row["search"].get("yoy_ratio"),
                                        "yoy_direction": row["search"].get("yoy_direction"),
                                        "source": row["search"].get("source"),
                                        "brand_term": row.get("brand_term")}),
            ConnectorObservation(attribute="consumer_heat_score", value=row.get("heat_score"),
                                 value_unit="0-100", confidence=row["heat_detail"]["confidence"],
                                 extra=row["heat_detail"]),
            ConnectorObservation(attribute="consumer_retail_rank",
                                 value=(row["retail"] or {}).get("best_rank"),
                                 confidence=0.5, extra=row.get("retail")),
            ConnectorObservation(attribute="consumer_social_velocity",
                                 value=(row["social"] or {}).get("velocity"),
                                 confidence=0.6, extra=row.get("social")),
        ]
        return self._ok(request, obs, raw=json.dumps({k: row[k] for k in ("ticker", "brand_term",
                                                                          "heat_score")}))


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    print(f"=== consumer_product_heat — trend velocity lane {_now()} ===")
    run(args or None, with_retail="--no-retail" not in sys.argv)
