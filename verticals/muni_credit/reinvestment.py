"""reinvestment — the rate risk a hold-to-maturity investor CANNOT hold through.

Holding to maturity neutralizes PRICE/rate risk (each rung returns par), but the coupons and the returned
principal still have to be redeployed at the THEN-prevailing rate. Two pieces:

  PER-BOND: when does principal likely come back? A bond marked at/above its call price with a NEAR call is
    likely CALLED (the issuer refinances) -> principal returns at the call date; otherwise at maturity.
    Tag 'reinvest-soon' when that's within ~3y. (Low-coupon DISCOUNT bonds carry LESS coupon-reinvestment
    risk — more of their return is the locked-in pull-to-par accretion, not future-rate-dependent coupons.)

  PORTFOLIO: a cash-back CALENDAR (par returning by year) + a falling-rate STRESS. The scenario that
    actually hurts is rates FALLING — calls fire exactly when rates drop (refinancing), handing cash back
    at the worst time to reinvest. Reinvestment risk and call risk are correlated, not independent.

  Note: reinvestment risk and price/duration risk are OPPOSITE-signed (rising rates hurt price, help
  reinvestment; falling rates the reverse). The horizon where they offset is duration — the immunization
  identity. A laddered book is the standard mitigant (only a fraction reinvests in any one year).
"""
import datetime, statistics as st
from collections import defaultdict

SETTLE = datetime.date(2026, 6, 19)


def _call_year(ncd):
    try:
        p = ncd.split("/")[-1]
        return int(p if len(p) == 4 else "20" + p)
    except Exception:
        return None


def principal_return(rec):
    """(year, kind) — when this bond's principal most likely returns to be reinvested."""
    mat_yr = int(rec["maturity"][:4])
    ncd = rec.get("next_call_date"); px = rec.get("px") or 100; cp = rec.get("call_price") or 100
    cyr = _call_year(ncd) if ncd else None
    if cyr and rec.get("call_risk") in ("HARD", "SOFT"):
        # likely-called only if it's economic to call: priced at/above the call price (premium/par) AND near.
        # a DISCOUNT bond's call is optional and unlikely -> principal stays to maturity (but optionality noted).
        if px >= cp - 1.0 and cyr <= SETTLE.year + 4:
            return cyr, "call(likely)"
    return mat_yr, "maturity"


def reinvest_flag(rec):
    yr, kind = principal_return(rec)
    fields = {"principal_return_year": yr, "principal_return_kind": kind}
    flags = []
    if "call" in kind and yr - SETTLE.year <= 3:
        flags.append(f"reinvest-soon:{kind}@{yr}")   # soft — concentrated near-term reinvestment
    return fields, flags


def calendar(holds):
    """{year: par returning} from expected calls + maturities (par-weighted; defaults par=1)."""
    cal = defaultdict(float)
    for r in holds:
        yr, _ = principal_return(r)
        cal[yr] += (r.get("par") or 1)
    return dict(sorted(cal.items()))


def concentration(holds):
    """The single year in which the most principal returns — a ladder should be even; a bunch is a
    concentrated reinvestment bet on one year's rates."""
    cal = calendar(holds); tot = sum(cal.values()) or 1
    peak = max(cal, key=cal.get)
    return {"peak_year": peak, "peak_share_pct": round(cal[peak] / tot * 100), "n_years": len(cal)}


def stress(holds, shock_bps=150, horizon=5):
    """Illustrative falling-rate reinvestment stress: the share of par whose principal returns within
    `horizon` years and must be reinvested at (book YTW - shock). Returns a summary dict."""
    ytws = [r.get("ytw") or 0 for r in holds if r.get("ytw")]
    base = st.mean(ytws) if ytws else 0.0
    tot = sum((r.get("par") or 1) for r in holds) or 1
    early = sum((r.get("par") or 1) for r in holds if principal_return(r)[0] - SETTLE.year <= horizon)
    reinv = max(0.0, base - shock_bps / 10000)
    w = early / tot
    # blended go-forward yield: the early-returning fraction earns the lower reinvested rate, rest holds base
    blended = base * (1 - w) + reinv * w
    return {"book_ytw_pct": round(base * 100, 2),
            "reinvest_within_%dy_pct" % horizon: round(w * 100),
            "reinvest_rate_after_shock_pct": round(reinv * 100, 2),
            "blended_goforward_ytw_pct": round(blended * 100, 2),
            "reinvest_drag_bps": round((base - blended) * 10000)}
