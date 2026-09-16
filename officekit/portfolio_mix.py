"""portfolio_mix — the stock/bond/cash split of the marketable book, and the
return + risk of any target mix. Shared by the growth calculator and the risk
officer so both speak one number.

House priors (first-pass, refine from realized returns):
  stocks  ~7.0% nominal, ~16% vol   bonds ~4.0%, ~5% vol   cash ~4.0%, ~0.5% vol
  stock/bond correlation ~0.15.
"""
from __future__ import annotations

import math

STOCK_RET, BOND_RET, CASH_RET = 0.070, 0.040, 0.040
STOCK_VOL, BOND_VOL, CASH_VOL = 0.16, 0.05, 0.005
SB_CORR = 0.15

_STOCKS = ("public_equity", "direct_index", "single_name_equity", "alpha_market_neutral")
_BONDS = ("fixed_income", "municipal_credit")
_CASH = ("cash",)


def current_mix(m):
    """{stocks, bonds, cash} dollar values + pct of the marketable book."""
    s = b = c = 0.0
    for a in (m or {}).get("assets", []):
        v = a["value"]
        if a["category"] in _STOCKS:
            s += v
        elif a["category"] in _BONDS:
            b += v
        elif a["category"] in _CASH:
            c += v
    s, b, c = max(s, 0), max(b, 0), max(c, 0)
    tot = s + b + c
    pct = (lambda x: round(x / tot * 100, 1) if tot else 0.0)
    sp = pct(s)
    bp = min(pct(b), 100 - sp)
    cp = round(100 - sp - bp, 1) if tot else 0.0
    return {"stocks": s, "bonds": b, "cash": c, "total": tot,
            "stocks_pct": sp, "bonds_pct": bp, "cash_pct": cp}


def mix_stats(stocks_pct, bonds_pct, cash_pct=None):
    """Expected return, volatility and a rough 1-in-20 drawdown for a mix (percents)."""
    mix = validate_mix(stocks_pct, bonds_pct, cash_pct)
    ws, wb, wc = (mix[k] / 100.0 for k in ("stocks_pct", "bonds_pct", "cash_pct"))
    ret = ws * STOCK_RET + wb * BOND_RET + wc * CASH_RET
    var = ((ws * STOCK_VOL) ** 2 + (wb * BOND_VOL) ** 2 + (wc * CASH_VOL) ** 2
           + 2 * ws * wb * STOCK_VOL * BOND_VOL * SB_CORR)
    vol = math.sqrt(max(var, 0))
    return {"exp_return": ret, "vol": vol, "drawdown_1in20": min(0.95, 1.645 * vol),
            "stocks_pct": round(ws * 100, 1), "bonds_pct": round(wb * 100, 1),
            "cash_pct": round(wc * 100, 1)}


def target_mix(answers_or_data, m=None):
    """The saved target mix, or the current mix as the default starting point."""
    tm = (answers_or_data or {}).get("target_mix")
    if isinstance(tm, dict) and tm.get("stocks_pct") is not None:
        try:
            return validate_mix(tm["stocks_pct"], tm["bonds_pct"], tm.get("cash_pct"))
        except (ValueError, TypeError, KeyError):
            pass  # invalid legacy target stays on disk until the user reviews and saves
    cur = current_mix(m) if m else {"stocks_pct": 60, "bonds_pct": 30, "cash_pct": 10}
    sp = min(100, cur["stocks_pct"])
    bp = min(100 - sp, cur["bonds_pct"])
    return validate_mix(sp, bp)


def validate_mix(stocks_pct, bonds_pct, cash_pct=None):
    """A target is a fully allocated, unlevered mix. Reject impossible inputs."""
    if any(isinstance(v, bool) for v in (stocks_pct, bonds_pct, cash_pct)):
        raise ValueError("Enter numeric percentages for stocks and bonds")
    try:
        sp, bp = float(stocks_pct), float(bonds_pct)
        cp = 100 - sp - bp if cash_pct is None else float(cash_pct)
    except (TypeError, ValueError):
        raise ValueError("Enter numeric percentages for stocks and bonds")
    if any(not math.isfinite(v) or v < -0.000001 or v > 100 for v in (sp, bp, cp)) or sp + bp > 100.000001 or abs(sp + bp + cp - 100) > 0.000001:
        raise ValueError("Stocks, bonds and cash must total 100%, with no negative allocation")
    return {"stocks_pct": sp, "bonds_pct": bp, "cash_pct": round(max(0, 100 - sp - bp), 4)}
