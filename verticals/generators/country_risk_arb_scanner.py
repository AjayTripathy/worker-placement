"""country_risk_arb_scanner — Stage 0b generator: companies trading at a WIDER discount than their
country risk justifies (Damodaran CRP vs market-implied premium).

Method: implied country premium = earnings-yield gap vs the US sector median (banks use COE = ROE/(P/B),
more robust than 1/PE for financials); EXCESS = implied - Damodaran CRP. FIVE HARD GUARDS (each a
demonstrated false-positive source from the 2026-07-02 build run):
  1. low-rating-CRP structural exclusion (China/VIE names — the sovereign rating misses delisting risk)
  2. hyperinflation gate (TRY/ARS/EGP nominal-EPS denominators are fake — excluded)
  3. bond-dominance 2x floor as a HARD GATE (TBC lesson: clearing 1x != edge; those go to a risk-premium tier)
  4. state-control flag (Petrobras pattern — appropriation discounts are correctly priced)
  5. sector-cheapness check (autos/cement cheap GLOBALLY != country dislocation; per-sector US medians)
Scanner proposes; the pipeline disposes. Quarterly relevance (Damodaran updates Jan/Jul) — the run
no-ops unless >75 days old or forced.

  python3 verticals/generators/country_risk_arb_scanner.py [--force]
Writes data/COUNTRY_RISK_ARB.json. READ-ONLY.
"""
from __future__ import annotations
import json, sys, math, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "data" / "COUNTRY_RISK_ARB.json"

# Damodaran vintage 2026-01-05 (embedded; refresh embedded table when he posts Jan/Jul updates)
VINTAGE = "2026-01-05"
CRP = {"Korea": 0.64, "Poland": 1.10, "Brazil": 3.24, "Colombia": 2.85, "Mexico": 2.07, "Chile": 1.10,
       "Peru": 2.07, "Greece": 2.85, "Kazakhstan": 2.07, "Georgia": 3.24, "Indonesia": 2.46,
       "Philippines": 2.46, "India": 2.07, "SouthAfrica": 3.24, "Japan": 0.91, "Israel": 1.31,
       "Italy": 2.46, "Spain": 1.55, "UK": 0.91}
DEFSPREAD = {"Korea": 0.42, "Poland": 0.72, "Brazil": 2.13, "Colombia": 1.87, "Mexico": 1.36,
             "Chile": 0.72, "Peru": 1.36, "Greece": 1.87, "Kazakhstan": 1.36, "Georgia": 2.13,
             "Indonesia": 1.61, "Philippines": 1.61, "India": 1.36, "SouthAfrica": 2.13,
             "Japan": 0.60, "Israel": 0.86, "Italy": 1.61, "Spain": 1.02, "UK": 0.60}
EXCLUDED_STRUCTURAL = {"China", "HongKong"}          # guard 1
EXCLUDED_INFLATION = {"Turkey", "Argentina", "Egypt", "Nigeria"}   # guard 2
STATE_CONTROL_FLAGS = {"PBR", "PEO.WA", "VALE"}      # guard 4 (flag, not auto-kill for banks)

# universe: (yf ticker, country, sector, name) — liquid ADRs/foreign lines
UNIVERSE = [
 ("316140.KS","Korea","bank","Woori Financial"),("055550.KS","Korea","bank","Shinhan"),
 ("086790.KS","Korea","bank","Hana Financial"),("PEO.WA","Poland","bank","Pekao"),
 ("SPL.WA","Poland","bank","Santander Polska"),("PKO.WA","Poland","bank","PKO BP"),
 ("BBD","Brazil","bank","Bradesco"),("ITUB","Brazil","bank","Itau"),("BSBR","Brazil","bank","Santander Brasil"),
 ("CIB","Colombia","bank","Bancolombia"),("BCH","Chile","bank","Banco de Chile"),("BAP","Peru","bank","Credicorp"),
 ("SBS","Brazil","utility","Sabesp"),("EBR","Brazil","utility","Eletrobras"),
 ("KOF","Mexico","staples","Coca-Cola Femsa"),("FMX","Mexico","staples","FEMSA"),
 ("TLK","Indonesia","telecom","Telkom Indonesia"),("PHI","Philippines","telecom","PLDT"),
 ("HDB","India","bank","HDFC Bank"),("IBN","India","bank","ICICI"),
 ("ETE.AT","Greece","bank","National Bank of Greece"),("EUROB.AT","Greece","bank","Eurobank"),
]
US_MEDIAN = {"bank": {"pe": 14.3, "coe": 0.098}, "utility": {"pe": 18.0}, "staples": {"pe": 20.0},
             "telecom": {"pe": 12.0}, "energy": {"pe": 18.0}, "auto": {"pe": 6.5}}


