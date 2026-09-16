"""ai_credit_basis — credit-versus-equity divergence member of the AI-capex break ensemble.

Sibling of desk.models.ai_capex_break (the mechanism member). Thesis: credit leads equity
at regime turns — ABX started widening Feb-07 while the S&P made its high Oct-07 (~9mo
lead). The tradeable observable is the BASIS: AI-complex equity strength coinciding with
QUIET deterioration in AI-exposed credit. Neither leg alone is the signal; the divergence is.

LEGS (each proxy labeled by what it can and cannot see):

1. EQUITY: SOXX + an equal-weight AI basket (NVDA AVGO ORCL VRT SMCI). 6m total return and
   60d log-price slope; the standardized series is the rolling 3m (63d) log return.

2. CREDIT — best-effort ladder, honest about resolution:
   a. BROAD spread-direction proxies: LQD-minus-IEF and HYG-minus-(IEI/SHY blend) excess
      total return over 3m/6m. Duration-matched, so the excess return ~= -(spread change) x
      spread-duration: positive excess = tightening. BROAD IG/HY only — an AI-specific
      widening inside a placid aggregate is invisible here.
   b. AI-ADJACENT single names, equity-implied (no yfinance bond series exists for either):
      Merton-style distance-to-default DIRECTION for ORCL and CRWV — debt held at latest
      reported level, equity value and 90d realized vol move daily; DD falling = implied
      spread widening. Direction-only: no recovery/term-structure, absolute DD not meaningful.
      CRWV equity itself (levered GPU landlord, take-or-pay book) is the purest listed
      AI-credit canary: its 3m trend + vol change enter as a credit-health component.
   c. FINRA TRACE (ORCL long bond): ONE unauthenticated attempt, skipped on any friction.

3. BASIS: z(equity 3m trend) - z(credit-health 3m trend), each standardized on its own full
   history (>=1y required). Large POSITIVE z = equity strong while credit deteriorates =
   the 2007 signature. GREEN |z|<1, AMBER 1<=z<2, RED z>=2 — RED only if the credit leg
   includes at least one AI-specific proxy (broad IG/HY can't convict the AI complex).

P(break) mapping is conservative: GREEN -> null (defer to the mechanism member's base
rates ~0.30/0.60); AMBER/RED -> elevated, with the ~9-month ABX lead setting the horizon
(a RED basis today implies the credit event lands well inside the 2027 window).

    python3 -m desk.models.ai_credit_basis
"""
from __future__ import annotations

import json
import math
import datetime as dt
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

OUT_PATH = Path(__file__).resolve().parents[1] / "data" / "ai_ensemble" / "credit_basis.json"

EQ_BASKET = ["NVDA", "AVGO", "ORCL", "VRT", "SMCI"]
TICKERS = ["SOXX"] + EQ_BASKET + ["LQD", "IEF", "HYG", "IEI", "SHY", "CRWV"]
# Exchange-listed baby-bond / ETD probes for the AI-adjacent names (none known to exist;
# probed so the absence is a checked fact, not an assumption):
BABY_BOND_PROBES = ["ORCL-PA", "CRWV-PA", "CRWVZ", "ORCLL"]

W3M, W6M, WVOL, WSLOPE = 63, 126, 90, 60
MIN_HIST = 252          # min obs to standardize a series on its own history
ABX_LEAD_NOTE = ("mapping: ABX widened ~9mo ahead of the equity top in 2007; a fired basis "
                 "today puts the modeled credit event ~2-4q out")


# ── data ──────────────────────────────────────────────────────────────────────

def fetch_prices() -> pd.DataFrame:
    import yfinance as yf
    px = yf.download(TICKERS, period="5y", auto_adjust=True, progress=False)["Close"]
    return px.dropna(how="all")


def zscore_latest(series: pd.Series, min_hist: int = MIN_HIST):
    """z of the latest obs vs the series' own full history; None if too short."""
    s = series.dropna()
    if len(s) < min_hist or s.std(ddof=0) == 0:
        return None
    return float((s.iloc[-1] - s.mean()) / s.std(ddof=0))


