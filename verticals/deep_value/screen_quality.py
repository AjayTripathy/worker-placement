"""Quality-overlay orchestrator: universe -> TTM fundamentals -> cheapness metrics + QUALITY gates
-> Magic-Formula (cheap AND good) rank. The cheap-and-quality survivor list for the small-cap
rotation thesis — far less trap-dense than the raw 'cheapest' screen.

  python -m verticals.deep_value.screen_quality [--top N]

Writes data/quality_shortlist.json.
"""
from __future__ import annotations
import argparse, json, os
from . import universe as U, fundamentals as F, score as S, quality as Q

DATA = os.path.join(os.path.dirname(__file__), "data")


def _range_positions(tickers):
    """52w-range position (0=at low, 1=at high) per ticker — the CCSI/EZPW lesson: a cheap MULTIPLE at the
    52w HIGH (already re-rated) is a different setup than the same multiple at the low. Soft flag, not a gate."""
    try:
        import yfinance as yf
        df = yf.download(list(tickers), period="1y", progress=False, auto_adjust=True)["Close"]
        out = {}
        for t in tickers:
            try:
                s = (df[t] if t in getattr(df, "columns", []) else df).dropna()
                lo, hi, last = float(s.min()), float(s.max()), float(s.iloc[-1])
                out[t] = round((last - lo) / (hi - lo), 2) if hi > lo and len(s) >= 20 else None
            except Exception:
                out[t] = None
        return out
    except Exception:
        return {}


def _parametric_holdings():
    """Parametric SMA holdings — to keep the harvest book DISJOINT (no cross-account wash sales)."""
    import sqlite3, os as _os
    db = _os.environ.get("MSPRIME_DB", "/Users/ajay/msprime/app/data/msprime.db")
    if not _os.path.exists(db):
        return set()
    con = sqlite3.connect(db)
    try:
        d = con.execute("SELECT MAX(reporting_date) FROM positions WHERE length(reporting_date)=10 AND reporting_date LIKE '2026-%'").fetchone()[0]
        return {r[0] for r in con.execute("SELECT DISTINCT symbol FROM positions WHERE reporting_date=? AND symbol!='USD'", (d,))}
    finally:
        con.close()


