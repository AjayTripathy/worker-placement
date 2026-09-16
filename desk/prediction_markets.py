"""prediction_markets — market_p ingestion from Kalshi + Polymarket (Product A, 2026-07-05).

PURPOSE: grade OUR frozen calls against the crowd — the Brier-vs-market autonomy gate (Rung 1)
is ungradeable with market_p=None. This module maps frozen calls to venue markets and annotates
the calibration ledger with market_p_current (+ source + mismatch flags). It NEVER changes
frozen our_p values.

DOCTRINE (from the feasibility sweep 2026-07-05):
- THRESHOLD-MISMATCH TRAP: a Cat-4 market cannot grade a Cat-3+ call (would manufacture a fake
  32pp edge). Every mapping carries match_quality: EXACT | RELATED (directional only, never an
  edge claim) | NONE. Only EXACT feeds Brier-vs-market.
- Coverage is honest: geopolitical/Fed map STRONG; single-name earnings, CMS-regulatory, and
  niche policy (PL ROE-cap, IL windfall) have NO markets — those calls stay market_p=None.
- Read APIs are keyless (Kalshi trade-api/v2, Polymarket gamma/CLOB). Kalshi has historical
  candles for backfill-to-prediction-date (the real Brier need) — TODO phase 2.

  python3 -m desk.prediction_markets          # refresh annotations on OPEN mapped calls
MAPPINGS maintained by hand — a wrong map is worse than no map.
"""
from __future__ import annotations
import json, datetime, urllib.request, urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "desk" / "data" / "calibration_ledger.jsonl"
OUT = ROOT / "desk" / "data" / "market_p_annotations.json"
HDRS = {"User-Agent": "signalos-research 4tripathy@gmail.com"}

# ticker|cat_date -> mapping spec. match: EXACT feeds Brier; RELATED = directional context only.
MAPPINGS = {
    # HCA's PTC option leg: the live combo market (decompose by the House leg ~0.82)
    "HCA|2026-12-15": {"venue": "polymarket", "slug_search": "ACA premium tax credits extended",
        "relation": "RELATED — combo 'NOT extended AND Dem House' 0.81 w/ P(DemHouse)~0.82 => crowd ~certain NO pre-midterm extension; the PTC option is a POST-midterm/2027 event, not 2026",
        "prefer_end": "2026-11-03"},
    # BAH shutdown call: no direct Oct-1 market listed yet (Kalshi expected ~Aug/Sep); the Jan-31 combo = the nearest read
    "BAH|2026-10-01": {"venue": "polymarket", "slug_search": "government shutdown",
        "relation": "RELATED — 'shutdown by Jan-31 AND Rep House' 0.16 (conditioning muddies it); STANDING TASK: re-search weekly via refresh() for a direct Oct-1 market as venues list it",
        "prefer_end": "2026-11-03"},
    "FRO|2026-08-31": {
        "venue": "polymarket", "slug_search": "Strait of Hormuz traffic returns to normal",
        "prefer_end": "2026-12", "match": "RELATED",
        "mismatch_note": "market = 'normal' by DEC-31; our call = >=50%-of-baseline by AUG-31 — stricter date, looser bar; directional context only, NOT Brier-comparable. Context markets 2026-07-04: 'normal by end of JUNE' resolved ~0.002 (crowd confirms the stall); 'US-Iran Final Deal by Aug-18' ~0.19 YES (whale $57.5k NO @0.81 — the 60-day MOU clock)"},
    "BBD|2026-10-25": {
        "venue": "polymarket", "slug_search": "Brazil presidential election",
        "prefer_end": "2026-10", "match": "RELATED",
        "mismatch_note": "market = per-candidate WIN legs (Lula 60.5% / market-friendly field ~37% at 2026-07-04); our call = the market-friendly-list WINS aggregate — leg-sum comparable but candidate-list definitions must be re-checked at resolution"},
    # add EXACT maps as venues list them; CMS/earnings/PL/IL classes verified NONE 2026-07-05
}