def r63(prices: pd.Series) -> pd.Series:
    """Rolling 3m (63d) log total return — the standardized trend series for every leg."""
    return np.log(prices / prices.shift(W3M))


# ── equity leg ────────────────────────────────────────────────────────────────

def equity_leg(px: pd.DataFrame) -> dict:
    out = {}
    basket = px[EQ_BASKET].dropna()
    basket_ew = np.exp(np.log(basket / basket.iloc[0]).mean(axis=1))  # equal-weight TR index
    for name, s in (("SOXX", px["SOXX"].dropna()), ("ai_basket_ew", basket_ew)):
        if len(s) < W6M + 1:
            out[name] = {"error": "insufficient history"}
            continue
        logp = np.log(s.iloc[-WSLOPE:])
        slope = float(np.polyfit(np.arange(WSLOPE), logp, 1)[0])
        out[name] = {
            "tr_6m_pct": round(100 * float(s.iloc[-1] / s.iloc[-W6M - 1] - 1), 1),
            "slope_60d_ann_pct": round(100 * slope * 252, 1),
            "z_3m_trend": zscore_latest(r63(s)),
        }
    zs = [v["z_3m_trend"] for v in out.values() if isinstance(v.get("z_3m_trend"), float)]
    out["composite_z"] = round(float(np.mean(zs)), 2) if zs else None
    return out


# ── credit leg (a): broad ETF excess return ───────────────────────────────────

def broad_credit_leg(px: pd.DataFrame) -> dict:
    """Duration-matched excess TR ~= spread-change direction. BROAD market, not AI-specific."""
    out = {}
    pairs = {
        "LQD_vs_IEF": (px["LQD"], px["IEF"], "IG spread direction, ~7y duration-matched"),
        "HYG_vs_IEI_SHY": (px["HYG"], np.exp(0.5 * (np.log(px["IEI"] / px["IEI"].iloc[0])
                                                    + np.log(px["SHY"] / px["SHY"].iloc[0]))),
                           "HY spread direction, ~4y blend-matched"),
    }
    zs = []
    for name, (credit, tsy, label) in pairs.items():
        both = pd.concat([credit, tsy], axis=1).dropna()
        if len(both) < W6M + 1:
            out[name] = {"error": "insufficient history"}
            continue
        c, t = both.iloc[:, 0], both.iloc[:, 1]
        ex = r63(c) - r63(t)                       # 3m excess log TR
        ex6 = (np.log(c / c.shift(W6M)) - np.log(t / t.shift(W6M))).iloc[-1]
        z = zscore_latest(ex)
        out[name] = {
            "measures": f"{label}; positive excess = tightening. BROAD-market proxy: "
                        "cannot see AI-specific widening inside a calm aggregate.",
            "excess_tr_3m_pct": round(100 * float(ex.iloc[-1]), 2),
            "excess_tr_6m_pct": round(100 * float(ex6), 2),
            "z_3m_health": z,                      # health: tightening positive
        }
        if z is not None:
            zs.append(z)
    out["composite_z"] = round(float(np.mean(zs)), 2) if zs else None
    return out


# ── credit leg (b): equity-implied single-name stress ─────────────────────────

def _total_debt(tkr) -> float | None:
    try:
        bs = tkr.get_balance_sheet()
        for row in ("TotalDebt", "Total Debt"):
            if row in bs.index:
                v = bs.loc[row].dropna()
                if len(v):
                    return float(v.iloc[0])
    except Exception:
        pass
    try:
        v = tkr.info.get("totalDebt")
        return float(v) if v else None
    except Exception:
        return None


