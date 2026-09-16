"""preferred_oddlot_scanner — Stage 0b generator: mispriced $25-par preferreds & baby bonds (CARRY).

THE PUREST OFFICE-THESIS EDGE: institutions cannot trade odd lots of $25-par exchange-traded
preferreds / baby bonds economically — the tickets are too small to bother, so deep-discount +
illiquid names carry a pull-to-par + credit-mispricing that nobody at size captures. A small
investor + AI screening the full universe IS the edge (capacity-ceilinged, fee-replication carry).

v1 screens a SEED universe on the three things computable from live data — no hardcoded coupons
(dividend pulled from yfinance so nothing is fabricated), par assumed $25 exchange-traded:
  1. DISCOUNT-TO-PAR   price vs $25 -> pull-to-par convexity if the credit is money-good
  2. CURRENT YIELD     live trailing dividend / price
  3. ILLIQUIDITY       $-volume (LOW = the odd-lot / institutional-neglect signature)
The odd-lot score = discount × illiquidity-neglect. Credit-is-money-good is the DD step (a deep
discount on impaired credit is a value trap, not a gift — verify the issuer's senior curve/coverage).
The universe is a SEED to EXPAND + VERIFY; unresolvable tickers self-drop (reported, never silent).

    python3 verticals/generators/preferred_oddlot_scanner.py
Writes data/PREFERRED_ODDLOT.json. READ-ONLY.
"""
from __future__ import annotations

import datetime
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "data" / "PREFERRED_ODDLOT.json"
PAR = 25.0

# SEED universe (exchange-traded $25-par preferreds & baby bonds). ticker | issuer | sector.
# NO coupons hardcoded — the live trailing dividend is pulled from yfinance. Bad tickers self-drop.
# We already hold OXLCZ (a baby bond) ad hoc — this systematizes the sleeve. EXPAND this list.
UNIVERSE = [
    ("OXLCZ", "Oxford Lane Capital", "BDC/CLO baby bond"),
    ("OXLCL", "Oxford Lane Capital", "BDC/CLO baby bond"),
    ("OXLCN", "Oxford Lane Capital", "BDC/CLO baby bond"),
    ("ECCC",  "Eagle Point Credit", "BDC/CLO baby bond"),
    ("ECCV",  "Eagle Point Credit", "BDC/CLO baby bond"),
    ("ECCX",  "Eagle Point Credit", "BDC/CLO baby bond"),
    ("ECCF",  "Eagle Point Credit", "BDC/CLO baby bond"),
    ("PBB",   "Prospect Capital", "BDC baby bond"),
    ("SACC",  "Sachem Capital", "mortgage-REIT baby bond"),
    ("SCCB",  "Sachem Capital", "mortgage-REIT baby bond"),
    ("AGNCP", "AGNC Investment", "agency-mREIT preferred"),
    ("AGNCN", "AGNC Investment", "agency-mREIT preferred"),
    ("AGNCM", "AGNC Investment", "agency-mREIT preferred"),
    ("NLY-PF", "Annaly Capital", "agency-mREIT preferred"),
    ("NLY-PI", "Annaly Capital", "agency-mREIT preferred"),
    ("RITM-PA", "Rithm Capital", "mortgage-REIT preferred"),
    ("RITM-PB", "Rithm Capital", "mortgage-REIT preferred"),
    ("RITM-PD", "Rithm Capital", "mortgage-REIT preferred"),
    ("TWO-PA", "Two Harbors", "mortgage-REIT preferred"),
    ("TWO-PB", "Two Harbors", "mortgage-REIT preferred"),
    ("GSL-PB", "Global Ship Lease", "shipping preferred"),
    ("SB-PC", "Safe Bulkers", "shipping preferred"),
    ("SB-PD", "Safe Bulkers", "shipping preferred"),
    ("GNL-PA", "Global Net Lease", "net-lease-REIT preferred"),
    ("GNL-PB", "Global Net Lease", "net-lease-REIT preferred"),
    ("SLG-PI", "SL Green Realty", "office-REIT preferred"),
    ("CIM-PA", "Chimera Investment", "mortgage-REIT preferred"),
    ("CIM-PB", "Chimera Investment", "mortgage-REIT preferred"),
]

DISCOUNT_FLOOR = 0.04       # >=4% below par to matter (pull-to-par convexity)
ODDLOT_ADV_USD = 1_500_000  # <=~$1.5M/day $-volume = the institutional-neglect / odd-lot signature


