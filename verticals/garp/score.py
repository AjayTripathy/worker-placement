"""GARP composite = growth x quality x reasonable-price, with anti-growth-trap guards.

Growth  : 3-yr trailing CAGR of revenue + net income (higher better).
Quality : ROIC, operating margin, margin TREND, low leverage (higher better).
Price   : PEG (trailing P/E / earnings-growth%), EV/EBIT, P/FCF (lower better = "reasonable").
Composite = 0.35*growth + 0.30*quality + 0.35*price (percentile blend).

Flags (the growth-trap tells the R/f(M) filter then verifies): DECEL (latest-year growth
<< 3-yr CAGR), NONCASH (FCF << net income — accrual growth), LEVERED, EXPENSIVE.
"""
from __future__ import annotations
import statistics as st

TAX = 0.21


def _cagr(latest, base, yrs):
    if latest is None or base is None or base <= 0 or latest <= 0:
        return None
    return (latest / base) ** (1.0 / yrs) - 1.0


def compute_metrics(u: dict, f: dict) -> dict:
    g = f.get
    rev_l, rev_b = g("Revenues_CY2025"), g("Revenues_CY2022")
    rev_pp = g("Revenues_CY2024")                      # prior year for deceleration
    rev_m = g("Revenues_CY2023")                       # mid for margin-trend
    ni_l, ni_b = g("NetIncomeLoss_CY2025"), g("NetIncomeLoss_CY2022")
    ebit = g("OperatingIncomeLoss_CY2025")
    ebit_m = g("OperatingIncomeLoss_CY2023")
    eq = g("StockholdersEquity")
    cash = (g("CashAndCashEquivalentsAtCarryingValue") or 0) + (g("ShortTermInvestments") or 0)
    debt = (g("LongTermDebtNoncurrent") or g("LongTermDebt") or 0) + (g("DebtCurrent") or 0)
    cfo, capx = g("cfo"), g("capx")
    fcf = (cfo - capx) if (cfo is not None and capx is not None) else cfo
    m = u["mktcap"]
    ev = m + debt - cash

    rev_cagr = _cagr(rev_l, rev_b, 3)
    ni_cagr = _cagr(ni_l, ni_b, 3)
    rev_yoy = (rev_l / rev_pp - 1.0) if (rev_l and rev_pp and rev_pp > 0) else None

    pe = (m / ni_l) if (ni_l and ni_l > 0) else None
    ev_ebit = (ev / ebit) if (ev > 0 and ebit and ebit > 0) else None
    peg = (pe / (ni_cagr * 100)) if (pe and ni_cagr and ni_cagr > 0) else None
    pfcf = (m / fcf) if (fcf and fcf > 0) else None
    roe = (ni_l / eq) if (eq and eq > 0 and ni_l is not None) else None
    ic = (eq or 0) + debt - cash
    roic = (ebit * (1 - TAX) / ic) if (ic > 0 and ebit and ebit > 0) else None
    opm = (ebit / rev_l) if (ebit is not None and rev_l and rev_l > 0) else None
    opm_m = (ebit_m / rev_m) if (ebit_m is not None and rev_m and rev_m > 0) else None
    opm_trend = (opm - opm_m) if (opm is not None and opm_m is not None) else None
    nd_ebit = ((debt - cash) / ebit) if (ebit and ebit > 0) else None

    r = {**u, "ev": ev, "rev_l": rev_l, "ni_l": ni_l, "ebit": ebit, "fcf": fcf, "eq": eq,
         "rev_cagr": rev_cagr, "ni_cagr": ni_cagr, "rev_yoy": rev_yoy,
         "pe": pe, "ev_ebit": ev_ebit, "peg": peg, "pfcf": pfcf,
         "roe": roe, "roic": roic, "opm": opm, "opm_trend": opm_trend, "nd_ebit": nd_ebit}
    # growth-trap flags
    r["decel"] = (rev_yoy is not None and rev_cagr is not None and rev_yoy < 0.5 * rev_cagr)
    r["noncash"] = (ni_l and ni_l > 0 and fcf is not None and fcf < 0.6 * ni_l)
    r["levered"] = (nd_ebit is not None and nd_ebit > 3.0)
    r["expensive"] = (pe is not None and pe > 40) or (peg is not None and peg > 2.5)
    # base-effect artifact: growth off a tiny base (or hyper-CAGR) is not GARP growth
    r["base_effect"] = (rev_cagr is not None and rev_cagr > 0.60) or (rev_b is not None and rev_b < 25e6)
    # emerging profitability: no prior-year earnings => no meaningful EPS-CAGR / PEG
    r["emerging"] = (ni_b is None or ni_b <= 0)
    return r


def _pctile(vals, reverse=False):
    xs = sorted(v for v in vals if v is not None)
    n = len(xs) or 1
    def fn(v):
        if v is None:
            return None
        r = sum(1 for x in xs if x <= v) / n
        return (1 - r) if reverse else r
    return fn


def composite(records: list[dict]) -> list[dict]:
    have = [r for r in records if r["rev_cagr"] is not None and r["ni_l"] is not None]
    p_revg = _pctile([r["rev_cagr"] for r in have])
    p_nig = _pctile([r["ni_cagr"] for r in have])
    p_roic = _pctile([r["roic"] for r in have])
    p_opm = _pctile([r["opm"] for r in have])
    p_trend = _pctile([r["opm_trend"] for r in have])
    p_lev = _pctile([r["nd_ebit"] for r in have], reverse=True)      # low leverage better
    p_peg = _pctile([r["peg"] for r in have], reverse=True)          # low PEG better
    p_evebit = _pctile([r["ev_ebit"] for r in have], reverse=True)
    p_pfcf = _pctile([r["pfcf"] for r in have], reverse=True)

    def blend(parts):
        xs = [x for x in parts if x is not None]
        return st.mean(xs) if xs else None

    for r in have:
        g = blend([p_revg(r["rev_cagr"]), p_nig(r["ni_cagr"])])
        q = blend([p_roic(r["roic"]), p_opm(r["opm"]), p_trend(r["opm_trend"]), p_lev(r["nd_ebit"])])
        pr = blend([p_peg(r["peg"]), p_evebit(r["ev_ebit"]), p_pfcf(r["pfcf"])])
        r["g_score"], r["q_score"], r["p_score"] = g, q, pr
        r["score"] = (round(0.35 * g + 0.30 * q + 0.35 * pr, 3)
                      if (g is not None and q is not None and pr is not None) else None)
    return have


def shortlist(records, min_rev_cagr=0.08, exclude_adr=True):
    """Profitable, genuinely-growing, FCF-positive, reasonably-priced, US."""
    out = [r for r in records if r.get("score") is not None
           and r["ni_l"] and r["ni_l"] > 0
           and r["rev_cagr"] is not None and r["rev_cagr"] >= min_rev_cagr
           and (r["fcf"] is None or r["fcf"] > 0)
           and not r["expensive"]
           and not r["base_effect"]
           and not (exclude_adr and r.get("adr"))]
    out.sort(key=lambda r: -r["score"])
    return out