def merton_direction(px: pd.DataFrame, sym: str) -> dict:
    """Direction-only Merton DD: debt frozen at latest reported, E and sigma move daily.
    DD falling = implied spread widening. Not a level model — no recovery, no term structure."""
    import yfinance as yf
    s = px[sym].dropna()
    if len(s) < WVOL + W3M + 5:
        return {"error": f"insufficient price history ({len(s)}d)"}
    tkr = yf.Ticker(sym)
    debt = _total_debt(tkr)
    try:
        mcap = float(tkr.fast_info["market_cap"])
    except Exception:
        mcap = None
    if not debt or not mcap:
        return {"error": "missing debt or market cap"}
    shares = mcap / float(s.iloc[-1])
    E = s * shares
    sig_e = np.log(s).diff().rolling(WVOL).std() * math.sqrt(252)
    A = E + debt
    sig_a = sig_e * E / A
    dd = np.log(A / debt) / sig_a
    d_dd = dd - dd.shift(W3M)                      # 3m change in DD
    z = zscore_latest(d_dd, min_hist=min(MIN_HIST, max(150, len(d_dd.dropna()))))
    return {
        "measures": "equity-implied credit stress DIRECTION (Merton DD, debt frozen at latest "
                    "reported): DD falling = spread widening. AI-specific but equity-derived — "
                    "partially circular with the equity leg, weight accordingly.",
        "total_debt_bn": round(debt / 1e9, 1),
        "leverage_D_over_A": round(float(debt / A.iloc[-1]), 3),
        "vol_90d_ann_pct": round(100 * float(sig_e.iloc[-1]), 1),
        "vol_90d_chg_3m_pp": round(100 * float(sig_e.iloc[-1] - sig_e.iloc[-1 - W3M]), 1),
        "dd_now": round(float(dd.iloc[-1]), 1),
        "dd_chg_3m": round(float(d_dd.iloc[-1]), 2),
        "z_3m_health": round(z, 2) if z is not None else None,  # DD up = health up
        "history_days": int(len(dd.dropna())),
    }


def crwv_canary(px: pd.DataFrame) -> dict:
    """CRWV equity as the purest listed AI-credit canary (levered GPU landlord: equity is a
    thin first-loss strip on a take-or-pay loan book; equity down + vol up = credit stress)."""
    if "CRWV" not in px.columns:
        return {"error": "CRWV not served by yfinance"}
    s = px["CRWV"].dropna()
    if len(s) < WVOL + W3M + 5:
        return {"error": f"insufficient history ({len(s)}d since IPO)"}
    sig = np.log(s).diff().rolling(WVOL).std() * math.sqrt(252)
    trend = r63(s)
    z_tr = zscore_latest(trend, min_hist=120)      # short post-IPO history: 120d floor
    z_vol = zscore_latest((sig - sig.shift(W3M)), min_hist=120)
    z_health = None
    if z_tr is not None and z_vol is not None:
        z_health = round(0.5 * z_tr - 0.5 * z_vol, 2)   # price up / vol down = healthy
    return {
        "measures": "levered-neocloud equity canary: 3m trend minus 3m vol change. Short "
                    "post-IPO history — z standardized on its own limited sample.",
        "tr_3m_pct": round(100 * float(s.iloc[-1] / s.iloc[-W3M - 1] - 1), 1),
        "tr_6m_pct": (round(100 * float(s.iloc[-1] / s.iloc[-W6M - 1] - 1), 1)
                      if len(s) > W6M else None),
        "vol_90d_ann_pct": round(100 * float(sig.iloc[-1]), 1),
        "vol_90d_chg_3m_pp": round(100 * float(sig.iloc[-1] - sig.iloc[-1 - W3M]), 1),
        "z_3m_health": z_health,
        "history_days": int(len(s)),
    }


# ── credit leg (b/c): probes ──────────────────────────────────────────────────

def probe_baby_bonds() -> dict:
    import logging
    import yfinance as yf
    logging.getLogger("yfinance").setLevel(logging.CRITICAL)
    found, missing = {}, []
    for sym in BABY_BOND_PROBES:
        try:
            p = yf.Ticker(sym).fast_info["last_price"]
            if p and not math.isnan(p):
                found[sym] = round(float(p), 2)
                continue
        except Exception:
            pass
        missing.append(sym)
    return {"found": found, "not_found": missing}


