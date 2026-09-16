"""political_risk_xsec — cross-sectional bank valuation: regress P/B on ROE, GROWTH (g), and country risk
(sovereign USD spread) across a pooled DM + EM panel, so a bank's RESIDUAL is its idiosyncratic/political
over- or under-pricing AFTER controlling for profitability, growth, AND country risk.

Adding g (per-country nominal bank growth) fixes the artifact where high-growth markets (India) were mislabeled
'rich' because their growth premium had nowhere to go. Pooled DM+EM so the g coefficient is estimable (DM banks
alone have ~no growth variation). DM banks anchor the baseline (they dominate the panel and carry ~zero country
risk); EM residuals beyond ~1 RMSE = genuine idiosyncratic mispricing the ROE/growth/country-risk factors miss.

DATA CAVEAT: DM P/B+ROE pulled live (reliable). EM P/B+ROE + the g/sov tables are CURATED approximations
(yfinance EM data is garbage). Illustrative — production needs verified per-bank fundamentals + live rates.

  python3 -m desk.political_risk_xsec
"""
from __future__ import annotations
import numpy as np

# country -> {g: nominal sustainable bank growth %, sov_bps: 5y USD sovereign spread over UST}
COUNTRY = {
    "US": {"g": 4.5, "sov_bps": 0}, "UK": {"g": 3.5, "sov_bps": 15}, "France": {"g": 3.0, "sov_bps": 30},
    "Spain": {"g": 3.5, "sov_bps": 70}, "Italy": {"g": 2.5, "sov_bps": 110}, "Netherlands": {"g": 3.0, "sov_bps": 15},
    "Germany": {"g": 3.0, "sov_bps": 0}, "Finland": {"g": 3.0, "sov_bps": 20},
    "Georgia": {"g": 9.5, "sov_bps": 152}, "Brazil": {"g": 8.0, "sov_bps": 250}, "Chile": {"g": 6.0, "sov_bps": 120},
    "Peru": {"g": 6.0, "sov_bps": 150}, "Colombia": {"g": 8.0, "sov_bps": 250}, "India": {"g": 12.0, "sov_bps": 100},
    "Korea": {"g": 4.5, "sov_bps": 55}, "Kazakhstan": {"g": 12.0, "sov_bps": 150},
}
# DM banks pulled live (yfinance reliable) -> country
DM = {"JPM": "US", "BAC": "US", "WFC": "US", "C": "US", "USB": "US", "PNC": "US", "TFC": "US", "MS": "US", "GS": "US",
      "HSBA.L": "UK", "BARC.L": "UK", "LLOY.L": "UK", "BNP.PA": "France", "ACA.PA": "France", "GLE.PA": "France",
      "SAN.MC": "Spain", "BBVA.MC": "Spain", "ISP.MI": "Italy", "UCG.MI": "Italy", "INGA.AS": "Netherlands",
      "DBK.DE": "Germany", "NDA-FI.HE": "Finland"}
# EM banks (P/B, trailing ROE) -> country.  VERIFIED 2026-06-30 (stockanalysis, per the BGEO re-underwrite).
EM = {
    "TBCG.L": ("Georgia", 1.34, 0.240), "BGEO.L": ("Georgia", 1.93, 0.274),
    "ITUB": ("Brazil", 2.19, 0.218), "BBD": ("Brazil", 1.00, 0.134), "BSAC": ("Chile", 2.91, 0.221),
    "BAP": ("Peru", 2.67, 0.192), "CIB": ("Colombia", 1.99, 0.169),
    "IBN": ("India", 2.58, 0.164), "HDB": ("India", 2.00, 0.138),
    "KB": ("Korea", 1.00, 0.109), "SHG": ("Korea", 0.73, 0.086), "KSPI": ("Kazakhstan", 2.95, 0.468),
    "HSBK.L": ("Kazakhstan", 1.11, 0.300),
}
# NOTE 2026-06-30: KB refreshed 0.91->1.00 P/B, 0.100->0.109 ROE (deep-DD verified vs KB's own FY25/Q1'26
# disclosures — the old 0.91 understated cheapness; KB has re-rated to ~1.0x book, revealed COE~=ROE).
# HSBK.L (Halyk/Kazakhstan) added from its run-down (ROE ~30%, ~1.1x book) — note the linear fit OVER-credits
# ultra-high-ROE EM banks; read HSBK's residual de-biased (peer-anchored ~-0.3x book), not the raw z~-2.8.


