"""aumovio_peer_watch — PREVIEW Aumovio's Aug-6-2026 H1 print before it lands, via the European tier-1
peer read-across. Aumovio's whole thesis hinges on ONE swing variable: does Q2 order intake recover
(book-to-bill back above 1.0) after the Q1'26 -32% collapse? Every relevant comp reports BEFORE Aug-6, so
their order-intake/book-to-bill trend previews whether Aumovio's -32% was an INDUSTRY air-pocket (structural,
dead-money) or IDIOSYNCRATIC to Aumovio (timing, "delayed not cancelled").

The watch is a LIVING previewer: as each peer reports (Valeo Jul-22 first), update its `trend`/`b2b` below and
`reported=True`; the read-across adjustment and the probability recompute. It also runs the PRICED-IN check —
our read-across-derived probability vs the market-implied probability from the live price — so we know whether
the Aug-6 order recovery is already discounted (it mostly is) or a fresh edge.

READ-ONLY. No orders. Built 2026-07-01 from a SignalOS read-across pass (see AMV0.DE.json `peer_readacross`).

  python3 verticals/deep_value/aumovio_peer_watch.py
"""
from __future__ import annotations
import json, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUMOVIO_REPORT = datetime.date(2026, 8, 6)
AUMOVIO_YF = "AMV0.DE"
IBKR_REF_PX = 37.85          # last authoritative IBKR IBIS snapshot 2026-07-01 (yfinance fallback/override)

# --- scenario FVs (from AMV0.DE.json): drives the priced-in / market-implied solve ---
FV = {"bear": 26.0, "base": 44.0, "bull": 55.0, "e_fv": 41.30, "net_cash_floor": 14.0}
P_BULL_TAIL = 0.10           # thin tail (strong beat / IHO-blessed deal)

# --- probability model for P(Q2 book-to-bill > 1.0) ---
BASE_PROB = 0.55             # single-quarter B2B>1.0 base rate for a lumpy tier-1 order book
CONCENTRATION_ADJ = 0.06     # -32% isolated to ACM (base effect); Q2'25 comp far easier (no PY mega-award)
STRUCTURAL_HAIRCUT = -0.11   # EU Mobility Package 2 volumes PERMANENTLY gone + some postponed noms slip to H2
P_MARGIN_LEG = 0.62          # the SECOND proof leg (H1 adj-EBITDA margin >3.5% + real FCF+); ~Nov Q3 first hard read

# Aumovio competes in ADAS/driver-assist, braking/safety, cockpit-electronics. CLOSE comps weight 2x.
CLOSE = {"FR.PA", "APTV", "EO.PA", "SHA0.DE"}
TREND_SCORE = {"strongly_improving": 2, "improving": 1, "stable_up": 1,
               "underlying_ok_optically_down_on_EDS_spin": 1,
               "stable": 0, "stable_booked": 0, "stable_mixshift": 0, "qualitative_stable": 0,
               "deteriorating": -1, "collapsing": -2, "na": None}