def probe_trace_orcl() -> dict:
    """ONE unauthenticated attempt at FINRA TRACE via morningstar; skip on any friction."""
    url = ("https://finra-markets.morningstar.com/bondSearch.jsp?count=5&searchtype=B"
           "&query=%7B%22Keywords%22%3A%5B%7B%22Name%22%3A%22debtOrAssetClass%22%2C%22"
           "Value%22%3A%223%2C6%22%7D%2C%7B%22Name%22%3A%22issuerName%22%2C%22Value%22"
           "%3A%22Oracle%22%7D%5D%7D")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0",
                                                   "Referer": "https://finra-markets.morningstar.com/BondCenter/Results.jsp"})
        with urllib.request.urlopen(req, timeout=8) as r:
            body = r.read(4000).decode("utf-8", "ignore")
        if '"yield"' in body.lower() or '"B":' in body:
            return {"status": "responded", "raw_head": body[:300]}
        return {"status": "no_usable_payload", "note": "endpoint answered but no yield fields "
                                                       "without a session cookie; skipped"}
    except Exception as e:
        return {"status": "skipped", "note": f"friction ({type(e).__name__}); not pursued per spec"}


# ── basis ─────────────────────────────────────────────────────────────────────

def compute_basis(eq: dict, broad: dict, singles: dict) -> dict:
    z_eq = eq.get("composite_z")
    credit_zs, ai_specific = [], []
    if broad.get("composite_z") is not None:
        credit_zs.append(broad["composite_z"])
    for name, d in singles.items():
        z = d.get("z_3m_health")
        if isinstance(z, (int, float)):
            credit_zs.append(z)
            ai_specific.append(name)
    if z_eq is None or not credit_zs:
        return {"state": "DATA_MISSING", "basis_z": None, "ai_specific_proxies": ai_specific}
    z_credit = float(np.mean(credit_zs))
    basis_z = round(z_eq - z_credit, 2)
    if abs(basis_z) < 1:
        state = "GREEN"
    elif basis_z >= 2 and ai_specific:
        state = "RED"
    else:
        state = "AMBER"
    capped = basis_z >= 2 and not ai_specific
    return {"state": state, "basis_z": basis_z, "z_equity": round(z_eq, 2),
            "z_credit_health": round(z_credit, 2), "ai_specific_proxies": ai_specific,
            "capped_at_amber": capped}