def _panel():
    import yfinance as yf
    rows = []
    for tk, ctry in DM.items():
        try:
            info = yf.Ticker(tk).info
            pb, roe = info.get("priceToBook"), info.get("returnOnEquity")
            if pb and roe and pb > 0 and 0.0 < roe < 0.5:
                rows.append({"tk": tk, "country": ctry, "em": False, "pb": float(pb), "roe": float(roe)})
        except Exception:
            pass
    for tk, (ctry, pb, roe) in EM.items():
        rows.append({"tk": tk, "country": ctry, "em": True, "pb": pb, "roe": roe})
    for r in rows:
        c = COUNTRY[r["country"]]
        r["g"], r["sov_bps"] = c["g"], c["sov_bps"]
    return rows


def _fit(rows, cols):
    X = np.array([[1.0] + [r[c] for c in cols] for r in rows])
    y = np.array([r["pb"] for r in rows])
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    pred = X @ beta
    resid = y - pred
    rmse = float(np.sqrt((resid @ resid) / max(len(rows) - X.shape[1], 1)))
    return beta, pred, resid, rmse


def run():
    rows = _panel()
    if len([r for r in rows if not r["em"]]) < 8:
        return {"error": "need >=8 DM banks live", "rows": rows}
    # Model 1: no growth term (the old model) ; Model 2: with g
    b1, p1, e1, rmse1 = _fit(rows, ["roe", "sov_bps"])
    b2, p2, e2, rmse2 = _fit(rows, ["roe", "g", "sov_bps"])
    for i, r in enumerate(rows):
        r["resid_nog"], r["resid_g"] = round(float(e1[i]), 2), round(float(e2[i]), 2)
        r["pred_g"] = round(float(p2[i]), 2)
        r["z_g"] = round(float(e2[i] / rmse2), 2) if rmse2 else None
    return {"n": len(rows), "rmse_nog": round(rmse1, 3), "rmse_g": round(rmse2, 3),
            "coef_nog": {"intercept": round(b1[0], 3), "roe": round(b1[1], 3), "sov_bps": round(b1[2], 6)},
            "coef_g": {"intercept": round(b2[0], 3), "roe": round(b2[1], 3), "g": round(b2[2], 4), "sov_bps": round(b2[3], 6)},
            "rows": rows}


def main():
    r = run()
    if r.get("error"):
        print(r["error"]); return
    cg = r["coef_g"]
    print(f"=== POOLED DM+EM (n={r['n']}) ===")
    print(f"  no-g model:   P/B = {r['coef_nog']['intercept']} + {r['coef_nog']['roe']}*ROE + {r['coef_nog']['sov_bps']}*sov   (RMSE {r['rmse_nog']})")
    print(f"  WITH-g model: P/B = {cg['intercept']} + {cg['roe']}*ROE + {cg['g']}*g + {cg['sov_bps']}*sov   (RMSE {r['rmse_g']})")
    print(f"  → g coefficient {cg['g']:+} (P/B per 1pp growth); RMSE {r['rmse_nog']} → {r['rmse_g']} ({'tighter' if r['rmse_g']<r['rmse_nog'] else 'looser'} fit)")
    print(f"\n  EM-bank residuals (P/B): the GROWTH ADJUSTMENT — does adding g change the read?")
    print(f"  {'tk':<8}{'country':<12}{'P/B':>6}{'ROE':>6}{'g':>5}{'sov':>6}{'pred_g':>8}{'resid(noG)':>11}{'resid(+G)':>11}{'z':>6}")
    for x in sorted([r2 for r2 in r["rows"] if r2["em"]], key=lambda v: v["resid_g"]):
        print(f"  {x['tk']:<8}{x['country']:<12}{x['pb']:>6.2f}{x['roe']*100:>5.0f}%{x['g']:>5.0f}{x['sov_bps']:>6}{x['pred_g']:>8.2f}{x['resid_nog']:>+11.2f}{x['resid_g']:>+11.2f}{x['z_g']:>+6.2f}")
    ind = [x for x in r["rows"] if x["country"] == "India"]
    geo = [x for x in r["rows"] if x["country"] == "Georgia"]
    print(f"\n  INDIA (the artifact): residual {np.mean([x['resid_nog'] for x in ind]):+.2f} (no g) → {np.mean([x['resid_g'] for x in ind]):+.2f} (with g)"
          f"  {'— richness shrinks once growth is credited' if abs(np.mean([x['resid_g'] for x in ind]))<abs(np.mean([x['resid_nog'] for x in ind])) else ''}")
    print(f"  GEORGIA: residual {np.mean([x['resid_nog'] for x in geo]):+.2f} (no g) → {np.mean([x['resid_g'] for x in geo]):+.2f} (with g)  (low-growth → barely moves; its cheap residual is more trustworthy)")


if __name__ == "__main__":
    main()