# report_date, before_aug6, book-to-bill / order-intake signal, trend. UPDATE as each prints (set reported+trend).
PEERS = [
    {"name": "Autoliv",     "tkr": "ALV",     "yf": "ALV",    "date": "2026-07-17", "b2b": "intake/share only; China OEMs >30% of 2025 intake", "trend": "stable_mixshift", "reported": False},
    {"name": "Valeo",       "tkr": "FR.PA",   "yf": "FR.PA",  "date": "2026-07-22", "b2b": "FY25 order intake EUR24.6B, +38% YoY (H2 +47%)", "trend": "strongly_improving", "reported": False},
    {"name": "Aptiv",       "tkr": "APTV",    "yf": "APTV",   "date": "2026-07-30", "b2b": "FY25 ~$27B; Q1'26 $4.6B (+15% vs qtly avg); FY26 >$20B", "trend": "underlying_ok_optically_down_on_EDS_spin", "reported": False},
    {"name": "ZF (private)","tkr": "-",       "yf": None,     "date": "2026-07-31", "b2b": "no formal # ; new BMW 8HP award", "trend": "stable", "reported": False, "est_date": True},
    {"name": "Forvia",      "tkr": "EO.PA",   "yf": "EO.PA",  "date": "2026-07-31", "b2b": "FY25 order intake EUR27B vs EUR31B (2024)", "trend": "deteriorating", "reported": False},
    {"name": "Magna",       "tkr": "MGA",     "yf": "MGA",    "date": "2026-07-31", "b2b": "no single backlog; 2028 ~90% booked", "trend": "stable_booked", "reported": False},
    {"name": "Continental", "tkr": "CON.DE",  "yf": "CON.DE", "date": "2026-08-04", "b2b": "N/A (auto order book moved to Aumovio)", "trend": "na", "reported": False},
    {"name": "Schaeffler",  "tkr": "SHA0.DE", "yf": "SHA.DE", "date": "2026-08-05", "b2b": "E-Mobility EUR15.5B new orders FY25; E-Mob rev +6% Q1'26", "trend": "stable_up", "reported": False},
    {"name": "BorgWarner",  "tkr": "BWA",     "yf": "BWA",    "date": "2026-08-05", "b2b": "award counts only (12 new awards Q1'26)", "trend": "qualitative_stable", "reported": False},
    {"name": "Bosch (priv)","tkr": "-",       "yf": None,     "date": "2026-08-05", "b2b": "Mobility ~EUR10B software/AD/sensor orders FY25", "trend": "stable", "reported": False, "est_date": True},
]

# Aumovio Q1'26 order-intake decomposition (from the Q1 results 2026-05-07).
Q1_DECOMP = {
    "intake_q1_26": 3949, "intake_q1_25": 5769, "yoy_pct": -31.5, "b2b": 0.90,  # b2b DERIVED (3949/~4400 sales)
    "concentration": "CONCENTRATED in ACM (Autonomous & Commercial Mobility)",
    "driver": "prior-year base effect: terminated EU Mobility Package 2 volumes + a large PY driver-assist mega-award; OEM sourcing POSTPONED not cancelled",
    "other_segments": "SAM/UX strong momentum, A&N major wins, UX recovered a Q4'25 postponed win",
    "structural_note": "part of the ACM base (Mobility Package 2) is PERMANENTLY terminated, not deferred — lowers the run-rate; the rest is timing",
}


def _px(yf_sym):
    if not yf_sym:
        return None
    try:
        import yfinance as yf
        s = yf.download(yf_sym, period="3d", progress=False, auto_adjust=True)["Close"].dropna()
        return round(float(s.iloc[-1]), 2) if len(s) else None
    except Exception:
        return None


def _read_across():
    """Weighted vote over peer trends -> industry read + probability adjustment. Recomputes as peers update."""
    num = den = 0.0
    imp = stab = det = 0
    for p in PEERS:
        sc = TREND_SCORE.get(p["trend"])
        if sc is None:
            continue
        w = 2.0 if p["tkr"] in CLOSE else 1.0
        num += sc * w
        den += w
        imp += sc > 0
        det += sc < 0
        stab += sc == 0
    wmean = (num / den) if den else 0.0
    adj = max(-0.10, min(0.15, round(wmean * 0.22, 3)))      # scale weighted-mean into a prob adjustment
    read = ("IDIOSYNCRATIC (industry NOT collapsing -> supports 'delayed not cancelled')" if wmean > 0.25 else
            "STRUCTURAL (industry-wide air-pocket -> Aumovio -32% would be sector, thesis dead-money)" if wmean < -0.25 else
            "MIXED")
    return adj, read, imp, stab, det, wmean


def market_implied_p_base(px):
    """Solve p_base from px = bear + p_base*(base-bear) + p_bull*(bull-bear), p_bull fixed tail."""
    b, base, bull = FV["bear"], FV["base"], FV["bull"]
    return round((px - b - P_BULL_TAIL * (bull - b)) / (base - b), 3)


