"""contrarian_test — the lead_lag found a NEGATIVE pipeline→DFIN-stock relation (surge = late-cycle).
This tests the contrarian form properly over more cycles (2017-2026): is a DEPRESSED pipeline a better
DFIN entry than a HOT one — and does conditioning on the OPEN financing gate help?

Point-in-time rank (no look-ahead): each month's pipeline level is ranked vs its TRAILING 36 months, so
"depressed/hot" uses only past data. Buckets by trailing-rank tercile; compare mean forward 3/6/12-month
DFIN return per bucket. If bottom-tercile (depressed) > top-tercile (hot), the contrarian thesis holds.
"""
from __future__ import annotations
import statistics as st
from . import edgar_pipeline as EP, conditions as CO


def _dfin_monthly():
    import yfinance as yf
    close = yf.download("DFIN", start="2017-01-01", end="2026-06-28", progress=False, auto_adjust=True)["Close"]
    if hasattr(close, "columns"):
        close = close.iloc[:, 0]
    close = close.dropna()
    return {ts.strftime("%Y-%m"): float(px) for ts, px in close.items()}


def _trailing_rank(series_by_month, key, window=36):
    months = sorted(series_by_month)
    i = months.index(key)
    hist = [series_by_month[m] for m in months[max(0, i - window):i + 1]]
    if len(hist) < 12:
        return None
    cur = series_by_month[key]
    return sum(1 for x in hist if x <= cur) / len(hist)     # 0..1 percentile vs trailing window


def run(start_ym="2017-01", end_ym="2026-06") -> dict:
    pipe = EP.pipeline_series(start_ym, end_ym)
    ipo = {m: pipe[m]["ipo_lead"] for m in pipe}             # IPO funnel = the deal-supply level
    hy = CO.monthly_series("hy_oas", start_ym, end_ym)
    px = _dfin_monthly()
    months = sorted(set(ipo) & set(px))

    def fwd(m, k):
        i = months.index(m)
        if i + k >= len(months):
            return None
        return px[months[i + k]] / px[m] - 1 if px.get(m) else None

    rows = []
    for m in months:
        rnk = _trailing_rank(ipo, m)
        if rnk is None:
            continue
        rows.append({"m": m, "rank": rnk, "hy": hy.get(m),
                     "f3": fwd(m, 3), "f6": fwd(m, 6), "f12": fwd(m, 12)})

    def bucket_stats(rows, horizon):
        lo = [r[horizon] for r in rows if r["rank"] <= 0.33 and r[horizon] is not None]
        mid = [r[horizon] for r in rows if 0.33 < r["rank"] <= 0.66 and r[horizon] is not None]
        hi = [r[horizon] for r in rows if r["rank"] > 0.66 and r[horizon] is not None]
        f = lambda xs: (round(st.mean(xs) * 100, 1), len(xs)) if xs else (None, 0)
        return {"depressed_botTercile": f(lo), "mid": f(mid), "hot_topTercile": f(hi)}

    out = {"window": f"{start_ym}..{end_ym}", "n_months": len(rows)}
    for h in ("f3", "f6", "f12"):
        out[f"DFIN_fwd_{h[1:]}mo_ret_by_pipeline_tercile_pct"] = bucket_stats(rows, h)

    # gate-conditioned: depressed pipeline AND open financing (HY<4) vs hot pipeline
    gate_rows = [r for r in rows if r["hy"] is not None]
    dep_open = [r["f6"] for r in gate_rows if r["rank"] <= 0.33 and r["hy"] < 4.0 and r["f6"] is not None]
    hot_any = [r["f6"] for r in gate_rows if r["rank"] > 0.66 and r["f6"] is not None]
    g = lambda xs: (round(st.mean(xs) * 100, 1), len(xs)) if xs else (None, 0)
    out["gate_conditioned_fwd6mo_pct"] = {"depressed_pipeline_AND_gate_open": g(dep_open),
                                          "hot_pipeline_any_gate": g(hot_any)}
    # verdict
    s6 = out["DFIN_fwd_6mo_ret_by_pipeline_tercile_pct"]
    lo6, hi6 = s6["depressed_botTercile"][0], s6["hot_topTercile"][0]
    holds = (lo6 is not None and hi6 is not None and lo6 > hi6 + 3)   # depressed beats hot by >3pp
    out["contrarian_holds"] = holds
    out["verdict"] = ("CONTRARIAN CONFIRMED — depressed pipeline = better DFIN entry than hot"
                      if holds else "contrarian NOT robust at 6mo (weak/mixed)")
    return out


if __name__ == "__main__":
    import json
    print(json.dumps(run(), indent=1))
