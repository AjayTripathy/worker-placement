"""crossborder_twin_scanner — Stage 0b generator: EM/DM TWIN-PAIR valuation gaps vs justified country risk.

USER HYPOTHESIS (2026-07-03): find companies with comparables in low-risk countries whose valuation gap
EXCEEDS what the country risk premium justifies. Twin pairs (parent/subsidiary or same-business) isolate
the country+structure wedge better than sector medians.

FOUR GUARDS ENCODED FROM THE WEEK'S LESSONS (before first run, so the first run can't flatter itself):
 (1) GROWTH: a PE gap explained by a growth differential is DESERVED (GARP/PEG-fragility lesson) —
     every pair carries rev-growth columns; excess with growth_gap > 3pp against the EM name = suspect;
 (2) STRUCTURE-EARNED: controlling shareholders / float / withholding make discounts PARTLY CORRECT
     (BSBR verdict 2026-07-03) — curated structural notes render beside the number, never hidden;
 (3) LAMBDA: CRP applies to where revenue is EARNED not where the ticker lists (Damodaran λ);
     curated lambda_em on each pair (1.0 = fully domestic);
 (4) DATA BASIS: no ADR priceToBook anywhere; PE-only math with 1<PE<80 sanity + trailing-vs-forward
     flagged; any |excess| > 15pp = artifact trap (ADR/currency basis, the BCH class), rejected.
The scanner proposes; the pipeline disposes. Seeds carry NO priority pre-validation.

  python3 verticals/generators/crossborder_twin_scanner.py
Writes data/CROSSBORDER_TWINS.json. READ-ONLY.
"""
from __future__ import annotations
import json, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "data" / "CROSSBORDER_TWINS.json"

# Damodaran CRP (Jan-2026 vintage, pp) — subset needed by the pairs table
CRP = {"Brazil": 3.24, "Mexico": 2.42, "Indonesia": 2.46, "India": 2.26, "Chile": 1.10,
       "Peru": 2.05, "Colombia": 2.85, "Poland": 1.10, "Philippines": 2.46, "S.Africa": 3.43,
       "Malaysia": 1.64, "Thailand": 2.26, "US": 0.0, "UK": 0.79, "Switzerland": 0.0,
       "Netherlands": 0.0, "France": 0.79, "Germany": 0.0, "Japan": 0.99}

# curated twin pairs: (em_ticker, em_name, em_country, lambda_em, dm_ticker, dm_name, dm_country, match_quality, structure_note)
PAIRS = [
 ("WALMEX.MX","Wal-Mart de México","Mexico",0.95,"WMT","Walmart","US","parent-sub","WMT owns ~70%; float ok; same format/brand"),
 ("KOF","Coca-Cola FEMSA (ADR)","Mexico",0.85,"KO","Coca-Cola","US","system-twin","KO owns ~28% + FEMSA control; bottler vs brand — margin structure differs"),
 ("AC.MX","Arca Continental","Mexico",0.80,"KO","Coca-Cola","US","system-twin","bottler vs brand caveat as KOF"),
 ("ABEV","Ambev (ADR)","Brazil",0.90,"BUD","AB InBev","Belgium","parent-sub","ABI owns ~62%; same brands; BUD itself carries EM mix (lambda_dm high)"),
 ("UNVR.JK","Unilever Indonesia","Indonesia",1.00,"ULVR.L","Unilever plc","UK","parent-sub","parent owns ~85%; float thin; SAME products"),
 ("HINDUNILVR.NS","Hindustan Unilever","India",1.00,"ULVR.L","Unilever plc","UK","parent-sub","parent ~62%; the REVERSE tell — India glamour premium"),
 ("NESTLEIND.NS","Nestlé India","India",1.00,"NESN.SW","Nestlé SA","Switzerland","parent-sub","parent ~63%; reverse-tell candidate"),
 ("CX","Cemex (ADR)","Mexico",0.60,"HOLN.SW","Holcim","Switzerland","same-business","CX ~40% US/EU revenue -> lambda 0.6; leverage differs (CX heavier)"),
 ("TLK","Telkom Indonesia (ADR)","Indonesia",1.00,"DTE.DE","Deutsche Telekom","Germany","same-business","SOE (state 52%) — structure-earned discount candidate"),
 ("BAP","Credicorp (Peru)","Peru",0.90,"JPM","JPMorgan","US","same-business","bank pair kept for continuity w/ CRP scanner; Lima-listed via NYSE holdco"),
 ("SQM","SQM (ADR)","Chile",0.70,"ALB","Albemarle","US","same-business","lithium twins; both cyclical — PE unstable at cycle turns, EV/EBITDA sanity advised"),
 ("GFNORTEO.MX","Banorte","Mexico",1.00,"USB","US Bancorp","US","same-business","bank; no controlling parent (true float) — cleaner than BSBR"),
 ("BIMBOA.MX","Grupo Bimbo","Mexico",0.55,"K","Kellanova/US packaged","US","same-business","~45% US revenue -> lambda 0.55"),
 ("JSE-like SAB? skip","","S.Africa",1.0,"","","","skip","placeholder pruned at runtime"),
 ("MHPC.L","MHP (Ukraine GDR)","Ukraine",1.0,"TSN","Tyson Foods","US","same-business","war-risk extreme case; CRP table lacks Ukraine -> handled as 15pp manual"),
]
US_ERP = 4.23


