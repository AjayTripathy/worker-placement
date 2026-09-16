"""classification_error — the DFIN-species finder.

Screens for the MECHANICAL signature of a market mislabel: OPERATING INCOME rising while
REVENUE is flat-or-declining = margins expanding on a shrinking top line = a high-margin
segment eating a low-margin one, which the market prices as "the aggregate is dying."
DFIN is the won template (SaaS eating print; EBIT up as revenue fell; 8.6x → +22%).

This finds the CANDIDATES; the two-mode DD then VERIFIES the actual mislabel from the 10-K
segment note and grades WIDE-cheap (court) vs narrow/fair (WATCH). Reuses the GARP 4-year
cross-section (Revenues + OperatingIncomeLoss CY2022-25) + deep_value cheapness metrics.

Discipline (from the DFIN-win / QCOM-Gartner-pass split): the mislabel existing is not enough
— it pays only when the multiple is CHEAP (the divergence is WIDE). So we require low EV/EBIT.

    python -m verticals.deep_value.classification_error [--top N]
"""
from __future__ import annotations
import argparse, json, os
from . import universe as U, fundamentals as F, score as S
from ..garp import fundamentals as G

DATA = os.path.join(os.path.dirname(__file__), "data")


def _cagr(series):
    """CAGR over a list of (year-ordered) values; None if <2 clean or sign-flip makes it meaningless."""
    xs = [x for x in series if x is not None]
    if len(xs) < 2 or xs[0] == 0:
        return None
    first, last, n = xs[0], xs[-1], len(xs) - 1
    if first <= 0 or last <= 0:            # CAGR undefined across a sign change — use simple avg growth
        return (last - first) / (abs(first) * n)
    return (last / first) ** (1 / n) - 1


def run(top=30):
    uni = U.fetch_universe()
    dv = F.build_cross_section()                 # TTM metrics (cheapness)
    g = G.build_cross_section()                  # 4yr Revenues + OperatingIncomeLoss
    yrs = ["CY2022", "CY2023", "CY2024", "CY2025"]
    recs = []
    for u in uni:
        cik = u["cik"]
        if cik not in dv or cik not in g:
            continue
        m = S.compute_metrics(u, dv[cik])
        gr = g[cik]
        rev = [gr.get(f"Revenues_{y}") for y in yrs]
        ebit = [gr.get(f"OperatingIncomeLoss_{y}") for y in yrs]
        rev_cagr, ebit_cagr = _cagr(rev), _cagr(ebit)
        if rev_cagr is None or ebit_cagr is None:
            continue
        # THE SIGNATURE: revenue flat-or-declining, EBIT rising, margins EXPANDING, and CHEAP.
        rev_flat_down = rev_cagr <= 0.03                       # the "dying aggregate" optics
        ebit_rising = ebit_cagr >= 0.08                        # operating income compounding
        margin_expanding = ebit_cagr - rev_cagr >= 0.10        # the mix-shift wedge (>=10pp/yr)
        cheap = m.get("am") is not None and 0 < m["am"] <= 12  # divergence must be WIDE (cheap EV/EBIT)
        if not (rev_flat_down and ebit_rising and margin_expanding and cheap):
            continue
        if m["burning"] or m["neg_equity"] or m.get("mlp_artifact") or m.get("subcash"):
            continue
        latest_ebit = next((x for x in reversed(ebit) if x is not None), None)
        if latest_ebit is None or latest_ebit <= 0:            # must currently earn money
            continue
        m["rev_cagr"], m["ebit_cagr"] = rev_cagr, ebit_cagr
        m["wedge"] = ebit_cagr - rev_cagr
        recs.append(m)
        m["adr"] = u.get("country") not in ("United States", "")

    # ADR confirmation on the survivors (cheap; the list is small)
    for r in recs:
        if not r["adr"] and F.is_foreign_filer(r["cik"]):
            r["adr"] = True
    recs = [r for r in recs if not r["adr"]]
    recs.sort(key=lambda r: -r["wedge"])          # widest margin-expansion wedge first

    os.makedirs(DATA, exist_ok=True)
    json.dump([{k: r.get(k) for k in ("sym", "cik", "mktcap", "px", "sec", "am", "fcfy",
               "rev_cagr", "ebit_cagr", "wedge", "ncash_r")} for r in recs],
              open(os.path.join(DATA, "classification_error.json"), "w"), indent=1)

    print(f"CLASSIFICATION-ERROR CANDIDATES (EBIT up + revenue flat/down + cheap)  n={len(recs)}")
    print(f"  {'sym':6s}{'mc$M':>7s}{'EV/EBIT':>8s}{'FCFy':>6s}{'revCAGR':>8s}{'ebitCAGR':>9s}{'wedge':>7s}  sector")
    for r in recs[:top]:
        print(f"  {r['sym']:6s}{r['mktcap']/1e6:7.0f}{r['am']:8.1f}"
              f"{(r['fcfy'] or 0)*100:5.0f}%{r['rev_cagr']*100:7.0f}%{r['ebit_cagr']*100:8.0f}%"
              f"{r['wedge']*100:6.0f}%  {r['sec'][:16]}")
    return recs


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=30)
    run(ap.parse_args().top)
