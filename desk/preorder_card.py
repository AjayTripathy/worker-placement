"""preorder_card — the PRE-ORDER MICROSTRUCTURE CARD (2026-07-03, after three human-beats-machine
execution moments in one day: stale-close limit under live tape, missing Midprice recommendation,
thin-float handling learned by scar tissue instead of checklist).

Before ANY staging, assemble the microstructure facts and emit a recommended order type + params.
The recommendation engine is rules, not vibes — every rule cites its lesson.

  python3 -m desk.preorder_card IBEX --usd 5000 [--cap 32.50]
READ-ONLY.
"""
from __future__ import annotations
import json, sys, argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

VENUE_QUIRKS = {
    "KRX": "close-only via our feeds intraday; account permission gates execution — verify is_close on every quote",
    "LSE": "pence-vs-pounds-vs-USD-GDR triple ambiguity — confirm the quote currency vs the registry before any level",
    "TSE": "JPY; lot sizes of 100; morning/afternoon sessions with a lunch halt",
    "XETRA": "EUR; continuous 09:00-17:30 CET with auctions; thin names gap at the open",
    "TSX": "CAD; interlisted names — check which side has the volume",
    "BIT": "EUR; MTA auctions; small caps can be auction-only liquidity",
    "WSE": "PLN; thin books common; use limits always",
    "US": None,
}


def build_card(ticker: str, usd: float, side: str = "BUY", cap: float | None = None) -> dict:
    from desk import prices as P
    try:
        reg = P.resolve(ticker)
    except P.UnknownSymbol:
        return {"ticker": ticker, "error": "not in the price registry — add it before staging anything"}
    q = P.get_price(ticker)
    facts = {"ticker": ticker, "side": side, "order_usd": usd,
             "px": q["px"], "basis": q["basis"], "fresh": q["fresh"], "suspect": q["suspect"],
             "ccy": reg["ccy"], "exchange": reg["exchange"],
             "venue_quirk": VENUE_QUIRKS.get(reg["exchange"])}
    # liquidity facts via yfinance (best-effort)
    adv_usd = flt = spread_note = None
    try:
        import yfinance as yf
        info = yf.Ticker(reg["yf"]).info
        av = info.get("averageVolume")
        flt = info.get("floatShares")
        if av and q["px"]:
            adv_usd = av * q["px"]
        bid, ask = info.get("bid"), info.get("ask")
        if bid and ask and bid > 0:
            spread_note = round((ask - bid) / ((ask + bid) / 2) * 1e4)   # bps
    except Exception:
        pass
    facts.update({"adv_usd": round(adv_usd) if adv_usd else None,
                  "float_shares": flt, "spread_bps": spread_note,
                  "pct_of_adv": round(usd / adv_usd * 100, 2) if adv_usd else None})
    # ---- the rules engine (each rule cites its lesson) ----
    rec, why = None, []
    thin_float = bool(flt and flt < 15_000_000)
    big_vs_adv = bool(facts["pct_of_adv"] and facts["pct_of_adv"] > 2.0)
    wide = bool(spread_note and spread_note > 50)
    stale = (not q["fresh"]) or q["basis"] == "close" or q["suspect"]
    if q["suspect"]:
        rec = {"order_type": "DO_NOT_STAGE", "params": "quote quarantined — resolve the data problem first"}
        why.append("suspect quote (phantom-tick guard) — never stage against quarantined data")
    elif thin_float or big_vs_adv or wide:
        cap_px = cap or (q["px"] * 1.01 if q["px"] else None)
        rec = {"order_type": "MIDPRICE (IBKR algo; user-placed — MCP can't stage it)",
               "params": f"price cap {round(cap_px,2) if cap_px else 'the plan ceiling'}, DAY; "
                         f"if working a large order: <=25% ADV participation",
               "fallback_stageable": f"LIMIT at ask+1 tick (marketable), cap {round(cap_px,2) if cap_px else '—'}"}
        why.append(f"thin float ({flt/1e6:.1f}M)" if thin_float else "")
        why.append(f"order = {facts['pct_of_adv']}% of ADV" if big_vs_adv else "")
        why.append(f"spread {spread_note}bps" if wide else "")
        why.append("Midprice pegs the NBBO mid — captures half the spread and floats WITH the tape (IBEX lesson: never a static limit below spot on a starter)")
    else:
        rec = {"order_type": "LIMIT (marketable)", "params": "ask + 1 tick, DAY; MARKET acceptable only if <0.1% of ADV on a liquid US name"}
        why.append("liquid name, tight spread — pay the spread, own the position (taxonomy: size carries risk, not price)")
    if stale and rec.get("order_type") != "DO_NOT_STAGE":
        why.append("WARNING: quote basis is stale/close — the USER'S LIVE SCREEN outranks this card's px "
                   "(the $32.00-under-live-tape lesson); confirm the live level before choosing the limit")
    facts["recommendation"] = rec
    facts["why"] = [w for w in why if w]
    return facts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ticker"); ap.add_argument("--usd", type=float, default=5000)
    ap.add_argument("--side", default="BUY"); ap.add_argument("--cap", type=float, default=None)
    a = ap.parse_args()
    print(json.dumps(build_card(a.ticker, a.usd, a.side, a.cap), indent=1))


if __name__ == "__main__":
    main()
