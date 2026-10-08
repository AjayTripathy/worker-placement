"""PURE template logic for the 0DTE sleeve — no broker, no clock, no files.

A chain snapshot is a list of rows: {"strike", "right" ("P"/"C"), "bid", "ask", "delta"} (delta
signed; puts negative). Every fill is at the TOUCH: we SELL at the bid and BUY at the ask. The mid
is never used for a fill — the 0DTE mid is the most common backtest lie.

Prices are per-share; dollars = price * MULTIPLIER * contracts.
"""
from __future__ import annotations

import math

from desk.odte.doctrine import (MULTIPLIER, MIN_CREDIT, MAX_LEG_SPREAD_FRAC, TEMPLATES)


def _mid(r: dict) -> float:
    return (float(r["bid"]) + float(r["ask"])) / 2.0


def _ok_quote(r: dict | None) -> bool:
    if not r:
        return False
    try:
        b, a = float(r["bid"]), float(r["ask"])
    except (TypeError, ValueError, KeyError):
        return False
    return a > 0 and b >= 0 and a >= b and not (math.isnan(a) or math.isnan(b))


def pick_short(rows: list[dict], right: str, target_delta: float) -> dict | None:
    """The quoted strike whose |delta| is nearest the target (ties -> further OTM)."""
    cands = [r for r in rows if r.get("right") == right and _ok_quote(r) and r.get("delta") is not None]
    if not cands:
        return None
    key = (lambda r: (abs(abs(float(r["delta"])) - target_delta), -float(r["strike"]) if right == "P" else float(r["strike"])))
    return min(cands, key=key)


def row_at(rows: list[dict], right: str, strike: float) -> dict | None:
    for r in rows:
        if r.get("right") == right and abs(float(r["strike"]) - strike) < 1e-6:
            return r
    return None


def build_condor(rows: list[dict], short_delta: float, wing: float) -> dict:
    """Iron condor at the touch. Returns {"ok", "why", "legs", "credit", "max_loss_usd", ...}.
    legs: sp (short put), lp (long put), sc (short call), lc (long call)."""
    sp = pick_short(rows, "P", short_delta); sc = pick_short(rows, "C", short_delta)
    if not sp or not sc:
        return {"ok": False, "why": "no quoted strike near target delta"}
    lp = row_at(rows, "P", float(sp["strike"]) - wing); lc = row_at(rows, "C", float(sc["strike"]) + wing)
    if not (_ok_quote(lp) and _ok_quote(lc)):
        return {"ok": False, "why": "wing strike unquoted"}
    if float(sc["strike"]) <= float(sp["strike"]):
        return {"ok": False, "why": "call short at/below put short (spot too close / delta map broken)"}
    legs = {"sp": sp, "lp": lp, "sc": sc, "lc": lc}
    for k, r in legs.items():
        m = _mid(r)
        if m > 0 and (float(r["ask"]) - float(r["bid"])) / m > MAX_LEG_SPREAD_FRAC and (float(r["ask"]) - float(r["bid"])) > 0.05:
            return {"ok": False, "why": f"illiquid leg {k} ({r['strike']}{r['right']} {r['bid']}/{r['ask']})"}
    credit = (float(sp["bid"]) - float(lp["ask"])) + (float(sc["bid"]) - float(lc["ask"]))
    credit = round(credit, 2)
    if credit < MIN_CREDIT:
        return {"ok": False, "why": f"credit {credit:.2f} < MIN_CREDIT {MIN_CREDIT}", "credit": credit}
    out = {"ok": True, "why": "", "credit": credit, "max_loss_usd": round((wing - credit) * MULTIPLIER, 2),
           "legs": {k: {"strike": float(r["strike"]), "right": r["right"], "bid": float(r["bid"]), "ask": float(r["ask"]),
                        "delta": r.get("delta"), "conId": r.get("conId")} for k, r in legs.items()},
           "short_put": float(sp["strike"]), "short_call": float(sc["strike"]), "wing": wing}
    return out


def cost_to_close(legs: dict, rows: list[dict]) -> float | None:
    """What it costs NOW to buy back the condor at the touch (buy shorts at ask, sell wings at bid)."""
    sp = row_at(rows, "P", legs["sp"]["strike"]); lp = row_at(rows, "P", legs["lp"]["strike"])
    sc = row_at(rows, "C", legs["sc"]["strike"]); lc = row_at(rows, "C", legs["lc"]["strike"])
    if not all(_ok_quote(r) for r in (sp, lp, sc, lc)):
        return None
    return round((float(sp["ask"]) - float(lp["bid"])) + (float(sc["ask"]) - float(lc["bid"])), 2)


def settle(legs: dict, settlement: float) -> float:
    """Cash settlement value of the SHORT condor at expiry (what we owe, per share)."""
    put_loss = min(max(0.0, legs["sp"]["strike"] - settlement), legs["sp"]["strike"] - legs["lp"]["strike"])
    call_loss = min(max(0.0, settlement - legs["sc"]["strike"]), legs["lc"]["strike"] - legs["sc"]["strike"])
    return round(put_loss + call_loss, 2)


def manage(pos: dict, rows: list[dict], now_et: tuple[int, int], stop_mult: float, time_exit_et: tuple[int, int]) -> dict:
    """HOLD / CLOSE_STOP / CLOSE_TIME. pos = {"credit", "legs"}."""
    if now_et >= time_exit_et:
        c = cost_to_close(pos["legs"], rows)
        return {"action": "CLOSE_TIME", "cost": c}
    c = cost_to_close(pos["legs"], rows)
    if c is None:
        return {"action": "HOLD", "cost": None, "note": "no quote"}
    if c >= stop_mult * float(pos["credit"]):
        return {"action": "CLOSE_STOP", "cost": c}
    return {"action": "HOLD", "cost": c}


def pnl_usd(credit: float, exit_cost: float, contracts: int = 1) -> float:
    return round((credit - exit_cost) * MULTIPLIER * contracts, 2)


def entry_allowed(template: str, ctx: dict) -> tuple[bool, str]:
    """ctx: {"now_et": (h,m), "is_event_day", "first30_range" (SPX hi-lo / open), "vix1d_open", "vix1d_now"}."""
    t = TEMPLATES[template]
    if not (tuple(t["entry_et"]) <= tuple(ctx["now_et"]) <= tuple(t["entry_close_et"])):
        return False, "outside entry window"
    if t["blackout"] and ctx.get("is_event_day"):
        return False, "event-day blackout"
    reg = t.get("regime")
    if reg:
        fr = ctx.get("first30_range")
        if fr is None or fr > reg["first30_range_max"]:
            return False, f"first-30 range {fr} > {reg['first30_range_max']}"
        if reg.get("vix1d_compressing"):
            vo, vn = ctx.get("vix1d_open"), ctx.get("vix1d_now")
            if vo is None or vn is None or vn > vo:
                return False, f"VIX1D not compressing ({vo} -> {vn})"
    return True, ""


def bs_delta(spot: float, strike: float, t_years: float, iv: float, right: str) -> float:
    """Fallback delta when the feed carries no model greeks (flagged in the capture row)."""
    if t_years <= 0 or iv <= 0 or spot <= 0:
        intrinsic = (spot > strike) if right == "C" else (spot < strike)
        return (1.0 if intrinsic else 0.0) * (1 if right == "C" else -1)
    d1 = (math.log(spot / strike) + 0.5 * iv * iv * t_years) / (iv * math.sqrt(t_years))
    n = 0.5 * (1 + math.erf(d1 / math.sqrt(2)))
    return n if right == "C" else n - 1.0