def _met(sym):
    try:
        import yfinance as yf
        info = yf.Ticker(sym).info
        pe_f = info.get("forwardPE"); pe_t = info.get("trailingPE")
        g = info.get("revenueGrowth")
        pe = pe_f if pe_f and 1 < pe_f < 80 else (pe_t if pe_t and 1 < pe_t < 80 else None)
        return pe, ("fwd" if pe is pe_f else "trl"), (round(g * 100, 1) if g is not None else None)
    except Exception:
        return None, None, None


def scan():
    rows, rejects = [], []
    for em, em_n, ctry, lam, dm, dm_n, dm_c, quality, note in PAIRS:
        if quality == "skip" or not dm:
            continue
        pe_e, basis_e, g_e = _met(em)
        pe_d, basis_d, g_d = _met(dm)
        if not pe_e or not pe_d:
            rejects.append({"pair": f"{em}/{dm}", "guard": "no usable PE"})
            continue
        ey_gap = (1 / pe_e - 1 / pe_d) * 100
        crp = CRP.get(ctry, 15.0 if ctry == "Ukraine" else None)
        if crp is None:
            rejects.append({"pair": f"{em}/{dm}", "guard": f"no CRP for {ctry}"})
            continue
        justified = crp * lam - CRP.get(dm_c, 0.0)
        excess = ey_gap - justified
        if abs(excess) > 15:
            rejects.append({"pair": f"{em}/{dm}", "guard": f"artifact trap |excess| {excess:.0f}pp (BCH class)"})
            continue
        growth_gap = (g_d - g_e) if (g_d is not None and g_e is not None) else None
        growth_flag = bool(growth_gap is not None and growth_gap > 3 and excess > 0)
        rows.append({"em": em, "em_name": em_n, "dm": dm, "country": ctry, "lambda": lam,
                     "pe_em": round(pe_e, 1), "pe_dm": round(pe_d, 1), "basis": f"{basis_e}/{basis_d}",
                     "ey_gap_pp": round(ey_gap, 1), "justified_pp": round(justified, 1),
                     "excess_pp": round(excess, 1), "rev_g_em": g_e, "rev_g_dm": g_d,
                     "growth_explains": growth_flag, "match": quality, "structure": note})
    rows.sort(key=lambda r: -r["excess_pp"])
    return {"asof": datetime.date.today().isoformat(), "crp_vintage": "Jan-2026",
            "doctrine": "guards 1-4 in docstring; excess>0 + growth_explains=False + structure surmountable = candidate; "
                        "NEGATIVE excess rows = glamour-premium calibration (the India tell), not shorts",
            "pairs": rows, "rejects": rejects}


BASELINE = HERE / "data" / "CROSSBORDER_TWINS_BASELINE_20260703.json"
DRIFT_FLAG_PP = 2.0     # a pair moving >=2pp vs its baseline excess = a dislocation candidate, not a level


def main():
    res = scan()
    # dislocation detection: daily cadence exists to catch a pair BLOWING OUT vs its own history
    try:
        base = {p["em"]: p["excess_pp"] for p in json.loads(BASELINE.read_text()).get("pairs", [])}
        for p in res["pairs"]:
            b = base.get(p["em"])
            if b is not None:
                p["drift_pp"] = round(p["excess_pp"] - b, 1)
    except Exception:
        pass
    print(f"=== CROSS-BORDER TWIN SCANNER  {res['asof']}  ({len(res['pairs'])} pairs, {len(res['rejects'])} rejected) ===")
    for p in res["pairs"]:
        d = p.get("drift_pp")
        if d is not None and abs(d) >= DRIFT_FLAG_PP:
            print(f"  >>> FLAG TWIN-DISLOCATION: {p['em']} vs {p['dm']} excess moved {d:+}pp vs the Jul-2026 baseline "
                  f"(now {p['excess_pp']}pp) — check what broke: FX panic / country headline / earnings; "
                  f"same-business pair = the Oakland-playbook shape IF the cause doesn't touch the business")
    for r in res["pairs"]:
        gf = " GROWTH-EXPLAINED" if r["growth_explains"] else ""
        print(f"  {r['em']:<14} PE {r['pe_em']:>5} vs {r['dm']:<7} PE {r['pe_dm']:>5} | EY gap {r['ey_gap_pp']:>5}pp"
              f" just. {r['justified_pp']:>4}pp -> EXCESS {r['excess_pp']:>5}pp{gf} | {r['structure'][:45]}")
    for x in res["rejects"]:
        print(f"  REJECT {x['pair']}: {x['guard']}")
    OUT.write_text(json.dumps(res, indent=1))
    print(f"[-> {OUT.name}]  The scanner proposes; the pipeline disposes.")


if __name__ == "__main__":
    main()
