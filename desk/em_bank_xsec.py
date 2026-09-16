"""em_bank_xsec — cross-sectional EM-bank valuation regression: normalize a bank's P/B against ROE + sovereign
risk across a peer panel, so its political/idiosyncratic RESIDUAL has a real noise band — not one sister bank.

Replaces the single-comparable (TBC-vs-BGEO) normalization. Regress P/B ~ ROE + sovereign-USD-spread across the
panel; a bank's residual = how much CHEAPER/dearer it trades than its ROE + country risk justify. A large negative
residual beyond ~1 RMSE = candidate idiosyncratic mispricing (the 'political residual'); within ~1 RMSE = noise
(no robust edge). The RMSE is the confidence band the single-comparable method lacked.

  python3 -m desk.em_bank_xsec          # pull live P/B + ROE, run the regression, rank residuals
"""
from __future__ import annotations
import sys
import numpy as np

# panel: ticker -> {name, country, sov_bps (5y USD sovereign spread over UST, approx from ratings/CDS), pb, roe}
# DATA QUALITY: free EM-bank fundamentals (yfinance) are unreliable — Korean-bank P/B comes back ~4-10x (wrong;
# they trade ~0.5-0.6x book), ADR P/B is often miscomputed (HDB ~10x vs real ~2.7x), and Argentine banks'
# book values are HYPERINFLATION-distorted (excluded — not comparable on P/B). So pb/roe below are CURATED
# approximations (illustrative; a production version needs a verified feed — Bloomberg/CapitalIQ/per-name 10-K).
PANEL = {
    "TBCG.L": {"name": "TBC Bank", "country": "Georgia", "sov_bps": 152, "pb": 1.40, "roe": 0.242},   # verified
    "BGEO.L": {"name": "Lion Finance (BGEO)", "country": "Georgia", "sov_bps": 152, "pb": 2.00, "roe": 0.300},  # verified
    "ITUB":  {"name": "Itau Unibanco", "country": "Brazil", "sov_bps": 250, "pb": 1.90, "roe": 0.205},
    "BBD":   {"name": "Bradesco", "country": "Brazil", "sov_bps": 250, "pb": 1.05, "roe": 0.135},
    "BSBR":  {"name": "Santander Brasil", "country": "Brazil", "sov_bps": 250, "pb": 1.30, "roe": 0.120},
    "BAP":   {"name": "Credicorp", "country": "Peru", "sov_bps": 150, "pb": 1.85, "roe": 0.190},
    "BSAC":  {"name": "Banco Santander Chile", "country": "Chile", "sov_bps": 120, "pb": 1.90, "roe": 0.210},
    "CIB":   {"name": "Bancolombia", "country": "Colombia", "sov_bps": 250, "pb": 1.15, "roe": 0.160},
    "IBN":   {"name": "ICICI Bank", "country": "India", "sov_bps": 100, "pb": 3.00, "roe": 0.170},
    "HDB":   {"name": "HDFC Bank", "country": "India", "sov_bps": 100, "pb": 2.70, "roe": 0.160},
    "KB":    {"name": "KB Financial", "country": "Korea", "sov_bps": 55, "pb": 0.58, "roe": 0.095},
    "SHG":   {"name": "Shinhan Financial", "country": "Korea", "sov_bps": 55, "pb": 0.55, "roe": 0.090},
    "KSPI":  {"name": "Kaspi.kz", "country": "Kazakhstan", "sov_bps": 150, "pb": 3.50, "roe": 0.450},
}


def _fundamentals():
    import yfinance as yf
    rows = []
    for tk, m in PANEL.items():
        pb, roe = m.get("pb"), m.get("roe")
        if pb is None or roe is None:
            try:
                info = yf.Ticker(m.get("yf", tk)).info
                pb = pb if pb is not None else info.get("priceToBook")
                roe = roe if roe is not None else info.get("returnOnEquity")
            except Exception:
                pass
        if pb and roe and pb > 0 and -0.5 < roe < 1.5:
            rows.append({"ticker": tk, "name": m["name"], "country": m["country"],
                         "sov_bps": m["sov_bps"], "pb": float(pb), "roe": float(roe)})
    return rows


def regress(rows: list) -> dict:
    n = len(rows)
    if n < 6:
        return {"error": f"only {n} usable panel names — need >=6 for a meaningful regression", "rows": rows}
    X = np.array([[1.0, r["roe"], r["sov_bps"]] for r in rows])
    y = np.array([r["pb"] for r in rows])
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    pred = X @ beta
    resid = y - pred
    k = X.shape[1]
    rmse = float(np.sqrt((resid @ resid) / max(n - k, 1)))
    out = []
    for i, r in enumerate(rows):
        out.append({**r, "pred_pb": round(float(pred[i]), 3), "resid": round(float(resid[i]), 3),
                    "z": round(float(resid[i] / rmse), 2) if rmse else None})
    out.sort(key=lambda x: x["resid"])   # cheapest (most negative residual) first
    return {"n": n, "rmse": round(rmse, 3),
            "coef": {"intercept": round(float(beta[0]), 3), "roe": round(float(beta[1]), 3),
                     "sov_bps": round(float(beta[2]), 6)},
            "rows": out}


def main():
    rows = _fundamentals()
    r = regress(rows)
    if r.get("error"):
        print(r["error"]);
        for x in r.get("rows", []): print(" ", x["ticker"], "pb", x["pb"], "roe", round(x["roe"], 3))
        return
    c = r["coef"]
    print(f"=== EM-BANK CROSS-SECTION  (n={r['n']}, RMSE={r['rmse']} P/B) ===")
    print(f"  P/B = {c['intercept']} + {c['roe']}*ROE + {c['sov_bps']}*sov_bps   (residual band ±{r['rmse']} = ±1 RMSE)")
    print(f"  {'ticker':<8}{'country':<12}{'P/B':>6}{'ROE':>7}{'sov':>6}{'pred':>7}{'resid':>8}{'z':>6}  read")
    for x in r["rows"]:
        read = ("CHEAP vs fundamentals" if x["z"] <= -1 else "RICH vs fundamentals" if x["z"] >= 1 else "in-line (noise)")
        print(f"  {x['ticker']:<8}{x['country']:<12}{x['pb']:>6.2f}{x['roe']*100:>6.1f}%{x['sov_bps']:>6}{x['pred_pb']:>7.2f}{x['resid']:>+8.3f}{x['z']:>+6.2f}  {read}")
    tb = next((x for x in r["rows"] if x["ticker"] == "TBCG.L"), None)
    if tb:
        print(f"\n  TBC residual {tb['resid']:+.3f} P/B (z {tb['z']:+.2f}) vs RMSE {r['rmse']}:")
        print("  " + ("WITHIN the noise band -> NO robust idiosyncratic/political edge (confirms the BGEO single-comparable read)"
                      if abs(tb['z']) < 1 else
                      "BEYOND ~1 RMSE -> a genuine residual the ROE+sovereign-risk panel does NOT explain (candidate edge)"))


if __name__ == "__main__":
    main()
