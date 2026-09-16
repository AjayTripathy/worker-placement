"""regional_factors — measure foreign holdings on their OWN market's Fama-French 5-factor set.

US FF5 cannot describe a Tokyo or Warsaw stock — the factors don't span those markets, so foreign
names come back "missing" from the US model (desk/factor_drift). This module regresses each foreign
name against the Ken French REGIONAL 5-factor set for its market (Japan / Europe / Emerging / ...),
on a **USD basis** (Ken French regional factors are USD-denominated, so local returns are dollar-
converted via the listing-currency FX before regressing).

The payoff is the measurement layer for the office thesis's foreign edge: it shows the foreign
sleeve loading on factors ORTHOGONAL to the US ones (Japan-value is not US-value), which is exactly
the diversification a US-factor-concentrated household is buying. READ-ONLY; caches to
desk/data/regional_loadings.json.

    python3 -m desk.regional_factors           # compute + cache the mapped foreign names
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

import pandas as pd
import pandas_datareader.data as web
import statsmodels.api as sm
import yfinance as yf

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "desk" / "data" / "regional_loadings.json"
FACTORS = ["mkt_rf", "smb", "hml", "rmw", "cma"]
FF_COLS = ["Mkt-RF", "SMB", "HML", "RMW", "CMA"]
START = "2022-07-01"

# region -> (Ken French dataset name, frequency)
REGIONS = {
    "Japan":          ("Japan_5_Factors_Daily", "D"),
    "Europe":         ("Europe_5_Factors_Daily", "D"),
    "NorthAmerica":   ("North_America_5_Factors_Daily", "D"),
    "AsiaPacExJapan": ("Asia_Pacific_ex_Japan_5_Factors_Daily", "D"),
    "Emerging":       ("Emerging_5_Factors", "M"),
}

# base ticker -> (yfinance symbol, region, listing currency; "USD" => no FX conversion needed)
REGION_MAP = {
    "3388": ("3388.T", "Japan", "JPY"),
    "7222": ("7222.T", "Japan", "JPY"),
    "8750": ("8750.T", "Japan", "JPY"),
    "BRBY": ("BRBY.L", "Europe", "GBP"),
    "BAVA": ("BAVA.CO", "Europe", "DKK"),
    "AST":  ("AST.WA", "Europe", "PLN"),      # Poland — Europe proxy (MSCI-EM, no daily FF set)
    "PEO":  ("PEO.WA", "Europe", "PLN"),      # Poland — Europe proxy
    "HSBK": ("HSBK.L", "Emerging", "USD"),    # Kazakhstan GDR on LSE, USD-denominated
    "WF":   ("WF", "Emerging", "USD"),        # Korea ADR, USD
    "BBD":  ("BBD", "Emerging", "USD"),       # Brazil ADR, USD
}


def _series(sym):
    raw = yf.download(sym, start=START, progress=False, auto_adjust=True)
    close = raw["Close"]
    if hasattr(close, "columns"):
        close = close.iloc[:, 0]
    s = close.pct_change()
    s.index = pd.to_datetime(s.index).tz_localize(None).normalize()
    return s


def _usd_returns(yfsym, ccy):
    """Daily USD total returns: local return compounded with the listing-currency FX return."""
    r = _series(yfsym)
    if ccy and ccy != "USD":
        fx = _series(f"{ccy}USD=X").reindex(r.index)
        r = (1 + r) * (1 + fx) - 1
    return r.rename("r").dropna()


def compute_one(base: str) -> dict:
    if base not in REGION_MAP:
        return {"error": "no region map"}
    yfsym, region, ccy = REGION_MAP[base]
    ds, freq = REGIONS[region]
    try:
        r = _usd_returns(yfsym, ccy)
        ff = web.DataReader(ds, "famafrench", start=START)[0] / 100.0   # PeriodIndex
        if freq == "D":
            ff.index = ff.index.to_timestamp()
            stock = r
        else:  # monthly — resample stock to month, align both to month-start timestamps
            stock = (1 + r).resample("ME").prod() - 1
            stock.index = stock.index.to_period("M").to_timestamp()
            ff.index = ff.index.to_timestamp()
        df = pd.concat([stock.rename("r"), ff], axis=1, join="inner").dropna()
        if len(df) < 24:
            return {"error": f"only {len(df)} obs", "region": region}
        y = df["r"] - df["RF"]
        X = sm.add_constant(df[FF_COLS])
        m = sm.OLS(y, X).fit()
        p = m.params
        return {"region": region, "freq": freq, "n": int(m.nobs), "r2": round(m.rsquared, 3),
                "alpha": round(float(p["const"]), 5), "ccy": ccy,
                "loadings": {f: round(float(p[c]), 3) for f, c in zip(FACTORS, FF_COLS)}}
    except Exception as e:
        return {"error": f"{type(e).__name__}: {str(e)[:90]}", "region": region}


def compute_all(bases=None, write=True) -> dict:
    bases = bases or list(REGION_MAP)
    out = {}
    for b in bases:
        out[b] = compute_one(b)
        r = out[b]
        print(f"  {b:<6} {r.get('region','?'):<10} " +
              (f"R2={r['r2']} " + " ".join(f"{k}{v:+.2f}" for k, v in r['loadings'].items())
               if "loadings" in r else f"[{r.get('error')}]"), flush=True)
    if write:
        CACHE.write_text(json.dumps(out, indent=1))
    return out


def load_cached() -> dict:
    return json.loads(CACHE.read_text()) if CACHE.exists() else {}


def block_aggregate(positions: list, us_loadings: dict) -> dict:
    """Group the whole book into factor BLOCKS (US + each foreign region) and report the
    weighted-average FF5 vector per block + each block's $ share. positions: [{sym, mv}].
    us_loadings: {sym: {mkt_rf,...}} for US names (from factor_drift). Foreign names use the
    regional cache. This is the household 'factor vector' — orthogonal blocks side by side."""
    reg = load_cached()
    blocks = {}
    for p in positions:
        s, mv = p["sym"], p["mv"]
        if s in reg and "loadings" in reg[s]:
            region, ld = reg[s]["region"], reg[s]["loadings"]
        elif s in us_loadings:
            region, ld = "US", us_loadings[s]
        else:
            region, ld = "UNMAPPED", None
        b = blocks.setdefault(region, {"gross": 0.0, "acc": {f: 0.0 for f in FACTORS}})
        b["gross"] += abs(mv)
        if ld:
            for f in FACTORS:
                b["acc"][f] += mv * ld.get(f, 0.0)
    total = sum(b["gross"] for b in blocks.values()) or 1.0
    out = {}
    for region, b in blocks.items():
        g = b["gross"] or 1.0
        out[region] = {"gross": round(b["gross"]), "weight": round(b["gross"] / total, 4),
                       "vector": {f: round(b["acc"][f] / g, 3) for f in FACTORS}}
    return out


if __name__ == "__main__":
    bases = sys.argv[1:] or None
    print("computing regional loadings (Ken French regional sets, USD basis)...")
    compute_all(bases)
    print(f"cached -> {CACHE}")
