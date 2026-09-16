"""expedition_inventory — forward-booking telemetry for expedition-cruise operators.

WHY THIS EXISTS. Expedition cruising books 2-4 QUARTERS AHEAD, so the operator knows its season
long before it reports it — and the booking surface is public the whole time. Sold-out status,
promotional depth and deployed departure counts sit in the operator's own site payload, refreshed
continuously, against a company that reports quarterly. That gap between what the website knows
and what the income statement has said is the entire opportunity, and it is available for the
same reason the BDC schedule reconciliation was: reading it is tedious, not clever.

MECHANISM. Discounting is the INVERSE of forward demand. An operator with a full book raises
price and withdraws promotions; one with a soft book adds departures to promotion, deepens the
discount, and holds price while quietly discounting. Because the cruise is a perishable inventory
with a hard sail date, that decision is forced early — which is what makes it a LEADING read
rather than a coincident one.

WHAT IT READS. Lindblad's site is a Next.js app whose `__NEXT_DATA__` payload carries an
Algolia-backed itinerary index with, per itinerary: isSoldOut, nrDepartures, lowestFullPrice,
lowestDiscountedPrice, discount, per-market promotion labels, the ship list and every departure
timestamp. No API key, no scraping of rendered HTML — the JSON is embedded in the page.

TWO CALIBRATIONS FROM THE FIRST LIVE RUN (2026-08-17, Antarctica), both load-bearing:
  1. THE PROMOTION FLAG IS ALWAYS-ON MARKETING AND ITS LEVEL IS MEANINGLESS — 66 of 72 itineraries
     carry one. But the DEPTH metric is dead too, and for a more interesting reason: across the
     ENTIRE 72-itinerary book there is NOT ONE FARE CUT (lowestFullPrice == lowestDiscountedPrice
     on all 72, discount field 0 on all 72). The single promotion in the whole book is
     "50% Reduced Deposit". So the operator is conceding on TERMS, not on PRICE — which preserves
     headline fare and revenue per berth while shifting working-capital float and cancellation
     exposure onto itself. A fare cut shows up in any price series; this does not, which is
     precisely why it earns its own metric (deposit_terms_concession_pct). Reporting a "mean
     discount depth of 0.0%" would have read as "no discounting measured" when the truth is
     "no PRICE discounting exists, but a terms concession is universal" — opposite implications
     for pricing power.
  2. isSoldOut IS AN ITINERARY-LEVEL FLAG, NOT A DEPARTURE-LEVEL ONE. An itinerary offering 50
     departures reporting "not sold out" is nearly uninformative; one offering 3 is meaningful.
     Sold-out rate is therefore reported BOTH raw and DEPARTURE-WEIGHTED, and the weighted figure
     is the one to use.

FIRST RUN ESTABLISHES A BASELINE AND SAYS SO LOUDLY. The signal is the delta between snapshots;
a single observation of "62% promoted" means nothing without the prior. Snapshots MERGE by
itinerary slug so the history is the asset.

    python3 -m verticals.buyside_dd.connectors.expedition_inventory [--operator LIND]

Writes verticals/buyside_dd/outputs/expedition_inventory/EXPEDITION_INVENTORY.json (merged).
"""
from __future__ import annotations

# Knowledge-graph dispatch contract. Keyed on the verification attribute — forward-booked
# perishable inventory whose price and availability are publicly posted — not on the sector.
APPLIES_TO = {
    "kind": 'm_source',
    "sic_codes": [],
    "sic_prefixes": ['4481', '4724', '7011', '7990', '4700'],
    "issuer_features": ['expedition_cruise_operator', 'forward_booked_inventory',
                        'published_departure_calendar', 'tour_operator', 'perishable_inventory'],
    "asset_classes": ['public_equity', 'corporate_ipo_dd'],
    "applies_universally": False,
    "summary": ('Forward-booking telemetry for expedition/tour operators: departure-weighted '
                'sold-out rate, promotional DEPTH and deployed capacity from the operator\'s own '
                'booking payload — a leading read on a season the income statement has not reported.'),
    "verification_question": ("Is this operator's forward book filling or softening — i.e. is it "
                              "withdrawing promotions and raising price, or deepening discounts to "
                              "move perishable inventory?"),
}

import argparse
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

HERE = Path(__file__).resolve()
if str(HERE.parents[3]) not in sys.path:
    sys.path.insert(0, str(HERE.parents[3]))

from .base import (BaseConnector, ConnectorObservation, ConnectorRequest,
                   ConnectorResult, ErrorKind)

OUT_DIR = HERE.parents[1] / "outputs" / "expedition_inventory"
OUT = OUT_DIR / "EXPEDITION_INVENTORY.json"

_UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
_HDRS = {"User-Agent": _UA, "Accept-Language": "en-US,en;q=0.9",
         "Accept": "text/html,application/xhtml+xml,*/*;q=0.8"}

OPERATORS = {
    "LIND": {
        "name": "Lindblad Expeditions",
        "base": "https://www.expeditions.com",
        # Destination slugs are the natural shard: each page's payload carries the itineraries
        # for that region, so region-level softness is visible before the consolidated number.
        "paths": ["/destinations/antarctica", "/destinations/arctic", "/destinations/alaska",
                  "/destinations/galapagos", "/destinations/baja-california",
                  "/destinations/central-america", "/destinations/caribbean",
                  "/destinations/asia", "/destinations/europe", "/destinations/south-america"],
    },
}


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _next_data(url: str, timeout: float = 30.0) -> dict | None:
    try:
        r = requests.get(url, headers=_HDRS, timeout=timeout)
        if r.status_code != 200:
            return None
        m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', r.text, re.S)
        return json.loads(m.group(1)) if m else None
    except (requests.RequestException, ValueError):
        return None


def _itineraries(payload: dict) -> list[dict]:
    """Pull every itinerary record. Identified by carrying BOTH isSoldOut and name, which is what
    distinguishes an Algolia hit from the surrounding page furniture."""
    out: list[dict] = []

    def walk(o):
        if isinstance(o, dict):
            if "isSoldOut" in o and "name" in o:
                out.append(o)
                return
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    walk(payload)
    return out


def _norm(r: dict) -> dict:
    ships = r.get("ships") or []
    ship_names = sorted({(s.get("name") if isinstance(s, dict) else str(s)) for s in ships if s})
    full = r.get("lowestFullPrice")
    disc = r.get("lowestDiscountedPrice")
    depth = None
    try:
        if full and disc and float(full) > 0:
            depth = round((1 - float(disc) / float(full)) * 100, 2)
    except (TypeError, ValueError):
        depth = None
    promos = r.get("promotionsUS") or []
    labels = [(p.get("label") if isinstance(p, dict) else str(p)) for p in promos]
    # DEPOSIT-TERMS CONCESSION (first live run 2026-08-17): the only promotion across Lindblad's
    # entire 72-itinerary book is "50% Reduced Deposit" — a TERMS concession, not a fare cut.
    # It eases the cash barrier to booking while leaving headline price (and reported revenue per
    # berth) untouched, and it quietly moves working capital and cancellation risk onto the
    # operator. A fare cut is visible in any price series; this is not, which is exactly why it
    # is worth a dedicated metric.
    deposit_terms = any(re.search(r"deposit", str(l), re.I) for l in labels)
    fare_promo = any(not re.search(r"deposit", str(l), re.I) for l in labels)
    return {
        "slug": r.get("pageSlug") or r.get("objectID") or r.get("name"),
        "name": r.get("name"),
        "product_type": r.get("productType"),
        "ships": ship_names,
        "n_departures": r.get("nrDepartures"),
        "is_sold_out": bool(r.get("isSoldOut")),
        "price_full": full,
        "price_discounted": disc,
        "discount_depth_pct": depth,
        "discount_field": r.get("discount"),
        "promo_labels_us": labels[:4],
        "deposit_terms_concession": deposit_terms,
        "fare_promo": fare_promo,
        "has_promo_us": bool(promos) or bool(r.get("hasPromotionUS")),
        "duration": r.get("duration"),
        "n_departure_dates": len(r.get("departureDates") or []),
    }


