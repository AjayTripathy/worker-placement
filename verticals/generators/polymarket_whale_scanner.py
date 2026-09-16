"""polymarket_whale_scanner — Stage 0b generator: LARGE single-wallet prints on Polymarket.

STATUS: ATTENTION-ALLOCATION ONLY — the pre-registered drift test (PREREGISTRATION_polymarket_
whale.md, frozen 2026-07-05) has NOT run. Seeds carry NO priority; whale flow must never be
cited as drift evidence (the Form-4 NULL lesson). What this scanner IS for today: (1) surfacing
which EVENTS informed-looking money is engaging (attention routing to our event calendar);
(2) accumulating the observation log the backtest needs.

Pipeline: data-api.polymarket.com/trades?filterAmount=50000 (keyless) -> log {proxyWallet, side,
size, price, title, ts}; wallet track-record enrichment = phase 2 (Dune/Polygon join).

  python3 verticals/generators/polymarket_whale_scanner.py [--min-usd 50000]
Writes data/POLYMARKET_WHALES.json + appends data/whale_observation_log.jsonl. READ-ONLY.
"""
from __future__ import annotations
import json, datetime, argparse, urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "data" / "POLYMARKET_WHALES.json"
LOG = HERE / "data" / "whale_observation_log.jsonl"
HDRS = {"User-Agent": "signalos-research 4tripathy@gmail.com"}


def scan(min_usd: int) -> dict:
    url = f"https://data-api.polymarket.com/trades?filterType=CASH&filterAmount={min_usd}&limit=60"
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=HDRS), timeout=30) as r:
            trades = json.load(r)
    except Exception as e:
        return {"asof": datetime.datetime.utcnow().isoformat(), "error": str(e), "whales": []}
    SPORTS = ("vs.", "Spread:", "O/U", "Exact Score", "win on", "Team to Advance", "World Cup",
              "NBA", "NFL", "MLB", "NHL", "UFC", "F1", "Wimbledon", "Grand Prix")
    LEAK_PRONE = ("acquired", "acquisition", "merger", "buyout", "FDA", "approval", "approve",
                  "announce", "IPO", "delist", "SEC ", "DOJ ", "indict", "pardon", "recall")
    rows = []
    for t in trades if isinstance(trades, list) else []:
        title = t.get("title") or ""
        if any(k in title for k in SPORTS):
            continue          # sports = the bulk of whale flow and pure noise for event-mapping
        usd = float(t.get("size", 0)) * float(t.get("price", 0) or 1)
        rows.append({"wallet": (t.get("proxyWallet") or "")[:12], "side": t.get("side"),
                     "usd": round(usd), "price": t.get("price"), "outcome": t.get("outcome"),
                     "title": (t.get("title") or "")[:80], "ts": t.get("timestamp"),
                     "leak_prone_class": any(k.lower() in title.lower() for k in LEAK_PRONE)})
    seen = set()
    if LOG.exists():
        for l in LOG.read_text().splitlines()[-500:]:
            try:
                d = json.loads(l); seen.add((d["wallet"], d["ts"], d["usd"]))
            except Exception:
                pass
    with LOG.open("a") as f:
        for r in rows:
            if (r["wallet"], r["ts"], r["usd"]) not in seen:
                f.write(json.dumps(r) + "\n")
    return {"asof": datetime.datetime.utcnow().isoformat(), "min_usd": min_usd, "whales": rows}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--min-usd", type=int, default=50000)
    a = ap.parse_args()
    res = scan(a.min_usd)
    print(f"=== POLYMARKET WHALE SCANNER  {res['asof'][:16]}  (>= ${a.min_usd/1000:.0f}k prints) ===")
    for w in res.get("whales", [])[:15]:
        print(f"  ${w['usd']:>8,}  {w['side']:<4} {w['outcome'] or '?':<4} @{w['price']}  {w['title']}")
    if not res.get("whales"):
        print("  no qualifying prints this pass" + (f"  [error: {res.get('error')}]" if res.get("error") else ""))
    lp = [w for w in res.get("whales", []) if w.get("leak_prone_class")]
    if lp:
        print(f"  LEAK-PRONE CLASS prints ({len(lp)}) — the insider-signature arm's watch cohort (M&A/approvals/announcements):")
        for w in lp[:5]:
            print(f"    >>> ${w['usd']:>8,}  {w['side']} {w['outcome']}  {w['title']}")
    print("  DOCTRINE: attention-allocation ONLY — pre-registered drift test NOT yet run; no seed priority.")
    OUT.write_text(json.dumps(res, indent=1))
    print(f"[-> {OUT.name} + whale_observation_log.jsonl]")


if __name__ == "__main__":
    main()