def probabilities(basis: dict) -> tuple[float | None, float | None, str]:
    """Conservative mapping. GREEN defers to the mechanism member's base rates (null here).
    AMBER/RED elevate with the ~9-month ABX lead as the horizon anchor."""
    st, z = basis.get("state"), basis.get("basis_z")
    if st == "RED":
        return 0.55, 0.75, "RED basis + 9mo ABX lead -> credit event modeled inside 2027"
    if st == "AMBER" and z is not None and z > 0:
        return 0.35, 0.65, "positive AMBER: mild bump over mechanism-member base (~0.30/0.60)"
    if st == "AMBER":
        return None, None, "AMBER on a NEGATIVE basis (credit strong vs equity) — not the 2007 signature; defer to base rates"
    return None, None, "no divergence fired; this member defers to base rates"


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    asof = dt.date.today().isoformat()
    notes = []
    print(f"=== AI CREDIT-EQUITY BASIS ({asof}) ===\n")
    try:
        px = fetch_prices()
    except Exception as e:
        px = None
        notes.append(f"price fetch failed: {e}")

    eq = broad = {}
    singles: dict[str, dict] = {}
    if px is not None:
        eq = equity_leg(px)
        broad = broad_credit_leg(px)
        for sym, fn in (("ORCL_merton", lambda: merton_direction(px, "ORCL")),
                        ("CRWV_merton", lambda: merton_direction(px, "CRWV")),
                        ("CRWV_canary", lambda: crwv_canary(px))):
            try:
                singles[sym] = fn()
            except Exception as e:
                singles[sym] = {"error": f"{type(e).__name__}: {e}"}

    baby = probe_baby_bonds()
    if not baby["found"]:
        notes.append(f"no exchange-listed ORCL/CRWV baby bonds/ETDs on yfinance (probed {baby['not_found']})")
    trace = probe_trace_orcl()
    if trace["status"] != "responded":
        notes.append(f"FINRA TRACE ORCL: {trace['status']} — {trace.get('note', '')}")

    basis = compute_basis(eq, broad, singles)
    if basis.get("capped_at_amber"):
        notes.append("z>=2 but no AI-specific credit proxy resolved — capped at AMBER: broad "
                     "IG/HY divergence alone cannot convict the AI complex")
    for name, d in singles.items():
        if "error" in d:
            notes.append(f"{name}: {d['error']}")
    notes.append("credit leg limits: (a) is broad-market; (b) is equity-derived and partially "
                 "circular with the equity leg; no true AI single-name SPREAD series is free")
    notes.append(ABX_LEAD_NOTE)

    p27, p28, why = probabilities(basis)
    reading = {"equity": eq, "credit_broad": broad, "credit_singles": singles,
               "baby_bond_probe": baby, "trace_probe": {k: v for k, v in trace.items() if k != "raw_head"},
               "basis": basis}
    payload = {"member": "credit_equity_basis", "asof": asof, "state": basis.get("state", "DATA_MISSING"),
               "reading": reading, "P_break_by_2027": p27, "P_break_by_2028": p28,
               "prob_rationale": why, "notes": notes}

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(payload, indent=1))

    # readable summary
    print("-- equity leg --")
    for k in ("SOXX", "ai_basket_ew"):
        v = eq.get(k, {})
        if "error" not in v and v:
            print(f"  {k:14} 6m TR {v['tr_6m_pct']:+6.1f}%  60d slope {v['slope_60d_ann_pct']:+6.1f}%/yr  z(3m) {v['z_3m_trend']:+.2f}")
    print("\n-- credit leg (broad ETF excess TR; +ve = tightening) --")
    for k, v in broad.items():
        if isinstance(v, dict) and "error" not in v:
            print(f"  {k:14} 3m {v['excess_tr_3m_pct']:+.2f}%  6m {v['excess_tr_6m_pct']:+.2f}%  z {v['z_3m_health']:+.2f}")
    print("\n-- credit leg (AI-specific, equity-implied) --")
    for k, v in singles.items():
        z = v.get("z_3m_health")
        z_s = f"{z:+.2f}" if isinstance(z, (int, float)) else "n/a"
        if "error" in v:
            print(f"  {k:14} UNAVAILABLE: {v['error']}")
        elif "dd_now" in v:
            print(f"  {k:14} DD {v['dd_now']:.1f} (3m chg {v['dd_chg_3m']:+.2f})  vol {v['vol_90d_ann_pct']:.0f}% "
                  f"({v['vol_90d_chg_3m_pp']:+.1f}pp)  lev {v['leverage_D_over_A']:.2f}  z {z_s}")
        else:
            print(f"  {k:14} 3m TR {v['tr_3m_pct']:+.1f}%  vol {v['vol_90d_ann_pct']:.0f}% "
                  f"({v['vol_90d_chg_3m_pp']:+.1f}pp)  z {z_s}")
    print(f"\n-- basis --\n  z_equity {basis.get('z_equity')}  z_credit_health {basis.get('z_credit_health')}"
          f"  basis_z {basis.get('basis_z')}  ->  STATE: {basis.get('state')}")
    print(f"  P(break by 2027) {p27}   P(break by 2028) {p28}   [{why}]")
    print("\n-- notes --")
    for n in notes:
        print(f"  * {n}")
    print(f"\nwrote {OUT_PATH}")


if __name__ == "__main__":
    main()
