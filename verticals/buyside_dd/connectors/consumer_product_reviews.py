"""consumer_product_reviews — REVIEW TRAJECTORY for a consumer brand's top products.

Sibling of consumer_product_heat in the consumer-products lane (principal directive 2026-08-15).
Heat answers "is attention accelerating?"; this answers "is the PRODUCT still landing with the
people who actually bought it?" — the channel that catches a brand whose search is fine while the
repeat-buyer experience rots (formulation change, shrinkflation, supply substitution).

THE SIGNAL IS DIRECTION AND VELOCITY, NOT ABSOLUTE STARS. A 4.6 lifetime average tells you almost
nothing (retail review distributions are all clustered 4.2-4.8); what discriminates is:
  (a) REVIEW VELOCITY — reviews/month, i.e. the rate new buyers are arriving, and its change;
  (b) RECENT-COHORT RATING minus LIFETIME RATING — the beauty_velocity insight, carried over: the
      cohort delta LEADS the aggregate by many months because the lifetime mean is a slow-moving
      denominator that buries a fresh cohort of 2-star reviews.

Two independent ways of getting the cohort delta, both implemented:
  1. EXACT (needs 2 snapshots) — from consecutive stored snapshots of (lifetime_rating, n_reviews):
         cohort_avg = (R1*N1 - R0*N0) / (N1 - N0)
     This is arithmetic, not estimation: it is the exact mean of the reviews added in between.
     First run on a product therefore establishes a BASELINE and says so LOUDLY — it does not
     pretend to a delta it cannot have.
  2. VISIBLE-COHORT (available on run 1) — the dated reviews the product page exposes; low-N and
     retailer-ordered (not a random sample), so it is reported as a weak corroborator only.

SOURCES / REACHABILITY (probed from this egress 2026-08-15 — read before trusting output):
  - Walmart via the r.jina.ai text proxy: WORKS. Search pages give per-SKU rating + review count;
    product pages give lifetime rating, ratings/reviews counts, the star histogram and ~3 dated
    reviews. The /reviews/product/<id> deep page hits Walmart's "Robot or human?" wall.
  - Amazon: direct GET = bot shell; /s search through the proxy = image-only stub; product pages
    are inconsistent through the proxy. Attempted, then labelled DEGRADED — never silently dropped.
  - Target / Trustpilot / Influenster: 403 (Cloudflare / Akamai). Not used.
  So the standing free channel is WALMART, and the honest output names the retailer it came from.
  FRAGILE by construction: proxy-mediated markdown parsing breaks when a retailer reskins. Every
  failure surfaces as a status string in the output, never as a missing/zero metric.
"""

from __future__ import annotations

