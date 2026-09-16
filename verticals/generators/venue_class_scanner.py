"""venue_class_scanner — Stage 0b generator: retailer VENUE-CLASS mix vs valuation (the A-mall lift screen).

THE MECHANISM (born from the BKE mall census + the malls-bifurcation theme, 2026-07-03): the market prices
"mall retailers" as a CATEGORY while actual venue-class mix varies enormously within it (BKE measured 12.3%
A-tier / 22.5% distressed; premium chains plausibly 60-70% A). A-mall traffic is verified recovering (+4.5-7.3%
real visits; SPG occupancy 95.7%) while B/C dies. If multiples don't discriminate by venue class, A-heavy names
carry the category discount without the category problem — and C-heavy names hide the decay.

THE MOAT: venue-mix data does NOT exist publicly — it must be built store-by-store (locator scrape x mall-owner
classification). Aggregation cost = the edge's half-life protection.

HONESTY DOCTRINE (encoded before first run):
 (1) landlords capture part of the lift — SPG's +MSD leasing spreads ARE tenant margin repricing; the 2-3yr
     lease lag delivers traffic before rent resets (near-term tenant-favorable, structurally shared);
 (2) causality is bidirectional — strong brands SELECT INTO A-malls; venue mix partly proxies brand heat,
     which IS priced. The claim is NARROW: venue mix = an unpriced quality discriminator WITHIN the cheap
     mall-retailer cohort, never a standalone buy signal;
 (3) FIRST DD TEST (BBW 2026-07-02): the long-side causal claim FAILED — the divergence (VQ 44 at 5.8x)
     had name-specific explanations (earnings plateau, CEO exit, tariff overhang, 22.7% short), NOT venue
     mispricing. Venue quality DID survive as a DOWNSIDE-SUPPORT input (good real estate floors the bear).
     RULE: before attributing any cheap-multiple divergence to venue-guilt, check the name-specific
     candidates first (plateau? management change? shorts? tariffs?); the screen's honest role so far is
     bear-case CALIBRATION (venue drag vs venue floor), not long generation;
 (4) validation pending: venue-mix vs comp-surprise correlation against the apparel ground-truth table
     (n small — say so). Seeds carry NO priority until validated. The scanner proposes; the pipeline disposes.

Census data lives in data/venue_class_census.json — populated by census agents (the BKE-method enumeration:
sample >=40 stores in top states, classify by property OWNER: Simon/Taubman/premier=A, Macerich/secondary=B,
CBL/WPG/Kohan/foreclosure=C, open-air/power/lifestyle=OA, outlet=OUT).

  python3 verticals/generators/venue_class_scanner.py
Writes data/VENUE_CLASS_SCREEN.json. READ-ONLY.
"""
from __future__ import annotations
import json, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
CENSUS = HERE / "data" / "venue_class_census.json"
OUT = HERE / "data" / "VENUE_CLASS_SCREEN.json"
UNCENSUSED = ["ANF", "AEO", "URBN", "ZUMZ", "TLYS", "BBWI", "VSCO", "BBW", "GES", "CRI"]


def _val(sym: str) -> dict:
    """Valuation snapshot via the desk price service + yfinance fundamentals (proposes-only precision)."""
    out = {"px": None, "ev_ebitda": None, "pe_fwd": None, "pct_off_52wk_hi": None}
    try:
        import yfinance as yf
        t = yf.Ticker(sym)
        fi = t.fast_info
        px, hi = fi.get("last_price"), fi.get("year_high")
        out["px"] = round(px, 2) if px else None
        if px and hi:
            out["pct_off_52wk_hi"] = round((px / hi - 1) * 100, 1)
        info = t.info
        out["ev_ebitda"] = info.get("enterpriseToEbitda")
        out["pe_fwd"] = info.get("forwardPE")
    except Exception:
        pass
    return out


def scan() -> dict:
    census = json.loads(CENSUS.read_text()) if CENSUS.exists() else {}
    rows = []
    for sym, c in census.items():
        mix = c.get("mix", {})
        a, b, cc = mix.get("A", 0), mix.get("B", 0), mix.get("C", 0)
        oa, outl = mix.get("OA", 0), mix.get("OUT", 0)
        # venue-quality score: A-share + open-air (both winning classes) minus distressed exposure
        vq = round(a + oa * 0.8 + outl * 0.5 - cc * 1.2, 1)
        rows.append({"symbol": sym, "A_pct": a, "B_pct": b, "C_pct": cc, "OA_pct": oa, "OUT_pct": outl,
                     "venue_quality": vq, "sample_n": c.get("sample_n"), "asof": c.get("asof"),
                     "census_note": (c.get("note") or "")[:120], **_val(sym)})
    rows.sort(key=lambda r: -(r["venue_quality"] or 0))
    return {"asof": datetime.date.today().isoformat(),
            "doctrine": "NARROW claim: venue mix = quality discriminator WITHIN the cheap mall-retailer cohort; "
                        "landlord-capture + brand-selection confounders encoded; seeds carry NO priority pre-validation",
            "screen": "LONG divergence = high venue_quality + cheap vs cohort; SHORT/AVOID tell = low venue_quality "
                      "masked by category multiple (the BKE-class venue drag, unmodeled)",
            "censused": rows, "uncensused_candidates": [u for u in UNCENSUSED if u not in census],
            "next": "dispatch census agents for uncensused candidates; validate venue-mix vs comp-surprise on the apparel ground truth"}


def main():
    res = scan()
    print(f"=== VENUE-CLASS SCANNER  {res['asof']}  ({len(res['censused'])} censused / {len(res['uncensused_candidates'])} pending) ===")
    for r in res["censused"]:
        print(f"   {r['symbol']:<5} A {r['A_pct']:>4.1f}%  B {r['B_pct']:>4.1f}%  C {r['C_pct']:>4.1f}%  OA {r['OA_pct']:>4.1f}%  "
              f"VQ {r['venue_quality']:>6.1f}  n={r['sample_n']}  EV/EBITDA {r['ev_ebitda'] or '—'}  off-hi {r['pct_off_52wk_hi'] or '—'}%")
    if res["uncensused_candidates"]:
        print(f"   PENDING CENSUS: {', '.join(res['uncensused_candidates'])}")
    OUT.write_text(json.dumps(res, indent=1))
    print(f"[-> {OUT.name}]")


if __name__ == "__main__":
    main()