def run(top=30, adr_check=90, include_foreign=False, disjoint_parametric=False, max_mcap=2e9):
    from . import pfic_screen as PF
    uni = U.fetch_universe(max_mcap=max_mcap)
    print(f"universe (ex-fin, mcap<${max_mcap/1e9:.0f}B): {len(uni)}  | include_foreign={include_foreign}")
    cs = F.build_cross_section()
    print(f"fundamentals cross-section (us-gaap): {len(cs)} filers")
    if include_foreign:
        from . import ifrs_fundamentals as IF
        fcik = {u["cik"] for u in uni if u.get("country") not in ("United States", "", None)} - set(cs)
        print(f"pulling IFRS fundamentals for {len(fcik)} uncovered foreign filers (annual)...")
        ifrs = IF.fetch_ifrs_cross_section(fcik)
        cs.update(ifrs)
        print(f"  +{len(ifrs)} IFRS filers added (now {len(cs)} total)")
    para = _parametric_holdings() if disjoint_parametric else set()

    cand, rejects = [], {}
    for u in uni:
        f = cs.get(u["cik"])
        if not f:
            continue
        r = S.compute_metrics(u, f)
        r["foreign"] = r.get("country") not in ("United States", "")
        r["adr"] = r["foreign"]
        if r["foreign"]:
            if not include_foreign:
                continue
            pf = PF.pfic_risk(r, f)          # PFIC landmine filter on foreign names
            r["pfic"] = pf
            if pf.get("pfic"):
                rejects["PFIC"] = rejects.get("PFIC", 0) + 1
                continue
            r["adr"] = False                 # PFIC-screened foreign name stays in
        q = Q.compute_quality(r, f)
        ok, why = Q.passes_quality(r, q)
        if ok:
            r["q"] = q
            cand.append(r)
        else:
            rejects[why.split(" (")[0].split(" ")[0] if why == "ok" else why.split(" ")[0]] = \
                rejects.get(why.split(" ")[0], 0) + 1

    # on the cheapest by earn-yield: confirm ADR + GATE OUT pending-merger names (the CPRX catch — a stock
    # at its deal price is a merger claim, not value), then magic-formula rank
    cand.sort(key=lambda r: -(r["q"]["earn_yield"] or 0))
    n_merger = 0
    for r in cand[:adr_check]:
        if not include_foreign and F.is_foreign_filer(r["cik"]):
            r["adr"] = True
        elif F.merger_pending(r["cik"]):
            r["merger"] = True
            n_merger += 1
    cand = [r for r in cand if not r.get("adr") and not r.get("merger")]
    # keep the harvest book DISJOINT from the Parametric SMA (wash-sale safety)
    n_overlap = 0
    if para:
        before = len(cand)
        cand = [r for r in cand if r["sym"] not in para]
        n_overlap = before - len(cand)
    ranked = Q.magic_formula(cand)
    # 52w-range position on the displayed shortlist (soft flag: HI = top quartile = already re-rated)
    rng = _range_positions([r["sym"] for r in ranked[:max(top, 30)]])
    for r in ranked:
        r["rng"] = rng.get(r["sym"])
    if n_merger:
        print(f"[merger-pending excluded: {n_merger}]")

    os.makedirs(DATA, exist_ok=True)
    out = [{**{k: r[k] for k in ("sym", "cik", "mktcap", "px", "sec", "ind", "am", "fcfy", "pb",
            "ev", "ebit", "fcf", "netcash")}, **r["q"], "mf_rank": r["mf_rank"],
            "foreign": r.get("foreign", False), "country": r.get("country"),
            "pfic_screen": r.get("pfic", {}).get("reason") if r.get("foreign") else "US",
            "ebit_quality": r["q"].get("ebit_quality")} for r in ranked]
    fname = "verified_harvest_candidates.json" if (include_foreign or disjoint_parametric) else "quality_shortlist.json"
    json.dump(out, open(os.path.join(DATA, fname), "w"), indent=1, default=str)
    print(f"[-> {fname}: {len(out)} disjoint candidates"
          + (f"; {n_overlap} Parametric-overlaps excluded" if para else "")
          + (f"; {rejects.get('PFIC', 0)} PFIC-flagged excluded" if include_foreign else "") + "]")

    print(f"\nrejects by gate: {dict(sorted(rejects.items(), key=lambda x: -x[1]))}")
    print(f"\nCHEAP-AND-QUALITY SURVIVORS (Magic-Formula rank; US, fresh, ROIC>10%, <3.5x lev, EBIT not collapsing)  n={len(ranked)}")
    print(f"  {'#':>2} {'sym':6s}{'mc$M':>7s}{'EV/EBIT':>8s}{'EYld':>6s}{'ROIC':>6s}{'EBITg':>7s}{'NDbt/E':>7s}{'52wRng':>7s}  sector")
    print("     (52wRng: position in 52w range, 0=low/1=high; >0.75 = HI = already re-rated, deprioritize)")
    for i, r in enumerate(ranked[:top], 1):
        q = r["q"]
        am = f"{r['am']:.1f}" if r["am"] else "sub$"
        ey = f"{q['earn_yield']*100:.0f}%" if q["earn_yield"] else " -"
        rc = f"{q['roic']*100:.0f}%" if q["roic"] else " -"
        gr = f"{q['ebit_growth']*100:+.0f}%" if q["ebit_growth"] is not None else " -"
        nd = f"{q['net_debt_ebit']:.1f}" if q["net_debt_ebit"] is not None else ("nc" if (r.get('netcash') or 0) > 0 else " -")
        rp = r.get("rng")
        rng_s = (f"{rp:.2f}{'HI' if rp >= 0.75 else ''}") if rp is not None else " -"
        eq = q.get("ebit_quality", "clean")
        flag = "" if eq == "clean" else "  ⚠ " + eq
        print(f"  {i:>2} {r['sym']:6s}{r['mktcap']/1e6:7.0f}{am:>8s}{ey:>6s}{rc:>6s}{gr:>7s}{nd:>7s}{rng_s:>7s}  {r['sec'][:16]}{flag}")
    return ranked


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=40)
    ap.add_argument("--include-foreign", action="store_true", help="include US-listed foreign filers, PFIC-screened")
    ap.add_argument("--disjoint", action="store_true", help="exclude names the Parametric SMA holds (wash-sale safety)")
    ap.add_argument("--all-cap", action="store_true", help="all market caps, not just micro/small")
    a = ap.parse_args()
    run(a.top, include_foreign=a.include_foreign, disjoint_parametric=a.disjoint,
        max_mcap=1e13 if a.all_cap else 2e9)