# --- FIRE thresholds (what surfaces to the daily cron as actionable) ---
# edge_pp = P(proof) - market-implied P(base re-rate). It scales STEEPLY with price (e_FV fixed): ~+20pp at the
# EUR36 band top, ~+40pp at EUR31-32. So the edge threshold IS the entry-band discipline expressed as a number.
# CRITICAL asymmetry: only fire a BUY if the read-across is still idiosyncratic (p_proof high). A price drop with
# peers ALSO weak = the melting-ice-cube confirming => cheapness is a TRAP, not an edge => suppress (KILL-WATCH).
FIRE_ADD_EDGE = 20        # px re-entered the EUR31-36 band; below this = mostly-priced noise (today +11pp = quiet)
FIRE_STRONG_EDGE = 40     # deep-in-band "truck" level (~EUR31-32)
FRONTRUN_EDGE = 25        # front-run the print IF peers have de-risked the order leg
STRUCTURAL_KILL = 0.45    # p_proof below this = read-across flipped structural -> do NOT buy weakness
FRONT_HALF = {"FR.PA", "APTV", "EO.PA"}   # Valeo Jul-22 / Aptiv Jul-30 / Forvia Jul-31 — the pre-Aug-6 tells


def _fire(edge_pp, px, p_proof):
    """Return (level, surface_line). Only the definitive Aug-6 print (b2b>1.0 + margin>=3.5%) is a full add;
    pre-print fires are calibrated to the modest-conviction RP name + net-cash floor."""
    if p_proof < STRUCTURAL_KILL:
        return "KILL", f">>> FLAG KILL-WATCH: read-across flipped STRUCTURAL (p_proof {p_proof:.2f}) — Aumovio -32% looks sector-wide; cheapness = TRAP. Do NOT buy weakness; re-underwrite the thesis."
    confirmed = [p for p in PEERS if p["tkr"] in FRONT_HALF and p["reported"] and (TREND_SCORE.get(p["trend"]) or 0) >= 0]
    if edge_pp >= FRONTRUN_EDGE and len(confirmed) >= 2 and px <= 34:
        return "STRONG", f">>> FIRE-STRONG (front-run): edge +{edge_pp}pp, px EUR{px} in-band, {len(confirmed)}/3 front-half peers confirm idiosyncratic — order leg de-risked pre-print, add toward 1.5%."
    if edge_pp >= FIRE_STRONG_EDGE and px <= 32:
        return "STRONG", f">>> FIRE-STRONG: edge +{edge_pp}pp, px EUR{px} deep-in-band (truck) + read-across intact — add toward 1.5%."
    if edge_pp >= FIRE_ADD_EDGE and px <= 36:
        return "ADD", f">>> FIRE-ADD: edge +{edge_pp}pp, px EUR{px} entered the EUR31-36 band, read-across idiosyncratic — add the starter toward 1%."
    return "QUIET", f"    quiet: edge +{edge_pp}pp (mostly priced), px EUR{px} {'above band' if px > 36 else 'in-band but edge<20pp'} — no pre-print action; the definitive add is the Aug-6 print (b2b>1.0 + margin>=3.5%)."