def scan(operator: str = "LIND", verbose: bool = True) -> dict:
    cfg = OPERATORS[operator]
    rows: dict[str, dict] = {}
    per_region, failures = {}, []
    for path in cfg["paths"]:
        url = cfg["base"] + path
        payload = _next_data(url)
        if payload is None:
            failures.append(path)          # NEVER silent — an unreachable region is not an empty one
            continue
        hits = [_norm(r) for r in _itineraries(payload)]
        region = path.rsplit("/", 1)[-1]
        for h in hits:
            h["region"] = region
            if h["slug"]:
                rows[h["slug"]] = h
        dep = sum((h["n_departures"] or 0) for h in hits)
        so_dep = sum((h["n_departures"] or 0) for h in hits if h["is_sold_out"])
        per_region[region] = {
            "itineraries": len(hits),
            "sold_out_raw_pct": round(100 * sum(h["is_sold_out"] for h in hits) / len(hits), 1) if hits else None,
            "sold_out_departure_weighted_pct": round(100 * so_dep / dep, 1) if dep else None,
            "departures": dep,
            "promo_pct": round(100 * sum(h["has_promo_us"] for h in hits) / len(hits), 1) if hits else None,
            "deposit_terms_pct": (round(100 * sum(h["deposit_terms_concession"] for h in hits) / len(hits), 1)
                                  if hits else None),
        }
        time.sleep(0.8)

    allr = list(rows.values())
    dep_tot = sum((h["n_departures"] or 0) for h in allr)
    so_dep = sum((h["n_departures"] or 0) for h in allr if h["is_sold_out"])
    # A fare cut requires price_full > price_discounted. On the first run that was true 0/72:
    # report the ABSENCE explicitly rather than a mean of zeros, which reads like "no discounting
    # measured" when it means "no discounting exists" — opposite implications for pricing power.
    fare_cuts = [h for h in allr if (h["discount_depth_pct"] or 0) > 0]
    depths = [h["discount_depth_pct"] for h in fare_cuts]
    agg = {
        "itineraries": len(allr),
        "departures": dep_tot,
        "sold_out_raw_pct": round(100 * sum(h["is_sold_out"] for h in allr) / len(allr), 1) if allr else None,
        "sold_out_departure_weighted_pct": round(100 * so_dep / dep_tot, 1) if dep_tot else None,
        "promo_pct": round(100 * sum(h["has_promo_us"] for h in allr) / len(allr), 1) if allr else None,
        "fare_cut_count": len(fare_cuts),
        "fare_cut_pct_of_itineraries": round(100 * len(fare_cuts) / len(allr), 1) if allr else None,
        "mean_fare_cut_depth_pct": round(sum(depths) / len(depths), 2) if depths else None,
        "deposit_terms_concession_pct": (round(100 * sum(h["deposit_terms_concession"] for h in allr)
                                               / len(allr), 1) if allr else None),
        "pricing_read": (
            "NO FARE DISCOUNTING ANYWHERE — headline price fully intact; the concession is being "
            "made on DEPOSIT TERMS instead, which preserves revenue per berth but shifts working "
            "capital and cancellation risk to the operator" if not fare_cuts else
            f"FARE CUTS PRESENT on {len(fare_cuts)} itineraries — price integrity broken"),
        "ships_deployed": sorted({s for h in allr for s in h["ships"]}),
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    store = json.loads(OUT.read_text()) if OUT.exists() else {"runs": [], "itineraries": {}}
    prev_run = store["runs"][-1] if store["runs"] else None
    delta = None
    if prev_run and prev_run.get("operator") == operator:
        pa = prev_run["aggregate"]
        def d(k):
            a, b = agg.get(k), pa.get(k)
            return round(a - b, 2) if (a is not None and b is not None) else None
        delta = {"vs_run": prev_run["asof"],
                 "sold_out_departure_weighted_pct": d("sold_out_departure_weighted_pct"),
                 "promo_pct": d("promo_pct"),
                 "mean_fare_cut_depth_pct": d("mean_fare_cut_depth_pct"),
                 "deposit_terms_concession_pct": d("deposit_terms_concession_pct"),
                 "fare_cut_pct_of_itineraries": d("fare_cut_pct_of_itineraries"),
                 "departures": d("departures"),
                 "read": None}
        # Direction must be readable in a NO-FARE-CUT world: the original logic required a fare
        # depth that does not exist here, so `read` was permanently None (the LIND blue bench
        # correctly called the output degraded). Re-based on the metrics that actually move —
        # sold-out rate and the spread of the TERMS concession — with fare cuts as an escalation.
        sow = delta["sold_out_departure_weighted_pct"]
        dtc = delta.get("deposit_terms_concession_pct")
        fcp = delta.get("fare_cut_pct_of_itineraries")
        if fcp is not None and fcp > 0:
            delta["read"] = ("CYCLE ROLLING — true FARE CUTS have appeared where before there were "
                             "none. This is a worse signal than any terms concession: price "
                             "integrity is broken and revenue per berth falls with it.")
        elif sow is not None:
            if sow < -2 and (dtc or 0) > 2:
                delta["read"] = ("SOFTENING — sold-out rate falling while the terms concession "
                                 "spreads. The book is being bought rather than sold, and the "
                                 "deposit float that funds operations thins with it.")
            elif sow > 2 and (dtc or 0) < -2:
                delta["read"] = ("FIRMING — sold-out rate rising while the terms concession is "
                                 "withdrawn. Pricing power on perishable inventory.")
            else:
                delta["read"] = "MIXED / within noise — do not trade a single-snapshot delta."

    store["runs"].append({"asof": _now(), "operator": operator, "aggregate": agg,
                          "per_region": per_region, "unreachable_paths": failures})
    for h in allr:
        prev = store["itineraries"].get(h["slug"], {})
        h["first_seen"] = prev.get("first_seen", _now())
        h["last_seen"] = _now()
        store["itineraries"][h["slug"]] = h
    OUT.write_text(json.dumps(store, indent=1))

    res = {"operator": operator, "asof": _now(), "aggregate": agg, "per_region": per_region,
           "delta_vs_prior": delta, "unreachable_paths": failures,
           "baseline_only": delta is None,
           "caveats": [
               "PROMO FLAG LEVEL IS NON-DISCRIMINATING — 7/7 Antarctica itineraries carried a US "
               "promotion on the first run. Always-on marketing. Use DEPTH and DELTA, never the level.",
               "isSoldOut is ITINERARY-level, not departure-level; the departure-weighted figure is "
               "the one to use.",
               "First run is a BASELINE — the signal is the delta between snapshots.",
           ]}
    if verbose:
        b = " (BASELINE ONLY — no prior snapshot)" if delta is None else ""
        print(f"[expedition_inventory] {operator}{b}: {agg['itineraries']} itineraries, "
              f"{agg['departures']} departures, sold-out {agg['sold_out_departure_weighted_pct']}% "
              f"(dep-weighted) / {agg['sold_out_raw_pct']}% raw, promo {agg['promo_pct']}%, "
              f"fare cuts {agg['fare_cut_count']}/{agg['itineraries']}, "
              f"deposit-terms concession {agg['deposit_terms_concession_pct']}%")
        print(f"    PRICING: {agg['pricing_read']}")
        for r, v in sorted(per_region.items()):
            print(f"    {r:20s} itin {v['itineraries']:>3d}  dep {v['departures']:>4d}  "
                  f"soldout {str(v['sold_out_departure_weighted_pct']):>6s}%  "
                  f"promo {str(v['promo_pct']):>6s}%")
        if failures:
            print(f"    UNREACHABLE (never counted as empty): {failures}")
        if delta:
            print(f"    DELTA vs {delta['vs_run']}: {delta['read']}")
    return res


class ExpeditionInventoryConnector(BaseConnector):
    source_id = "expedition_inventory"
    rate_limit_per_min = 20

    def query(self, request: ConnectorRequest) -> ConnectorResult:
        # NEVER DEFAULT TO AN ISSUER. The original `or "LIND"` meant an empty request returned
        # LINDBLAD's book with success=True — a caller who named no operator, or named one we do
        # not map, got real-looking numbers for the wrong company. The NCLH bench hit exactly this
        # and reported "byte-identical output for ncl.com and rssc.com; 1,986 departures". That is
        # the silent-wrong-answer class, strictly worse than a crash, and the contract smoke test
        # PASSED it because a well-formed result was returned. Unknown or missing => fail loudly.
        op = (request.extra.get("operator") or request.extra.get("ticker") or "").upper()
        if not op:
            return self._fail(request, ErrorKind.UNSUPPORTED,
                              "no operator named — pass extra.operator or extra.ticker; this "
                              "connector will NOT guess an issuer")
        if op not in OPERATORS:
            return self._fail(request, ErrorKind.UNSUPPORTED,
                              f"no booking-surface map for {op}; known: {sorted(OPERATORS)}")
        d = scan(op, verbose=False)
        a = d["aggregate"]
        obs = [
            ConnectorObservation(attribute="forward_sold_out_pct",
                                 value=a["sold_out_departure_weighted_pct"],
                                 value_unit="% of departures, departure-weighted",
                                 confidence=0.8, extra={"raw_pct": a["sold_out_raw_pct"]}),
            ConnectorObservation(attribute="fare_integrity",
                                 value=a["pricing_read"], confidence=0.85,
                                 extra={"fare_cuts": a["fare_cut_count"],
                                        "deposit_terms_concession_pct": a["deposit_terms_concession_pct"],
                                        "promo_pct_level_non_discriminating": a["promo_pct"]}),
            ConnectorObservation(attribute="deployed_departures", value=a["departures"],
                                 value_unit="departures across scanned regions",
                                 extra={"ships": a["ships_deployed"]}),
        ]
        if d["delta_vs_prior"]:
            obs.append(ConnectorObservation(attribute="forward_book_direction",
                                            value=d["delta_vs_prior"]["read"],
                                            confidence=0.7, extra=d["delta_vs_prior"]))
        else:
            obs.append(ConnectorObservation(attribute="forward_book_direction",
                                            value="BASELINE_ONLY — no prior snapshot; delta is the signal",
                                            confidence=0.0))
        return self._ok(request, obs, raw=json.dumps(d)[:2000])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--operator", default="LIND")
    a = ap.parse_args()
    scan(a.operator)
