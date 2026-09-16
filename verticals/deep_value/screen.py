"""Orchestrator: universe -> TTM fundamentals -> composite -> shortlist.

  python -m verticals.deep_value.screen [--top N] [--adr-check K]

Writes data/shortlist.json. ADR check (20-F filer test) runs on the top-K only to
keep it cheap; the country field alone is unreliable.
"""
from __future__ import annotations
import argparse, json, os
from . import universe as U, fundamentals as F, score as S

DATA = os.path.join(os.path.dirname(__file__), "data")


def run(top=25, adr_check=60):
    uni = U.fetch_universe()
    print(f"universe (micro/small-cap ex-fin): {len(uni)}")
    cs = F.build_cross_section()
    cov = sum(1 for u in uni if u["cik"] in cs and cs[u["cik"]].get("OperatingIncomeLoss") is not None)
    print(f"fundamentals cross-section: {len(cs)} filers | universe EBIT coverage: {cov}")

    recs = [S.compute_metrics(u, cs[u["cik"]]) for u in uni if u["cik"] in cs]
    for r in recs:                                  # cheap first-pass ADR tag (country field)
        r["adr"] = r.get("country") not in ("United States", "")
    scored = S.composite(recs)
    shortlist = S.clean_shortlist(scored)

    # robust ADR/VIE confirmation (20-F filer) on the top candidates only
    for r in shortlist[:adr_check]:
        if not r["adr"] and F.is_foreign_filer(r["cik"]):
            r["adr"] = True
    shortlist = [r for r in shortlist if not r["adr"]]

    os.makedirs(DATA, exist_ok=True)
    json.dump([{k: r[k] for k in ("sym", "cik", "mktcap", "px", "sec", "ind", "score",
                "am", "fcfy", "pb", "ncash_r", "ncav_r", "ebit", "fcf", "subcash",
                "holdco", "neg_equity", "ttm_rolling", "wc_fcf", "ebit_onetime")} for r in shortlist[:80]],
              open(os.path.join(DATA, "shortlist.json"), "w"), indent=1)

    def fmt(r):
        am = f"{r['am']:.1f}" if r["am"] else ("sub$" if r["subcash"] else " -")
        fy = f"{r['fcfy']*100:.0f}%" if r["fcfy"] is not None else " -"
        pb = f"{r['pb']:.2f}" if r["pb"] else " -"
        nc = f"{r['ncash_r']:.2f}" if r["ncash_r"] is not None else " -"
        nv = f"{r['ncav_r']:.2f}" if r["ncav_r"] is not None else " -"
        fl = " ".join(t for t, on in [("WC-FCF", r["wc_fcf"]), ("holdco", r["holdco"]),
                                       ("neg-eq", r["neg_equity"]), ("ann", not r["ttm_rolling"])] if on)
        return f"  {r['sym']:6s}{r['mktcap']/1e6:7.0f} {am:>6s}{fy:>6s}{pb:>6s}{nc:>7s}{nv:>6s}  {r['sec'][:14]:14s} {fl}"

    print(f"\nFRESH (TTM) DEEP-VALUE SHORTLIST  (US, ex-burners, ex-ADR)  n={len(shortlist)}")
    print(f"  {'sym':6s}{'mc$M':>7s}{'EV/EBIT':>6s}{'FCFy':>6s}{'P/B':>6s}{'ncash/m':>7s}{'NCAV/m':>6s}  sector  flags")
    for r in shortlist[:top]:
        print(fmt(r))
    return shortlist


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=25)
    ap.add_argument("--adr-check", type=int, default=60)
    run(ap.parse_args().top, ap.parse_args().adr_check)