def _recent_whale_in(question: str, hours: int = 24) -> str | None:
    """TWO-SIGNAL DOCTRINE (2026-07-05): crowd_p is a STATE variable; whale flow is a FLOW event.
    In thin markets Kyle's lambda makes a whale print temporarily BE the mid (~13pp/$1M early-market)
    — so a market_p read within `hours` of a large print in the same market is the whale wearing the
    crowd's clothes. Flag it; a flagged read grades nothing and conditions nothing until it decays."""
    log = ROOT / "verticals" / "generators" / "data" / "whale_observation_log.jsonl"
    if not log.exists() or not question:
        return None
    cutoff = (datetime.datetime.utcnow() - datetime.timedelta(hours=hours)).timestamp()
    qkey = question.lower()[:40]
    for l in log.read_text().splitlines()[-300:]:
        try:
            w = json.loads(l)
        except Exception:
            continue
        ts = w.get("ts")
        try:
            ts = float(ts)
        except Exception:
            continue
        if ts >= cutoff and (w.get("title") or "").lower()[:40] == qkey and w.get("usd", 0) >= 50000:
            return f"${w['usd']:,} {w['side']} {w.get('outcome')} within {hours}h — mid may be flow-painted"
    return None


def _poly_price(slug_search: str, prefer_end: str | None = None) -> dict | None:
    url = f"https://gamma-api.polymarket.com/public-search?q={urllib.parse.quote(slug_search)}"
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=HDRS), timeout=20) as r:
            d = json.load(r)
        today = datetime.date.today().isoformat()
        cands = []
        for ev in d.get("events", []):
            for m in ev.get("markets", []):
                if not m.get("outcomePrices"):
                    continue
                # ACTIVE ONLY: resolved/expired markets poisoned earlier reads (a 2025
                # shutdown market at 1.0 surfaced as "the" shutdown price in 2026)
                if m.get("closed") is True:
                    continue
                end = (m.get("endDate") or "")[:10]
                if end and end < today:
                    continue
                prices = m["outcomePrices"]
                if isinstance(prices, str):
                    prices = json.loads(prices)
                cands.append({"question": m.get("question"), "yes_p": float(prices[0]),
                              "volume": m.get("volumeNum"), "end": m.get("endDate") or ""})
        if not cands:
            return None
        if prefer_end:
            pref = [c for c in cands if (c["end"] or "").startswith(prefer_end)]
            if pref:
                return pref[0]
        cands.sort(key=lambda c: -(c.get("volume") or 0))
        return cands[0]
    except Exception:
        return None
    return None


def refresh() -> dict:
    ann = {"asof": datetime.date.today().isoformat(), "annotations": []}
    lines = LEDGER.read_text().splitlines()
    out = []
    for l in lines:
        if not l.strip():
            out.append(l); continue
        r = json.loads(l)
        key = f"{r.get('ticker')}|{r.get('cat_date')}"
        spec = MAPPINGS.get(key)
        if spec and r.get("status") == "OPEN":
            q = _poly_price(spec["slug_search"], spec.get("prefer_end")) if spec["venue"] == "polymarket" else None
            if q:
                q["flow_contaminated"] = _recent_whale_in(q.get("question") or "")
                # match-quality label: some maps use 'match' (EXACT/RELATED enum), older ones use
                # 'relation' (a descriptive RELATED string). Default RELATED (never feeds Brier — safe).
                match_q = spec.get("match") or ("RELATED" if spec.get("relation") else "NONE")
                r["market_p_current"] = q["yes_p"]
                r["market_p_source"] = f"{spec['venue']}: {q['question']} ({match_q})"
                if q.get("flow_contaminated"):
                    r["market_p_flow_contaminated"] = q["flow_contaminated"]
                if match_q != "EXACT":
                    r["market_p_mismatch"] = spec.get("mismatch_note") or spec.get("relation") or match_q
                ann["annotations"].append({"call": key, "market_p": q["yes_p"],
                                           "match": match_q, "question": q["question"]})
        out.append(json.dumps(r))
    LEDGER.write_text("\n".join(out))
    OUT.write_text(json.dumps(ann, indent=1))
    return ann


if __name__ == "__main__":
    res = refresh()
    print(f"=== PREDICTION-MARKET market_p REFRESH  {res['asof']} ===")
    for a in res["annotations"]:
        print(f"  {a['call']:<22} market_p={a['market_p']:.3f}  [{a['match']}]  {a['question'][:60]}")
    if not res["annotations"]:
        print("  no OPEN mapped calls annotated (mappings are hand-curated; most classes have NO venue coverage)")