def _pull(tickers):
    """Live price + trailing dividend + $-volume via yfinance. Returns {t: {...}} for resolvers."""
    import yfinance as yf
    out = {}
    try:
        data = yf.Tickers(" ".join(tickers))
    except Exception:
        return out
    for t in tickers:
        try:
            tk = data.tickers.get(t) or yf.Ticker(t)
            fi = getattr(tk, "fast_info", {}) or {}
            px = fi.get("last_price") or fi.get("lastPrice")
            vol = fi.get("last_volume") or fi.get("lastVolume")
            info = {}
            if px is None:
                info = tk.info or {}
                px = info.get("regularMarketPrice") or info.get("previousClose")
                vol = vol or info.get("regularMarketVolume") or info.get("averageVolume")
            if not px:
                continue
            # trailing dividend: prefer explicit rate, else sum last 12m of the dividend series
            div = None
            info = info or (tk.info or {})
            div = info.get("trailingAnnualDividendRate") or info.get("dividendRate")
            if not div:
                try:
                    dv = tk.dividends
                    if len(dv):
                        cut = datetime.datetime.now(dv.index.tz) - datetime.timedelta(days=365) if dv.index.tz else \
                              datetime.datetime.now() - datetime.timedelta(days=365)
                        div = float(dv[dv.index >= cut].sum())
                except Exception:
                    div = None
            out[t] = {"px": float(px), "vol": float(vol or 0), "div": float(div) if div else None}
        except Exception:
            continue
    return out


def scan() -> dict:
    px = _pull([t for t, _, _ in UNIVERSE])
    resolved, dropped, rows = 0, [], []
    for t, issuer, sector in UNIVERSE:
        d = px.get(t)
        if not d or not d.get("px"):
            dropped.append(t)
            continue
        resolved += 1
        p = d["px"]
        disc = PAR / p - 1 if p else 0            # +ve = trading below par
        cur_yld = (d["div"] / p) if d.get("div") and p else None
        advusd = d["px"] * d["vol"]               # crude 1-day $-volume proxy
        oddlot = advusd <= ODDLOT_ADV_USD
        rows.append({
            "ticker": t, "issuer": issuer, "sector": sector, "price": round(p, 2),
            "disc_to_par_pct": round(disc * 100, 1), "current_yield_pct": round(cur_yld * 100, 2) if cur_yld else None,
            "dollar_vol_1d": round(advusd), "oddlot_illiquid": oddlot,
        })
    # candidates: below par by the floor AND odd-lot-illiquid (the neglect signature).
    cands = [r for r in rows if r["disc_to_par_pct"] >= DISCOUNT_FLOOR * 100 and r["oddlot_illiquid"]]
    # score = discount (pull-to-par upside) × neglect (how far below the odd-lot ADV line)
    for r in cands:
        neglect = min(1.0, (ODDLOT_ADV_USD - r["dollar_vol_1d"]) / ODDLOT_ADV_USD) if r["dollar_vol_1d"] < ODDLOT_ADV_USD else 0
        r["oddlot_score"] = round((r["disc_to_par_pct"] / 100) * (0.5 + 0.5 * neglect) + (r["current_yield_pct"] or 0) / 200, 3)
    cands.sort(key=lambda r: -r["oddlot_score"])
    return {"asof": datetime.date.today().isoformat(), "par": PAR,
            "universe": len(UNIVERSE), "resolved": resolved, "dropped": dropped,
            "candidates": cands, "all": sorted(rows, key=lambda r: -r["disc_to_par_pct"]),
            "note": "PULL-TO-PAR + odd-lot NEGLECT screen on $25-par preferreds/baby bonds. A deep discount is only a "
                    "gift if the credit is MONEY-GOOD — the DD/court step is the issuer's senior curve + coverage + "
                    "call schedule (a deep discount on impaired credit is a value trap). Seed universe — EXPAND + VERIFY; "
                    "dropped tickers didn't resolve on yfinance (bad symbol or no data), never silently omitted."}


def main():
    res = scan()
    OUT.write_text(json.dumps(res, indent=1))
    print(f"=== PREFERRED / BABY-BOND ODD-LOT SCANNER  {res['asof']}  "
          f"({res['resolved']}/{res['universe']} resolved, {len(res['candidates'])} candidates) ===")
    print("  ODD-LOT MISPRICING CANDIDATES (below par + illiquid — verify credit money-good in DD):")
    for r in res["candidates"][:12]:
        y = f"{r['current_yield_pct']:.1f}%y" if r["current_yield_pct"] else "y?"
        print(f"    {r['ticker']:8} {r['issuer'][:22]:22} ${r['price']:6.2f}  {r['disc_to_par_pct']:+5.1f}% vs par  "
              f"{y:7} ${r['dollar_vol_1d']/1e3:6.0f}k/d  score {r['oddlot_score']}")
    if res["dropped"]:
        print(f"  dropped (unresolved): {res['dropped']}")
    print(f"[-> {OUT.name}]")


if __name__ == "__main__":
    main()
