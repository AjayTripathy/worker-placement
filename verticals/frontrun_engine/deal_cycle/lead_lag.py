"""lead_lag — the decisive experiment. A leading indicator is only a FRONTRUN if its public series
LEADS the price. The MAUDE pilot died here (public stream lagged the firm's internal view); the
gov-contract pilot lived here (civilian postings ~0-day). So before wiring any DFIN entry trigger we
test: does the deal-pipeline composite lead DFIN's stock — and at what lag — or is DFIN already
coincident with the IPO-window narrative (in which case there's no edge)?

Composite leading index (monthly, z-scored):  z(ipo_lead) + z(ma_lead) − z(hy_oas)
  (more IPO/M&A filings + tighter credit = more deal activity coming = DFIN forward revenue.)

Test: Pearson corr of the composite's monthly CHANGE at month t vs DFIN's forward k-month return.
  k>0 with positive corr peaking at some lead = the indicator FRONTRUNS DFIN (good).
  peak at k=0 / negative lead = coincident or lagging (no edge — kill it, honestly).
"""
from __future__ import annotations
import statistics as st
from . import edgar_pipeline as EP
from . import conditions as CO


def _z(d: dict[str, float]) -> dict[str, float]:
    vals = [v for v in d.values() if v is not None]
    if len(vals) < 3:
        return {k: 0.0 for k in d}
    m, s = st.mean(vals), (st.pstdev(vals) or 1.0)
    return {k: ((v - m) / s if v is not None else 0.0) for k, v in d.items()}


def _pearson(xs, ys):
    pts = [(x, y) for x, y in zip(xs, ys) if x is not None and y is not None]
    if len(pts) < 6:
        return None, len(pts)
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    mx, my = st.mean(xs), st.mean(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = (sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys)) ** 0.5
    return (num / den if den else None), len(pts)


def composite(start_ym="2021-01", end_ym="2026-06") -> dict[str, float]:
    pipe = EP.pipeline_series(start_ym, end_ym)
    ipo = {m: pipe[m]["ipo_lead"] for m in pipe}
    ma = {m: pipe[m]["ma_lead"] for m in pipe}
    hy = CO.monthly_series("hy_oas", start_ym, end_ym)
    zi, zm, zh = _z(ipo), _z(ma), _z(hy)
    months = sorted(set(ipo) & set(hy))
    return {m: zi.get(m, 0) + zm.get(m, 0) - zh.get(m, 0) for m in months}


def _dfin_monthly(start_ym="2021-01", end_ym="2026-06") -> dict[str, float]:
    import yfinance as yf
    close = yf.download("DFIN", start=f"{start_ym}-01", end=f"{end_ym}-28", progress=False, auto_adjust=True)["Close"]
    if hasattr(close, "columns"):            # single-ticker can still return a 1-col DataFrame
        close = close.iloc[:, 0]
    close = close.dropna()
    out = {}
    for ts, px in close.items():
        out[ts.strftime("%Y-%m")] = float(px)        # last write per month = month-end
    return out


def run(start_ym="2021-01", end_ym="2026-06", max_lag=6) -> dict:
    comp = composite(start_ym, end_ym)
    months = sorted(comp)
    # monthly change in the composite (the impulse)
    dcomp = {months[i]: comp[months[i]] - comp[months[i - 1]] for i in range(1, len(months))}
    px = _dfin_monthly(start_ym, end_ym)

    def fwd_ret(m, k):
        i = months.index(m) if m in months else None
        if i is None or i + k >= len(months):
            return None
        m0, mk = months[i], months[i + k]
        if m0 in px and mk in px and px[m0]:
            return px[mk] / px[m0] - 1
        return None

    results = {}
    impulse_months = [m for m in months if m in dcomp]
    for k in range(0, max_lag + 1):
        xs = [dcomp[m] for m in impulse_months]
        ys = [fwd_ret(m, k) for m in impulse_months]
        r, n = _pearson(xs, ys)
        results[k] = {"corr": round(r, 3) if r is not None else None, "n": n}
    # the verdict: which forward lag has the strongest POSITIVE correlation
    valid = {k: v["corr"] for k, v in results.items() if v["corr"] is not None}
    best_lag = max(valid, key=lambda k: valid[k]) if valid else None
    leads = best_lag is not None and best_lag >= 1 and valid[best_lag] > 0.15
    return {"window": f"{start_ym}..{end_ym}", "n_months": len(months),
            "corr_by_lag_months": results, "best_lag_months": best_lag,
            "best_corr": valid.get(best_lag) if best_lag is not None else None,
            "frontruns_dfin": leads,
            "verdict": ("LEADS — frontrun valid" if leads else
                        "coincident/weak — NOT a clean frontrun (honest kill)")}


if __name__ == "__main__":
    import json
    print(json.dumps(run(), indent=1))
