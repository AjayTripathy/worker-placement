"""revenue_test — does the EDGAR deal-pipeline lead DFIN's REVENUE prints? (A different, likely-stronger
claim than leading the stock — the stock is efficient, but recognized revenue must physically lag the
filings DFIN gets paid to process.)

Pipeline (IPO DRS+S-1 + M&A S-4+proxy) aggregated to calendar quarters, YoY-growth (kills DFIN's heavy
proxy-season seasonality + secular decline). Tested vs DFIN quarterly revenue YoY at lags 0..3 quarters.
DFIN CIK 1647088 (Donnelley Financial Solutions), revenue from SEC XBRL quarterly frames.
"""
from __future__ import annotations
import json, urllib.request, statistics as st
from . import edgar_pipeline as EP

HDRS = {"User-Agent": "signalos-dealcycle research 4tripathy@gmail.com"}
DFIN_CIK = 1647088


def _dfin_quarterly_revenue() -> dict[str, float]:
    """{'YYYYQn': revenue} from XBRL quarterly frames (3-month values SEC stamps with a CYxxxxQn frame)."""
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{DFIN_CIK:010d}.json"
    cf = json.load(urllib.request.urlopen(urllib.request.Request(url, headers=HDRS), timeout=45))
    g = cf["facts"]["us-gaap"]
    out = {}
    for concept in ("RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues"):
        if concept not in g:
            continue
        for r in g[concept]["units"].get("USD", []):
            fr = r.get("frame", "")
            # quarterly frame looks like 'CY2023Q1'; skip annual ('CY2023') / instant ('...I')
            if fr.startswith("CY") and "Q" in fr and not fr.endswith("I"):
                q = fr[2:]                       # '2023Q1'
                q = f"{q[:4]}Q{q[5]}"
                out.setdefault(q, r["val"])      # first concept wins (prefer the modern tag)
    return out


def _pipeline_quarterly(start_ym="2017-01", end_ym="2026-06") -> dict[str, float]:
    pipe = EP.pipeline_series(start_ym, end_ym)
    q = {}
    for ym, d in pipe.items():
        y, m = ym.split("-")
        qn = (int(m) - 1) // 3 + 1
        key = f"{y}Q{qn}"
        q[key] = q.get(key, 0) + d["ipo_lead"] + d["ma_lead"]
    return q


def _yoy(series: dict[str, float]) -> dict[str, float]:
    out = {}
    for k, v in series.items():
        y, qn = int(k[:4]), k[5]
        prior = f"{y-1}Q{qn}"
        if prior in series and series[prior]:
            out[k] = v / series[prior] - 1
    return out


def _pearson(xs, ys):
    pts = [(x, y) for x, y in zip(xs, ys) if x is not None and y is not None]
    if len(pts) < 5:
        return None, len(pts)
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    mx, my = st.mean(xs), st.mean(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = (sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys)) ** 0.5
    return (num / den if den else None), len(pts)


def _qkeys_sorted(keys):
    return sorted(keys, key=lambda k: (int(k[:4]), int(k[5])))


def _shift(qkey, k):
    y, qn = int(qkey[:4]), int(qkey[5])
    qn += k
    while qn > 4:
        y, qn = y + 1, qn - 4
    while qn < 1:
        y, qn = y - 1, qn + 4
    return f"{y}Q{qn}"


def run(start_ym="2017-01", end_ym="2026-06", max_lag=3) -> dict:
    rev = _dfin_quarterly_revenue()
    pipe = _pipeline_quarterly(start_ym, end_ym)
    rev_yoy, pipe_yoy = _yoy(rev), _yoy(pipe)
    common = _qkeys_sorted(set(pipe_yoy))
    res = {}
    for k in range(0, max_lag + 1):
        xs, ys = [], []
        for q in common:
            tgt = _shift(q, k)
            if q in pipe_yoy and tgt in rev_yoy:
                xs.append(pipe_yoy[q]); ys.append(rev_yoy[tgt])
        r, n = _pearson(xs, ys)
        res[k] = {"corr": round(r, 3) if r is not None else None, "n": n}
    valid = {k: v["corr"] for k, v in res.items() if v["corr"] is not None}
    best = max(valid, key=lambda k: valid[k]) if valid else None
    leads = best is not None and valid[best] > 0.30
    return {"window": f"{start_ym}..{end_ym}",
            "dfin_rev_quarters": len(rev_yoy), "pipeline_quarters": len(pipe_yoy),
            "corr_pipelineYoY_vs_DFINrevYoY_by_lag_q": res,
            "best_lag_quarters": best, "best_corr": valid.get(best) if best is not None else None,
            "leads_revenue": leads,
            "verdict": ("pipeline LEADS DFIN revenue — real (revenue, not stock)" if leads else
                        "no strong revenue lead at this aggregation")}


if __name__ == "__main__":
    print(json.dumps(run(), indent=1))