def main():
    force = "--force" in sys.argv
    if OUT.exists() and not force:
        prev = json.loads(OUT.read_text())
        age = (datetime.date.today() - datetime.date.fromisoformat(prev.get("asof", "2000-01-01"))).days
        if age < 75:
            print(f"country_risk_arb: last run {age}d ago (<75d quarterly cadence) — no-op. --force to override.")
            return
    import yfinance as yf
    rows, rejects = [], []
    for sym, ctry, sector, name in UNIVERSE:
        if ctry in EXCLUDED_STRUCTURAL:
            rejects.append({"name": name, "guard": "structural-CRP-understatement"}); continue
        if ctry in EXCLUDED_INFLATION:
            rejects.append({"name": name, "guard": "hyperinflation nominal-EPS"}); continue
        try:
            t = yf.Ticker(sym); info = t.info
            pe = info.get("trailingPE"); pb = info.get("priceToBook"); roe = info.get("returnOnEquity")
            px = info.get("currentPrice") or info.get("regularMarketPrice")
        except Exception:
            continue
        implied = None
        if sector == "bank" and pb and roe and 0.2 < pb < 5 and 0 < roe < 0.5:
            # GUARD 6 (PHI mislabel 2026-07-03): the ROE/PB=CoE shortcut is ONLY valid for actual
            # depositories — verify from the feed's industry, never the input list's tag
            ind = (info.get("industry") or "") + " " + (info.get("sector") or "")
            if "bank" not in ind.lower():
                rejects.append({"name": name, "guard": f"sector-tag says bank but feed industry says '{ind.strip()[:40]}' — mislabel"})
                continue
            coe = roe / pb                       # bank COE track (guard: sane pb/roe only)
            # GUARD 7 (BCH ADR-book artifact 2026-07-03: implied 20% vs truth 6.3%): for a bank,
            # ROE/PB must ~equal the earnings yield 1/PE (same equity denominator). Divergence >40%
            # means the book value is on the wrong ADR-share/currency basis — yfinance priceToBook
            # is UNRELIABLE for ADRs; reject rather than report a fabricated edge.
            if pe and pe > 1:
                ey = 1.0 / pe
                if coe > 0 and abs(coe - ey) / max(coe, ey) > 0.4:
                    rejects.append({"name": name, "guard": f"CoE {coe:.1%} vs earnings-yield {ey:.1%} diverge — ADR book-basis artifact (BCH lesson)"})
                    continue
            implied = (coe - US_MEDIAN["bank"]["coe"]) * 100
        elif pe and 1 < pe < 60:
            implied = (1/pe - 1/US_MEDIAN.get(sector, {"pe": 17.0})["pe"]) * 100
        if implied is None:
            continue
        if abs(implied) > 25:                      # ADR/currency artifact trap (CIB COP-book lesson)
            rejects.append({"name": name, "guard": f"data-artifact implied {implied:.0f}pp — currency-mismatched book/EPS"})
            continue
        excess = implied - CRP[ctry]
        floor2 = DEFSPREAD[ctry] * 2
        gate = "EDGE_2x" if implied > floor2 and excess > 0.5 else \
               ("RISK_PREMIUM_1x" if implied > DEFSPREAD[ctry] else "FAILS_FLOOR")
        rows.append({"ticker": sym, "name": name, "country": ctry, "px": px, "sector": sector,
                     "implied_pp": round(implied, 1), "crp_pp": CRP[ctry], "excess_pp": round(excess, 1),
                     "floor_2x_pp": round(floor2, 2), "gate": gate,
                     "state_flag": sym in STATE_CONTROL_FLAGS})
    rows.sort(key=lambda r: -r["excess_pp"])
    res = {"asof": datetime.date.today().isoformat(), "crp_vintage": VINTAGE,
           "note": "scanner PROPOSES; guards 1-5 hard-coded; EDGE_2x tier only = candidates; refresh embedded CRP each Jan/Jul",
           "edge_tier": [r for r in rows if r["gate"] == "EDGE_2x"],
           "risk_premium_tier": [r for r in rows if r["gate"] == "RISK_PREMIUM_1x"],
           "fails": [r for r in rows if r["gate"] == "FAILS_FLOOR"], "guard_rejects": rejects}
    OUT.write_text(json.dumps(res, indent=1))
    print(f"=== COUNTRY-RISK ARB SCANNER  {res['asof']}  (CRP vintage {VINTAGE}; {len(rows)} scored) ===")
    for r in res["edge_tier"][:10]:
        print(f"   {r['ticker']:<11} {r['name']:<22} {r['country']:<10} implied {r['implied_pp']:>5}pp  CRP {r['crp_pp']:>4}  EXCESS {r['excess_pp']:+5}pp  {'STATE-FLAG' if r['state_flag'] else ''}")
    print(f"  risk-premium tier: {[r['ticker'] for r in res['risk_premium_tier']]}")
    print(f"[-> {OUT.name}]")


if __name__ == "__main__":
    main()
