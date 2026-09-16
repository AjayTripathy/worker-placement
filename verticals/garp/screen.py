"""GARP orchestrator: universe (<$15B) -> multi-year fundamentals -> composite -> shortlist.

  python -m verticals.garp.screen [--top N] [--max-cap 15e9] [--adr-check K]

Writes data/garp_shortlist.json. Trailing-growth GARP (no forward estimates).
"""
from __future__ import annotations
import argparse, json, os
from ..deep_value import universe as U, fundamentals as DVF
from . import fundamentals as F, score as S

DATA = os.path.join(os.path.dirname(__file__), "data")


def run(top=25, max_cap=15e9, adr_check=60):
    uni = U.fetch_universe(min_mcap=1e8, max_mcap=max_cap)     # $100M–$15B, ex-fin
    print(f"universe (small/mid-cap ex-fin <${max_cap/1e9:.0f}B): {len(uni)}")
    cs = F.build_cross_section()
    cov = sum(1 for u in uni if u["cik"] in cs and cs[u["cik"]].get("Revenues_CY2025") is not None)
    print(f"fundamentals cross-section: {len(cs)} filers | universe FY2025-revenue coverage: {cov}")

    recs = [S.compute_metrics(u, cs[u["cik"]]) for u in uni if u["cik"] in cs]
    for r in recs:
        r["adr"] = r.get("country") not in ("United States", "")
    scored = S.composite(recs)
    sl = S.shortlist(scored)

    for r in sl[:adr_check]:                                    # robust ADR/VIE confirm on top-K
        if not r["adr"] and DVF.is_foreign_filer(r["cik"]):
            r["adr"] = True
    sl = [r for r in sl if not r["adr"]]

    os.makedirs(DATA, exist_ok=True)
    keys = ("sym", "cik", "mktcap", "px", "sec", "ind", "score", "g_score", "q_score", "p_score",
            "rev_cagr", "ni_cagr", "rev_yoy", "pe", "peg", "ev_ebit", "pfcf", "roic", "opm",
            "opm_trend", "nd_ebit", "decel", "noncash", "levered", "emerging", "base_effect")
    json.dump([{k: r.get(k) for k in keys} for r in sl[:80]],
              open(os.path.join(DATA, "garp_shortlist.json"), "w"), indent=1)

    def pct(x): return f"{x*100:.0f}%" if x is not None else " -"
    def num(x, d=1): return f"{x:.{d}f}" if x is not None else " -"
    def fmt(r):
        fl = " ".join(t for t, on in [("emerging", r["emerging"]), ("decel", r["decel"]),
                                      ("noncash", r["noncash"]), ("lev", r["levered"])] if on)
        return (f"  {r['sym']:6s}{r['mktcap']/1e9:6.1f}B  {pct(r['rev_cagr']):>5s}{pct(r['ni_cagr']):>6s}"
                f"{num(r['pe']):>6s}{num(r['peg'],2):>6s}{num(r['ev_ebit']):>6s}{pct(r['roic']):>6s}"
                f"{pct(r['opm']):>6s}   {r['sec'][:13]:13s} {fl}")
    print(f"\nGARP SHORTLIST (growth+quality+reasonable price; US, ex-ADR, profitable, FCF+)  n={len(sl)}")
    print(f"  {'sym':6s}{'mcap':>6s}  {'revG':>5s}{'epsG':>6s}{'P/E':>6s}{'PEG':>6s}{'EV/EB':>6s}{'ROIC':>6s}{'OpM':>6s}   sector  flags")
    for r in sl[:top]:
        print(fmt(r))
    return sl


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=25)
    ap.add_argument("--max-cap", type=float, default=15e9)
    ap.add_argument("--adr-check", type=int, default=60)
    a = ap.parse_args()
    run(a.top, a.max_cap, a.adr_check)