# Same dispatch key as consumer_product_heat — keyed on the verification attribute (consumer demand
# / product-reception trajectory), NOT the birth sector.
APPLIES_TO = {
    "kind": 'm_source',
    "sic_codes": [],
    "sic_prefixes": ['20', '208', '209', '28', '284', '30', '31', '51', '54', '56', '59'],
    "issuer_features": ['consumer_brand', 'cpg_product', 'dtc_brand', 'consumer_virality_claim'],
    "asset_classes": ['public_equity', 'corporate_ipo_dd'],
    "applies_universally": False,
    "summary": 'Review trajectory for a consumer brand: reviews/month velocity + recent-cohort vs lifetime rating delta.',
    "verification_question": "Are the people actually buying this brand rating it better or worse than its lifetime average, and are they arriving faster or slower?",
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
    sys.path.insert(0, str(HERE.parents[3]))

from .base import (BaseConnector, ConnectorObservation, ConnectorRequest,
                   ConnectorResult, ErrorKind)
from .consumer_product_heat import (EXCLUDED, OUT_DIR, TRACKED, _brands_for, brand_tokens,
                                    merge_heat_store)

SNAPSHOTS = OUT_DIR / "review_snapshots.jsonl"
_JINA = "https://r.jina.ai/"

# cohort-delta thresholds (stars). Retail rating distributions are tight, so 0.15 is material.
DELTA_IMPROVING, DELTA_DETERIORATING = 0.15, -0.15
MIN_COHORT_N = 5          # below this the cohort mean is noise
MIN_SNAPSHOT_GAP_DAYS = 3.0  # two snapshots hours apart measure nothing — refuse to call it velocity
VISIBLE_WINDOW_DAYS = 180  # a page-visible review older than this is NOT part of a "recent" cohort
_MONTH_DAYS = 30.4375


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def _iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _num(s: str) -> Optional[float]:
    try:
        return float(str(s).replace(",", "").strip())
    except (TypeError, ValueError):
        return None


# ── pure math (offline-testable; no network) ────────────────────────────────────────────────
def implied_cohort_rating(prev_rating: float, prev_n: int,
                          cur_rating: float, cur_n: int) -> Optional[float]:
    """EXACT mean of the reviews added between two snapshots: (R1*N1 - R0*N0)/(N1 - N0).

    Returns None when no reviews were added (or the count went backwards — retailers do purge
    reviews; that is a data event, not a rating signal, so we refuse to compute rather than
    emit a nonsense number).
    """
    if None in (prev_rating, prev_n, cur_rating, cur_n):
        return None
    dn = cur_n - prev_n
    if dn <= 0:
        return None
    val = (cur_rating * cur_n - prev_rating * prev_n) / dn
    if val < 0.5 or val > 5.5:      # displayed ratings are rounded to 0.1 -> tiny dn explodes
        return None
    return round(val, 2)


def reviews_per_month(prev_n: int, cur_n: int, days: float) -> Optional[float]:
    if None in (prev_n, cur_n) or not days or days <= 0:
        return None
    dn = cur_n - prev_n
    if dn < 0:
        return None
    return round(dn / days * _MONTH_DAYS, 2)


def trajectory_flag(cohort_avg: Optional[float], lifetime: Optional[float],
                    cohort_n: Optional[int] = None) -> dict:
    """DIRECTION read. Returns {flag, delta, note}. Never invents a flag it cannot support."""
    if cohort_avg is None or lifetime is None:
        return {"flag": "NO_COHORT", "delta": None,
                "note": "needs a second snapshot (or dated reviews) — baseline only"}
    delta = round(cohort_avg - lifetime, 2)
    if cohort_n is not None and cohort_n < MIN_COHORT_N:
        return {"flag": "LOW_N", "delta": delta, "cohort_n": cohort_n,
                "note": f"only {cohort_n} new reviews — below the {MIN_COHORT_N} floor, direction not claimed"}
    flag = ("IMPROVING" if delta >= DELTA_IMPROVING
            else "DETERIORATING" if delta <= DELTA_DETERIORATING else "STABLE")
    return {"flag": flag, "delta": delta, "cohort_n": cohort_n,
            "note": "recent-cohort mean vs lifetime mean (the leading indicator)"}


def aggregate_products(products: list[dict]) -> dict:
    """Roll per-SKU reads up to a brand read, review-count-weighted (a 3-review SKU must not
    outvote a 2,670-review SKU)."""
    live = [p for p in products if p.get("lifetime_rating") is not None]
    if not live:
        return {"n_products": len(products), "lifetime_rating_wavg": None,
                "total_reviews": None, "note": "no product carried a rating"}
    wn = sum((p.get("n_reviews") or 0) for p in live) or len(live)
    life = sum((p["lifetime_rating"] * (p.get("n_reviews") or 1)) for p in live) / \
           (sum((p.get("n_reviews") or 1) for p in live))
    coh = [p for p in live if p.get("cohort_rating") is not None]
    cw = sum((p.get("cohort_n") or 0) for p in coh)
    cohort = (sum(p["cohort_rating"] * (p.get("cohort_n") or 1) for p in coh) /
              (sum((p.get("cohort_n") or 1) for p in coh))) if coh else None
    vel = [p.get("reviews_per_month") for p in live if p.get("reviews_per_month") is not None]
    return {"n_products": len(products), "n_with_rating": len(live),
            "lifetime_rating_wavg": round(life, 2), "total_reviews": wn,
            "cohort_rating_wavg": (round(cohort, 2) if cohort is not None else None),
            "cohort_n": cw or None,
            "reviews_per_month": (round(sum(vel), 2) if vel else None),
            "n_products_with_cohort": len(coh)}


# ── snapshot store (append-only; the second snapshot is what makes the delta exact) ──────────
def _load_snapshots() -> dict:
    """{(ticker, source, pid): [rows oldest-first]}"""
    out: dict[tuple, list] = {}
    if not SNAPSHOTS.exists():
        return out
    for line in SNAPSHOTS.read_text().splitlines():
        if not line.strip():
            continue
        try:
            r = json.loads(line)
        except Exception:
            continue
        out.setdefault((r.get("ticker"), r.get("source"), r.get("pid")), []).append(r)
    for v in out.values():
        v.sort(key=lambda r: r.get("asof", ""))
    return out


def _append_snapshots(rows: list[dict]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(SNAPSHOTS, "a") as f:
        for r in rows:
            f.write(json.dumps(r, default=str) + "\n")


def _days_between(a: str, b: str) -> Optional[float]:
    try:
        da = datetime.fromisoformat(a.replace("Z", "+00:00"))
        db = datetime.fromisoformat(b.replace("Z", "+00:00"))
        return abs((db - da).total_seconds()) / 86400.0
    except Exception:
        return None


# ── Walmart (the working free channel) ──────────────────────────────────────────────────────
_WM_ITEM = re.compile(r"###\s+\[([^\]]{4,200})\]\((https://www\.walmart\.com/ip/[^)\s]+)\)")
_WM_RATING = re.compile(r"([\d.]+)\s+out of 5 Stars\.\s+([\d,]+)\s+reviews")
_WM_PID = re.compile(r"/ip/[^/]+/(\d+)")


def walmart_search(query: str, timeout: float = 90.0, limit: int = 12,
                   tokens: Optional[list] = None) -> dict:
    """Brand SKU list with lifetime rating + review count, via the r.jina.ai text proxy.

    `tokens` is the brand-identity gate: retailer search pages are full of sponsored/related SKUs
    from OTHER brands (a 'suja' search returns Pomona juices), and scoring those would be a pure
    entity-resolution error. Titles that carry no brand token are DROPPED and counted, not silently
    mixed in.
    """
    import requests
    url = f"https://www.walmart.com/search?q={requests.utils.quote(query)}"
    try:
        r = requests.get(_JINA + url, timeout=timeout)
    except Exception as e:
        return {"status": "FETCH_ERROR", "note": f"r.jina.ai: {str(e)[:120]}", "url": url,
                "products": []}
    if r.status_code != 200:
        return {"status": f"HTTP_{r.status_code}", "note": "proxy/upstream blocked", "url": url,
                "products": []}
    txt = r.text
    if "Robot or human" in txt[:400]:
        return {"status": "BOT_WALL", "note": "Walmart bot interstitial through the proxy",
                "url": url, "products": []}
    # split the markdown into per-product blocks anchored on the ### [title](ip-url) header
    marks = [(m.start(), m.group(1), m.group(2)) for m in _WM_ITEM.finditer(txt)]
    products = []
    for i, (pos, title, purl) in enumerate(marks):
        end = marks[i + 1][0] if i + 1 < len(marks) else len(txt)
        blk = txt[pos:end]
        rm = _WM_RATING.search(blk)
        pid = (_WM_PID.search(purl) or [None, None])[1] if _WM_PID.search(purl) else None
        products.append({"pid": pid, "title": re.sub(r"\s+", " ", title).strip()[:120],
                         "url": purl.split("?")[0],
                         "lifetime_rating": _num(rm.group(1)) if rm else None,
                         "n_reviews": int(_num(rm.group(2))) if rm else None})
    # brand-identity gate (see docstring)
    toks = [t.lower() for t in (tokens or []) if t]
    n_seen = len(products)
    if toks:
        products = [p for p in products if any(t in p["title"].lower() for t in toks)]
    n_dropped = n_seen - len(products)
    # dedupe by pid, keep the highest-review-count SKUs (the ones with signal)
    seen: dict[str, dict] = {}
    for p in products:
        k = p["pid"] or p["title"]
        if k not in seen or (p.get("n_reviews") or 0) > (seen[k].get("n_reviews") or 0):
            seen[k] = p
    ranked = sorted(seen.values(), key=lambda p: -(p.get("n_reviews") or 0))[:limit]
    status = "OK" if ranked else ("NO_BRAND_SKUS" if n_seen else "EMPTY_PARSE")
    return {"status": status, "url": url, "products": ranked,
            "n_titles_seen": n_seen, "n_dropped_other_brands": n_dropped,
            "brand_tokens": toks,
            "source": "walmart.com search via r.jina.ai text proxy (FRAGILE, proxy-cached)"}


_WM_DATED = re.compile(r"([A-Z][a-z]{2} \d{1,2}, \d{4})(.{0,400}?)(\d(?:\.\d)?) out of 5 stars review",
                       re.S)
_WM_LIFE = re.compile(r"([\d,]+)\s+ratings\|\[([\d,]+)\s+reviews\]")
_WM_HIST = re.compile(r"(\d)\s+stars?\s+(\d+)%\s+\(([\d,]+)\)")


def walmart_product(url: str, timeout: float = 90.0) -> dict:
    """Product page: lifetime rating, counts, star histogram, and the visible dated cohort."""
    import requests
    try:
        r = requests.get(_JINA + url, timeout=timeout)
    except Exception as e:
        return {"status": "FETCH_ERROR", "note": f"r.jina.ai: {str(e)[:120]}", "url": url}
    if r.status_code != 200:
        return {"status": f"HTTP_{r.status_code}", "url": url}
    txt = r.text
    if "Robot or human" in txt[:400]:
        return {"status": "BOT_WALL", "url": url,
                "note": "Walmart bot wall (the /reviews/product deep page always hits this)"}
    life = _WM_LIFE.search(txt)
    rating = None
    m = re.search(r"([\d.]+) out of 5\b", txt)
    if m:
        rating = _num(m.group(1))
    hist = {int(s): {"pct": int(p), "n": int(_num(n))} for s, p, n in _WM_HIST.findall(txt)}
    dated = []
    for d, _mid, stars in _WM_DATED.findall(txt):
        v = _num(stars)
        if v is None:
            continue
        try:
            when = datetime.strptime(d, "%b %d, %Y").replace(tzinfo=timezone.utc)
        except ValueError:
            continue
        age = (datetime.now(timezone.utc) - when).days
        dated.append({"date": d, "stars": v, "age_days": age})
    seen = set()
    dated = [d for d in dated if not (d["date"] + str(d["stars"]) in seen
                                      or seen.add(d["date"] + str(d["stars"])))]
    # "recent" has to MEAN recent: the page mixes a 2023 review in with a 2026 one, so only the
    # in-window ones may be called a cohort.
    recent = [d for d in dated if d["age_days"] <= VISIBLE_WINDOW_DAYS]
    visible = (round(sum(d["stars"] for d in recent) / len(recent), 2) if recent else None)
    return {"status": "OK", "url": url, "lifetime_rating": rating,
            "n_ratings": int(_num(life.group(1))) if life else None,
            "n_reviews": int(_num(life.group(2))) if life else None,
            "histogram": hist, "visible_reviews": dated,
            "visible_cohort_avg": visible, "visible_cohort_n": len(recent),
            "visible_window_days": VISIBLE_WINDOW_DAYS,
            "source": "walmart.com product page via r.jina.ai text proxy"}


def amazon_attempt(query: str, timeout: float = 60.0) -> dict:
    """Amazon is attempted so the degradation is VISIBLE rather than assumed. It is expected to
    fail from a datacenter/plain egress (bot shell / image-only stub); we label it, never drop it."""
    import requests
    url = f"https://www.amazon.com/s?k={requests.utils.quote(query)}"
    try:
        r = requests.get(_JINA + url, timeout=timeout)
    except Exception as e:
        return {"status": "FETCH_ERROR", "note": str(e)[:120], "url": url}
    body = r.text or ""
    if r.status_code != 200:
        return {"status": f"HTTP_{r.status_code}", "url": url}
    hits = re.findall(r"([\d.]+) out of 5 stars", body)
    if not hits:
        return {"status": "DEGRADED_BOT_SHELL", "url": url,
                "note": "Amazon returned a bot/image stub through the proxy — NO review data "
                        "(expected; escalation = Product Advertising API or a logged-in browser)"}
    return {"status": "OK", "url": url, "ratings_seen": hits[:10],
            "note": "partial — search-card ratings only, no per-SKU review counts"}


# ── the read ────────────────────────────────────────────────────────────────────────────────
def read_reviews(ticker: str, *, max_products: int = 4, probe_amazon: bool = True) -> dict:
    """Review trajectory for one ticker's brand. Snapshot-diffs against the stored history."""
    tk = ticker.upper()
    if tk in EXCLUDED:
        return {"ticker": tk, "status": "OUT_OF_LANE", "note": EXCLUDED[tk]}
    ent = _brands_for(tk)
    # An explicit retail_q=None in the tracked lane means "this issuer has NO packaged-goods SKUs on
    # another retailer's shelf" (restaurants, specialty retailers, own-label chains). Falling back to
    # the brand name there manufactures category errors — a 'Chipotle' Walmart search returns chipotle
    # PEPPERS, a 'Buckle' search returns belt buckles. Refuse the read instead.
    q = ent.get("retail_q")
    if q is None and tk not in TRACKED:
        q = (ent.get("brands") or [tk])[0]
    if not q:
        return {"ticker": tk, "status": "NO_RETAIL_SKUS",
                "note": "no packaged-goods SKU channel for this issuer (service/restaurant/retailer "
                        "— use restaurant_ratings for unit-level reception instead)",
                "asof": _now()}

    srch = walmart_search(q, tokens=brand_tokens(tk))
    prev = _load_snapshots()
    products, snaps = [], []
    for p in (srch.get("products") or [])[:max_products]:
        detail = walmart_product(p["url"]) if p.get("pid") else {"status": "NO_PID"}
        ok = detail.get("status") == "OK"
        rating = (detail.get("lifetime_rating") if ok else None) or p.get("lifetime_rating")
        n_rev = (detail.get("n_reviews") if ok else None)
        n_rat = detail.get("n_ratings") if ok else None
        hist_n = sum(v.get("n", 0) for v in (detail.get("histogram") or {}).values()) or None
        # prefer the ratings count (bigger, moves faster) as the velocity denominator; fall back to
        # the histogram total and then the search card — a small SKU has no "N ratings|M reviews" line
        count = n_rat or n_rev or hist_n or p.get("n_reviews")
        row = {"pid": p.get("pid"), "title": p.get("title"), "url": p.get("url"),
               "lifetime_rating": rating, "n_reviews": count,
               "n_written_reviews": n_rev, "histogram": detail.get("histogram"),
               "visible_cohort_avg": detail.get("visible_cohort_avg"),
               "visible_reviews": detail.get("visible_reviews"),
               "star_histogram_low_share": (
                   round(((detail.get("histogram") or {}).get(1, {}).get("pct", 0)
                          + (detail.get("histogram") or {}).get(2, {}).get("pct", 0)) / 100.0, 3)
                   if detail.get("histogram") else None),
               "detail_status": detail.get("status")}
        hist = prev.get((tk, "walmart", p.get("pid")), [])
        # the baseline must be OLD enough to have measured something: newest snapshot at least
        # MIN_SNAPSHOT_GAP_DAYS back (re-running the watch twice in an hour must not print "0/month")
        base = next((h for h in reversed(hist)
                     if (_days_between(h.get("asof", ""), _iso()) or 0) >= MIN_SNAPSHOT_GAP_DAYS), None)
        if base and rating is not None and count is not None:
            days = _days_between(base.get("asof", ""), _iso())
            row["snapshot_prev"] = {"asof": base.get("asof"), "rating": base.get("rating"),
                                    "n": base.get("n"), "days": round(days, 2) if days else None}
            row["cohort_rating"] = implied_cohort_rating(base.get("rating"), base.get("n"),
                                                         rating, count)
            row["cohort_n"] = (count - base.get("n")) if base.get("n") is not None else None
            row["reviews_per_month"] = reviews_per_month(base.get("n"), count, days or 0)
            row["trajectory"] = trajectory_flag(row.get("cohort_rating"), rating, row.get("cohort_n"))
        else:
            row["trajectory"] = {
                "flag": "BASELINE_ONLY", "delta": None,
                "note": (f"{len(hist)} stored snapshot(s), none older than {MIN_SNAPSHOT_GAP_DAYS}d "
                         "— exact cohort delta/velocity not claimed yet" if hist else
                         "FIRST SNAPSHOT for this SKU — exact cohort delta needs a second run; "
                         "visible_cohort_avg below is the weak run-1 proxy")}
            if row.get("visible_cohort_avg") is not None and rating is not None:
                row["visible_delta"] = round(row["visible_cohort_avg"] - rating, 2)
                row["visible_cohort_n"] = detail.get("visible_cohort_n")
                row["visible_note"] = (f"page-visible reviews <= {detail.get('visible_window_days')}d "
                                       "old vs lifetime — LOW-N and retailer-ordered, corroborator only")
        products.append(row)
        if rating is not None and count is not None and p.get("pid"):
            snaps.append({"asof": _iso(), "ticker": tk, "source": "walmart", "pid": p["pid"],
                          "rating": rating, "n": count, "title": p.get("title")})
        time.sleep(0.5)

    if snaps:
        _append_snapshots(snaps)
    agg = aggregate_products(products)
    traj = trajectory_flag(agg.get("cohort_rating_wavg"), agg.get("lifetime_rating_wavg"),
                           agg.get("cohort_n"))
    amz = amazon_attempt(q) if probe_amazon else {"status": "SKIPPED"}
    degraded = []
    if srch.get("status") != "OK":
        degraded.append(f"walmart_search={srch.get('status')}")
    if amz.get("status") not in ("OK", "SKIPPED"):
        degraded.append(f"amazon={amz.get('status')}")
    if traj["flag"] in ("NO_COHORT", "BASELINE_ONLY"):
        degraded.append("cohort_delta=BASELINE_ONLY(needs 2nd snapshot)")
    return {"ticker": tk, "name": ent.get("name"), "query": q, "asof": _now(),
            "status": "OK" if products else (srch.get("status") or "NO_PRODUCTS"),
            "walmart_status": srch.get("status"), "amazon": amz,
            "products": products, "aggregate": agg, "trajectory": traj,
            "review_velocity_per_month": agg.get("reviews_per_month"),
            "rating_delta": traj.get("delta"), "degraded": degraded,
            "source_note": "Walmart via r.jina.ai text proxy (FRAGILE). Amazon/Target/Trustpilot "
                           "blocked from this egress — see module docstring."}


def run(tickers: Optional[list] = None, *, max_products: int = 4, verbose: bool = True) -> dict:
    tickers = [t.upper() for t in (tickers or list(TRACKED))]
    rows, degraded = {}, []
    for tk in tickers:
        row = read_reviews(tk, max_products=max_products)
        rows[tk] = row
        if row.get("degraded"):
            degraded.append(f"{tk}:{'|'.join(row['degraded'])}")
        if verbose:
            agg = row.get("aggregate") or {}
            print(f"  {tk:6} {str(row.get('status')):16} n_sku={agg.get('n_with_rating')} "
                  f"life={agg.get('lifetime_rating_wavg')} traj={row.get('trajectory',{}).get('flag')} "
                  f"delta={row.get('rating_delta')} rpm={row.get('review_velocity_per_month')}")
    p = merge_heat_store("reviews", rows, {"n": len(rows), "degraded": degraded,
                                           "channel": "walmart via r.jina.ai (amazon probed+labelled)"})
    if verbose:
        print(f"[consumer_product_reviews] {len(rows)} brands -> {p}")
        if degraded:
            print(f"  DEGRADED (loud): {'; '.join(degraded)}")
    return {"asof": _now(), "n": len(rows), "rows": rows, "degraded": degraded, "out": str(p)}


# ── uniform connector wrapper (dispatchable) ────────────────────────────────────────────────
class ConsumerProductReviewsConnector(BaseConnector):
    source_id = "consumer_product_reviews"
    rate_limit_per_min = 20

    def query(self, request: ConnectorRequest) -> ConnectorResult:
        x = request.extra or {}
        ticker = str(x.get("ticker") or request.entity_name or "").upper()
        if not ticker:
            return self._fail(request, ErrorKind.UNSUPPORTED,
                              "consumer_product_reviews needs a TICKER (extra.ticker or entity_name)")
        if ticker in EXCLUDED:
            return self._fail(request, ErrorKind.UNSUPPORTED, EXCLUDED[ticker])
        row = read_reviews(ticker, max_products=int(x.get("max_products", 4)),
                           probe_amazon=bool(x.get("probe_amazon", True)))
        if row.get("status") not in ("OK", "NO_RETAIL_SKUS"):
            return self._fail(request, ErrorKind.PARSE_FAIL,
                              f"review channel degraded: {row.get('status')} "
                              f"({'; '.join(row.get('degraded') or [])})",
                              raw=json.dumps(row, default=str))
        agg = row.get("aggregate") or {}
        obs = [
            ConnectorObservation(attribute="review_trajectory", value=row["trajectory"]["flag"],
                                 confidence=0.75 if row["trajectory"]["flag"] in
                                 ("IMPROVING", "DETERIORATING", "STABLE") else 0.3,
                                 extra={**row["trajectory"], "products": len(row.get("products") or []),
                                        "source": row.get("source_note")}),
            ConnectorObservation(attribute="review_rating_delta", value=row.get("rating_delta"),
                                 value_unit="stars_vs_lifetime",
                                 extra={"lifetime_wavg": agg.get("lifetime_rating_wavg"),
                                        "cohort_wavg": agg.get("cohort_rating_wavg"),
                                        "cohort_n": agg.get("cohort_n")}),
            ConnectorObservation(attribute="review_velocity",
                                 value=row.get("review_velocity_per_month"),
                                 value_unit="reviews_per_month",
                                 extra={"n_products": agg.get("n_products"),
                                        "total_reviews": agg.get("total_reviews")}),
            ConnectorObservation(attribute="review_channel_degradation",
                                 value=(row.get("degraded") or ["NONE"]),
                                 confidence=1.0,
                                 extra={"walmart": row.get("walmart_status"),
                                        "amazon": (row.get("amazon") or {}).get("status")}),
        ]
        return self._ok(request, obs, raw=json.dumps(agg, default=str))


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    print(f"=== consumer_product_reviews — review trajectory {_now()} ===")
    run(args or None)