def main():
    today = datetime.date.today()
    dte = (AUMOVIO_REPORT - today).days
    px = _px(AUMOVIO_YF) or IBKR_REF_PX
    src = "yfinance" if _px(AUMOVIO_YF) else f"IBKR ref {IBKR_REF_PX} (yfinance unavail)"

    adj, read, imp, stab, det, wmean = _read_across()
    p_order = round(BASE_PROB + adj + CONCENTRATION_ADJ + STRUCTURAL_HAIRCUT, 2)
    p_proof = round(0.5 * p_order + 0.5 * min(p_order, P_MARGIN_LEG), 2)   # correlated blend of the two legs
    mkt_p = market_implied_p_base(px)
    edge_pp = round((p_proof - mkt_p) * 100)
    e_fv_gap = round(FV["e_fv"] - px, 2)
    e_fv_pct = round(e_fv_gap / px * 100)

    print(f"=== AUMOVIO PEER READ-ACROSS WATCH  {today}  (preview the Aug-6 print; READ-ONLY) ===")
    print(f"  Aumovio AMV0.DE  EUR {px}  ({src}) | H1 print {AUMOVIO_REPORT} in {dte}d | swing = Q2 book-to-bill > 1.0?")

    print(f"\n  PEER PREVIEW CALENDAR (all report BEFORE Aug-6; * = closest ADAS/braking/electronics comp):")
    for p in sorted(PEERS, key=lambda x: x["date"]):
        d = datetime.date.fromisoformat(p["date"])
        away = (d - today).days
        star = "*" if p["tkr"] in CLOSE else " "
        est = " (est date)" if p.get("est_date") else ""
        flag = ""
        if p["trend"] != "na":
            if d < today and not p["reported"]:
                flag = "  <<< REPORTED — UPDATE its Q2 order intake + trend + reported=True"
            elif 0 <= away <= 3:
                flag = "  <<< IMMINENT — the fresh tell"
        rep = "[reported]" if p["reported"] else ""
        print(f"   {star}{p['date']} ({away:+d}d) {p['tkr']:<8} {p['name']:<14} {rep:<10} {p['trend']:<24} {p['b2b'][:52]}{est}{flag}")

    print(f"\n  INDUSTRY READ: {read}")
    print(f"   votes: {imp} improving / {stab} stable / {det} deteriorating  (weighted-mean trend {wmean:+.2f}; Valeo +38% is the anchor, only Forvia softens ~-13%)")

    print(f"\n  AUMOVIO Q1 -32% DECOMP: {Q1_DECOMP['concentration']}  (intake {Q1_DECOMP['intake_q1_26']} vs {Q1_DECOMP['intake_q1_25']} = {Q1_DECOMP['yoy_pct']}%, b2b ~{Q1_DECOMP['b2b']} derived)")
    print(f"   driver: {Q1_DECOMP['driver']}")
    print(f"   other 3 segments: {Q1_DECOMP['other_segments']}")
    print(f"   !! {Q1_DECOMP['structural_note']}")

    print(f"\n  PROBABILITY  P(Q2 book-to-bill > 1.0) = {p_order:.2f}")
    print(f"   base {BASE_PROB:+.2f}  read-across {adj:+.2f}  concentration/easier-Q2-comp {CONCENTRATION_ADJ:+.2f}  structural {STRUCTURAL_HAIRCUT:+.2f}")
    print(f"   P(full proof: order + margin>3.5% + FCF+) ~= {p_proof:.2f}   (margin leg ~{P_MARGIN_LEG:.2f}, first hard read ~Nov Q3)")

    print(f"\n  PRICED-IN CHECK  @ EUR {px}:")
    print(f"   market-implied p(base re-rate) = {mkt_p:.2f}   [solve bear{FV['bear']:.0f}/base{FV['base']:.0f}/bull{FV['bull']:.0f}, {P_BULL_TAIL:.0%} tail]")
    print(f"   our p(proof) = {p_proof:.2f}   ->  EDGE {edge_pp:+d}pp")
    print(f"   prob-wtd e_FV EUR {FV['e_fv']} vs EUR {px} = {e_fv_gap:+.2f} ({e_fv_pct:+d}%); downside floored ~EUR{FV['net_cash_floor']:.0f} net cash + IHO 46% anchor")
    verdict = ("MOSTLY PRICED / modest under-pricing" if 0 < edge_pp <= 15 else
               "UNDER-PRICED (fresh edge)" if edge_pp > 15 else
               "FULLY PRICED / dead money" if -5 <= edge_pp <= 0 else "OVER-PRICED (fade)")
    print(f"   VERDICT: {verdict}. The order-recovery leg is largely priced (stock re-rated into the print);")
    print(f"            residual asymmetry = the 2nd proof leg (margin/FCF, ~Nov) + the net-cash floor, NOT the order line.")

    # --- FIRE (what the daily cron surfaces) ---
    stale = [p["name"] for p in PEERS if p["trend"] != "na"
             and datetime.date.fromisoformat(p["date"]) < today and not p["reported"]]
    if stale:
        print(f"\n  >>> FLAG UPDATE-NEEDED: {', '.join(stale)} reported — refresh Q2 order intake + trend + reported=True in the watch, then re-run.")
    level, msg = _fire(edge_pp, px, p_proof)
    print(f"\n  {msg}")

    print(f"\n  ACTION: starter 0.5-1.0% @ EUR31-36 (Xetra AMV0, not PINK AMVOY); ADD to ~1.5% only on Aug-6 confirming")
    print(f"          Q2 book-to-bill > 1.0 AND margin stepping to >=3.5%. Front-half tells: Valeo Jul-22, Aptiv Jul-30, Forvia Jul-31.")


if __name__ == "__main__":
    main()
